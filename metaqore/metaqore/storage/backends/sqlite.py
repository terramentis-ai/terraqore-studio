"""SQLite-backed implementation of the storage backend interface."""

from __future__ import annotations

import contextlib
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Type

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, create_engine, delete, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from metaqore.core.models import Artifact, Checkpoint, Conflict, Project, SpecialistModel, Task
from metaqore.storage.backend import StorageBackend


class Base(DeclarativeBase):
    pass


class ProjectTable(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ArtifactTable(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    artifact_type: Mapped[str] = mapped_column(String, index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class TaskTable(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String, index=True, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ConflictTable(Base):
    __tablename__ = "conflicts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    artifact_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class CheckpointTable(Base):
    __tablename__ = "checkpoints"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


def _serialize(model) -> dict:
    payload = model.model_dump(mode="json")
    payload.pop("is_blocked", None)
    return payload


class SQLiteBackend(StorageBackend):
    """SQLAlchemy-powered SQLite backend."""

    ARTIFACT_MODEL_REGISTRY: Dict[str, Type[Artifact]] = {
        "specialist_model": SpecialistModel,
    }

    def __init__(self, dsn: str = "sqlite:///metaqore.db") -> None:
        self.engine = create_engine(dsn, future=True)
        Base.metadata.create_all(self.engine)

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------
    def save_project(self, project: Project) -> Project:
        payload = _serialize(project.model_copy(update={"artifacts": [], "tasks": []}))
        with Session(self.engine) as session:
            existing = session.get(ProjectTable, project.id)
            if existing:
                existing.payload = payload
                existing.created_at = project.created_at
                existing.updated_at = project.updated_at
            else:
                session.add(
                    ProjectTable(
                        id=project.id,
                        payload=payload,
                        created_at=project.created_at,
                        updated_at=project.updated_at,
                    )
                )
            session.commit()
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        with Session(self.engine) as session:
            row = session.get(ProjectTable, project_id)
            if not row:
                return None
            project = Project.model_validate(row.payload)
            return project

    def delete_project(self, project_id: str) -> None:
        with Session(self.engine) as session:
            session.execute(delete(ArtifactTable).where(ArtifactTable.project_id == project_id))
            session.execute(delete(TaskTable).where(TaskTable.project_id == project_id))
            session.execute(delete(ConflictTable).where(ConflictTable.project_id == project_id))
            session.execute(delete(CheckpointTable).where(CheckpointTable.project_id == project_id))
            row = session.get(ProjectTable, project_id)
            if row:
                session.delete(row)
            session.commit()

    def list_projects(self) -> List[Project]:
        with Session(self.engine) as session:
            stmt = select(ProjectTable).order_by(ProjectTable.created_at)
            rows = session.execute(stmt).scalars().all()
            return [Project.model_validate(row.payload) for row in rows]

    # ------------------------------------------------------------------
    # Artifacts
    # ------------------------------------------------------------------
    def save_artifact(self, artifact: Artifact) -> Artifact:
        payload = _serialize(artifact)
        with Session(self.engine) as session:
            existing = session.get(ArtifactTable, artifact.id)
            if existing:
                existing.payload = payload
                existing.version = artifact.version
                existing.artifact_type = artifact.artifact_type
                existing.created_by = artifact.created_by
                existing.project_id = artifact.project_id
                existing.created_at = artifact.created_at
            else:
                session.add(
                    ArtifactTable(
                        id=artifact.id,
                        project_id=artifact.project_id,
                        artifact_type=artifact.artifact_type,
                        version=artifact.version,
                        created_by=artifact.created_by,
                        payload=payload,
                        created_at=artifact.created_at,
                    )
                )
            session.commit()
        return artifact

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        with Session(self.engine) as session:
            row = session.get(ArtifactTable, artifact_id)
            if not row:
                return None
            return self._deserialize_artifact(row.payload)

    def list_artifacts(self, project_id: str) -> List[Artifact]:
        with Session(self.engine) as session:
            stmt = select(ArtifactTable).where(ArtifactTable.project_id == project_id).order_by(ArtifactTable.version)
            rows = session.execute(stmt).scalars().all()
            return [self._deserialize_artifact(row.payload) for row in rows]

    def delete_artifact(self, artifact_id: str) -> None:
        with Session(self.engine) as session:
            row = session.get(ArtifactTable, artifact_id)
            if row:
                session.delete(row)
                session.commit()

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------
    def save_task(self, task: Task) -> Task:
        payload = _serialize(task)
        with Session(self.engine) as session:
            existing = session.get(TaskTable, task.id)
            if existing:
                existing.payload = payload
                existing.status = task.status.value
                existing.project_id = task.project_id
                existing.created_at = task.created_at
                existing.updated_at = task.updated_at
            else:
                session.add(
                    TaskTable(
                        id=task.id,
                        project_id=task.project_id,
                        status=task.status.value,
                        payload=payload,
                        created_at=task.created_at,
                        updated_at=task.updated_at,
                    )
                )
            session.commit()
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        with Session(self.engine) as session:
            row = session.get(TaskTable, task_id)
            if not row:
                return None
            return Task.model_validate(row.payload)

    def list_tasks(self, project_id: str) -> List[Task]:
        with Session(self.engine) as session:
            stmt = select(TaskTable).where(TaskTable.project_id == project_id).order_by(TaskTable.created_at)
            rows = session.execute(stmt).scalars().all()
            return [Task.model_validate(row.payload) for row in rows]

    def delete_task(self, task_id: str) -> None:
        with Session(self.engine) as session:
            row = session.get(TaskTable, task_id)
            if row:
                session.delete(row)
                session.commit()

    # ------------------------------------------------------------------
    # Conflicts
    # ------------------------------------------------------------------
    def save_conflicts(self, conflicts: Iterable[Conflict]) -> None:
        with Session(self.engine) as session:
            for conflict in conflicts:
                payload = _serialize(conflict)
                row = session.get(ConflictTable, conflict.id)
                if row:
                    row.payload = payload
                    row.resolved = conflict.resolved
                    row.resolved_at = conflict.resolved_at
                else:
                    session.add(
                        ConflictTable(
                            id=conflict.id,
                            project_id=conflict.project_id,
                            artifact_id=conflict.artifact_id,
                            resolved=conflict.resolved,
                            payload=payload,
                            created_at=conflict.created_at,
                            resolved_at=conflict.resolved_at,
                        )
                    )
            session.commit()

    def get_conflict(self, conflict_id: str) -> Optional[Conflict]:
        with Session(self.engine) as session:
            row = session.get(ConflictTable, conflict_id)
            if not row:
                return None
            return Conflict.model_validate(row.payload)

    def update_conflict(self, conflict: Conflict) -> Conflict:
        self.save_conflicts([conflict])
        return conflict

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @classmethod
    def _deserialize_artifact(cls, payload: dict) -> Artifact:
        artifact_type = payload.get("artifact_type")
        model_cls = cls.ARTIFACT_MODEL_REGISTRY.get(artifact_type, Artifact)
        return model_cls.model_validate(payload)

    def list_conflicts(self, project_id: str) -> List[Conflict]:
        with Session(self.engine) as session:
            stmt = select(ConflictTable).where(ConflictTable.project_id == project_id)
            rows = session.execute(stmt).scalars().all()
            return [Conflict.model_validate(row.payload) for row in rows]

    # ------------------------------------------------------------------
    # Checkpoints
    # ------------------------------------------------------------------
    def save_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint:
        payload = _serialize(checkpoint)
        with Session(self.engine) as session:
            existing = session.get(CheckpointTable, checkpoint.id)
            if existing:
                existing.snapshot = payload["snapshot"]
                existing.label = checkpoint.label
                existing.created_at = checkpoint.created_at
            else:
                session.add(
                    CheckpointTable(
                        id=checkpoint.id,
                        project_id=checkpoint.project_id,
                        label=checkpoint.label,
                        snapshot=payload["snapshot"],
                        created_at=checkpoint.created_at,
                    )
                )
            session.commit()
        return checkpoint

    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        with Session(self.engine) as session:
            row = session.get(CheckpointTable, checkpoint_id)
            if not row:
                return None
            payload = {
                "id": row.id,
                "project_id": row.project_id,
                "label": row.label,
                "snapshot": row.snapshot,
                "created_at": row.created_at.isoformat(),
            }
            return Checkpoint.model_validate(payload)

    def list_checkpoints(self, project_id: str) -> List[Checkpoint]:
        with Session(self.engine) as session:
            stmt = select(CheckpointTable).where(CheckpointTable.project_id == project_id).order_by(CheckpointTable.created_at)
            rows = session.execute(stmt).scalars().all()
            payloads = [
                {
                    "id": row.id,
                    "project_id": row.project_id,
                    "label": row.label,
                    "snapshot": row.snapshot,
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ]
            return [Checkpoint.model_validate(payload) for payload in payloads]

    def delete_checkpoint(self, checkpoint_id: str) -> None:
        with Session(self.engine) as session:
            row = session.get(CheckpointTable, checkpoint_id)
            if row:
                session.delete(row)
                session.commit()

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def close(self) -> None:
        with contextlib.suppress(Exception):
            self.engine.dispose()


__all__ = ["SQLiteBackend"]
