"""Webhook dispatcher for pushing events with signature validation."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from metaqore.streaming.events import Event

logger = logging.getLogger(__name__)


class WebhookEndpoint:
    """Represents a registered webhook endpoint."""

    def __init__(
        self,
        webhook_id: str,
        url: str,
        secret: str,
        event_types: Optional[list[str]] = None,
        active: bool = True,
    ) -> None:
        self.webhook_id = webhook_id
        self.url = url
        self.secret = secret
        self.event_types = event_types or ["*"]
        self.active = active
        self.retries = 3
        self.timeout_seconds = 10

    def should_deliver(self, event: Event) -> bool:
        """Check if event matches webhook subscription."""
        if not self.active:
            return False
        if "*" in self.event_types:
            return True
        return event.event_type.value in self.event_types


class WebhookDispatcher:
    """Dispatches events to registered webhook endpoints with HMAC signature validation."""

    def __init__(self) -> None:
        self._endpoints: Dict[str, WebhookEndpoint] = {}
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> WebhookDispatcher:
        self._client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client:
            await self._client.aclose()

    def register_endpoint(self, endpoint: WebhookEndpoint) -> None:
        """Register a webhook endpoint."""
        self._endpoints[endpoint.webhook_id] = endpoint
        logger.info("Registered webhook endpoint %s: %s", endpoint.webhook_id, endpoint.url)

    def unregister_endpoint(self, webhook_id: str) -> None:
        """Unregister a webhook endpoint."""
        self._endpoints.pop(webhook_id, None)
        logger.info("Unregistered webhook endpoint %s", webhook_id)

    async def dispatch(self, event: Event) -> Dict[str, Dict[str, Any]]:
        """Dispatch an event to all matching webhook endpoints."""
        results = {}
        if not self._client:
            logger.warning("Webhook dispatcher not initialized (use async context manager)")
            return results

        for webhook_id, endpoint in self._endpoints.items():
            if not endpoint.should_deliver(event):
                continue

            success = await self._send_webhook(endpoint, event)
            results[webhook_id] = {
                "success": success,
                "endpoint": endpoint.url,
                "event_type": event.event_type.value,
            }

        return results

    async def _send_webhook(self, endpoint: WebhookEndpoint, event: Event) -> bool:
        """Send a webhook with HMAC signature."""
        payload = event.to_dict()
        payload_json = json.dumps(payload, default=str)
        signature = self._compute_signature(payload_json, endpoint.secret)

        headers = {
            "Content-Type": "application/json",
            "X-MetaQore-Signature": signature,
            "X-MetaQore-Event-ID": event.event_id,
            "X-MetaQore-Timestamp": datetime.now(timezone.utc).isoformat(),
        }

        for attempt in range(endpoint.retries):
            try:
                response = await self._client.post(
                    endpoint.url,
                    content=payload_json,
                    headers=headers,
                    timeout=endpoint.timeout_seconds,
                )
                if response.status_code in (200, 201, 202):
                    logger.info("Webhook %s delivered (attempt %d)", endpoint.webhook_id, attempt + 1)
                    return True
                logger.warning(
                    "Webhook %s failed with %d (attempt %d)",
                    endpoint.webhook_id,
                    response.status_code,
                    attempt + 1,
                )
            except httpx.RequestError as exc:
                logger.warning("Webhook %s request error: %s (attempt %d)", endpoint.webhook_id, exc, attempt + 1)
                if attempt < endpoint.retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        logger.error("Webhook %s failed after %d retries", endpoint.webhook_id, endpoint.retries)
        return False

    @staticmethod
    def _compute_signature(payload: str, secret: str) -> str:
        """Compute HMAC-SHA256 signature for webhook payload."""
        return "sha256=" + hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


# Global dispatcher instance
_dispatcher: Optional[WebhookDispatcher] = None


async def get_webhook_dispatcher() -> WebhookDispatcher:
    """Get the global webhook dispatcher (use as async context manager)."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = WebhookDispatcher()
    return _dispatcher


__all__ = ["WebhookEndpoint", "WebhookDispatcher", "get_webhook_dispatcher"]


# Add missing import
import asyncio
