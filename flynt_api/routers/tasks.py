"""
Tasks Router
API endpoints for task management.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from flynt_api.models import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
)
from flynt_api.service import get_flynt_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate):
    """Create a new task.
    
    Args:
        task: Task creation request.
        
    Returns:
        Created task.
    """
    try:
        # Check project exists
        service = get_flynt_service()
        project = service.get_project(task.project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Create task
        created = service.create_task(
            project_id=task.project_id,
            title=task.title,
            description=task.description,
            milestone=task.milestone,
            priority=task.priority,
            estimated_hours=task.estimated_hours,
            agent_type=task.agent_type.value if task.agent_type else None
        )
        
        return created
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    project_id: int = Query(..., description="Project ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    milestone: Optional[str] = Query(None, description="Filter by milestone")
):
    """List tasks for project.
    
    Args:
        project_id: Project ID.
        status: Optional status filter.
        milestone: Optional milestone filter.
        
    Returns:
        Task list.
    """
    try:
        service = get_flynt_service()
        
        # Check project exists
        project = service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # List tasks
        tasks = service.list_tasks(project_id, status=status, milestone=milestone)
        
        return TaskListResponse(
            tasks=tasks,
            total=len(tasks),
            project_id=project_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing tasks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int):
    """Get task by ID.
    
    Args:
        task_id: Task ID.
        
    Returns:
        Task data.
    """
    try:
        service = get_flynt_service()
        task = service.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task_update: TaskUpdate):
    """Update task.
    
    Args:
        task_id: Task ID.
        task_update: Update request.
        
    Returns:
        Updated task.
    """
    try:
        service = get_flynt_service()
        
        # Check if exists
        existing = service.get_task(task_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Update
        update_data = task_update.dict(exclude_unset=True)
        if task_update.status:
            update_data['status'] = task_update.status.value
        
        updated = service.update_task(task_id, **update_data)
        
        return updated
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: int):
    """Delete a task.
    
    Args:
        task_id: Task ID.
    """
    try:
        service = get_flynt_service()
        
        # Check if exists
        existing = service.get_task(task_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # TODO: Implement delete in state manager
        # service.delete_task(task_id)
        
        raise HTTPException(status_code=501, detail="Delete not yet implemented")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
