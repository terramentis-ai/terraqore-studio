"""Unit tests for MetaQore LLM Gateway infrastructure."""

from __future__ import annotations

from metaqore.gateway import (
    CacheAwareBatchScheduler,
    GatewayWorker,
    InMemoryGatewayQueue,
    PromptAssemblyEngine,
    build_gateway_job,
)
from metaqore.mock_llm import MockLLMClient


def test_in_memory_gateway_queue_roundtrip() -> None:
    queue = InMemoryGatewayQueue()
    job = build_gateway_job(
        artifact_id="art_1",
        project_id="proj",
        skill_id="skill",
        provider_hint="hmcp_gateway",
        profile_hash="hash_a",
        payload={"example": True},
        estimated_tokens=512,
    )

    queue.enqueue(job)
    assert queue.size() == 1
    peeked = queue.peek()
    assert peeked == job

    pulled = queue.dequeue()
    assert pulled == [job]
    assert queue.size() == 0


def test_cache_aware_scheduler_respects_profile_hash() -> None:
    scheduler = CacheAwareBatchScheduler(max_batch_tokens=1024)
    jobs = [
        build_gateway_job(
            artifact_id=f"art_{idx}",
            project_id="proj",
            skill_id="skill",
            provider_hint="hmcp_gateway",
            profile_hash="hash_a" if idx < 2 else "hash_b",
            payload={"idx": idx},
            estimated_tokens=600,
        )
        for idx in range(3)
    ]

    batches = scheduler.build_batches(jobs)
    assert len(batches) == 3  # hash_a split into two batches, hash_b single batch
    profile_hashes = {batch.profile_hash for batch in batches}
    assert profile_hashes == {"hash_a", "hash_b"}
    assert sum(batch.total_tokens for batch in batches) >= 1800


def test_gateway_worker_run_once_processes_batches() -> None:
    queue = InMemoryGatewayQueue()
    scheduler = CacheAwareBatchScheduler(max_batch_tokens=2048)
    processed_batches: list[str] = []

    def _processor(batch):
        processed_batches.append(batch.batch_id)

    worker = GatewayWorker(queue=queue, scheduler=scheduler, processor=_processor, max_dequeue=10)

    for idx in range(3):
        queue.enqueue(
            build_gateway_job(
                artifact_id=f"art_{idx}",
                project_id="proj",
                skill_id="skill",
                provider_hint="hmcp_gateway",
                profile_hash="hash_shared",
                payload={"idx": idx},
                estimated_tokens=500,
            )
        )

    processed = worker.run_once()
    assert processed == 1  # single batch because all share same profile hash
    assert len(processed_batches) == 1
    assert queue.size() == 0


def test_gateway_worker_executes_jobs_with_prompt_engine_and_llm() -> None:
    queue = InMemoryGatewayQueue()
    scheduler = CacheAwareBatchScheduler(max_batch_tokens=4096)
    prompt_engine = PromptAssemblyEngine()
    prompt_engine.register_profile("clean_akkadian_dates", template="{task_context}")
    llm_client = MockLLMClient(latency_range=(0, 0))

    captured_results = []

    worker = GatewayWorker(
        queue=queue,
        scheduler=scheduler,
        processor=lambda _: None,
        prompt_engine=prompt_engine,
        llm_client=llm_client,
        result_handler=captured_results.append,
    )

    job = build_gateway_job(
        artifact_id="art_gateway",
        project_id="proj_gateway",
        skill_id="clean_akkadian_dates",
        provider_hint="hmcp_gateway",
        profile_hash="hash_gateway",
        payload={
            "level_key": "level_1",
            "level_type": "domain_specialist",
            "parameter_count": 5_000_000,
            "confidence": 0.97,
            "teachers": ["BaseAgent", "ValidatorAgent"],
            "metadata": {
                "agent_name": "clean_akkadian_dates",
                "requested_size_mb": 25,
                "summary": "Normalize Akkadian date formats",
                "hmcp_metadata": {"intent": "specialist_training"},
            },
        },
        estimated_tokens=600,
    )
    queue.enqueue(job)

    processed = worker.run_once()
    assert processed == 1

    drained = worker.drain_results()
    assert len(drained) == 1
    result = drained[0]
    assert result.job_id == job.job_id
    assert result.success is True
    assert "clean_akkadian_dates" in result.content
    assert captured_results[0] == result
