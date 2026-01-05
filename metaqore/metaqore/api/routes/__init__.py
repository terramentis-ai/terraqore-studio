"""Router registration helpers for the MetaQore API."""

from __future__ import annotations

from fastapi import FastAPI

from metaqore.api.routes import artifacts, events, governance, health, projects, specialists, tasks

DEFAULT_API_PREFIX = "/api/v1"


def register_routes(app: FastAPI, *, prefix: str = DEFAULT_API_PREFIX) -> None:
	"""Include all API routers on the supplied FastAPI application."""

	app.include_router(health.router, prefix=prefix)
	app.include_router(projects.router, prefix=prefix)
	app.include_router(tasks.router, prefix=prefix)
	app.include_router(artifacts.router, prefix=prefix)
	app.include_router(governance.router, prefix=prefix)
	app.include_router(specialists.router, prefix=prefix)
	app.include_router(events.router, prefix=prefix)
	# Backward-compatible WebSocket endpoint for legacy clients
	app.add_api_websocket_route("/ws/stream", events.websocket_endpoint)


__all__ = ["register_routes", "DEFAULT_API_PREFIX"]
