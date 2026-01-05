"""Gateway request queue abstractions for the MetaQore LLM gateway."""

from __future__ import annotations

import threading
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Deque, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class GatewayJob:
    """Task describing a specialist training/inference request."""

    job_id: str
    artifact_id: str
    project_id: str
    skill_id: str
    provider_hint: str
    profile_hash: str
    payload: Dict[str, object]
    estimated_tokens: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class GatewayQueueError(RuntimeError):
    """Raised when queue operations fail."""


class GatewayQueue:
    """Abstract interface for queue implementations."""

    def enqueue(self, job: GatewayJob) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def dequeue(self, max_items: int = 1) -> List[GatewayJob]:  # pragma: no cover - interface
        raise NotImplementedError

    def peek(self) -> Optional[GatewayJob]:  # pragma: no cover - interface
        raise NotImplementedError

    def size(self) -> int:  # pragma: no cover - interface
        raise NotImplementedError


class InMemoryGatewayQueue(GatewayQueue):
    """Thread-safe queue used for development and testing."""

    def __init__(self) -> None:
        self._queue: Deque[GatewayJob] = deque()
        self._lock = threading.Lock()

    def enqueue(self, job: GatewayJob) -> None:
        with self._lock:
            self._queue.append(job)

    def dequeue(self, max_items: int = 1) -> List[GatewayJob]:
        if max_items <= 0:
            raise GatewayQueueError("max_items must be positive")
        jobs: List[GatewayJob] = []
        with self._lock:
            while self._queue and len(jobs) < max_items:
                jobs.append(self._queue.popleft())
        return jobs

    def peek(self) -> Optional[GatewayJob]:
        with self._lock:
            return self._queue[0] if self._queue else None

    def size(self) -> int:
        with self._lock:
            return len(self._queue)


def build_gateway_job(
    *,
    artifact_id: str,
    project_id: str,
    skill_id: str,
    provider_hint: str,
    profile_hash: str,
    payload: Dict[str, object],
    estimated_tokens: int = 0,
) -> GatewayJob:
    """Utility helper to create a job with a unique identifier."""

    job_id = f"gw_{uuid.uuid4().hex[:12]}"
    return GatewayJob(
        job_id=job_id,
        artifact_id=artifact_id,
        project_id=project_id,
        skill_id=skill_id,
        provider_hint=provider_hint,
        profile_hash=profile_hash,
        payload=payload,
        estimated_tokens=estimated_tokens,
    )


__all__ = [
    "GatewayJob",
    "GatewayQueue",
    "GatewayQueueError",
    "InMemoryGatewayQueue",
    "build_gateway_job",
]
