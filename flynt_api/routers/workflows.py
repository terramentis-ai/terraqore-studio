"""
Workflows Router
API endpoints for workflow management and agent execution.
"""

import logging
from fastapi import APIRouter, HTTPException
from typing import Optional

from flynt_api.models import (
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    AgentExecutionRequest,
    AgentExecutionResponse,
    ProjectBlockInfo,
)
from flynt_api.service import get_flynt_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/run", response_model=WorkflowExecutionResponse)
async def run_workflow(request: WorkflowExecutionRequest):
    """Execute a workflow.
    
    Args:
        request: Workflow execution request.
        
    Returns:
        Workflow execution result.
    """
    try:
        service = get_flynt_service()
        
        # Check project exists
        project = service.get_project(request.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Run appropriate workflow
        if request.workflow_type == "ideate":
            result = service.run_ideation(request.project_id)
        elif request.workflow_type == "plan":
            result = service.run_planning(request.project_id)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown workflow type: {request.workflow_type}")
        
        # Build response
        return WorkflowExecutionResponse(
            workflow_id=result.get("workflow_id"),
            project_id=request.project_id,
            workflow_type=request.workflow_type,
            status=result.get("status"),
            current_step=1,
            total_steps=1,
            steps=[],
            created_at="",
            updated_at="",
            completion_percentage=100.0 if result.get("status") == "completed" else 0.0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/run", response_model=AgentExecutionResponse)
async def run_agent(request: AgentExecutionRequest):
    """Execute an agent.
    
    Args:
        request: Agent execution request.
        
    Returns:
        Agent execution result.
    """
    try:
        service = get_flynt_service()
        
        # Check project exists
        project = service.get_project(request.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Map agent type to agent name
        agent_name_map = {
            "idea": "IdeaAgent",
            "idea_validator": "IdeaValidatorAgent",
            "planner": "PlannerAgent",
            "coder": "CoderAgent",
            "code_validator": "CodeValidationAgent",
            "security": "SecurityVulnerabilityAgent",
            "notebook": "NotebookAgent",
            "data_science": "DataScienceAgent",
            "mlops": "MLOpsAgent",
            "conflict_resolver": "ConflictResolverAgent",
            "test_critique": "TestCritiqueAgent",
        }
        
        agent_name = agent_name_map.get(request.agent_type.value)
        if not agent_name:
            raise HTTPException(status_code=400, detail=f"Unknown agent type: {request.agent_type}")
        
        # Execute agent
        result = service.run_agent(
            agent_name=agent_name,
            project_id=request.project_id,
            user_input=request.user_input,
            metadata=request.metadata
        )
        
        # Import datetime
        from datetime import datetime
        
        return AgentExecutionResponse(
            agent_name=result.get("agent_name"),
            project_id=request.project_id,
            success=result.get("success"),
            output=result.get("output"),
            execution_time=result.get("execution_time"),
            error=result.get("error"),
            metadata=result.get("metadata"),
            created_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conflicts/{project_id}", response_model=ProjectBlockInfo, status_code=200)
async def get_conflicts(project_id: int):
    """Get blocking conflicts for project.
    
    Args:
        project_id: Project ID.
        
    Returns:
        Blocking conflict information.
    """
    try:
        service = get_flynt_service()
        
        # Check project exists
        project = service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get conflicts
        conflicts = service.get_blocking_conflicts(project_id)
        
        if not conflicts:
            raise HTTPException(status_code=404, detail="No blocking conflicts")
        
        # Import datetime
        from datetime import datetime
        
        return ProjectBlockInfo(
            project_id=project_id,
            status="blocked",
            conflicts=conflicts,
            blocked_since=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conflicts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conflicts/{project_id}/resolve", status_code=200)
async def resolve_conflict(project_id: int, library: str, version: str):
    """Resolve a dependency conflict.
    
    Args:
        project_id: Project ID.
        library: Library name.
        version: Version to use.
        
    Returns:
        Resolve result.
    """
    try:
        service = get_flynt_service()
        
        # Check project exists
        project = service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Resolve conflict
        success = service.resolve_conflict(project_id, library, version)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to resolve conflict")
        
        return {
            "success": True,
            "message": f"Conflict resolved: {library} == {version}",
            "project_id": project_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving conflict: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/manifest/{project_id}", status_code=200)
async def get_manifest(project_id: int):
    """Get unified dependency manifest.
    
    Args:
        project_id: Project ID.
        
    Returns:
        Manifest content.
    """
    try:
        service = get_flynt_service()
        
        # Check project exists
        project = service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get manifest
        manifest = service.get_project_manifest(project_id)
        
        if not manifest:
            raise HTTPException(status_code=400, detail="Failed to generate manifest")
        
        return {
            "project_id": project_id,
            "manifest": manifest,
            "format": "requirements.txt"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting manifest: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
