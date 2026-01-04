"""Tests for task management API routes."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from metaqore.api.app import create_api_app
from metaqore.config import GovernanceMode, MetaQoreConfig


def _build_test_client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "tasks_api.db"
    config = MetaQoreConfig(
        governance_mode=GovernanceMode.PLAYGROUND,
        storage_dsn=f"sqlite:///{db_path}",
        max_parallel_branches=3,
    )
    return TestClient(create_api_app(config))


def _create_project(client: TestClient) -> str:
    response = client.post("/api/v1/projects", json={"name": "Tasks Host"})
    return response.json()["data"]["id"]


def test_task_crud_flow(tmp_path) -> None:
    client = _build_test_client(tmp_path)
    project_id = _create_project(client)

    list_response = client.get("/api/v1/tasks", params={"project_id": project_id})
    assert list_response.status_code == 200
    list_data = list_response.json()["data"]
    assert list_data["project_id"] == project_id
    assert list_data["tasks"] == []
    assert list_data["total"] == 0
    assert list_data["page"] == 1
    assert list_data["page_size"] == 25
    assert list_data["filters"] == {}

    create_payload = {
        "project_id": project_id,
        "title": "Draft prompts",
        "assigned_to": "agent-7",
        "metadata": {"priority": "medium"},
    }
    create_response = client.post("/api/v1/tasks", json=create_payload)
    assert create_response.status_code == 201
    task_id = create_response.json()["data"]["id"]

    get_response = client.get(f"/api/v1/tasks/{task_id}")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["title"] == "Draft prompts"

    update_payload = {"status": "in_progress", "title": "Draft prompts v2"}
    update_response = client.patch(f"/api/v1/tasks/{task_id}", json=update_payload)
    assert update_response.status_code == 200
    assert update_response.json()["data"]["status"] == "in_progress"

    delete_response = client.delete(f"/api/v1/tasks/{task_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["id"] == task_id

    missing_response = client.get(f"/api/v1/tasks/{task_id}")
    assert missing_response.status_code == 404


def test_task_update_requires_fields(tmp_path) -> None:
    client = _build_test_client(tmp_path)
    project_id = _create_project(client)
    task_id = client.post(
        "/api/v1/tasks",
        json={"project_id": project_id, "title": "Need changes"},
    ).json()["data"]["id"]

    empty_update = client.patch(f"/api/v1/tasks/{task_id}", json={})
    assert empty_update.status_code == 400
    assert empty_update.json()["detail"] == "No fields provided for update"


def test_task_list_pagination_and_filters(tmp_path) -> None:
    client = _build_test_client(tmp_path)
    project_id = _create_project(client)

    task_ids = []
    for idx in range(3):
        payload = {
            "project_id": project_id,
            "title": f"Task {idx}",
            "assigned_to": "agent-42" if idx < 2 else "agent-99",
        }
        response = client.post("/api/v1/tasks", json=payload)
        task_ids.append(response.json()["data"]["id"])

    client.patch(f"/api/v1/tasks/{task_ids[1]}", json={"status": "completed"})

    paged = client.get(
        "/api/v1/tasks",
        params={"project_id": project_id, "page": 2, "page_size": 1},
    )
    page_data = paged.json()["data"]
    assert page_data["page"] == 2
    assert page_data["page_size"] == 1
    assert page_data["total"] == 3
    assert len(page_data["tasks"]) == 1

    status_filtered = client.get(
        "/api/v1/tasks",
        params={"project_id": project_id, "status": "completed"},
    )
    status_data = status_filtered.json()["data"]
    assert status_data["filters"] == {"status": "completed"}
    assert status_data["total"] == 1

    assignee_filtered = client.get(
        "/api/v1/tasks",
        params={"project_id": project_id, "assigned_to": "agent-42"},
    )
    assignee_data = assignee_filtered.json()["data"]
    assert assignee_data["total"] == 2
    assert assignee_data["filters"] == {"assigned_to": "agent-42"}
