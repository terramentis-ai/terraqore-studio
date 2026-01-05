"""Hierarchical chaining orchestrator executing the Week 9 roadmap."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from metaqore.core.models import SpecialistLifecycle, SpecialistModel
from metaqore.core.state_manager import StateManager
from metaqore.exceptions import ConflictDetectedError

from .config_loader import load_hmcp_config
from .psmp_client import PSMPClient
from .skill_manager import ProposalContext, SkillRegistryManager
from .training import MOPDTrainingLoop, TrainingOutcome
from .validation_gate import ValidationGateReport, ValidationGateRunner
from .workflow import SpecialistProposal, SpecialistWorkflow, SpecialistWorkflowError


@dataclass(frozen=True)
class ChainingOutcome:
    """Result of executing the HMCP chaining orchestrator."""

    specialist: SpecialistModel
    training: TrainingOutcome
    validation: ValidationGateReport

    @property
    def activated(self) -> bool:
        return self.specialist.lifecycle_state == SpecialistLifecycle.ACTIVE


class ChainingOrchestrator:
    """Coordinates registry, PSMP client, training loop, and validation gate."""

    def __init__(
        self,
        *,
        skill_manager: SkillRegistryManager,
        psmp_client: PSMPClient,
        training_loop: MOPDTrainingLoop,
        validation_runner: ValidationGateRunner,
    ) -> None:
        self._skills = skill_manager
        self._psmp = psmp_client
        self._training = training_loop
        self._validation = validation_runner

    @classmethod
    def build_default(cls, state_manager: StateManager) -> "ChainingOrchestrator":
        policy = load_hmcp_config()
        workflow = SpecialistWorkflow.from_policy()
        skill_manager = SkillRegistryManager(workflow)
        psmp_client = PSMPClient(state_manager)
        training_loop = MOPDTrainingLoop(policy.get("specialist_creation_engine", {}))
        validation_runner = ValidationGateRunner(policy.get("validation_gate", {}))
        return cls(
            skill_manager=skill_manager,
            psmp_client=psmp_client,
            training_loop=training_loop,
            validation_runner=validation_runner,
        )

    def run_pipeline(
        self,
        proposal: SpecialistProposal,
        *,
        project_id: str,
        created_by: str,
        data: Dict[str, object],
        metadata: Optional[Dict[str, object]] = None,
    ) -> ChainingOutcome:
        context = self._skills.evaluate(proposal)
        if not context.evaluation.allowed:
            joined = "; ".join(context.evaluation.reasons)
            raise SpecialistWorkflowError(joined)

        specialist = self._skills.create_specialist_model(
            context,
            project_id=project_id,
            created_by=created_by,
            data=data,
            metadata=metadata,
        )
        specialist = self._psmp.register_specialist(specialist)
        specialist = self._psmp.advance_lifecycle(
            specialist,
            SpecialistLifecycle.PSMP_VALIDATING,
            actor=created_by,
            reason="PSMP validation started",
        )
        specialist = self._psmp.advance_lifecycle(
            specialist,
            SpecialistLifecycle.MOPD_TRAINING,
            actor=created_by,
            reason="Training loop initialized",
        )

        training_outcome = self._training.run_training(specialist)
        specialist = self._psmp.attach_metadata(
            specialist,
            updates={"hmcp_training": training_outcome.to_dict()},
        )

        specialist = self._psmp.advance_lifecycle(
            specialist,
            SpecialistLifecycle.VALIDATION_GATING,
            actor=created_by,
            reason="Validation gate running",
        )
        validation_report = self._validation.run(specialist, training_outcome)
        specialist = self._psmp.attach_metadata(
            specialist,
            updates={"hmcp_validation": validation_report.to_dict()},
        )

        final_state = SpecialistLifecycle.ACTIVE if validation_report.passed else SpecialistLifecycle.BLOCKED
        reason = "Validation gate passed" if validation_report.passed else "Validation gate failed"
        specialist = self._psmp.advance_lifecycle(
            specialist,
            final_state,
            actor=created_by,
            reason=reason,
        )
        return ChainingOutcome(specialist=specialist, training=training_outcome, validation=validation_report)


__all__ = ["ChainingOrchestrator", "ChainingOutcome"]
