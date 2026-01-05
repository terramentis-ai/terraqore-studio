"""Gateway worker that processes queued jobs into cache-aware batches."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from metaqore.logger import get_logger
from metaqore.mock_llm import MockLLMClient

from .engine import PromptAssemblyEngine
from .queue import GatewayJob, GatewayQueue
from .scheduler import CacheAwareBatchScheduler, GatewayBatch

logger = get_logger(__name__)

BatchProcessor = Callable[[GatewayBatch], None]


@dataclass(slots=True)
class GatewayJobResult:
    """LLM execution result for a single gateway job."""

    job_id: str
    artifact_id: str
    provider: str
    model: str
    content: str
    success: bool
    error: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


def logging_batch_processor(batch: GatewayBatch) -> None:
    """Default processor that logs batch metadata for observability."""

    logger.info(
        "Processing gateway batch",
        extra={
            "batch_id": batch.batch_id,
            "profile_hash": batch.profile_hash,
            "job_count": len(batch.jobs),
            "total_tokens": batch.total_tokens,
        },
    )


class GatewayWorker:
    """Background worker that dequeues jobs and assembles cache-friendly batches."""

    DEFAULT_PROFILE_TEMPLATE = (
        "You are a specialized MetaQore agent. Read the task context carefully and respond with" " actionable steps.\n\n"
        "{task_context}"
    )

    def __init__(
        self,
        *,
        queue: GatewayQueue,
        scheduler: CacheAwareBatchScheduler,
        processor: BatchProcessor = logging_batch_processor,
        poll_interval: float = 0.25,
        max_dequeue: int = 32,
        prompt_engine: Optional[PromptAssemblyEngine] = None,
        llm_client: Optional[MockLLMClient] = None,
        result_handler: Optional[Callable[[GatewayJobResult], None]] = None,
    ) -> None:
        if max_dequeue <= 0:
            raise ValueError("max_dequeue must be positive")
        self._queue = queue
        self._scheduler = scheduler
        self._processor = processor
        self._poll_interval = poll_interval
        self._max_dequeue = max_dequeue
        self._prompt_engine = prompt_engine or PromptAssemblyEngine()
        self._llm_client = llm_client or MockLLMClient(latency_range=(0, 0))
        self._result_handler = result_handler
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._recent_results: List[GatewayJobResult] = []

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="GatewayWorker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def run_once(self) -> int:
        jobs = self._queue.dequeue(max_items=self._max_dequeue)
        if not jobs:
            return 0
        batches = self._scheduler.build_batches(jobs)
        for batch in batches:
            results = self._execute_batch(batch)
            if results:
                self._recent_results.extend(results)
                if self._result_handler:
                    for result in results:
                        self._result_handler(result)
            self._processor(batch)
        return len(batches)

    def drain_results(self) -> List[GatewayJobResult]:
        drained = list(self._recent_results)
        self._recent_results.clear()
        return drained

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            processed = self.run_once()
            if processed == 0:
                self._stop_event.wait(self._poll_interval)

    def _execute_batch(self, batch: GatewayBatch) -> List[GatewayJobResult]:
        results: List[GatewayJobResult] = []
        for job in batch.jobs:
            agent_metadata = self._extract_metadata(job)
            agent_name = agent_metadata.get("agent_name") or job.skill_id
            self._ensure_profile(agent_name)
            task_context = self._build_task_context(job, agent_metadata)
            prompt = self._prompt_engine.assemble_prompt(
                agent_name,
                task_context,
                overrides=agent_metadata,
            )
            response = self._llm_client.generate(
                prompt.prompt,
                agent_name=agent_name,
                metadata={**agent_metadata, "job_id": job.job_id},
            )
            result = GatewayJobResult(
                job_id=job.job_id,
                artifact_id=job.artifact_id,
                provider=response.provider,
                model=response.model,
                content=response.content,
                success=response.success,
                error=response.error,
                metadata={
                    "profile_hash": prompt.profile_hash,
                    "job_payload": job.payload,
                    "llm_metadata": response.metadata,
                },
            )
            results.append(result)
        return results

    def _ensure_profile(self, agent_name: str) -> None:
        if not self._prompt_engine.has_profile(agent_name):
            self._prompt_engine.register_profile(agent_name, template=self.DEFAULT_PROFILE_TEMPLATE)

    @staticmethod
    def _extract_metadata(job: GatewayJob) -> Dict[str, Any]:
        payload_metadata = job.payload.get("metadata") if isinstance(job.payload, dict) else None
        if isinstance(payload_metadata, dict):
            return dict(payload_metadata)
        return {}

    @staticmethod
    def _format_teachers(job: GatewayJob) -> str:
        teachers = job.payload.get("teachers") if isinstance(job.payload, dict) else None
        if isinstance(teachers, list):
            return ", ".join(str(teacher) for teacher in teachers) or "(none)"
        return "(unknown)"

    def _build_task_context(self, job: GatewayJob, metadata: Dict[str, Any]) -> str:
        hmcp_meta = metadata.get("hmcp_metadata") if isinstance(metadata.get("hmcp_metadata"), dict) else {}
        intent = metadata.get("intent") or hmcp_meta.get("intent") or "specialist_training"
        level_key = job.payload.get("level_key") if isinstance(job.payload, dict) else None
        level_type = job.payload.get("level_type") if isinstance(job.payload, dict) else None
        parameter_count = job.payload.get("parameter_count") if isinstance(job.payload, dict) else None
        confidence = job.payload.get("confidence") if isinstance(job.payload, dict) else None
        requested_size = metadata.get("requested_size_mb") or hmcp_meta.get("requested_size_mb")
        summary = metadata.get("summary") or metadata.get("description")
        teachers = self._format_teachers(job)

        context_lines = [f"Intent: {intent}", f"Project: {job.project_id}"]
        context_lines.append(f"Skill: {job.skill_id}")
        if level_key:
            context_lines.append(f"Target level: {level_key} ({level_type or 'unknown'})")
        if parameter_count:
            context_lines.append(f"Parameter count: {parameter_count}")
        if confidence is not None:
            context_lines.append(f"Confidence: {confidence}")
        context_lines.append(f"Teachers: {teachers}")
        if requested_size:
            context_lines.append(f"Requested size: {requested_size} MB")
        if summary:
            context_lines.append(f"Summary: {summary}")
        if hmcp_meta:
            context_lines.append(f"HMCP Metadata: {hmcp_meta}")

        return "\n".join(context_lines)


__all__ = [
    "GatewayWorker",
    "logging_batch_processor",
    "BatchProcessor",
    "GatewayJobResult",
]
