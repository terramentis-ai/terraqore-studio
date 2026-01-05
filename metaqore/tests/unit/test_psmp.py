"""Unit tests for the PSMP engine's conflict logic."""

from __future__ import annotations

import pytest

from metaqore.config import GovernanceMode, MetaQoreConfig
from metaqore.core.models import Artifact, Conflict, Project
from metaqore.core.psmp import PSMPEngine
from metaqore.exceptions import ConflictDetectedError


class FakeStateManager:
    """In-memory stub that mimics the subset of StateManager used by PSMP."""

    def __init__(self, project: Project) -> None:
        self.project = project
        self.artifacts: dict[str, Artifact] = {}
        self.conflicts: dict[str, Conflict] = {}

    # Project helpers -------------------------------------------------
    def get_project(self, project_id: str) -> Project | None:
        return self.project if self.project.id == project_id else None

    # Artifact helpers ------------------------------------------------
    def list_artifacts(self, project_id: str):
        if project_id != self.project.id:
            return []
        return sorted(self.artifacts.values(), key=lambda art: art.version)

    def save_artifact(self, artifact: Artifact) -> Artifact:
        self.artifacts[artifact.id] = artifact
        return artifact

    def get_artifact(self, artifact_id: str) -> Artifact | None:
        return self.artifacts.get(artifact_id)

    # Conflict helpers ------------------------------------------------
    def update_conflict(self, conflict: Conflict) -> Conflict:
        self.conflicts[conflict.id] = conflict
        return conflict

    def save_conflicts(self, conflicts):  # pragma: no cover - not used directly
        for conflict in conflicts:
            self.conflicts[conflict.id] = conflict


def _make_artifact(project: Project, *, version: int = 1, created_by: str = "agent") -> Artifact:
    return Artifact(project_id=project.id, artifact_type="spec", data={"v": version}, version=version, created_by=created_by)


@pytest.fixture()
def psmp_engine() -> PSMPEngine:
    project = Project(name="PSMP Demo")
    state_manager = FakeStateManager(project)
    config = MetaQoreConfig(governance_mode=GovernanceMode.ADAPTIVE)
    return PSMPEngine(state_manager, config=config)


def test_create_artifact_increments_version(psmp_engine: PSMPEngine):
    # Seed an existing artifact to force version increment
    existing = _make_artifact(psmp_engine.state_manager.project)
    psmp_engine.state_manager.save_artifact(existing)

    artifact = psmp_engine.create_artifact(
        project_id=existing.project_id,
        artifact_type="spec",
        data={"doc": "v2"},
        created_by="agent",
    )

    assert artifact.version == 2


def test_declare_artifact_blocks_version_conflict(psmp_engine: PSMPEngine):
    project = psmp_engine.state_manager.project
    psmp_engine.state_manager.save_artifact(_make_artifact(project, version=1))

    bad_artifact = _make_artifact(project, version=1)

    with pytest.raises(ConflictDetectedError):
        psmp_engine.declare_artifact(bad_artifact)

    assert bad_artifact.blocked_by
    conflict_types = {conflict.conflict_type for conflict in bad_artifact.blocked_by}
    assert "version_mismatch" in conflict_types


def test_parallel_creation_triggers_conflict(psmp_engine: PSMPEngine):
    project = psmp_engine.state_manager.project
    psmp_engine.state_manager.save_artifact(_make_artifact(project, version=1, created_by="agent-a"))

    artifact = _make_artifact(project, version=2, created_by="agent-b")

    with pytest.raises(ConflictDetectedError):
        psmp_engine.declare_artifact(artifact)

    assert artifact.blocked_by
    conflict_types = {conflict.conflict_type for conflict in artifact.blocked_by}
    assert "parallel_creation" in conflict_types


def test_missing_dependency_detected(psmp_engine: PSMPEngine):
    project = psmp_engine.state_manager.project
    artifact = Artifact(
        project_id=project.id,
        artifact_type="plan",
        data={},
        created_by="agent",
        version=1,
        depends_on=["missing-artifact"],
    )

    with pytest.raises(ConflictDetectedError):
        psmp_engine.declare_artifact(artifact)

    assert artifact.blocked_by
    conflict_types = {conflict.conflict_type for conflict in artifact.blocked_by}
    assert "missing_dependency" in conflict_types


def test_circular_dependency_conflict(psmp_engine: PSMPEngine):
    project = psmp_engine.state_manager.project
    dependency = Artifact(
        id="art_dependency",
        project_id=project.id,
        artifact_type="plan",
        data={},
        created_by="agent",
        version=1,
        depends_on=["art_candidate"],
    )
    psmp_engine.state_manager.save_artifact(dependency)

    artifact = Artifact(
        id="art_candidate",
        project_id=project.id,
        artifact_type="plan",
        data={},
        created_by="agent",
        version=2,
        depends_on=[dependency.id],
    )

    with pytest.raises(ConflictDetectedError):
        psmp_engine.declare_artifact(artifact)

    assert artifact.blocked_by
    conflict_types = {conflict.conflict_type for conflict in artifact.blocked_by}
    assert "circular_dependency" in conflict_types


def test_get_blocking_report_lists_blocked_artifacts(psmp_engine: PSMPEngine):
    project = psmp_engine.state_manager.project
    conflict = Conflict(artifact_id="art_blocked", project_id=project.id, description="Blocked")
    blocked_artifact = Artifact(
        id="art_blocked",
        project_id=project.id,
        artifact_type="spec",
        data={},
        created_by="agent",
        version=1,
        blocked_by=[conflict],
    )
    psmp_engine.state_manager.save_artifact(blocked_artifact)

    report = psmp_engine.get_blocking_report(project.id)

    assert report.blocked_artifacts == ["art_blocked"]
    assert report.conflicts[0].artifact_id == "art_blocked"


def test_resolve_conflict_marks_and_persists(psmp_engine: PSMPEngine):
    conflict = Conflict(artifact_id="x", project_id=psmp_engine.state_manager.project.id, description="Needs review")
    psmp_engine.state_manager.conflicts[conflict.id] = conflict

    resolved = psmp_engine.resolve_conflict(conflict, conflict.resolution_strategy)

    assert resolved.resolved is True
    assert resolved.resolved_at is not None
    assert psmp_engine.state_manager.conflicts[conflict.id].resolved is True
