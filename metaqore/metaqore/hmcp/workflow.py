"""HMCP specialist workflow utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Union

from metaqore.core.models import SpecialistLifecycle, SpecialistModel

from .policy import (
    ChainingLevel,
    ChainingPolicyError,
    HierarchicalChainingPolicy,
    SpawnDecision,
)
from .registry import SkillDefinition, SkillRegistry


LevelIdentifier = Union[int, str]


class SpecialistWorkflowError(RuntimeError):
    """Raised when a specialist proposal fails policy validation."""


@dataclass(frozen=True)
class SpecialistProposal:
    """Structured request to create or spawn a specialist model."""

    skill_id: str
    requested_size_mb: int
    teachers: Sequence[str]
    confidence: float
    task_isolation_passed: bool
    parent_level_identifier: Optional[LevelIdentifier] = None
    parameter_count: Optional[int] = None

    def __post_init__(self) -> None:
        if self.requested_size_mb <= 0:
            raise ValueError("requested_size_mb must be positive")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not self.teachers:
            raise ValueError("at least one teacher must be provided")
        object.__setattr__(self, "teachers", tuple(self.teachers))


@dataclass(frozen=True)
class ProposalEvaluation:
    """Outcome of validating a specialist proposal."""

    allowed: bool
    reasons: Sequence[str]
    skill: SkillDefinition
    target_level: Optional[ChainingLevel]
    spawn_decision: Optional[SpawnDecision]


class SpecialistWorkflow:
    """Coordinates SkillRegistry and hierarchy policy checks."""

    def __init__(self, registry: SkillRegistry, policy: HierarchicalChainingPolicy) -> None:
        self._registry = registry
        self._policy = policy

    @classmethod
    def from_policy(cls) -> "SpecialistWorkflow":
        return cls(SkillRegistry.from_policy(), HierarchicalChainingPolicy.from_policy())

    @property
    def registry(self) -> SkillRegistry:
        return self._registry

    @property
    def policy(self) -> HierarchicalChainingPolicy:
        return self._policy

    def evaluate_proposal(self, proposal: SpecialistProposal) -> ProposalEvaluation:
        skill = self._registry.ensure_registered(proposal.skill_id)
        errors: list[str] = []
        notes: list[str] = []

        if proposal.requested_size_mb > skill.max_specialist_size_mb:
            errors.append(
                "Requested specialist size exceeds registry maximum "
                f"({proposal.requested_size_mb} MB > {skill.max_specialist_size_mb} MB)"
            )
        else:
            notes.append("Requested size within registry limits")

        allowed_teachers = set(skill.allowed_teachers)
        invalid_teachers = [teacher for teacher in proposal.teachers if teacher not in allowed_teachers]
        if invalid_teachers:
            errors.append(
                    f"Teachers not permitted for skill '{skill.skill_id}': "
                + ", ".join(sorted(invalid_teachers))
            )
        else:
            notes.append("Teacher list approved by registry policy")

        target_level: Optional[ChainingLevel]
        spawn_decision: Optional[SpawnDecision] = None

        if proposal.parent_level_identifier is None:
            target_level = self._policy.get_level(1)
            notes.append("Top-level specialist proposal")
        else:
            spawn_decision = self._policy.evaluate_spawn_request(
                proposal.parent_level_identifier,
                confidence=proposal.confidence,
                task_isolation_passed=proposal.task_isolation_passed,
                candidate_parameter_count=proposal.parameter_count,
            )
            if spawn_decision.allowed:
                notes.extend(spawn_decision.reasons)
            else:
                errors.extend(spawn_decision.reasons)
            target_level = spawn_decision.next_level if spawn_decision.allowed else None

        if target_level is not None and proposal.parameter_count is not None:
            try:
                self._policy.validate_model_size(target_level.index, proposal.parameter_count)
                notes.append("Parameter count fits within hierarchy limits")
            except ChainingPolicyError as exc:
                errors.append(str(exc))
        elif target_level is None:
            errors.append("Unable to determine target specialist level from policy")

        allowed = not errors
        reasons = tuple(errors + (notes if allowed else []))
        return ProposalEvaluation(
            allowed=allowed,
            reasons=reasons,
            skill=skill,
            target_level=target_level,
            spawn_decision=spawn_decision,
        )

    def create_specialist_model(
        self,
        proposal: SpecialistProposal,
        *,
        project_id: str,
        created_by: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SpecialistModel:
        evaluation = self.evaluate_proposal(proposal)
        if not evaluation.allowed or evaluation.target_level is None:
            joined = "; ".join(evaluation.reasons)
            raise SpecialistWorkflowError(f"Specialist proposal rejected: {joined}")

        enriched_metadata: Dict[str, Any] = {**(metadata or {})}
        enriched_metadata.setdefault("skill_description", evaluation.skill.description)
        enriched_metadata.setdefault("hmcp_level", evaluation.target_level.key)
        enriched_metadata.setdefault("hmcp_level_type", evaluation.target_level.level_type)
        enriched_metadata.setdefault("teachers", list(proposal.teachers))
        enriched_metadata.setdefault("requested_size_mb", proposal.requested_size_mb)

        return SpecialistModel(
            project_id=project_id,
            data=data,
            created_by=created_by,
            skill_id=proposal.skill_id,
            parent_agent=evaluation.skill.parent_agent,
            teachers=list(proposal.teachers),
            level_key=evaluation.target_level.key,
            level_type=evaluation.target_level.level_type,
            parameter_count=proposal.parameter_count,
            confidence=proposal.confidence,
            lifecycle_state=SpecialistLifecycle.PROPOSED,
            task_isolation_passed=proposal.task_isolation_passed,
            metadata=enriched_metadata,
        )


__all__ = [
    "ProposalEvaluation",
    "SpecialistProposal",
    "SpecialistWorkflow",
    "SpecialistWorkflowError",
]
