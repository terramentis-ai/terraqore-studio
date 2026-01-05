"""SQLite backend regression tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from metaqore.core.models import Artifact, Checkpoint, Conflict, Project, Task, TaskStatus
from metaqore.storage.backends.sqlite import SQLiteBackend


@pytest.fixture()
def backend(tmp_path: Path) -> SQLiteBackend:
    db_path = tmp_path / "state.db"
    backend = SQLiteBackend(dsn=f"sqlite:///{db_path.as_posix()}")
    yield backend
    backend.close()


def test_project_roundtrip(backend: SQLiteBackend) -> None:
    project = Project(name="SQLite Demo", metadata={"owner": "meta"})

    backend.save_project(project)
    loaded = backend.get_project(project.id)

    assert loaded is not None
    assert loaded.name == project.name
    assert loaded.metadata["owner"] == "meta"


def test_artifact_version_ordering(backend: SQLiteBackend) -> None:
    project = Project(name="Artifacts")
    backend.save_project(project)

    a1 = Artifact(project_id=project.id, artifact_type="spec", data={}, created_by="agent", version=1)
    a2 = Artifact(project_id=project.id, artifact_type="spec", data={}, created_by="agent", version=2)
    backend.save_artifact(a2)
    backend.save_artifact(a1)

    artifacts = backend.list_artifacts(project.id)

    assert [artifact.version for artifact in artifacts] == [1, 2]


def test_task_storage_preserves_order(backend: SQLiteBackend) -> None:
    project = Project(name="Tasks")
    backend.save_project(project)

    older = Task(project_id=project.id, title="older", created_at=datetime.now(timezone.utc) - timedelta(days=1))
    newer = Task(project_id=project.id, title="newer")
    backend.save_task(newer)
    backend.save_task(older)

    tasks = backend.list_tasks(project.id)

    assert [task.title for task in tasks] == ["older", "newer"]


def test_conflict_save_and_update(backend: SQLiteBackend) -> None:
    project = Project(name="Conflicts")
    backend.save_project(project)
    conflict = Conflict(artifact_id="art", project_id=project.id, description="Issue")

    backend.save_conflicts([conflict])
    conflict.mark_resolved(conflict.resolution_strategy)
    backend.update_conflict(conflict)

    stored = backend.list_conflicts(project.id)[0]
    assert stored.resolved is True
    assert stored.resolved_at is not None


def test_checkpoint_roundtrip(backend: SQLiteBackend) -> None:
    project = Project(name="Checkpoints")
    backend.save_project(project)
    checkpoint = Checkpoint(project_id=project.id, label="baseline", snapshot={"project": project.model_dump()})

    backend.save_checkpoint(checkpoint)
    stored = backend.list_checkpoints(project.id)

    assert stored[0].label == "baseline"
    assert backend.get_checkpoint(stored[0].id) is not None

    backend.delete_checkpoint(stored[0].id)
    assert backend.list_checkpoints(project.id) == []
