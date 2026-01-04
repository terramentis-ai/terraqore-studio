"""Custom FastAPI middleware for MetaQore."""

from __future__ import annotations

import time
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from metaqore.config import MetaQoreConfig


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach request-scoped identifiers and latency tracking."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = str(uuid4())
        start = time.perf_counter()
        request.state.request_id = request_id
        response = await call_next(request)
        latency_ms = (time.perf_counter() - start) * 1000
        request.state.latency_ms = latency_ms
        response.headers.setdefault("X-Request-ID", request_id)
        response.headers.setdefault("X-Response-Time", f"{latency_ms:.2f}ms")
        return response


class GovernanceEnforcementMiddleware(BaseHTTPMiddleware):
    """Expose the active governance mode to downstream handlers."""

    def __init__(self, app: ASGIApp, config: MetaQoreConfig) -> None:
        super().__init__(app)
        self._config = config

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request.state.governance_mode = self._config.governance_mode
        response = await call_next(request)
        response.headers.setdefault("X-MetaQore-Governance-Mode", self._config.governance_mode.value)
        return response


class PrivilegedClientMiddleware(BaseHTTPMiddleware):
    """Flag requests coming from privileged clients (e.g., TerraQore Studio)."""

    HEADER_NAME = "X-MetaQore-Privileged"

    def __init__(self, app: ASGIApp, *, privileged_token: Optional[str] = None) -> None:
        super().__init__(app)
        self._privileged_token = privileged_token

    def _is_privileged(self, header_value: Optional[str]) -> bool:
        if not header_value:
            return False
        if not self._privileged_token:
            return header_value.lower() in {"1", "true", "yes", "terraqore"}
        return header_value == self._privileged_token

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        header_value = request.headers.get(self.HEADER_NAME)
        request.state.is_privileged = self._is_privileged(header_value)
        response = await call_next(request)
        if getattr(request.state, "is_privileged", False):
            response.headers.setdefault(self.HEADER_NAME, "true")
        return response


def register_middlewares(app: FastAPI, config: MetaQoreConfig, *, privileged_token: Optional[str] = None) -> None:
    """Register MetaQore middleware stack on the supplied FastAPI app."""

    app.add_middleware(GZipMiddleware, minimum_size=512)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(GovernanceEnforcementMiddleware, config=config)
    app.add_middleware(PrivilegedClientMiddleware, privileged_token=privileged_token)


__all__ = [
    "RequestContextMiddleware",
    "GovernanceEnforcementMiddleware",
    "PrivilegedClientMiddleware",
    "register_middlewares",
]
