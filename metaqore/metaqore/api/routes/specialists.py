"""HMCP specialist workflow endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from metaqore.api.dependencies import get_hmcp_service, get_state_manager
from metaqore.api.routes.utils import build_response_metadata
from metaqore.api.schemas import (
    SpecialistDraftData,
    SpecialistDraftResponse,
    SpecialistEvaluationData,
    SpecialistEvaluationResponse,
    SpecialistPipelineData,
    SpecialistPipelineResponse,
    SpecialistLevelInfo,
    SpecialistProposalRequest,
    SpecialistSkillInfo,
    SpecialistSpawnDecisionInfo,
)
from metaqore.core.state_manager import StateManager
from metaqore.exceptions import ConflictDetectedError
from metaqore.hmcp import (
    ChainingLevel,
    HMCPService,
    SpecialistProposal,
    SpecialistWorkflowError,
)
from metaqore.hmcp.policy import SpawnDecision

router = APIRouter(prefix="/hmcp/specialists", tags=["HMCP"])


def _skill_info(skill) -> SpecialistSkillInfo:
    return SpecialistSkillInfo(
        skill_id=skill.skill_id,
        description=skill.description,
        parent_agent=skill.parent_agent,
        max_specialist_size_mb=skill.max_specialist_size_mb,
        allowed_teachers=list(skill.allowed_teachers),
    )


def _level_info(level: ChainingLevel | None) -> SpecialistLevelInfo | None:
    if level is None:
        return None
    return SpecialistLevelInfo(
        index=level.index,
        key=level.key,
        level_type=level.level_type,
        example=level.example,
        max_parameters=level.max_parameters,
        raw_max_size=level.raw_max_size,
        can_spawn=level.can_spawn,
    )


def _spawn_info(decision: SpawnDecision | None) -> SpecialistSpawnDecisionInfo | None:
    if decision is None:
        return None
    next_key = decision.next_level.key if decision.next_level else None
    return SpecialistSpawnDecisionInfo(
        allowed=decision.allowed,
        reasons=list(decision.reasons),
        next_level_key=next_key,
    )


@router.post(
    "/evaluate",
    response_model=SpecialistEvaluationResponse,
    summary="Evaluate HMCP specialist proposal",
)
async def evaluate_specialist_proposal(
    payload: SpecialistProposalRequest,
    request: Request,
    hmcp_service: HMCPService = Depends(get_hmcp_service),
) -> SpecialistEvaluationResponse:
    try:
        proposal = SpecialistProposal(
            skill_id=payload.skill_id,
            requested_size_mb=payload.requested_size_mb,
            teachers=payload.teachers,
            confidence=payload.confidence,
            task_isolation_passed=payload.task_isolation_passed,
            parent_level_identifier=payload.parent_level_identifier,
            parameter_count=payload.parameter_count,
        )
    except ValueError as exc:  # pragma: no cover - pydantic should prevent, but guard anyway
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

    evaluation = hmcp_service.evaluate_proposal(proposal)
    data = SpecialistEvaluationData(
        allowed=evaluation.allowed,
        reasons=list(evaluation.reasons),
        skill=_skill_info(evaluation.skill),
        target_level=_level_info(evaluation.target_level),
        spawn_decision=_spawn_info(evaluation.spawn_decision),
    )
    return SpecialistEvaluationResponse(data=data, metadata=build_response_metadata(request))


@router.post(
    "/draft",
    response_model=SpecialistDraftResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Draft and persist HMCP specialist artifact",
)
async def draft_specialist(
    payload: SpecialistProposalRequest,
    request: Request,
    hmcp_service: HMCPService = Depends(get_hmcp_service),
    state_manager: StateManager = Depends(get_state_manager),
) -> SpecialistDraftResponse:
    try:
        proposal = SpecialistProposal(
            skill_id=payload.skill_id,
            requested_size_mb=payload.requested_size_mb,
            teachers=payload.teachers,
            confidence=payload.confidence,
            task_isolation_passed=payload.task_isolation_passed,
            parent_level_identifier=payload.parent_level_identifier,
            parameter_count=payload.parameter_count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

    try:
        specialist = hmcp_service.draft_specialist_model(
            proposal,
            project_id=payload.project_id,
            created_by=payload.created_by,
            data=payload.data,
            metadata=payload.metadata,
        )
    except SpecialistWorkflowError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

    try:
        persisted = state_manager.create_artifact(specialist)
    except ConflictDetectedError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    gateway_job_id = hmcp_service.enqueue_training_job(persisted)
    data = SpecialistDraftData(specialist=persisted, gateway_job_id=gateway_job_id)
    return SpecialistDraftResponse(data=data, metadata=build_response_metadata(request))


@router.post(
    "/run",
    response_model=SpecialistPipelineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute full HMCP autonomous workflow",
)
async def run_specialist_workflow(
    payload: SpecialistProposalRequest,
    request: Request,
    hmcp_service: HMCPService = Depends(get_hmcp_service),
) -> SpecialistPipelineResponse:
    try:
        proposal = SpecialistProposal(
            skill_id=payload.skill_id,
            requested_size_mb=payload.requested_size_mb,
            teachers=payload.teachers,
            confidence=payload.confidence,
            task_isolation_passed=payload.task_isolation_passed,
            parent_level_identifier=payload.parent_level_identifier,
            parameter_count=payload.parameter_count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

    try:
        outcome, gateway_job_id = hmcp_service.run_autonomous_workflow(
            proposal,
            project_id=payload.project_id,
            created_by=payload.created_by,
            data=payload.data,
            metadata=payload.metadata,
        )
    except SpecialistWorkflowError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    except ConflictDetectedError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    data = SpecialistPipelineData(
        specialist=outcome.specialist,
        training=outcome.training.to_dict(),
        validation=outcome.validation.to_dict(),
        gateway_job_id=gateway_job_id,
    )
    return SpecialistPipelineResponse(data=data, metadata=build_response_metadata(request))


__all__ = ["router"]
