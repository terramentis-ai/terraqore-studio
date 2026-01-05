"""Lightweight WebSocket subscription manager for streaming events."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional, Set

from fastapi import WebSocket

from metaqore.streaming.events import Event


@dataclass(slots=True)
class Subscription:
    websocket: WebSocket
    event_types: Set[str] = field(default_factory=set)
    project_ids: Set[str] = field(default_factory=set)
    filters: Dict[str, Any] = field(default_factory=dict)


class WebSocketConnectionManager:
    """Tracks active WebSocket connections and their subscriptions."""

    def __init__(self) -> None:
        self._subscriptions: Dict[WebSocket, Subscription] = {}
        self._lock = asyncio.Lock()

    async def register(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._subscriptions[websocket] = Subscription(websocket=websocket)

    async def unregister(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._subscriptions.pop(websocket, None)

    def get_connection_count(self) -> int:
        """Return the number of active WebSocket connections."""
        return len(self._subscriptions)

    async def subscribe(
        self,
        websocket: WebSocket,
        *,
        event_types: Iterable[str],
        project_ids: Iterable[str] | None = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> None:
        async with self._lock:
            subscription = self._subscriptions.get(websocket)
            if subscription is None:
                return
            subscription.event_types.update(event_types)
            if project_ids:
                subscription.project_ids.update(project_ids)
            if filters:
                subscription.filters.update(filters)

    async def unsubscribe(self, websocket: WebSocket, *, event_types: Iterable[str]) -> None:
        async with self._lock:
            subscription = self._subscriptions.get(websocket)
            if subscription is None:
                return
            for event_type in event_types:
                subscription.event_types.discard(event_type)

    async def broadcast(self, event: Event) -> None:
        payload = json.dumps(event.to_message())
        stale: list[WebSocket] = []
        async with self._lock:
            for websocket, subscription in self._subscriptions.items():
                if not self._should_deliver(subscription, event):
                    continue
                try:
                    await websocket.send_text(payload)
                except Exception:  # pragma: no cover - dependent on network failure
                    stale.append(websocket)
        for websocket in stale:
            await self.unregister(websocket)

    def _should_deliver(self, subscription: Subscription, event: Event) -> bool:
        if subscription.event_types:
            if not any(self._matches_pattern(pattern, event.event_type.value) for pattern in subscription.event_types):
                return False
        if subscription.project_ids and event.project_id not in subscription.project_ids:
            return False
        agent_filter = subscription.filters.get("agent_name")
        if agent_filter and event.metadata.get("agent_name") != agent_filter:
            return False
        return True

    @staticmethod
    def _matches_pattern(pattern: str, event_type: str) -> bool:
        if pattern == "*":
            return True
        if pattern.endswith(".*"):
            return event_type.startswith(pattern[:-1])
        return pattern == event_type


__all__ = ["WebSocketConnectionManager", "Subscription"]
