"""Integration tests for HMCP specialist API endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from metaqore.api.app import create_api_app
from metaqore.config import GovernanceMode, MetaQoreConfig


def _build_test_client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "hmcp_integration.db"
    config = MetaQoreConfig(
        governance_mode=GovernanceMode.PLAYGROUND,
        storage_dsn=f"sqlite:///{db_path}",
        max_parallel_branches=3,
    )
    app = create_api_app(config)
    return TestClient(app)


def test_specialist_draft_persists_and_enqueues_gateway_job(tmp_path) -> None:
    client = _build_test_client(tmp_path)

    project_payload = {"name": "HMCP Project"}
    project_id = client.post("/api/v1/projects", json=project_payload).json()["data"]["id"]

    payload = {
        "project_id": project_id,
        "created_by": "hmcp",
        "skill_id": "clean_akkadian_dates",
        "requested_size_mb": 10,
        "teachers": ["BaseAgent"],
        "confidence": 0.95,
        "task_isolation_passed": True,
        "parameter_count": 5_000_000,
        "data": {"summary": "demo"},
        "metadata": {"custom": "value"},
    }

    response = client.post("/api/v1/hmcp/specialists/draft", json=payload)
    assert response.status_code == 201
    body = response.json()

    specialist = body["data"]["specialist"]
    job_id = body["data"].get("gateway_job_id")
    assert specialist["artifact_type"] == "specialist_model"
    assert specialist["project_id"] == project_id
    assert job_id

    artifact_id = specialist["id"]
    artifact_response = client.get(f"/api/v1/artifacts/{artifact_id}")
    assert artifact_response.status_code == 200
    assert artifact_response.json()["data"]["id"] == artifact_id

    queue = client.app.state.gateway_queue
    assert queue.size() == 1
    queued_job = queue.peek()
    assert queued_job is not None
    assert queued_job.artifact_id == artifact_id
    assert queued_job.payload["skill_id"] == payload["skill_id"]
    assert queued_job.payload["metadata"]["custom"] == "value"


def test_specialist_draft_conflict_returns_409(tmp_path) -> None:
    client = _build_test_client(tmp_path)

    project_payload = {"name": "HMCP Project"}
    project_id = client.post("/api/v1/projects", json=project_payload).json()["data"]["id"]

    payload = {
        "project_id": project_id,
        "created_by": "hmcp",
        "skill_id": "clean_akkadian_dates",
        "requested_size_mb": 10,
        "teachers": ["BaseAgent"],
        "confidence": 0.95,
        "task_isolation_passed": True,
        "parameter_count": 5_000_000,
        "data": {"summary": "demo"},
    }

    first_response = client.post("/api/v1/hmcp/specialists/draft", json=payload)
    assert first_response.status_code == 201

    second_response = client.post("/api/v1/hmcp/specialists/draft", json=payload)
    assert second_response.status_code == 409
    assert "conflict" in second_response.json()["detail"].lower()


def test_specialist_draft_invalid_teachers_returns_422(tmp_path) -> None:
    client = _build_test_client(tmp_path)

    project_payload = {"name": "HMCP Project"}
    project_id = client.post("/api/v1/projects", json=project_payload).json()["data"]["id"]

    payload = {
        "project_id": project_id,
        "created_by": "hmcp",
        "skill_id": "clean_akkadian_dates",
        "requested_size_mb": 10,
        "teachers": ["RogueAgent"],
        "confidence": 0.95,
        "task_isolation_passed": True,
        "parameter_count": 5_000_000,
        "data": {"summary": "demo"},
    }

    response = client.post("/api/v1/hmcp/specialists/draft", json=payload)
    assert response.status_code == 422
    assert "teachers not permitted" in response.json()["detail"].lower()


def test_specialist_run_endpoint_executes_pipeline(tmp_path) -> None:
    client = _build_test_client(tmp_path)

    project_payload = {"name": "HMCP Project"}
    project_id = client.post("/api/v1/projects", json=project_payload).json()["data"]["id"]

    payload = {
        "project_id": project_id,
        "created_by": "hmcp",
        "skill_id": "clean_akkadian_dates",
        "requested_size_mb": 8,
        "teachers": ["BaseAgent"],
        "confidence": 0.95,
        "task_isolation_passed": True,
        "parameter_count": 6_000_000,
        "data": {"summary": "demo"},
        "metadata": {"custom": "value"},
    }

    response = client.post("/api/v1/hmcp/specialists/run", json=payload)
    assert response.status_code == 201
    body = response.json()
    data = body["data"]
    specialist = data["specialist"]
    assert specialist["project_id"] == project_id
    assert specialist["lifecycle_state"] == "active"
    assert "training" in data
    assert data["training"]["success"] is True
    assert "validation" in data
    assert data["validation"]["passed"] is True
    assert data["gateway_job_id"]
