"""Tests for governance-focused API routes."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from metaqore.api.app import create_api_app
from metaqore.config import GovernanceMode, MetaQoreConfig
from metaqore.core.models import Conflict, ConflictSeverity, ResolutionStrategy


def _build_test_client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "governance.db"
    config = MetaQoreConfig(
        governance_mode=GovernanceMode.PLAYGROUND,
        storage_dsn=f"sqlite:///{db_path}",
        max_parallel_branches=2,
    )
    app = create_api_app(config)
    return TestClient(app)


def _get_state_manager(client: TestClient):
    return client.app.state.state_manager


def test_blocking_report_returns_empty_sets_for_new_project(tmp_path) -> None:
    client = _build_test_client(tmp_path)
    project_id = client.post("/api/v1/projects", json={"name": "Gov Project"}).json()["data"]["id"]

    response = client.get("/api/v1/governance/blocking-report", params={"project_id": project_id})
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["project_id"] == project_id
    assert payload["data"]["blocked_artifacts"] == []
    assert payload["data"]["conflicts"] == []


def test_blocking_report_missing_project_returns_404(tmp_path) -> None:
    client = _build_test_client(tmp_path)
    response = client.get("/api/v1/governance/blocking-report", params={"project_id": "proj_missing"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_compliance_export_json_returns_report_structure(tmp_path) -> None:
    client = _build_test_client(tmp_path)
    response = client.get("/api/v1/governance/compliance/export")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["format"] == "json"
    assert "report" in payload["data"]
    assert "events" in payload["data"]


def test_compliance_export_csv_returns_text_payload(tmp_path) -> None:
    client = _build_test_client(tmp_path)
    response = client.get("/api/v1/governance/compliance/export", params={"format": "csv"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    body = response.text.splitlines()
    assert body[0] == "timestamp,event_type,organization,payload"


def test_conflict_listing_supports_filters(tmp_path) -> None:
    client = _build_test_client(tmp_path)
    project_id = client.post("/api/v1/projects", json={"name": "Conflicts"}).json()["data"]["id"]
    state_manager = _get_state_manager(client)

    conflicts = []
    severities = [ConflictSeverity.LOW, ConflictSeverity.HIGH, ConflictSeverity.MEDIUM]
    for idx, severity in enumerate(severities):
        conflict = Conflict(
            project_id=project_id,
            artifact_id=f"art_{idx}",
            description=f"Conflict {idx}",
            severity=severity,
            conflict_type="parallel_creation" if severity is ConflictSeverity.HIGH else "version_mismatch",
        )
        if severity is ConflictSeverity.LOW:
            conflict.mark_resolved(ResolutionStrategy.RETRY)
        conflicts.append(conflict)
    state_manager.save_conflicts(conflicts)

    base_response = client.get("/api/v1/governance/conflicts", params={"project_id": project_id})
    assert base_response.status_code == 200
    base_data = base_response.json()["data"]
    assert base_data["total"] == 3
    assert len(base_data["conflicts"]) == 3

    severity_response = client.get(
        "/api/v1/governance/conflicts",
        params={"project_id": project_id, "severity": ConflictSeverity.HIGH.value},
    )
    severity_data = severity_response.json()["data"]
    assert severity_data["total"] == 1
    assert severity_data["conflicts"][0]["severity"] == ConflictSeverity.HIGH.value

    unresolved_response = client.get(
        "/api/v1/governance/conflicts",
        params={"project_id": project_id, "resolved": False},
    )
    unresolved_data = unresolved_response.json()["data"]
    assert unresolved_data["total"] == 2

    paged_response = client.get(
        "/api/v1/governance/conflicts",
        params={"project_id": project_id, "page": 2, "page_size": 2},
    )
    paged_data = paged_response.json()["data"]
    assert paged_data["page"] == 2
    assert len(paged_data["conflicts"]) == 1


def test_conflict_resolution_endpoint_updates_state(tmp_path) -> None:
    client = _build_test_client(tmp_path)
    project_id = client.post("/api/v1/projects", json={"name": "Resolve"}).json()["data"]["id"]
    state_manager = _get_state_manager(client)

    conflict = Conflict(
        project_id=project_id,
        artifact_id="art_pending",
        description="Needs attention",
        severity=ConflictSeverity.CRITICAL,
    )
    state_manager.save_conflicts([conflict])

    resolve_response = client.post(
        f"/api/v1/governance/conflicts/{conflict.id}/resolve",
        json={"strategy": ResolutionStrategy.OVERRIDE.value},
    )
    assert resolve_response.status_code == 200
    payload = resolve_response.json()["data"]
    assert payload["resolved"] is True
    assert payload["resolution_strategy"] == ResolutionStrategy.OVERRIDE.value

    stored_conflict = state_manager.get_conflict(conflict.id)
    assert stored_conflict is not None and stored_conflict.resolved is True

    missing = client.post(
        "/api/v1/governance/conflicts/conf_missing/resolve",
        json={"strategy": ResolutionStrategy.RETRY.value},
    )
    assert missing.status_code == 404


def test_compliance_audit_endpoint_returns_events(tmp_path) -> None:
    client = _build_test_client(tmp_path)
    gateway = client.app.state.secure_gateway
    gateway.auditor.log_routing_decision(
        {
            "agent_name": "CoderAgent",
            "task_type": "code_generation",
            "sensitivity": "public",
            "provider": "ollama",
            "policy": gateway.policy.name,
            "reason": "allowed",
        }
    )
    gateway.auditor.flush()

    response = client.get(
        "/api/v1/governance/compliance/audit",
        params={"provider": "ollama", "page_size": 10},
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["total"] >= 1
    assert payload["events"][0]["payload"]["provider"] == "ollama"
