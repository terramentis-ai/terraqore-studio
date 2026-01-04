"""Shared API schemas for MetaQore endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from metaqore.config import GovernanceMode
from metaqore.core.models import Artifact, Project, ProjectStatus, Task, TaskStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ResponseStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"


class ResponseMetadata(BaseModel):
    request_id: str = Field(default="-")
    timestamp: datetime = Field(default_factory=_utcnow)
    latency_ms: float = Field(default=0.0, ge=0.0)


class HealthStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"


class HealthPayload(BaseModel):
    service: Literal["metaqore-api"] = "metaqore-api"
    status: HealthStatus = HealthStatus.OK
    uptime_seconds: float = Field(default=0.0, ge=0.0)
    governance_mode: GovernanceMode = GovernanceMode.STRICT
    version: str = Field(default="0.1.0")


class HealthResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: HealthPayload
    metadata: ResponseMetadata


class ProjectCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    owner_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[str] = None
    status: Optional[ProjectStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: Project
    metadata: ResponseMetadata


class ProjectListData(BaseModel):
    projects: List[Project]
    total: int
    page: int
    page_size: int
    filters: Dict[str, Any] = Field(default_factory=dict)


class ProjectListResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: ProjectListData
    metadata: ResponseMetadata


class TaskCreateRequest(BaseModel):
    project_id: str
    title: str
    assigned_to: Optional[str] = None
    depends_on: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    status: Optional[TaskStatus] = None
    assigned_to: Optional[str] = None
    depends_on: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: Task
    metadata: ResponseMetadata


class TaskListData(BaseModel):
    project_id: str
    tasks: List[Task]
    total: int
    page: int
    page_size: int
    filters: Dict[str, Any] = Field(default_factory=dict)


class TaskListResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: TaskListData
    metadata: ResponseMetadata


class ArtifactCreateRequest(BaseModel):
    project_id: str
    artifact_type: str
    data: Dict[str, Any]
    created_by: str
    depends_on: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ArtifactUpdateRequest(BaseModel):
    artifact_type: Optional[str] = None
    version: Optional[int] = Field(default=None, ge=1)
    data: Optional[Dict[str, Any]] = None
    depends_on: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ArtifactResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: Artifact
    metadata: ResponseMetadata


class ArtifactListData(BaseModel):
    project_id: str
    artifacts: List[Artifact]
    total: int
    page: int
    page_size: int
    filters: Dict[str, Any] = Field(default_factory=dict)


class ArtifactListResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: ArtifactListData
    metadata: ResponseMetadata


__all__ = [
    "ResponseStatus",
    "ResponseMetadata",
    "HealthStatus",
    "HealthPayload",
    "HealthResponse",
    "ProjectCreateRequest",
    "ProjectUpdateRequest",
    "ProjectResponse",
    "ProjectListResponse",
    "TaskCreateRequest",
    "TaskUpdateRequest",
    "TaskResponse",
    "TaskListResponse",
    "ArtifactCreateRequest",
    "ArtifactUpdateRequest",
    "ArtifactResponse",
    "ArtifactListResponse",
]
