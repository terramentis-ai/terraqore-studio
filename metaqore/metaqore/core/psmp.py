"""Implementation of the Project State Management Protocol (PSMP)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from metaqore.config import MetaQoreConfig
from metaqore.core.models import (
    Artifact,
    BlockingReport,
    Conflict,
    ConflictSeverity,
    Project,
    ResolutionStrategy,
)
from metaqore.exceptions import ConflictDetectedError
from metaqore.streaming.events import Event, EventType
from metaqore.streaming.hub import get_event_hub
from metaqore.logger import get_logger

logger = get_logger(__name__)


class PSMPEngine:
    """Core governance layer that validates and declares artifacts."""

    def __init__(self, state_manager: Any, *, config: Optional[MetaQoreConfig] = None) -> None:
        self.config = config or MetaQoreConfig()
        self.state_manager = state_manager

    # ------------------------------------------------------------------
    # Artifact lifecycle
    # ------------------------------------------------------------------
    def create_artifact(
        self,
        *,
        project_id: str,
        artifact_type: str,
        data: Dict[str, Any],
        created_by: str,
        depends_on: Optional[Sequence[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Artifact:
        project = self._get_project(project_id)
        version = self._next_version(project_id, artifact_type)
        artifact = Artifact(
            project_id=project.id,
            artifact_type=artifact_type,
            data=data,
            created_by=created_by,
            version=version,
            depends_on=list(depends_on or []),
            metadata=metadata or {},
        )
        return artifact

    def declare_artifact(self, artifact: Artifact, *, persist: bool = True) -> Artifact:
        conflicts = self.check_conflicts(artifact)
        if conflicts:
            artifact.blocked_by = conflicts
            conflict_ids = ", ".join(conflict.id for conflict in conflicts)
            logger.warning(
                "Artifact %s blocked by conflicts: %s", artifact.id, conflict_ids, extra={"project_id": artifact.project_id}
            )
            self._emit_conflict_event(artifact.project_id, artifact.id, conflicts)
            raise ConflictDetectedError(
                "Artifact declaration blocked by conflicts",
                metadata={
                    "artifact_id": artifact.id,
                    "project_id": artifact.project_id,
                    "conflict_ids": conflict_ids,
                },
            )
        if persist:
            self.state_manager.save_artifact(artifact)
        return artifact

    def check_conflicts(self, artifact: Artifact) -> List[Conflict]:
        conflicts: List[Conflict] = []
        existing = self.state_manager.list_artifacts(artifact.project_id)
        conflicts.extend(self._check_version_conflict(artifact, existing))
        conflicts.extend(self._check_parallel_agent_conflict(artifact, existing))
        conflicts.extend(self._validate_dependencies(artifact))
        return conflicts

    def get_blocking_report(self, project_id: str) -> BlockingReport:
        artifacts = self.state_manager.list_artifacts(project_id)
        return BlockingReport.from_artifacts(project_id, artifacts)

    def resolve_conflict(self, conflict: Conflict, strategy: ResolutionStrategy) -> Conflict:
        conflict.mark_resolved(strategy)
        self.state_manager.update_conflict(conflict)
        logger.info("Resolved conflict %s via %s", conflict.id, strategy.value, extra={"project_id": conflict.project_id})
        return conflict

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_project(self, project_id: str) -> Project:
        project = self.state_manager.get_project(project_id)
        if project is None:
            raise ValueError(f"Project {project_id} not found")
        return project

    def _next_version(self, project_id: str, artifact_type: str) -> int:
        artifacts = self.state_manager.list_artifacts(project_id)
        versions = [artifact.version for artifact in artifacts if artifact.artifact_type == artifact_type]
        return (max(versions) + 1) if versions else 1

    def _check_version_conflict(self, artifact: Artifact, existing: Sequence[Artifact]) -> List[Conflict]:
        conflicts: List[Conflict] = []
        relevant = [a for a in existing if a.artifact_type == artifact.artifact_type]
        if not relevant:
            return conflicts
        expected_version = max(a.version for a in relevant) + 1
        if artifact.version != expected_version:
            conflicts.append(
                Conflict(
                    artifact_id=artifact.id,
                    project_id=artifact.project_id,
                    description=(
                        f"Invalid version: expected {expected_version} after {len(relevant)} prior versions, "
                        f"got {artifact.version}."
                    ),
                    severity=ConflictSeverity.MEDIUM,
                    conflict_type="version_mismatch",
                    resolution_strategy=ResolutionStrategy.RETRY,
                )
            )
        return conflicts

    def _check_parallel_agent_conflict(self, artifact: Artifact, existing: Sequence[Artifact]) -> List[Conflict]:
        conflicts: List[Conflict] = []
        clashes = [a for a in existing if a.artifact_type == artifact.artifact_type and a.created_by != artifact.created_by]
        if clashes:
            conflicts.append(
                Conflict(
                    artifact_id=artifact.id,
                    project_id=artifact.project_id,
                    description="Parallel artifact creation detected from multiple agents",
                    severity=ConflictSeverity.HIGH,
                    conflict_type="parallel_creation",
                    resolution_strategy=ResolutionStrategy.MERGE,
                )
            )
        return conflicts

    def _validate_dependencies(self, artifact: Artifact) -> List[Conflict]:
        conflicts: List[Conflict] = []
        for dependency_id in artifact.depends_on:
            dependency = self.state_manager.get_artifact(dependency_id)
            if dependency is None:
                conflicts.append(
                    Conflict(
                        artifact_id=artifact.id,
                        project_id=artifact.project_id,
                        description=f"Missing dependency {dependency_id}",
                        severity=ConflictSeverity.HIGH,
                        conflict_type="missing_dependency",
                        resolution_strategy=ResolutionStrategy.RETRY,
                    )
                )
                continue
            if artifact.id == dependency_id or artifact.id in dependency.depends_on:
                conflicts.append(
                    Conflict(
                        artifact_id=artifact.id,
                        project_id=artifact.project_id,
                        description=f"Circular dependency between {artifact.id} and {dependency_id}",
                        severity=ConflictSeverity.CRITICAL,
                        conflict_type="circular_dependency",
                        resolution_strategy=ResolutionStrategy.ESCALATE,
                    )
                )
        return conflicts

    def _emit_conflict_event(self, project_id: str, artifact_id: str, conflicts: Sequence[Conflict]) -> None:
        # Serialize conflicts to dicts before including in event changes
        conflicts_data = [conflict.model_dump(mode='json') for conflict in conflicts]
        event = Event(
            event_type=EventType.CONFLICT_DETECTED,
            resource_id=artifact_id,
            resource_type="artifact",
            project_id=project_id,
            changes={
                "artifact_id": artifact_id,
                "conflicts": conflicts_data,
            },
        )
        get_event_hub().emit(event)


__all__ = ["PSMPEngine"]
