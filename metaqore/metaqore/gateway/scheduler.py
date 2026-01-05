"""Cache-aware batch scheduling for the MetaQore LLM Gateway."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Dict, Iterable, List

from .queue import GatewayJob


@dataclass
class GatewayBatch:
    """Batch of gateway jobs sharing the same profile hash."""

    batch_id: str
    profile_hash: str
    jobs: List[GatewayJob]
    total_tokens: int


class CacheAwareBatchScheduler:
    """Groups queued jobs by profile hash to maximize KV cache reuse."""

    def __init__(self, *, max_batch_tokens: int = 8192) -> None:
        if max_batch_tokens <= 0:
            raise ValueError("max_batch_tokens must be positive")
        self.max_batch_tokens = max_batch_tokens

    def build_batches(self, jobs: Iterable[GatewayJob]) -> List[GatewayBatch]:
        grouped: Dict[str, List[GatewayJob]] = {}
        for job in jobs:
            grouped.setdefault(job.profile_hash, []).append(job)

        batches: List[GatewayBatch] = []
        for profile_hash, job_list in grouped.items():
            current_batch: List[GatewayJob] = []
            current_tokens = 0
            for job in job_list:
                estimated = job.estimated_tokens or 0
                if current_batch and current_tokens + estimated > self.max_batch_tokens:
                    batches.append(
                        GatewayBatch(
                            batch_id=self._build_batch_id(),
                            profile_hash=profile_hash,
                            jobs=list(current_batch),
                            total_tokens=current_tokens,
                        )
                    )
                    current_batch.clear()
                    current_tokens = 0
                current_batch.append(job)
                current_tokens += estimated
            if current_batch:
                batches.append(
                    GatewayBatch(
                        batch_id=self._build_batch_id(),
                        profile_hash=profile_hash,
                        jobs=list(current_batch),
                        total_tokens=current_tokens,
                    )
                )
        return batches

    @staticmethod
    def _build_batch_id() -> str:
        return f"batch_{uuid.uuid4().hex[:12]}"


__all__ = ["CacheAwareBatchScheduler", "GatewayBatch"]
