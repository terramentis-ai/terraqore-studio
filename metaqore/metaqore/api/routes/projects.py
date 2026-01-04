"""Project management endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from metaqore.api.dependencies import get_state_manager
from metaqore.api.routes.utils import build_response_metadata, paginate_items
from metaqore.api.schemas import (
    ProjectCreateRequest,
    ProjectListData,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)
from metaqore.core.models import Project, ProjectStatus
from metaqore.core.state_manager import StateManager

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=ProjectListResponse, summary="List projects")
async def list_projects(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    status_filter: ProjectStatus | None = Query(None, alias="status"),
    owner_id: str | None = Query(None, description="Filter by owner"),
    state_manager: StateManager = Depends(get_state_manager),
) -> ProjectListResponse:
    projects = state_manager.list_projects()
    if status_filter is not None:
        projects = [project for project in projects if project.status == status_filter]
    if owner_id:
        projects = [project for project in projects if project.owner_id == owner_id]

    paged_projects, total = paginate_items(projects, page, page_size)
    filters: Dict[str, str] = {}
    if status_filter is not None:
        filters["status"] = status_filter.value
    if owner_id:
        filters["owner_id"] = owner_id

    data = ProjectListData(
        projects=paged_projects,
        total=total,
        page=page,
        page_size=page_size,
        filters=filters,
    )
    return ProjectListResponse(data=data, metadata=build_response_metadata(request))


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create project",
)
async def create_project(
    payload: ProjectCreateRequest,
    request: Request,
    state_manager: StateManager = Depends(get_state_manager),
) -> ProjectResponse:
    project = Project(**payload.model_dump())
    saved = state_manager.create_project(project)
    return ProjectResponse(data=saved, metadata=build_response_metadata(request))


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project",
)
async def get_project(
    project_id: str,
    request: Request,
    state_manager: StateManager = Depends(get_state_manager),
) -> ProjectResponse:
    project = state_manager.get_project(project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectResponse(data=project, metadata=build_response_metadata(request))


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
)
async def update_project(
    project_id: str,
    payload: ProjectUpdateRequest,
    request: Request,
    state_manager: StateManager = Depends(get_state_manager),
) -> ProjectResponse:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")
    updates["updated_at"] = datetime.now(timezone.utc)
    project = state_manager.update_project(project_id, updates)
    return ProjectResponse(data=project, metadata=build_response_metadata(request))


@router.delete(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Delete project",
)
async def delete_project(
    project_id: str,
    request: Request,
    state_manager: StateManager = Depends(get_state_manager),
) -> ProjectResponse:
    project = state_manager.get_project(project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Project not found")
    state_manager.delete_project(project_id)
    return ProjectResponse(data=project, metadata=build_response_metadata(request))
