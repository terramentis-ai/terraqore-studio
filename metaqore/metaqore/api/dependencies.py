"""FastAPI dependency helpers for MetaQore services."""

from __future__ import annotations

from fastapi import Request

from metaqore.config import MetaQoreConfig
from metaqore.core.psmp import PSMPEngine
from metaqore.core.security import SecureGateway
from metaqore.core.state_manager import StateManager


def _ensure_app_state(request: Request) -> None:
    if not hasattr(request.app.state, "config"):
        raise RuntimeError("MetaQore API app state not initialized")


def get_config(request: Request) -> MetaQoreConfig:
    _ensure_app_state(request)
    return request.app.state.config


def get_state_manager(request: Request) -> StateManager:
    _ensure_app_state(request)
    state_manager = getattr(request.app.state, "state_manager", None)
    if state_manager is None:
        raise RuntimeError("StateManager not initialized on app state")
    return state_manager


def get_psmp_engine(request: Request) -> PSMPEngine:
    _ensure_app_state(request)
    engine = getattr(request.app.state, "psmp_engine", None)
    if engine is None:
        raise RuntimeError("PSMPEngine not initialized on app state")
    return engine


def get_secure_gateway(request: Request) -> SecureGateway:
    _ensure_app_state(request)
    gateway = getattr(request.app.state, "secure_gateway", None)
    if gateway is None:
        raise RuntimeError("SecureGateway not initialized on app state")
    return gateway


__all__ = [
    "get_config",
    "get_state_manager",
    "get_psmp_engine",
    "get_secure_gateway",
]
