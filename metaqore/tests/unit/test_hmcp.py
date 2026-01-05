"""Unit tests for HMCP registry and workflow components."""

from __future__ import annotations

import pytest

from metaqore.config import GovernanceMode, MetaQoreConfig
from metaqore.core.models import Project, SpecialistLifecycle
from metaqore.core.psmp import PSMPEngine
from metaqore.core.state_manager import StateManager
from metaqore.gateway import InMemoryGatewayQueue
from metaqore.hmcp import (
    ChainingOrchestrator,
    HMCPService,
    HierarchicalChainingPolicy,
    SkillRegistry,
    SpecialistProposal,
    SpecialistWorkflow,
    SpecialistWorkflowError,
)
from metaqore.storage.backends.sqlite import SQLiteBackend


def _build_state_manager(tmp_path) -> StateManager:
    db_path = tmp_path / "hmcp_unit.db"
    backend = SQLiteBackend(f"sqlite:///{db_path.as_posix()}")
    state_manager = StateManager(backend=backend)
    config = MetaQoreConfig(governance_mode=GovernanceMode.PLAYGROUND)
    psmp_engine = PSMPEngine(state_manager=state_manager, config=config)
    state_manager.attach_psmp_engine(psmp_engine)
    return state_manager


def test_skill_registry_loads_policy() -> None:
    registry = SkillRegistry.from_policy()
    skill = registry.ensure_registered("clean_akkadian_dates")

    assert skill.parent_agent == "DataScienceAgent"
    assert registry.validate_teachers(skill.skill_id, ["BaseAgent"])
    assert registry.discovery_policy == "registry_only"


def test_chaining_policy_parses_levels() -> None:
    policy = HierarchicalChainingPolicy.from_policy()

    assert policy.depth == 2
    level_one = policy.get_level(1)
    assert level_one.key == "level_1"
    level_two = policy.next_level(level_one.index)
    assert level_two is not None
    assert level_two.key == "level_2"


def test_workflow_creates_specialist_model_from_policy() -> None:
    workflow = SpecialistWorkflow.from_policy()
    proposal = SpecialistProposal(
        skill_id="clean_akkadian_dates",
        requested_size_mb=10,
        teachers=["BaseAgent"],
        confidence=0.95,
        task_isolation_passed=True,
        parameter_count=5_000_000,
    )

    specialist = workflow.create_specialist_model(
        proposal,
        project_id="proj",
        created_by="system",
        data={"summary": "demo"},
    )

    assert specialist.artifact_type == "specialist_model"
    assert specialist.level_key == "level_1"
    assert specialist.parent_agent == "DataScienceAgent"
    assert specialist.metadata["hmcp_level"] == "level_1"


def test_workflow_rejects_invalid_teachers() -> None:
    workflow = SpecialistWorkflow.from_policy()
    proposal = SpecialistProposal(
        skill_id="clean_akkadian_dates",
        requested_size_mb=10,
        teachers=["UnknownTeacher"],
        confidence=0.95,
        task_isolation_passed=True,
    )

    evaluation = workflow.evaluate_proposal(proposal)

    assert evaluation.allowed is False
    assert any("Teachers not permitted" in reason for reason in evaluation.reasons)

    with pytest.raises(SpecialistWorkflowError):
        workflow.create_specialist_model(
            proposal,
            project_id="proj",
            created_by="system",
            data={},
        )


def test_workflow_spawn_requires_confidence_threshold() -> None:
    workflow = SpecialistWorkflow.from_policy()
    proposal = SpecialistProposal(
        skill_id="clean_akkadian_dates",
        requested_size_mb=5,
        teachers=["BaseAgent"],
        confidence=0.5,
        task_isolation_passed=True,
        parent_level_identifier="level_1",
        parameter_count=1_000_000,
    )

    evaluation = workflow.evaluate_proposal(proposal)

    assert evaluation.allowed is False
    assert any("Confidence" in reason for reason in evaluation.reasons)


def test_hmcp_service_enriches_metadata_for_gateway() -> None:
    service = HMCPService()
    proposal = SpecialistProposal(
        skill_id="clean_akkadian_dates",
        requested_size_mb=5,
        teachers=["BaseAgent"],
        confidence=0.95,
        task_isolation_passed=True,
    )

    specialist = service.draft_specialist_model(
        proposal,
        project_id="proj",
        created_by="hmcp",
        data={"summary": "demo"},
        metadata={"custom": "value"},
    )

    assert specialist.metadata["task_type"] == "hmcp_specialist_creation"
    assert specialist.metadata["agent_name"] == "clean_akkadian_dates"
    assert specialist.metadata["llm_provider"] == "hmcp_gateway"
    assert specialist.metadata["custom"] == "value"


def test_hmcp_service_enqueue_training_job_places_items_on_queue() -> None:
    queue = InMemoryGatewayQueue()
    service = HMCPService(gateway_queue=queue)
    proposal = SpecialistProposal(
        skill_id="clean_akkadian_dates",
        requested_size_mb=5,
        teachers=["BaseAgent"],
        confidence=0.95,
        task_isolation_passed=True,
    )

    specialist = service.draft_specialist_model(
        proposal,
        project_id="proj",
        created_by="hmcp",
        data={"summary": "demo"},
    )

    job_id = service.enqueue_training_job(specialist)

    assert job_id is not None
    assert queue.size() == 1
    job = queue.peek()
    assert job is not None and job.artifact_id == specialist.id


def test_chaining_orchestrator_advances_specialist_lifecycle(tmp_path) -> None:
    state_manager = _build_state_manager(tmp_path)
    project = Project(name="HMCP Project")
    state_manager.create_project(project)
    orchestrator = ChainingOrchestrator.build_default(state_manager)
    proposal = SpecialistProposal(
        skill_id="clean_akkadian_dates",
        requested_size_mb=10,
        teachers=["BaseAgent"],
        confidence=0.97,
        task_isolation_passed=True,
        parameter_count=8_000_000,
    )

    outcome = orchestrator.run_pipeline(
        proposal,
        project_id=project.id,
        created_by="hmcp",
        data={"summary": "demo"},
    )

    specialist = outcome.specialist
    assert outcome.validation.passed is True
    assert outcome.training.success is True
    assert specialist.lifecycle_state == SpecialistLifecycle.ACTIVE
    assert "hmcp_training" in specialist.metadata
    assert "hmcp_validation" in specialist.metadata


def test_hmcp_service_autonomous_workflow_returns_job_id(tmp_path) -> None:
    state_manager = _build_state_manager(tmp_path)
    project = Project(name="HMCP Project")
    state_manager.create_project(project)
    orchestrator = ChainingOrchestrator.build_default(state_manager)
    queue = InMemoryGatewayQueue()
    service = HMCPService(gateway_queue=queue, orchestrator=orchestrator)
    proposal = SpecialistProposal(
        skill_id="clean_akkadian_dates",
        requested_size_mb=12,
        teachers=["BaseAgent"],
        confidence=0.96,
        task_isolation_passed=True,
        parameter_count=9_500_000,
    )

    outcome, job_id = service.run_autonomous_workflow(
        proposal,
        project_id=project.id,
        created_by="hmcp",
        data={"summary": "demo"},
    )

    assert outcome.activated is True
    assert job_id is not None
    assert queue.size() == 1
