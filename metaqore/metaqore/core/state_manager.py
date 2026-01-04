"""StateManager orchestrates persistence with governance safeguards."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, TYPE_CHECKING

from metaqore.core.models import Artifact, Checkpoint, Conflict, Project, Task
from metaqore.core.security import SecureGateway
from metaqore.exceptions import ConflictDetectedError, VetoAppliedError, VetoExceptionContext
from metaqore.logger import get_logger
from metaqore.storage.backend import StorageBackend

if TYPE_CHECKING:  # pragma: no cover - circular import guard
    from metaqore.core.psmp import PSMPEngine

logger = get_logger(__name__)


class StateManager:
    """High-level persistence API with PSMP-aware safeguards."""

    def __init__(
        self,
        backend: StorageBackend,
        *,
        psmp_engine: Optional["PSMPEngine"] = None,
        checkpoint_retention: Optional[int] = 5,
        secure_gateway: Optional[SecureGateway] = None,
    ) -> None:
        self._backend = backend
        self._psmp_engine = psmp_engine
        self._checkpoint_retention = checkpoint_retention
        self._secure_gateway = secure_gateway

    # ------------------------------------------------------------------
    # Wiring helpers
    # ------------------------------------------------------------------
    def attach_psmp_engine(self, psmp_engine: "PSMPEngine") -> None:
        """Attach the PSMP engine after initialization to avoid import cycles."""

        self._psmp_engine = psmp_engine

    def attach_secure_gateway(self, secure_gateway: SecureGateway) -> None:
        """Attach SecureGateway dynamically for security-aware routing."""

        self._secure_gateway = secure_gateway

    def _require_psmp_engine(self) -> "PSMPEngine":
        if self._psmp_engine is None:
            raise RuntimeError("PSMP engine not attached to StateManager")
        return self._psmp_engine

    # ------------------------------------------------------------------
    # Project lifecycle
    # ------------------------------------------------------------------
    def create_project(self, project: Project) -> Project:
        logger.debug("Creating project %s", project.id)
        return self._backend.save_project(project)

    def get_project(self, project_id: str) -> Optional[Project]:
        project = self._backend.get_project(project_id)
        if project is None:
            return None
        project.artifacts = self.list_artifacts(project_id)
        project.tasks = self.list_tasks(project_id)
        return project

    def update_project(self, project_id: str, updates: Dict[str, object]) -> Project:
        project = self.get_project(project_id)
        if project is None:
            raise ValueError(f"Project {project_id} not found")
        updated = project.model_copy(update=updates)
        logger.debug("Updating project %s", project_id)
        return self._backend.save_project(updated)

    def delete_project(self, project_id: str) -> None:
        logger.info("Deleting project %s", project_id)
        self._backend.delete_project(project_id)

    def list_projects(self) -> List[Project]:
        return self._backend.list_projects()

    # ------------------------------------------------------------------
    # Artifact lifecycle
    # ------------------------------------------------------------------
    def create_artifact(self, artifact: Artifact) -> Artifact:
        """Run artifact through PSMP before persisting."""

        engine = self._require_psmp_engine()
        self._enforce_security_for_artifact(artifact)
        try:
            return engine.declare_artifact(artifact, persist=True)
        except ConflictDetectedError:
            # Conflicts already logged by engine; bubble up for caller handling.
            raise

    def save_artifact(self, artifact: Artifact) -> Artifact:
        return self._backend.save_artifact(artifact)

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        return self._backend.get_artifact(artifact_id)

    def get_artifacts(self, project_id: str) -> List[Artifact]:
        return self._backend.list_artifacts(project_id)

    def list_artifacts(self, project_id: str) -> List[Artifact]:
        return self.get_artifacts(project_id)

    def delete_artifact(self, artifact_id: str) -> None:
        self._backend.delete_artifact(artifact_id)

    # ------------------------------------------------------------------
    # Task lifecycle
    # ------------------------------------------------------------------
    def create_task(self, task: Task) -> Task:
        logger.debug("Creating task %s for project %s", task.id, task.project_id)
        return self._backend.save_task(task)

    def save_task(self, task: Task) -> Task:
        return self._backend.save_task(task)

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._backend.get_task(task_id)

    def get_tasks(self, project_id: str) -> List[Task]:
        return self._backend.list_tasks(project_id)

    def list_tasks(self, project_id: str) -> List[Task]:
        return self.get_tasks(project_id)

    def delete_task(self, task_id: str) -> None:
        self._backend.delete_task(task_id)

    # ------------------------------------------------------------------
    # Conflicts
    # ------------------------------------------------------------------
    def save_conflicts(self, conflicts: Iterable[Conflict]) -> None:
        self._backend.save_conflicts(conflicts)

    def update_conflict(self, conflict: Conflict) -> Conflict:
        return self._backend.update_conflict(conflict)

    def list_conflicts(self, project_id: str) -> List[Conflict]:
        return self._backend.list_conflicts(project_id)

    # ------------------------------------------------------------------
    # Checkpoints (stubs for future expansion)
    # ------------------------------------------------------------------
    def create_checkpoint(self, project_id: str, label: str) -> Checkpoint:
        project = self.get_project(project_id)
        if project is None:
            raise ValueError(f"Cannot checkpoint missing project {project_id}")
        snapshot = self._capture_state(project)
        checkpoint = Checkpoint(project_id=project_id, label=label, snapshot=snapshot)
        saved = self._write_checkpoint(checkpoint)
        self._enforce_checkpoint_retention(project_id)
        logger.info("Checkpoint %s captured for project %s", saved.id, project_id)
        return saved

    def get_checkpoints(self, project_id: str) -> List[Checkpoint]:
        return self._backend.list_checkpoints(project_id)

    def restore_checkpoint(self, checkpoint_id: str) -> Project:
        checkpoint = self._backend.get_checkpoint(checkpoint_id)
        if checkpoint is None:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        project_id = checkpoint.project_id
        existing_project = self.get_project(project_id)
        if existing_project is not None:
            backup_label = f"auto-backup-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
            self.create_checkpoint(project_id, backup_label)

        stored_checkpoints = self._backend.list_checkpoints(project_id)
        snapshot = checkpoint.snapshot or {}
        project_payload: Optional[Dict[str, Any]] = snapshot.get("project")
        if not project_payload:
            raise ValueError(f"Checkpoint {checkpoint_id} missing project payload")

        artifacts_payload = snapshot.get("artifacts", [])
        tasks_payload = snapshot.get("tasks", [])
        conflicts_payload = snapshot.get("conflicts", [])

        project = Project.model_validate(project_payload)
        artifacts = [Artifact.model_validate(payload) for payload in artifacts_payload]
        tasks = [Task.model_validate(payload) for payload in tasks_payload]
        conflicts = [Conflict.model_validate(payload) for payload in conflicts_payload]

        logger.info("Restoring project %s from checkpoint %s", project_id, checkpoint_id)
        self._backend.delete_project(project_id)
        self._backend.save_project(project)
        for artifact in artifacts:
            self._backend.save_artifact(artifact)
        for task in tasks:
            self._backend.save_task(task)
        if conflicts:
            self._backend.save_conflicts(conflicts)

        for stored_checkpoint in stored_checkpoints:
            self._backend.save_checkpoint(stored_checkpoint)

        restored = self.get_project(project_id)
        if restored is None:
            raise RuntimeError(f"Failed to restore project {project_id} from checkpoint {checkpoint_id}")
        return restored

    def save_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint:
        return self._backend.save_checkpoint(checkpoint)

    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        return self._backend.get_checkpoint(checkpoint_id)

    def list_checkpoints(self, project_id: str) -> List[Checkpoint]:
        return self._backend.list_checkpoints(project_id)

    def delete_checkpoint(self, checkpoint_id: str) -> None:
        self._backend.delete_checkpoint(checkpoint_id)

    # ------------------------------------------------------------------
    # Checkpoint helpers
    # ------------------------------------------------------------------
    def _capture_state(self, project: Project) -> Dict[str, Any]:
        def _artifact_payload(artifact: Artifact) -> Dict[str, Any]:
            payload = artifact.model_dump(mode="json")
            payload.pop("is_blocked", None)
            return payload

        artifacts = [_artifact_payload(artifact) for artifact in project.artifacts]
        tasks = [task.model_dump(mode="json") for task in project.tasks]
        conflicts = [conflict.model_dump(mode="json") for conflict in self.list_conflicts(project.id)]
        project_payload = project.model_dump(mode="json")
        project_payload["artifacts"] = artifacts
        return {
            "project": project_payload,
            "artifacts": artifacts,
            "tasks": tasks,
            "conflicts": conflicts,
        }

    def _write_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint:
        return self._backend.save_checkpoint(checkpoint)

    def _enforce_checkpoint_retention(self, project_id: str) -> None:
        if not self._checkpoint_retention or self._checkpoint_retention <= 0:
            return
        checkpoints = self._backend.list_checkpoints(project_id)
        if len(checkpoints) <= self._checkpoint_retention:
            return
        checkpoints.sort(key=lambda chk: chk.created_at)
        excess = len(checkpoints) - self._checkpoint_retention
        for checkpoint in checkpoints[:excess]:
            logger.debug(
                "Pruning checkpoint %s for project %s (retention=%s)",
                checkpoint.id,
                project_id,
                self._checkpoint_retention,
            )
            self._backend.delete_checkpoint(checkpoint.id)

    def _enforce_security_for_artifact(self, artifact: Artifact) -> None:
        if self._secure_gateway is None:
            return
        metadata = artifact.metadata or {}
        provider = metadata.get("llm_provider")
        if not provider:
            return
        agent_name = metadata.get("agent_name", artifact.created_by)
        task_type = metadata.get("task_type") or f"{artifact.artifact_type}_creation"
        has_private_data = bool(metadata.get("has_private_data"))
        has_sensitive_data = bool(metadata.get("has_sensitive_data"))
        is_security_task = bool(metadata.get("is_security_task"))

        allowed = self._secure_gateway.enforce_policy(
            agent_name=agent_name,
            task_type=task_type,
            provider=provider,
            has_private_data=has_private_data,
            has_sensitive_data=has_sensitive_data,
            is_security_task=is_security_task,
        )
        if allowed:
            return

        veto = self._secure_gateway.veto_graph_node(f"artifact:{artifact.id}")
        reason = veto.reason if veto else f"Provider '{provider}' blocked by {self._secure_gateway.policy.name}"
        policy = veto.policy_violated if veto else self._secure_gateway.policy.name
        severity = veto.severity.value if veto else "critical"
        context = VetoExceptionContext(
            agent_name=agent_name,
            task_type=task_type,
            reason=reason,
            policy=policy,
            severity=severity,
        )
        raise VetoAppliedError(context)


__all__ = ["StateManager"]
