"""Service layer exposing HMCP specialist workflow operations."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional

from metaqore.core.models import SpecialistModel
from metaqore.gateway import GatewayQueue, build_gateway_job

from .orchestrator import ChainingOrchestrator, ChainingOutcome
from .workflow import ProposalEvaluation, SpecialistProposal, SpecialistWorkflow


class HMCPService:
    """High-level facade for evaluating and drafting HMCP specialists."""

    def __init__(
        self,
        workflow: Optional[SpecialistWorkflow] = None,
        gateway_queue: Optional[GatewayQueue] = None,
        orchestrator: Optional[ChainingOrchestrator] = None,
    ) -> None:
        self._workflow = workflow or SpecialistWorkflow.from_policy()
        self._gateway_queue = gateway_queue
        self._orchestrator = orchestrator

    @property
    def workflow(self) -> SpecialistWorkflow:
        return self._workflow

    def attach_gateway_queue(self, queue: GatewayQueue) -> None:
        self._gateway_queue = queue

    def attach_orchestrator(self, orchestrator: ChainingOrchestrator) -> None:
        self._orchestrator = orchestrator

    def evaluate_proposal(self, proposal: SpecialistProposal) -> ProposalEvaluation:
        """Run registry + policy checks for a specialist proposal."""

        return self._workflow.evaluate_proposal(proposal)

    def run_autonomous_workflow(
        self,
        proposal: SpecialistProposal,
        *,
        project_id: str,
        created_by: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> tuple[ChainingOutcome, Optional[str]]:
        """Execute the full chaining orchestrator pipeline."""

        if self._orchestrator is None:
            raise RuntimeError("ChainingOrchestrator not configured for HMCPService")
        outcome = self._orchestrator.run_pipeline(
            proposal,
            project_id=project_id,
            created_by=created_by,
            data=data,
            metadata=metadata,
        )
        gateway_job_id = self.enqueue_training_job(outcome.specialist) if outcome.activated else None
        return outcome, gateway_job_id

    def draft_specialist_model(
        self,
        proposal: SpecialistProposal,
        *,
        project_id: str,
        created_by: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SpecialistModel:
        """Generate a SpecialistModel instance for downstream persistence."""

        merged_metadata = self._prepare_metadata(proposal, metadata)
        return self._workflow.create_specialist_model(
            proposal,
            project_id=project_id,
            created_by=created_by,
            data=data,
            metadata=merged_metadata,
        )

    def enqueue_training_job(self, specialist: SpecialistModel) -> Optional[str]:
        """Dispatch a training job to the LLM gateway queue."""

        if self._gateway_queue is None:
            return None

        metadata = specialist.metadata or {}
        provider = metadata.get("llm_provider", "hmcp_gateway")
        profile_hash = self._build_profile_hash(specialist)
        payload: Dict[str, Any] = {
            "skill_id": specialist.skill_id,
            "teachers": specialist.teachers,
            "level_key": specialist.level_key,
            "level_type": specialist.level_type,
            "parameter_count": specialist.parameter_count,
            "confidence": specialist.confidence,
            "metadata": metadata,
        }

        requested_size = int(metadata.get("requested_size_mb", 0))
        estimated_tokens = max(1024, requested_size * 1000)
        job = build_gateway_job(
            artifact_id=specialist.id,
            project_id=specialist.project_id,
            skill_id=specialist.skill_id,
            provider_hint=provider,
            profile_hash=profile_hash,
            payload=payload,
            estimated_tokens=estimated_tokens,
        )
        self._gateway_queue.enqueue(job)
        return job.job_id

    def _prepare_metadata(
        self,
        proposal: SpecialistProposal,
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        enriched = {**(metadata or {})}
        enriched.setdefault("task_type", "hmcp_specialist_creation")
        enriched.setdefault("agent_name", proposal.skill_id)
        enriched.setdefault("llm_provider", "hmcp_gateway")
        enriched.setdefault("has_private_data", False)
        enriched.setdefault("has_sensitive_data", True)
        enriched.setdefault("hmcp_teacher_count", len(proposal.teachers))
        hmcp_meta = enriched.setdefault("hmcp_metadata", {})
        hmcp_meta.setdefault("parent_level_identifier", proposal.parent_level_identifier)
        hmcp_meta.setdefault("requested_size_mb", proposal.requested_size_mb)
        hmcp_meta.setdefault("intent", "specialist_training")
        return enriched

    @staticmethod
    def _build_profile_hash(specialist: SpecialistModel) -> str:
        digest = hashlib.sha256()
        digest.update(f"{specialist.parent_agent}:{specialist.level_key}".encode("utf-8"))
        digest.update(
            ":".join(sorted(str(teacher) for teacher in specialist.teachers)).encode("utf-8")
        )
        return digest.hexdigest()[:32]


__all__ = ["HMCPService"]
