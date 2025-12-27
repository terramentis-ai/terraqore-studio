"""
Pydantic Models for TerraQore API
Defines all request/response schemas.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ProjectStatus(str, Enum):
    """Project status enumeration."""
    INITIALIZED = "initialized"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentType(str, Enum):
    """Types of agents available."""
    IDEA = "idea"
    IDEA_VALIDATOR = "idea_validator"
    PLANNER = "planner"
    CODER = "coder"
    CODE_VALIDATOR = "code_validator"
    SECURITY = "security"
    NOTEBOOK = "notebook"
    DATA_SCIENCE = "data_science"
    MLOPS = "mlops"
    CONFLICT_RESOLVER = "conflict_resolver"
    TEST_CRITIQUE = "test_critique"


# ============================================================================
# Project Models
# ============================================================================

class ProjectCreate(BaseModel):
    """Request model for creating a project."""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, max_length=1000, description="Project description")
    tech_stack: Optional[List[str]] = Field(None, description="Technology stack")
    goals: Optional[List[str]] = Field(None, description="Project goals")


class ProjectUpdate(BaseModel):
    """Request model for updating a project."""
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[ProjectStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    """Response model for project."""
    id: int
    name: str
    description: Optional[str]
    status: ProjectStatus
    created_at: datetime
    updated_at: Optional[datetime]
    task_count: int = 0
    completion_percentage: float = 0.0
    
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Response model for project list."""
    projects: List[ProjectResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Task Models
# ============================================================================

class TaskCreate(BaseModel):
    """Request model for creating a task."""
    project_id: int = Field(..., description="Parent project ID")
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    milestone: Optional[str] = Field(None, max_length=255, description="Milestone")
    priority: Optional[int] = Field(1, ge=1, le=5, description="Priority (1-5)")
    estimated_hours: Optional[float] = Field(None, ge=0, description="Estimated hours")
    agent_type: Optional[AgentType] = None


class TaskUpdate(BaseModel):
    """Request model for updating a task."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    milestone: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None


class TaskResponse(BaseModel):
    """Response model for task."""
    id: int
    project_id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    milestone: Optional[str]
    priority: int
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    agent_type: Optional[AgentType]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Response model for task list."""
    tasks: List[TaskResponse]
    total: int
    project_id: int


# ============================================================================
# Agent Models
# ============================================================================

class AgentExecutionRequest(BaseModel):
    """Request to execute an agent."""
    agent_type: AgentType = Field(..., description="Type of agent to execute")
    project_id: int = Field(..., description="Project ID")
    user_input: Optional[str] = Field(None, description="User input/guidance")
    metadata: Optional[Dict[str, Any]] = None


class AgentExecutionResponse(BaseModel):
    """Response from agent execution."""
    agent_name: str
    project_id: int
    success: bool
    output: str
    execution_time: float
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


# ============================================================================
# Workflow Models
# ============================================================================

class WorkflowStep(BaseModel):
    """Represents a step in a workflow."""
    step_number: int
    agent_type: AgentType
    title: str
    description: Optional[str]
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None


class WorkflowExecutionRequest(BaseModel):
    """Request to execute a workflow."""
    project_id: int = Field(..., description="Project ID")
    workflow_type: str = Field(
        ...,
        description="Type of workflow: ideate, plan, code, validate, deploy"
    )


class WorkflowExecutionResponse(BaseModel):
    """Response from workflow execution."""
    workflow_id: str
    project_id: int
    workflow_type: str
    status: str  # running, completed, failed
    current_step: int
    total_steps: int
    steps: List[WorkflowStep]
    created_at: datetime
    updated_at: datetime
    completion_percentage: float


# ============================================================================
# Dependency/PSMP Models
# ============================================================================

class DependencySpecRequest(BaseModel):
    """Request to declare a dependency."""
    name: str = Field(..., description="Package name")
    version_constraint: str = Field(..., description="Version constraint (e.g., >=2.0)")
    scope: str = Field(..., description="Scope: runtime, dev, or build")
    purpose: str = Field(..., description="Purpose/reason for dependency")


class ConflictInfo(BaseModel):
    """Information about a dependency conflict."""
    library: str
    requirements: List[Dict[str, str]]  # {agent, needs, purpose}
    severity: str
    suggested_resolutions: List[str]


class ProjectBlockInfo(BaseModel):
    """Information about why a project is blocked."""
    project_id: int
    status: str = "blocked"
    conflicts: List[ConflictInfo]
    blocked_since: datetime


# ============================================================================
# Error Response Models
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    type: str
    status_code: int


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    detail: List[Dict[str, Any]]
    type: str = "validation_error"
    status_code: int = 422
