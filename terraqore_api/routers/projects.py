"""
Projects Router
API endpoints for project management.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from terraqore_api.models import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
)
from terraqore_api.service import get_terraqore_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(project: ProjectCreate):
    """Create a new project.
    
    Args:
        project: Project creation request.
        
    Returns:
        Created project.
    """
    try:
        service = get_terraqore_service()
        created = service.create_project(
            name=project.name,
            description=project.description,
            tech_stack=project.tech_stack,
            goals=project.goals
        )
        
        if not created:
            raise HTTPException(status_code=500, detail="Failed to create project")
        
        return created
        
    except Exception as e:
        logger.error(f"Error creating project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all projects.
    
    Args:
        status: Optional status filter.
        limit: Result limit.
        offset: Result offset.
        
    Returns:
        Project list.
    """
    try:
        service = get_terraqore_service()
        result = service.list_projects(status=status, limit=limit, offset=offset)
        return result
        
    except Exception as e:
        logger.error(f"Error listing projects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int):
    """Get project by ID.
    
    Args:
        project_id: Project ID.
        
    Returns:
        Project data.
    """
    try:
        service = get_terraqore_service()
        project = service.get_project(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return project
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, project_update: ProjectUpdate):
    """Update project.
    
    Args:
        project_id: Project ID.
        project_update: Update request.
        
    Returns:
        Updated project.
    """
    try:
        service = get_terraqore_service()
        
        # Check if exists
        existing = service.get_project(project_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update
        update_data = project_update.dict(exclude_unset=True)
        updated = service.update_project(project_id, **update_data)
        
        return updated
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: int):
    """Delete a project.
    
    Args:
        project_id: Project ID.
    """
    try:
        service = get_terraqore_service()
        
        # Check if exists
        existing = service.get_project(project_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # TODO: Implement delete in state manager
        # service.delete_project(project_id)
        
        raise HTTPException(status_code=501, detail="Delete not yet implemented")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
