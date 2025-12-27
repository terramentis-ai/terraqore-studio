"""
TerraQoreService
Wrapper around orchestrator and state manager for API calls.
"""

import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from core.state import get_state_manager, Project, ProjectStatus, Task, TaskStatus
from orchestration.orchestrator import AgentOrchestrator
from agents.base import AgentContext

logger = logging.getLogger(__name__)


class TerraQoreService:
    """Service layer for API interactions with TerraQore Core."""
    
    def __init__(self):
        """Initialize service."""
        self.state_mgr = get_state_manager()
        self.orchestrator = AgentOrchestrator()
    
    # ========================================================================
    # Project Operations
    # ========================================================================
    
    def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        tech_stack: Optional[List[str]] = None,
        goals: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new project.
        
        Args:
            name: Project name.
            description: Project description.
            tech_stack: Technology stack.
            goals: Project goals.
            
        Returns:
            Created project data.
        """
        project = Project(
            name=name,
            description=description,
            status=ProjectStatus.INITIALIZED.value,
            created_at="",  # State manager will set this
        )
        
        project_id = self.state_mgr.create_project(project)
        
        # Store metadata
        if tech_stack or goals:
            metadata = {
                "tech_stack": tech_stack or [],
                "goals": goals or []
            }
            # TODO: Store metadata in project
        
        return self.get_project(project_id)
    
    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get project by ID.
        
        Args:
            project_id: Project ID.
            
        Returns:
            Project data or None.
        """
        project = self.state_mgr.get_project(project_id=project_id)
        
        if not project:
            return None
        
        # Get task count and completion
        tasks = self.state_mgr.get_tasks(project_id)
        task_count = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED.value)
        completion_pct = (completed / task_count * 100) if task_count > 0 else 0.0
        
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "task_count": task_count,
            "completion_percentage": completion_pct
        }
    
    def list_projects(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List projects.
        
        Args:
            status: Filter by status.
            limit: Result limit.
            offset: Result offset.
            
        Returns:
            Project list with pagination.
        """
        projects = self.state_mgr.get_projects()
        
        # Filter by status
        if status:
            projects = [p for p in projects if p.status == status]
        
        # Pagination
        total = len(projects)
        projects = projects[offset:offset+limit]
        
        # Convert to dict
        project_dicts = [self.get_project(p.id) for p in projects]
        
        return {
            "projects": project_dicts,
            "total": total,
            "page": offset // limit + 1,
            "page_size": limit
        }
    
    def update_project(
        self,
        project_id: int,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Update project.
        
        Args:
            project_id: Project ID.
            **kwargs: Fields to update.
            
        Returns:
            Updated project or None.
        """
        project = self.state_mgr.get_project(project_id=project_id)
        
        if not project:
            return None
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        self.state_mgr.update_project(project)
        return self.get_project(project_id)
    
    # ========================================================================
    # Task Operations
    # ========================================================================
    
    def create_task(
        self,
        project_id: int,
        title: str,
        description: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a task.
        
        Args:
            project_id: Parent project ID.
            title: Task title.
            description: Task description.
            **kwargs: Additional task fields.
            
        Returns:
            Created task data.
        """
        task = Task(
            project_id=project_id,
            title=title,
            description=description,
            status=TaskStatus.PENDING.value,
            **kwargs
        )
        
        task_id = self.state_mgr.create_task(task)
        return self.get_task(task_id)
    
    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get task by ID.
        
        Args:
            task_id: Task ID.
            
        Returns:
            Task data or None.
        """
        task = self.state_mgr.get_task(task_id)
        
        if not task:
            return None
        
        return {
            "id": task.id,
            "project_id": task.project_id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "milestone": task.milestone,
            "priority": task.priority,
            "estimated_hours": task.estimated_hours,
            "actual_hours": task.actual_hours,
            "agent_type": task.agent_type,
            "created_at": task.created_at,
            "completed_at": task.completed_at
        }
    
    def list_tasks(
        self,
        project_id: int,
        status: Optional[str] = None,
        milestone: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List tasks for project.
        
        Args:
            project_id: Project ID.
            status: Filter by status.
            milestone: Filter by milestone.
            
        Returns:
            List of task data.
        """
        tasks = self.state_mgr.get_tasks(project_id)
        
        # Filter
        if status:
            tasks = [t for t in tasks if t.status == status]
        if milestone:
            tasks = [t for t in tasks if t.milestone == milestone]
        
        # Convert to dict
        return [self.get_task(t.id) for t in tasks]
    
    def update_task(
        self,
        task_id: int,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Update a task.
        
        Args:
            task_id: Task ID.
            **kwargs: Fields to update.
            
        Returns:
            Updated task or None.
        """
        task = self.state_mgr.get_task(task_id)
        
        if not task:
            return None
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        self.state_mgr.update_task(task_id, **kwargs)
        return self.get_task(task_id)
    
    # ========================================================================
    # Workflow Operations
    # ========================================================================
    
    def run_ideation(self, project_id: int, user_input: Optional[str] = None) -> Dict[str, Any]:
        """Run ideation workflow.
        
        Args:
            project_id: Project ID.
            user_input: Optional user guidance.
            
        Returns:
            Workflow result.
        """
        result = self.orchestrator.run_ideation(project_id, user_input)
        
        return {
            "workflow_id": f"ideation_{project_id}",
            "project_id": project_id,
            "workflow_type": "ideate",
            "status": "completed" if result.success else "failed",
            "output": result.output,
            "error": result.error,
            "execution_time": result.execution_time
        }
    
    def run_planning(self, project_id: int, user_input: Optional[str] = None) -> Dict[str, Any]:
        """Run planning workflow.
        
        Args:
            project_id: Project ID.
            user_input: Optional user guidance.
            
        Returns:
            Workflow result.
        """
        result = self.orchestrator.run_planning(project_id, user_input)
        
        return {
            "workflow_id": f"planning_{project_id}",
            "project_id": project_id,
            "workflow_type": "plan",
            "status": "completed" if result.success else "failed",
            "output": result.output,
            "error": result.error,
            "execution_time": result.execution_time
        }
    
    def run_agent(
        self,
        agent_name: str,
        project_id: int,
        user_input: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Run specific agent.
        
        Args:
            agent_name: Name of agent to run.
            project_id: Project ID.
            user_input: User input.
            metadata: Additional metadata.
            
        Returns:
            Agent execution result.
        """
        context = AgentContext(
            project_id=project_id,
            task_id=None,
            user_input=user_input or "",
            previous_output="",
            metadata=metadata or {}
        )
        
        result = self.orchestrator.run_agent(agent_name, context)
        
        return {
            "agent_name": result.agent_name,
            "project_id": project_id,
            "success": result.success,
            "output": result.output,
            "execution_time": result.execution_time,
            "error": result.error,
            "metadata": result.metadata
        }
    
    # ========================================================================
    # PSMP/Conflict Operations
    # ========================================================================
    
    def get_blocking_conflicts(self, project_id: int) -> Optional[List[Dict[str, Any]]]:
        """Get blocking conflicts for project.
        
        Args:
            project_id: Project ID.
            
        Returns:
            List of conflicts or None.
        """
        from core.psmp import get_psmp_service
        
        psmp = get_psmp_service()
        
        try:
            conflicts = psmp.get_blocking_conflicts(project_id)
            return [c.to_dict() for c in conflicts] if conflicts else None
        except Exception as e:
            logger.error(f"Error getting conflicts: {e}")
            return None
    
    def resolve_conflict(self, project_id: int, library: str, version: str) -> bool:
        """Resolve a conflict.
        
        Args:
            project_id: Project ID.
            library: Library name.
            version: Version to use.
            
        Returns:
            True if resolved.
        """
        from core.psmp import get_psmp_service
        
        psmp = get_psmp_service()
        
        try:
            return psmp.resolve_conflict_manual(project_id, library, version)
        except Exception as e:
            logger.error(f"Error resolving conflict: {e}")
            return False
    
    def get_project_manifest(self, project_id: int) -> Optional[str]:
        """Get unified dependency manifest.
        
        Args:
            project_id: Project ID.
            
        Returns:
            Manifest content or None.
        """
        from core.psmp import get_psmp_service
        
        psmp = get_psmp_service()
        
        try:
            return psmp.get_unified_manifest(project_id)
        except Exception as e:
            logger.error(f"Error getting manifest: {e}")
            return None


def get_terraqore_service() -> TerraQoreService:
    """Get singleton TerraQore service instance.
    
    Returns:
        TerraQoreService instance.
    """
    if not hasattr(get_terraqore_service, "_instance"):
        get_terraqore_service._instance = TerraQoreService()
    return get_terraqore_service._instance
