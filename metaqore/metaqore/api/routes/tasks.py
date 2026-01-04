"""Task management endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from metaqore.api.dependencies import get_state_manager
from metaqore.api.routes.utils import build_response_metadata, paginate_items
from metaqore.api.schemas import (
    TaskCreateRequest,
    TaskListData,
    TaskListResponse,
    TaskResponse,
    TaskUpdateRequest,
)
from metaqore.core.models import Task, TaskStatus
from metaqore.core.state_manager import StateManager

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=TaskListResponse, summary="List tasks by project")
async def list_tasks(
    request: Request,
    project_id: str = Query(..., description="Project identifier"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    status_filter: TaskStatus | None = Query(None, alias="status"),
    assigned_to: str | None = Query(None, description="Filter by assignee"),
    state_manager: StateManager = Depends(get_state_manager),
) -> TaskListResponse:
    tasks = state_manager.list_tasks(project_id)
    if status_filter is not None:
        tasks = [task for task in tasks if task.status == status_filter]
    if assigned_to:
        tasks = [task for task in tasks if task.assigned_to == assigned_to]

    paged_tasks, total = paginate_items(tasks, page, page_size)
    filters = {}
    if status_filter is not None:
        filters["status"] = status_filter.value
    if assigned_to:
        filters["assigned_to"] = assigned_to

    data = TaskListData(
        project_id=project_id,
        tasks=paged_tasks,
        total=total,
        page=page,
        page_size=page_size,
        filters=filters,
    )
    return TaskListResponse(data=data, metadata=build_response_metadata(request))


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create task",
)
async def create_task(
    payload: TaskCreateRequest,
    request: Request,
    state_manager: StateManager = Depends(get_state_manager),
) -> TaskResponse:
    task = Task(**payload.model_dump())
    saved = state_manager.create_task(task)
    return TaskResponse(data=saved, metadata=build_response_metadata(request))


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task",
)
async def get_task(
    task_id: str,
    request: Request,
    state_manager: StateManager = Depends(get_state_manager),
) -> TaskResponse:
    task = state_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskResponse(data=task, metadata=build_response_metadata(request))


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update task",
)
async def update_task(
    task_id: str,
    payload: TaskUpdateRequest,
    request: Request,
    state_manager: StateManager = Depends(get_state_manager),
) -> TaskResponse:
    existing = state_manager.get_task(task_id)
    if existing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")

    updates["updated_at"] = datetime.now(timezone.utc)
    updated_task = existing.model_copy(update=updates)
    saved = state_manager.save_task(updated_task)
    return TaskResponse(data=saved, metadata=build_response_metadata(request))


@router.delete(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Delete task",
)
async def delete_task(
    task_id: str,
    request: Request,
    state_manager: StateManager = Depends(get_state_manager),
) -> TaskResponse:
    task = state_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    state_manager.delete_task(task_id)
    return TaskResponse(data=task, metadata=build_response_metadata(request))
