"""Artifact management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from metaqore.api.dependencies import get_state_manager
from metaqore.api.routes.utils import build_response_metadata, paginate_items
from metaqore.api.schemas import (
    ArtifactCreateRequest,
    ArtifactListData,
    ArtifactListResponse,
    ArtifactResponse,
    ArtifactUpdateRequest,
)
from metaqore.core.models import Artifact
from metaqore.core.state_manager import StateManager
from metaqore.exceptions import ConflictDetectedError

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


@router.get("", response_model=ArtifactListResponse, summary="List artifacts by project")
async def list_artifacts(
    request: Request,
    project_id: str = Query(..., description="Project identifier"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    artifact_type: str | None = Query(None, description="Filter by artifact type"),
    created_by: str | None = Query(None, description="Filter by creator"),
    state_manager: StateManager = Depends(get_state_manager),
) -> ArtifactListResponse:
    artifacts = state_manager.list_artifacts(project_id)
    if artifact_type:
        artifacts = [artifact for artifact in artifacts if artifact.artifact_type == artifact_type]
    if created_by:
        artifacts = [artifact for artifact in artifacts if artifact.created_by == created_by]

    paged_artifacts, total = paginate_items(artifacts, page, page_size)
    filters = {}
    if artifact_type:
        filters["artifact_type"] = artifact_type
    if created_by:
        filters["created_by"] = created_by

    data = ArtifactListData(
        project_id=project_id,
        artifacts=paged_artifacts,
        total=total,
        page=page,
        page_size=page_size,
        filters=filters,
    )
    return ArtifactListResponse(data=data, metadata=build_response_metadata(request))


@router.post(
    "",
    response_model=ArtifactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create artifact",
)
async def create_artifact(
    payload: ArtifactCreateRequest,
    request: Request,
    state_manager: StateManager = Depends(get_state_manager),
) -> ArtifactResponse:
    artifact = Artifact(**payload.model_dump())
    try:
        saved = state_manager.create_artifact(artifact)
    except ConflictDetectedError as exc:  # pragma: no cover - exercised via integration tests
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ArtifactResponse(data=saved, metadata=build_response_metadata(request))


@router.get(
    "/{artifact_id}",
    response_model=ArtifactResponse,
    summary="Get artifact",
)
async def get_artifact(
    artifact_id: str,
    request: Request,
    state_manager: StateManager = Depends(get_state_manager),
) -> ArtifactResponse:
    artifact = state_manager.get_artifact(artifact_id)
    if artifact is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    return ArtifactResponse(data=artifact, metadata=build_response_metadata(request))


@router.patch(
    "/{artifact_id}",
    response_model=ArtifactResponse,
    summary="Update artifact",
)
async def update_artifact(
    artifact_id: str,
    payload: ArtifactUpdateRequest,
    request: Request,
    state_manager: StateManager = Depends(get_state_manager),
) -> ArtifactResponse:
    existing = state_manager.get_artifact(artifact_id)
    if existing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")

    updated_artifact = existing.model_copy(update=updates)
    saved = state_manager.save_artifact(updated_artifact)
    return ArtifactResponse(data=saved, metadata=build_response_metadata(request))


@router.delete(
    "/{artifact_id}",
    response_model=ArtifactResponse,
    summary="Delete artifact",
)
async def delete_artifact(
    artifact_id: str,
    request: Request,
    state_manager: StateManager = Depends(get_state_manager),
) -> ArtifactResponse:
    artifact = state_manager.get_artifact(artifact_id)
    if artifact is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    state_manager.delete_artifact(artifact_id)
    return ArtifactResponse(data=artifact, metadata=build_response_metadata(request))
