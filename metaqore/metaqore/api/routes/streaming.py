"""WebSocket endpoint for MetaQore streaming events."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from metaqore.streaming.hub import get_event_hub

router = APIRouter()


@router.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket) -> None:
    """Expose a lightweight subscription-based event stream."""

    hub = get_event_hub()
    manager = hub.manager
    await manager.register(websocket)
    try:
        while True:
            message = await websocket.receive_text()
            payload = _parse_payload(message)
            action = payload.get("action")
            if action == "subscribe":
                event_types = _coerce_list(payload.get("event_types") or ["*"])
                project_ids = _coerce_list(payload.get("project_id"))
                filters = payload.get("filters") or {}
                await manager.subscribe(
                    websocket,
                    event_types=event_types,
                    project_ids=project_ids,
                    filters=filters,
                )
                await websocket.send_json({"type": "system.subscribed", "event_types": event_types})
            elif action == "unsubscribe":
                event_types = _coerce_list(payload.get("event_types") or ["*"])
                await manager.unsubscribe(websocket, event_types=event_types)
                await websocket.send_json({"type": "system.unsubscribed", "event_types": event_types})
            elif action == "ping":
                await websocket.send_json({"type": "system.pong"})
            else:
                await websocket.send_json({"type": "system.error", "message": "Unknown action"})
    except WebSocketDisconnect:
        await manager.unregister(websocket)


def _parse_payload(message: str) -> Dict[str, Any]:
    try:
        return json.loads(message)
    except json.JSONDecodeError:
        return {}


def _coerce_list(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, str)]
    return []


__all__ = ["router"]
