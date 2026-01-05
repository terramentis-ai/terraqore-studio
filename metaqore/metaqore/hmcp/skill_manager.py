"""Skill registry management utilities for HMCP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from .registry import SkillDefinition, SkillRegistry
from .workflow import ProposalEvaluation, SpecialistProposal, SpecialistWorkflow, SpecialistWorkflowError


@dataclass(frozen=True)
class ProposalContext:
    """Carries supporting information for a specialist proposal."""

    evaluation: ProposalEvaluation
    proposal: SpecialistProposal


class SkillRegistryManager:
    """Wrapper that ties SkillRegistry and SpecialistWorkflow together."""

    def __init__(self, workflow: Optional[SpecialistWorkflow] = None) -> None:
        self._workflow = workflow or SpecialistWorkflow.from_policy()

    @property
    def workflow(self) -> SpecialistWorkflow:
        return self._workflow

    @property
    def registry(self) -> SkillRegistry:
        return self._workflow.registry

    def list_skills(self) -> List[SkillDefinition]:
        return self.registry.list_skills()

    def allowed_teachers(self, skill_id: str) -> Iterable[str]:
        return self.registry.allowed_teachers(skill_id)

    def evaluate(self, proposal: SpecialistProposal) -> ProposalContext:
        evaluation = self._workflow.evaluate_proposal(proposal)
        return ProposalContext(evaluation=evaluation, proposal=proposal)

    def create_specialist_model(
        self,
        context: ProposalContext,
        *,
        project_id: str,
        created_by: str,
        data: dict,
        metadata: Optional[dict] = None,
    ):
        if not context.evaluation.allowed:
            joined = "; ".join(context.evaluation.reasons)
            raise SpecialistWorkflowError(f"Specialist proposal rejected: {joined}")
        return self._workflow.create_specialist_model(
            context.proposal,
            project_id=project_id,
            created_by=created_by,
            data=data,
            metadata=metadata,
        )


__all__ = ["ProposalContext", "SkillRegistryManager"]
