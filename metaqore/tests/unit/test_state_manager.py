"""Unit tests for the StateManager checkpoint workflow."""

from __future__ import annotations

from pathlib import Path

import pytest

from metaqore.core.audit import ComplianceAuditor
from metaqore.core.models import Artifact, Project, Task
from metaqore.core.security import SecureGateway
from metaqore.core.state_manager import StateManager
from metaqore.exceptions import VetoAppliedError
from metaqore.storage.backends.sqlite import SQLiteBackend


@pytest.fixture()
def backend(tmp_path: Path) -> SQLiteBackend:
    db_path = tmp_path / "state.sqlite3"
    dsn = f"sqlite:///{db_path.as_posix()}"
    backend = SQLiteBackend(dsn=dsn)
    yield backend
    backend.close()


@pytest.fixture()
def state_manager(backend: SQLiteBackend) -> StateManager:
    return StateManager(backend, checkpoint_retention=5)


class _PassthroughPSMP:
    def __init__(self, state_manager: StateManager) -> None:
        self.state_manager = state_manager

    def declare_artifact(self, artifact: Artifact, *, persist: bool = True) -> Artifact:
        if persist:
            self.state_manager.save_artifact(artifact)
        return artifact


def _seed_project(manager: StateManager, *, name: str = "Demo") -> tuple[Project, Artifact, Task]:
    project = manager.create_project(Project(name=name))
    artifact = Artifact(project_id=project.id, artifact_type="spec", data={"doc": "v1"}, created_by="agent")
    manager.save_artifact(artifact)
    task = Task(project_id=project.id, title="Outline spec")
    manager.save_task(task)
    return project, artifact, task


def test_create_checkpoint_captures_state(state_manager: StateManager) -> None:
    project, artifact, task = _seed_project(state_manager)

    checkpoint = state_manager.create_checkpoint(project.id, "baseline")

    assert checkpoint.project_id == project.id
    assert checkpoint.snapshot["project"]["id"] == project.id
    assert checkpoint.snapshot["artifacts"][0]["id"] == artifact.id
    assert checkpoint.snapshot["tasks"][0]["id"] == task.id
    assert len(state_manager.get_checkpoints(project.id)) == 1


def test_checkpoint_retention_prunes_old_entries(backend: SQLiteBackend) -> None:
    manager = StateManager(backend, checkpoint_retention=2)
    project, *_ = _seed_project(manager, name="Retention")

    manager.create_checkpoint(project.id, "cp-0")
    manager.create_checkpoint(project.id, "cp-1")
    manager.create_checkpoint(project.id, "cp-2")

    checkpoints = manager.get_checkpoints(project.id)
    assert len(checkpoints) == 2
    assert [cp.label for cp in checkpoints] == ["cp-1", "cp-2"]


def test_restore_checkpoint_reverts_project_state(backend: SQLiteBackend) -> None:
    manager = StateManager(backend, checkpoint_retention=10)
    project, artifact_v1, task_v1 = _seed_project(manager, name="Restore Demo")

    baseline = manager.create_checkpoint(project.id, "baseline")

    artifact_v2 = Artifact(project_id=project.id, artifact_type="spec", data={"doc": "v2"}, created_by="agent")
    manager.save_artifact(artifact_v2)
    task_v2 = Task(project_id=project.id, title="Second phase")
    manager.save_task(task_v2)
    manager.update_project(project.id, {"metadata": {"phase": "mutated"}})

    restored = manager.restore_checkpoint(baseline.id)

    assert len(restored.artifacts) == 1
    assert restored.artifacts[0].id == artifact_v1.id
    assert len(restored.tasks) == 1
    assert restored.tasks[0].id == task_v1.id
    assert not restored.metadata

    checkpoint_labels = [cp.label for cp in manager.get_checkpoints(project.id)]
    assert "baseline" in checkpoint_labels
    assert any(label.startswith("auto-backup-") for label in checkpoint_labels)


def test_secure_gateway_allows_local_provider(tmp_path: Path, backend: SQLiteBackend) -> None:
    manager = StateManager(backend)
    manager.attach_psmp_engine(_PassthroughPSMP(manager))
    auditor = ComplianceAuditor(log_dir=tmp_path)
    gateway = SecureGateway(auditor=auditor)
    manager.attach_secure_gateway(gateway)

    project = manager.create_project(Project(name="Secured"))
    artifact = Artifact(
        project_id=project.id,
        artifact_type="spec",
        data={"doc": "secured"},
        created_by="coder",
        metadata={
            "llm_provider": "ollama",
            "agent_name": "CoderAgent",
            "task_type": "code_generation",
        },
    )

    stored = manager.create_artifact(artifact)

    assert stored.id == artifact.id


def test_secure_gateway_blocks_disallowed_provider(tmp_path: Path, backend: SQLiteBackend) -> None:
    manager = StateManager(backend)
    manager.attach_psmp_engine(_PassthroughPSMP(manager))
    auditor = ComplianceAuditor(log_dir=tmp_path)
    gateway = SecureGateway(auditor=auditor)
    manager.attach_secure_gateway(gateway)

    project = manager.create_project(Project(name="Secured"))
    artifact = Artifact(
        project_id=project.id,
        artifact_type="spec",
        data={"doc": "secured"},
        created_by="coder",
        metadata={
            "llm_provider": "openrouter",
            "agent_name": "CoderAgent",
            "task_type": "code_generation",
            "has_sensitive_data": True,
        },
    )

    with pytest.raises(VetoAppliedError):
        manager.create_artifact(artifact)
