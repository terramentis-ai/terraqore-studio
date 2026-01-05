"""FastAPI application factory for the MetaQore Orchestration API."""

from __future__ import annotations

from datetime import datetime, timezone
from importlib import metadata
from typing import Optional

from fastapi import FastAPI

from metaqore.api.middleware import register_middlewares
from metaqore.api.routes import DEFAULT_API_PREFIX, register_routes
from metaqore.config import MetaQoreConfig
from metaqore.core.psmp import PSMPEngine
from metaqore.core.security import SecureGateway, resolve_routing_policy
from metaqore.core.state_manager import StateManager
from metaqore.gateway import InMemoryGatewayQueue
from metaqore.hmcp import HMCPService
from metaqore.logger import configure_logging, get_logger
from metaqore.storage.backends.sqlite import SQLiteBackend
from metaqore.streaming.hub import get_event_hub

logger = get_logger(__name__)


def _get_version() -> str:
    try:
        return metadata.version("metaqore")
    except metadata.PackageNotFoundError:  # type: ignore[attr-defined]
        return "0.1.0"


def _create_state_layer(
    config: MetaQoreConfig,
) -> tuple[StateManager, PSMPEngine, SecureGateway]:
    backend = SQLiteBackend(config.storage_dsn)
    state_manager = StateManager(backend=backend)
    psmp_engine = PSMPEngine(state_manager=state_manager, config=config)
    state_manager.attach_psmp_engine(psmp_engine)
    policy = resolve_routing_policy(config.secure_gateway_policy)
    secure_gateway = SecureGateway(policy=policy, organization=config.organization)
    state_manager.attach_secure_gateway(secure_gateway)
    return state_manager, psmp_engine, secure_gateway


def create_api_app(config: Optional[MetaQoreConfig] = None) -> FastAPI:
    """Instantiate and configure the FastAPI application."""

    configure_logging()
    config = config or MetaQoreConfig(max_parallel_branches=1)
    version = _get_version()

    app = FastAPI(
        title="MetaQore API",
        description="Governance-first orchestration API for multi-agent systems.",
        version=version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    state_manager, psmp_engine, secure_gateway = _create_state_layer(config)
    gateway_queue = InMemoryGatewayQueue()
    hmcp_service = HMCPService(gateway_queue=gateway_queue)

    app.state.config = config
    app.state.version = version
    app.state.start_time = datetime.now(timezone.utc)
    app.state.state_manager = state_manager
    app.state.psmp_engine = psmp_engine
    app.state.secure_gateway = secure_gateway
    app.state.gateway_queue = gateway_queue
    app.state.hmcp_service = hmcp_service
    app.state.event_hub = get_event_hub()

    register_middlewares(app, config)
    register_routes(app, prefix=DEFAULT_API_PREFIX)

    logger.info("MetaQore API initialized (mode=%s)", config.governance_mode.value)
    return app


app = create_api_app()


__all__ = ["create_api_app", "app"]
