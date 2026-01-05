"""Unit tests for MetaQore core data models."""

from __future__ import annotations

from datetime import datetime

from metaqore.core.models import (
    Artifact,
    BlockingReport,
    Conflict,
    Project,
    Provenance,
    SpecialistLifecycle,
    SpecialistModel,
    Task,
    TaskStatus,
)


def test_artifact_blocking_state_tracks_conflicts() -> None:
    conflict_open = Conflict(artifact_id="art", project_id="proj", description="Issue")
    conflict_open.resolved = False
    conflict_closed = Conflict(artifact_id="art", project_id="proj", description="Resolved")
    conflict_closed.mark_resolved(conflict_closed.resolution_strategy)

    artifact = Artifact(project_id="proj", artifact_type="spec", data={}, created_by="agent")
    artifact.add_conflict(conflict_open)
    artifact.add_conflict(conflict_closed)

    assert artifact.is_blocked is True

    conflict_open.mark_resolved(conflict_open.resolution_strategy)
    assert artifact.is_blocked is False


def test_task_mark_completed_updates_fields() -> None:
    task = Task(project_id="proj", title="Write design")
    prior_updated = task.updated_at

    task.mark_completed()

    assert task.status == TaskStatus.COMPLETED
    assert task.completed_at is not None
    assert task.updated_at >= prior_updated


def test_project_add_helpers_update_timestamps() -> None:
    project = Project(name="Demo")
    initial_updated = project.updated_at

    artifact = Artifact(project_id=project.id, artifact_type="spec", data={}, created_by="agent")
    task = Task(project_id=project.id, title="Draft plan")

    project.add_artifact(artifact)
    project.add_task(task)

    assert artifact in project.artifacts
    assert task in project.tasks
    assert project.updated_at >= initial_updated


def test_blocking_report_collects_unresolved_conflicts() -> None:
    project = Project(name="Status")
    conflict = Conflict(artifact_id="art", project_id=project.id, description="Blocked")
    blocked_artifact = Artifact(
        id="art",
        project_id=project.id,
        artifact_type="spec",
        data={},
        created_by="agent",
        blocked_by=[conflict],
    )
    clean_artifact = Artifact(project_id=project.id, artifact_type="spec", data={}, created_by="agent")

    report = BlockingReport.from_artifacts(project.id, [blocked_artifact, clean_artifact])

    assert report.project_id == project.id
    assert report.blocked_artifacts == ["art"]
    assert report.conflicts[0].artifact_id == "art"
    assert isinstance(report.generated_at, datetime)


def test_artifact_provenance_records_entries() -> None:
    artifact = Artifact(project_id="proj", artifact_type="spec", data={}, created_by="agent")
    assert artifact.provenance == []

    provenance = Provenance(artifact_id=artifact.id, actor="agent", action="create")
    artifact.add_provenance(provenance)

    assert artifact.provenance == [provenance]


def test_specialist_model_tracks_lifecycle_transitions() -> None:
    specialist = SpecialistModel(
        project_id="proj",
        data={"summary": "demo"},
        created_by="hmcp",
        skill_id="clean_akkadian_dates",
        parent_agent="DataScienceAgent",
        teachers=["BaseAgent"],
        level_key="level_1",
        level_type="domain_specialist",
        parameter_count=5_000_000,
    )

    assert specialist.artifact_type == "specialist_model"
    assert specialist.lifecycle_state == SpecialistLifecycle.PROPOSED

    specialist.advance_state(SpecialistLifecycle.MOPD_TRAINING)

    assert specialist.lifecycle_state == SpecialistLifecycle.MOPD_TRAINING
    assert specialist.metadata["lifecycle_history"][0]["state"] == SpecialistLifecycle.MOPD_TRAINING.value
