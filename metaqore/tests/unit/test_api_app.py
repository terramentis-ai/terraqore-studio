"""Tests for the MetaQore FastAPI application factory."""

from __future__ import annotations

from fastapi.testclient import TestClient

from metaqore.api.app import create_api_app
from metaqore.config import MetaQoreConfig, GovernanceMode


def test_create_api_app_populates_state_dependencies() -> None:
    config = MetaQoreConfig(governance_mode=GovernanceMode.ADAPTIVE)
    app = create_api_app(config)

    assert app.state.config.governance_mode is GovernanceMode.ADAPTIVE
    assert app.state.state_manager is not None
    assert app.state.psmp_engine is not None
    assert app.state.secure_gateway is not None


def test_health_endpoint_returns_success_payload() -> None:
    app = create_api_app()
    client = TestClient(app)

    response = client.get("/api/v1/health")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "success"
    assert payload["data"]["service"] == "metaqore-api"
    assert "request_id" in payload["metadata"]
    assert payload["data"]["governance_mode"] == app.state.config.governance_mode.value
