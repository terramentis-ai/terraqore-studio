"""Tests for artifact management API routes."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from metaqore.api.app import create_api_app
from metaqore.config import GovernanceMode, MetaQoreConfig


def _build_test_client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "artifacts_api.db"
    config = MetaQoreConfig(
        governance_mode=GovernanceMode.PLAYGROUND,
        storage_dsn=f"sqlite:///{db_path}",
        max_parallel_branches=3,
    )
    return TestClient(create_api_app(config))


def _create_project(client: TestClient) -> str:
    response = client.post("/api/v1/projects", json={"name": "Artifacts Host"})
    return response.json()["data"]["id"]


def test_artifact_crud_flow(tmp_path) -> None:
    client = _build_test_client(tmp_path)
    project_id = _create_project(client)

    list_response = client.get("/api/v1/artifacts", params={"project_id": project_id})
    assert list_response.status_code == 200
    list_data = list_response.json()["data"]
    assert list_data["project_id"] == project_id
    assert list_data["artifacts"] == []
    assert list_data["total"] == 0
    assert list_data["page"] == 1
    assert list_data["page_size"] == 25
    assert list_data["filters"] == {}

    create_payload = {
        "project_id": project_id,
        "artifact_type": "spec",
        "data": {"summary": "Initial"},
        "created_by": "coder",
    }
    create_response = client.post("/api/v1/artifacts", json=create_payload)
    assert create_response.status_code == 201
    artifact_id = create_response.json()["data"]["id"]

    get_response = client.get(f"/api/v1/artifacts/{artifact_id}")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["artifact_type"] == "spec"

    update_payload = {"data": {"summary": "Updated"}, "version": 2}
    update_response = client.patch(f"/api/v1/artifacts/{artifact_id}", json=update_payload)
    assert update_response.status_code == 200
    assert update_response.json()["data"]["version"] == 2

    delete_response = client.delete(f"/api/v1/artifacts/{artifact_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["id"] == artifact_id

    missing_response = client.get(f"/api/v1/artifacts/{artifact_id}")
    assert missing_response.status_code == 404


def test_artifact_update_requires_fields(tmp_path) -> None:
    client = _build_test_client(tmp_path)
    project_id = _create_project(client)
    artifact_id = client.post(
        "/api/v1/artifacts",
        json={
            "project_id": project_id,
            "artifact_type": "doc",
            "data": {"x": 1},
            "created_by": "agent",
        },
    ).json()["data"]["id"]

    empty_update = client.patch(f"/api/v1/artifacts/{artifact_id}", json={})
    assert empty_update.status_code == 400
    assert empty_update.json()["detail"] == "No fields provided for update"


def test_artifact_list_pagination_and_filters(tmp_path) -> None:
    client = _build_test_client(tmp_path)
    project_id = _create_project(client)

    creators = ["coder", "validator", "coder"]
    types = ["spec", "plan", "report"]
    for idx, (creator, artifact_type) in enumerate(zip(creators, types)):
        payload = {
            "project_id": project_id,
            "artifact_type": artifact_type,
            "created_by": creator,
            "data": {"idx": idx},
        }
        client.post("/api/v1/artifacts", json=payload)

    paged = client.get(
        "/api/v1/artifacts",
        params={"project_id": project_id, "page": 2, "page_size": 2},
    )
    page_data = paged.json()["data"]
    assert page_data["page"] == 2
    assert page_data["page_size"] == 2
    assert page_data["total"] == 3
    assert len(page_data["artifacts"]) == 1

    type_filtered = client.get(
        "/api/v1/artifacts",
        params={"project_id": project_id, "artifact_type": "plan"},
    )
    type_data = type_filtered.json()["data"]
    assert type_data["total"] == 1
    assert type_data["filters"] == {"artifact_type": "plan"}

    creator_filtered = client.get(
        "/api/v1/artifacts",
        params={"project_id": project_id, "created_by": "coder"},
    )
    creator_data = creator_filtered.json()["data"]
    assert creator_data["total"] == 2
    assert creator_data["filters"] == {"created_by": "coder"}
