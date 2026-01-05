"""Event subscription and streaming endpoints."""

from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, status
from fastapi.responses import Response

from metaqore.api.dependencies import get_state_manager
from metaqore.api.routes.utils import build_response_metadata
from metaqore.api.schemas import ResponseMetadata, ResponseStatus
from metaqore.core.state_manager import StateManager
from metaqore.metrics.aggregator import get_metrics_aggregator
from metaqore.metrics.exporter import generate_prometheus_metrics
from metaqore.streaming.websocket_manager import WebSocketConnectionManager

router = APIRouter(prefix="/events", tags=["Events & Streaming"])

# Global WebSocket manager instance
_ws_manager: WebSocketConnectionManager | None = None


def get_ws_manager() -> WebSocketConnectionManager:
    """Get or create the global WebSocket manager."""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketConnectionManager()
    return _ws_manager


class StreamResponse(ResponseMetadata):
    """Response wrapper for metrics/events."""

    status: ResponseStatus = ResponseStatus.SUCCESS
    data: Dict = {}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, project_id: str | None = None) -> None:
    """
    WebSocket endpoint for real-time event streaming.
    
    **Query Parameters:**
    - `project_id` (optional): Filter events to specific project
    
    **Subscribe Message (client → server):**
    ```json
    {
      "action": "subscribe",
      "event_types": ["artifact.*", "conflict.*"],
      "project_ids": ["proj_abc123"]
    }
    ```
    
    **Event Message (server → client):**
    ```json
    {
      "event_id": "evt_xyz",
      "event_type": "artifact.created",
      "timestamp": "2026-01-04T12:00:00Z",
      "resource_id": "art_123",
      "resource_type": "artifact",
      "project_id": "proj_abc123",
      "metadata": {"llm_provider": "ollama"}
    }
    ```
    """
    manager = get_ws_manager()

    await manager.register(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "subscribe":
                event_types = data.get("event_types", ["*"])
                project_ids = data.get("project_ids", [project_id] if project_id else [])
                await manager.subscribe(websocket, event_types=event_types, project_ids=project_ids)

                await websocket.send_json(
                    {
                        "action": "subscribed",
                        "event_types": event_types,
                        "project_ids": project_ids,
                    }
                )
            elif action == "ping":
                await websocket.send_json({"action": "pong"})

    except Exception as exc:
        await manager.unregister(websocket)


@router.get(
    "/metrics",
    summary="Prometheus metrics endpoint",
    responses={200: {"content": {"text/plain": {"example": "metaqore_events_total 42"}}}},
    response_class=Response,
)
async def get_metrics() -> Response:
    """
    Return Prometheus-formatted metrics.
    
    Includes:
    - Event counts by type and severity
    - API latency histograms (p50, p99, p999)
    - Mock LLM metadata (latencies, scenarios)
    - Active WebSocket connection count
    
    **Response:** Plain text, Prometheus format
    """
    manager = get_ws_manager()
    aggregator = get_metrics_aggregator()

    # Update active connection gauge
    aggregator.set_active_connections(manager.get_connection_count())

    return Response(content=generate_prometheus_metrics(), media_type="text/plain; charset=utf-8")


@router.get(
    "/metrics/json",
    summary="Metrics in JSON format",
)
async def get_metrics_json(request: Request) -> Dict:
    """
    Return metrics as structured JSON.
    
    **Response (200):**
    ```json
    {
      "status": "success",
      "data": {
        "timestamp": "2026-01-04T12:00:00Z",
        "counters": {"events_artifact.created": {"value": 42}},
        "gauges": {"websocket_connections_active": {"value": 5}},
        "histograms": {"api_latency_POST_/api/v1/artifacts": {...}}
      }
    }
    ```
    """
    manager = get_ws_manager()
    aggregator = get_metrics_aggregator()

    aggregator.set_active_connections(manager.get_connection_count())
    metrics = aggregator.get_all_metrics()

    return {
        "status": ResponseStatus.SUCCESS.value,
        "data": metrics,
        "metadata": build_response_metadata(request),
    }


__all__ = ["router", "get_ws_manager"]
