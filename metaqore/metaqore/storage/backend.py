"""Abstract storage backend interface for MetaQore state persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, List, Optional

from metaqore.core.models import Artifact, Checkpoint, Conflict, Project, Task


class StorageBackend(ABC):
    """Storage-agnostic CRUD interface used by :class:`StateManager`."""

    # ------------------------------------------------------------------
    # Project lifecycle
    # ------------------------------------------------------------------
    @abstractmethod
    def save_project(self, project: Project) -> Project:  # pragma: no cover - interface definition
        """Create or update a project record."""

    @abstractmethod
    def get_project(self, project_id: str) -> Optional[Project]:  # pragma: no cover
        """Return the project if it exists."""

    @abstractmethod
    def delete_project(self, project_id: str) -> None:  # pragma: no cover
        """Remove a project and all related data."""

    @abstractmethod
    def list_projects(self) -> List[Project]:  # pragma: no cover
        """Return all projects in storage."""

    # ------------------------------------------------------------------
    # Artifacts
    # ------------------------------------------------------------------
    @abstractmethod
    def save_artifact(self, artifact: Artifact) -> Artifact:  # pragma: no cover
        """Persist an artifact (insert or update)."""

    @abstractmethod
    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:  # pragma: no cover
        """Fetch single artifact by ID."""

    @abstractmethod
    def list_artifacts(self, project_id: str) -> List[Artifact]:  # pragma: no cover
        """Return all artifacts for a project."""

    @abstractmethod
    def delete_artifact(self, artifact_id: str) -> None:  # pragma: no cover
        """Remove an artifact by ID."""

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------
    @abstractmethod
    def save_task(self, task: Task) -> Task:  # pragma: no cover
        """Persist a task."""

    @abstractmethod
    def get_task(self, task_id: str) -> Optional[Task]:  # pragma: no cover
        """Return task by ID."""

    @abstractmethod
    def list_tasks(self, project_id: str) -> List[Task]:  # pragma: no cover
        """List tasks for a project."""

    @abstractmethod
    def delete_task(self, task_id: str) -> None:  # pragma: no cover
        """Delete task by ID."""

    # ------------------------------------------------------------------
    # Conflicts
    # ------------------------------------------------------------------
    @abstractmethod
    def save_conflicts(self, conflicts: Iterable[Conflict]) -> None:  # pragma: no cover
        """Persist new conflicts for auditing/triage."""

    @abstractmethod
    def get_conflict(self, conflict_id: str) -> Optional[Conflict]:  # pragma: no cover
        """Return conflict by ID if it exists."""

    @abstractmethod
    def update_conflict(self, conflict: Conflict) -> Conflict:  # pragma: no cover
        """Update existing conflict state (e.g., resolved)."""

    @abstractmethod
    def list_conflicts(self, project_id: str) -> List[Conflict]:  # pragma: no cover
        """Return conflicts associated with a project."""

    # ------------------------------------------------------------------
    # Checkpoints
    # ------------------------------------------------------------------
    @abstractmethod
    def save_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint:  # pragma: no cover
        """Persist snapshot checkpoint."""

    @abstractmethod
    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:  # pragma: no cover
        """Retrieve checkpoint by ID."""

    @abstractmethod
    def list_checkpoints(self, project_id: str) -> List[Checkpoint]:  # pragma: no cover
        """List checkpoints for project."""

    @abstractmethod
    def delete_checkpoint(self, checkpoint_id: str) -> None:  # pragma: no cover
        """Remove checkpoint."""

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def close(self) -> None:  # pragma: no cover
        """Override to release underlying resources if necessary."""

        return None
