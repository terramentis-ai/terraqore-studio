"""Tests for the project management API routes."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from metaqore.api.app import create_api_app
from metaqore.config import GovernanceMode, MetaQoreConfig


def _build_test_client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "projects.db"
    config = MetaQoreConfig(
        governance_mode=GovernanceMode.PLAYGROUND,
        storage_dsn=f"sqlite:///{db_path}",
        max_parallel_branches=3,
    )
    app = create_api_app(config)
    return TestClient(app)


def test_project_crud_flow(tmp_path) -> None:
    client = _build_test_client(tmp_path)

    list_response = client.get("/api/v1/projects")
    assert list_response.status_code == 200
    list_data = list_response.json()["data"]
    assert list_data["projects"] == []
    assert list_data["total"] == 0
    assert list_data["page"] == 1
    assert list_data["page_size"] == 25
    assert list_data["filters"] == {}

    create_payload = {
        "name": "Test Project",
        "description": "Initial description",
        "owner_id": "owner-123",
        "metadata": {"priority": "high"},
    }
    create_response = client.post("/api/v1/projects", json=create_payload)
    created = create_response.json()
    assert create_response.status_code == 201
    assert created["data"]["name"] == "Test Project"
    assert created["data"]["metadata"]["priority"] == "high"

    project_id = created["data"]["id"]
    get_response = client.get(f"/api/v1/projects/{project_id}")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["id"] == project_id

    update_payload = {"description": "Updated", "status": "planning"}
    update_response = client.patch(f"/api/v1/projects/{project_id}", json=update_payload)
    assert update_response.status_code == 200
    assert update_response.json()["data"]["description"] == "Updated"
    assert update_response.json()["data"]["status"] == "planning"

    delete_response = client.delete(f"/api/v1/projects/{project_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["id"] == project_id

    missing_response = client.get(f"/api/v1/projects/{project_id}")
    assert missing_response.status_code == 404


def test_project_update_requires_fields(tmp_path) -> None:
    client = _build_test_client(tmp_path)
    create_payload = {"name": "Needs Update"}
    project_id = client.post("/api/v1/projects", json=create_payload).json()["data"]["id"]

    empty_update = client.patch(f"/api/v1/projects/{project_id}", json={})
    assert empty_update.status_code == 400
    assert empty_update.json()["detail"] == "No fields provided for update"


def test_project_list_supports_filters_and_pagination(tmp_path) -> None:
    client = _build_test_client(tmp_path)

    owners = ["alice", "bob", "alice"]
    for idx, owner in enumerate(owners, start=1):
        payload = {"name": f"Proj {idx}", "owner_id": owner}
        created_id = client.post("/api/v1/projects", json=payload).json()["data"]["id"]
        if idx == 2:
            client.patch(f"/api/v1/projects/{created_id}", json={"status": "planning"})

    paged = client.get("/api/v1/projects", params={"page": 2, "page_size": 1})
    page_data = paged.json()["data"]
    assert page_data["page"] == 2
    assert page_data["page_size"] == 1
    assert page_data["total"] == 3
    assert len(page_data["projects"]) == 1

    filtered = client.get("/api/v1/projects", params={"owner_id": "alice"})
    filter_data = filtered.json()["data"]
    assert filter_data["total"] == 2
    assert filter_data["filters"] == {"owner_id": "alice"}

    status_filtered = client.get("/api/v1/projects", params={"status": "planning"})
    status_data = status_filtered.json()["data"]
    assert status_data["total"] == 1
    assert status_data["filters"] == {"status": "planning"}
