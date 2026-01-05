"""PSMP client utilities dedicated to HMCP specialist artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from metaqore.core.models import Provenance, SpecialistLifecycle, SpecialistModel
from metaqore.core.state_manager import StateManager
from metaqore.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class LifecycleTransition:
    """Represents a single lifecycle movement for a specialist."""

    from_state: SpecialistLifecycle
    to_state: SpecialistLifecycle
    reason: Optional[str] = None


class PSMPClient:
    """High-level helper that records HMCP specialist events via PSMP."""

    def __init__(self, state_manager: StateManager) -> None:
        self._state_manager = state_manager

    def register_specialist(self, specialist: SpecialistModel) -> SpecialistModel:
        """Declare the specialist artifact through PSMP."""

        persisted = self._state_manager.create_artifact(specialist)
        logger.info(
            "Registered specialist %s for project %s", persisted.id, persisted.project_id
        )
        return persisted

    def advance_lifecycle(
        self,
        specialist: SpecialistModel,
        next_state: SpecialistLifecycle,
        *,
        actor: str,
        reason: str | None = None,
        metadata: Optional[Dict[str, object]] = None,
    ) -> SpecialistModel:
        """Persist a lifecycle state change with provenance."""

        prior_state = specialist.lifecycle_state
        specialist.advance_state(next_state)
        if metadata:
            specialist.metadata.update(metadata)
        provenance = Provenance(
            artifact_id=specialist.id,
            actor=actor,
            action=f"hmcp.lifecycle.{next_state.value}",
            reason=reason,
            metadata={"from": prior_state.value, "to": next_state.value},
        )
        specialist.add_provenance(provenance)
        saved = self._state_manager.save_artifact(specialist)
        logger.info(
            "Specialist %s moved from %s to %s", saved.id, prior_state.value, next_state.value
        )
        return saved

    def attach_metadata(
        self,
        specialist: SpecialistModel,
        *,
        updates: Dict[str, object],
    ) -> SpecialistModel:
        """Merge metadata updates and persist via PSMP."""

        specialist.metadata.update(updates)
        return self._state_manager.save_artifact(specialist)


__all__ = ["LifecycleTransition", "PSMPClient"]
