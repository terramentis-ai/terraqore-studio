"""Integration tests for WebSocket streaming and metrics."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from metaqore.api.app import create_api_app
from metaqore.config import GovernanceMode, MetaQoreConfig
from metaqore.metrics.aggregator import get_metrics_aggregator
from metaqore.streaming.events import Event, EventType


def _build_test_client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "streaming.db"
    config = MetaQoreConfig(
        governance_mode=GovernanceMode.PLAYGROUND,
        storage_dsn=f"sqlite:///{db_path}",
    )
    app = create_api_app(config)
    return TestClient(app)


def test_metrics_endpoint_returns_prometheus_format(tmp_path) -> None:
    """Test that /metrics endpoint returns Prometheus format."""
    client = _build_test_client(tmp_path)

    response = client.get("/api/v1/events/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"

    text = response.text
    assert "# HELP" in text
    assert "# TYPE" in text
    assert "metaqore_" in text


def test_metrics_json_endpoint_returns_structured_data(tmp_path) -> None:
    """Test that /metrics/json returns structured JSON."""
    client = _build_test_client(tmp_path)

    response = client.get("/api/v1/events/metrics/json")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert "timestamp" in data["data"]
    assert "counters" in data["data"]
    assert "gauges" in data["data"]
    assert "histograms" in data["data"]


def test_aggregator_tracks_event_metrics() -> None:
    """Test that metrics aggregator properly tracks events."""
    aggregator = get_metrics_aggregator()
    aggregator.reset()

    event = Event(
        event_id="evt_test",
        event_type=EventType.ARTIFACT_CREATED,
        resource_id="art_123",
        resource_type="artifact",
        severity="info",
        metadata={"llm_metadata": {"latency_ms": 123.45, "provider": "ollama", "scenario_tag": "test"}},
    )
    aggregator.record_event(event)

    counters = aggregator.get_counters()
    assert "events_artifact.created" in counters
    assert counters["events_artifact.created"]["value"] == 1
    assert "mock_llm_scenarios_test" in counters

    histograms = aggregator.get_histograms()
    assert "llm_latency_ollama" in histograms
    assert histograms["llm_latency_ollama"]["count"] == 1


def test_aggregator_computes_percentiles() -> None:
    """Test that histogram percentile calculation works."""
    aggregator = get_metrics_aggregator()
    aggregator.reset()

    # Record 100 latencies from 1-100ms
    for i in range(1, 101):
        aggregator.record_api_latency("test_endpoint", float(i))

    histograms = aggregator.get_histograms()
    histogram = histograms.get("api_latency_test_endpoint")
    assert histogram is not None
    assert histogram["count"] == 100
    assert histogram["p50"] is not None
    assert histogram["p99"] is not None
    assert histogram["p999"] is not None
    # p50 should be around 50, p99 should be around 99
    assert 45 < histogram["p50"] < 55
    assert 95 < histogram["p99"] <= 100  # p99 can be exactly 100 with 100 samples


@pytest.mark.asyncio
async def test_websocket_connection_flow() -> None:
    """Test WebSocket connection, subscription, and metrics update."""
    from metaqore.api.routes.events import get_ws_manager
    from metaqore.streaming.websocket_manager import WebSocketConnectionManager

    # This test would require TestClient with WebSocket support
    # For now, we test the manager directly
    manager = WebSocketConnectionManager()
    assert manager.get_connection_count() == 0

    # Simulate connection registration
    from unittest.mock import AsyncMock

    ws = AsyncMock()
    await manager.register(ws)
    assert ws.accept.called
    assert manager.get_connection_count() == 1

    # Simulate disconnection
    await manager.unregister(ws)
    assert manager.get_connection_count() == 0


def test_metrics_gauge_updates(tmp_path) -> None:
    """Test that gauge metrics can be set."""
    aggregator = get_metrics_aggregator()
    aggregator.reset()

    aggregator.set_active_connections(5)
    gauges = aggregator.get_gauges()
    assert gauges["websocket_connections_active"]["value"] == 5.0

    aggregator.set_active_connections(10)
    gauges = aggregator.get_gauges()
    assert gauges["websocket_connections_active"]["value"] == 10.0
