"""Event hub that wires backend governance events to WebSocket clients."""

from __future__ import annotations

import asyncio
from typing import Optional

from metaqore.streaming.events import Event
from metaqore.streaming.websocket_manager import WebSocketConnectionManager


class StreamingEventHub:
    """Singleton-style hub coordinating streaming event delivery."""

    def __init__(self) -> None:
        self.manager = WebSocketConnectionManager()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Bind the hub to a specific event loop (usually the main app loop)."""
        self._loop = loop

    async def broadcast(self, event: Event) -> None:
        await self.manager.broadcast(event)

    def emit(self, event: Event) -> None:
        """Emit an event without forcing callers to manage async context."""
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        # Case 1: We have a bound loop, and we need to send to it
        if self._loop and self._loop.is_running():
            if current_loop == self._loop:
                # We are in the correct loop
                self._loop.create_task(self.broadcast(event))
            else:
                # We are in a different thread/loop
                asyncio.run_coroutine_threadsafe(self.broadcast(event), self._loop)
            return

        # Case 2: No bound loop, but we are in a running loop
        if current_loop and current_loop.is_running():
            current_loop.create_task(self.broadcast(event))
            return

        # Case 3: No loops at all - create one (fallback for scripts/tests without app)
        asyncio.run(self.broadcast(event))


_global_hub: Optional[StreamingEventHub] = None


def get_event_hub() -> StreamingEventHub:
    global _global_hub
    if _global_hub is None:
        _global_hub = StreamingEventHub()
    return _global_hub


__all__ = ["StreamingEventHub", "get_event_hub"]
