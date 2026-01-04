"""Service health check endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request

from metaqore.api.schemas import HealthPayload, HealthResponse, ResponseMetadata
from metaqore.config import MetaQoreConfig

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="MetaQore API health check")
async def health_check(request: Request) -> HealthResponse:
    """Return service health status and governance context."""

    app = request.app
    config: MetaQoreConfig = getattr(app.state, "config")
    start_time = getattr(app.state, "start_time", datetime.now(timezone.utc))
    version = getattr(app.state, "version", "0.1.0")

    uptime_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
    latency_ms = float(getattr(request.state, "latency_ms", 0.0))

    metadata = ResponseMetadata(
        request_id=getattr(request.state, "request_id", "-"),
        latency_ms=latency_ms,
    )
    payload = HealthPayload(
        uptime_seconds=uptime_seconds,
        governance_mode=config.governance_mode,
        version=version,
    )
    return HealthResponse(data=payload, metadata=metadata)
