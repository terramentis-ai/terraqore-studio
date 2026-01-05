"""Shared API schemas for MetaQore endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field

from metaqore.config import GovernanceMode
from metaqore.core.models import (
    Artifact,
    BlockingReport,
    Conflict,
    Project,
    ProjectStatus,
    ResolutionStrategy,
    SpecialistModel,
    Task,
    TaskStatus,
)


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


class ConflictListData(BaseModel):
    project_id: str
    conflicts: List[Conflict]
    total: int
    page: int
    page_size: int
    filters: Dict[str, Any] = Field(default_factory=dict)


class ConflictListResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: ConflictListData
    metadata: ResponseMetadata


class ConflictResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: Conflict
    metadata: ResponseMetadata


class ConflictResolutionRequest(BaseModel):
    strategy: ResolutionStrategy = ResolutionStrategy.RETRY


class SpecialistProposalRequest(BaseModel):
    project_id: str
    created_by: str
    skill_id: str
    requested_size_mb: int = Field(gt=0)
    teachers: List[str] = Field(default_factory=list, min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    task_isolation_passed: bool
    parent_level_identifier: Optional[Union[str, int]] = None
    parameter_count: Optional[int] = Field(default=None, ge=1)
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SpecialistSkillInfo(BaseModel):
    skill_id: str
    description: str
    parent_agent: str
    max_specialist_size_mb: int
    allowed_teachers: List[str]


class SpecialistLevelInfo(BaseModel):
    index: int
    key: str
    level_type: str
    example: str
    max_parameters: int
    raw_max_size: str
    can_spawn: bool


class SpecialistSpawnDecisionInfo(BaseModel):
    allowed: bool
    reasons: List[str]
    next_level_key: Optional[str] = None


class SpecialistEvaluationData(BaseModel):
    allowed: bool
    reasons: List[str]
    skill: SpecialistSkillInfo
    target_level: Optional[SpecialistLevelInfo] = None
    spawn_decision: Optional[SpecialistSpawnDecisionInfo] = None


class SpecialistEvaluationResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: SpecialistEvaluationData
    metadata: ResponseMetadata


class SpecialistDraftData(BaseModel):
    specialist: SpecialistModel
    gateway_job_id: Optional[str] = None


class SpecialistDraftResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: SpecialistDraftData
    metadata: ResponseMetadata


class SpecialistPipelineData(BaseModel):
    specialist: SpecialistModel
    training: Dict[str, Any]
    validation: Dict[str, Any]
    gateway_job_id: Optional[str] = None


class SpecialistPipelineResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: SpecialistPipelineData
    metadata: ResponseMetadata


class AuditEventRecord(BaseModel):
    timestamp: str
    event_type: str
    organization: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class BlockingReportResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: BlockingReport
    metadata: ResponseMetadata


class ComplianceReportData(BaseModel):
    organization: str
    format: Literal["json", "csv"] = "json"
    report: Dict[str, Any]
    events: List[AuditEventRecord] = Field(default_factory=list)


class ComplianceReportResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: ComplianceReportData
    metadata: ResponseMetadata


class AuditTrailData(BaseModel):
    organization: str
    events: List[AuditEventRecord]
    total: int
    page: int
    page_size: int
    filters: Dict[str, Any] = Field(default_factory=dict)


class AuditTrailResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: AuditTrailData
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
    "ConflictListData",
    "ConflictListResponse",
    "ConflictResponse",
    "ConflictResolutionRequest",
    "SpecialistProposalRequest",
    "SpecialistSkillInfo",
    "SpecialistLevelInfo",
    "SpecialistSpawnDecisionInfo",
    "SpecialistEvaluationData",
    "SpecialistEvaluationResponse",
    "SpecialistDraftData",
    "SpecialistDraftResponse",
    "SpecialistPipelineData",
    "SpecialistPipelineResponse",
    "AuditEventRecord",
    "BlockingReportResponse",
    "ComplianceReportData",
    "ComplianceReportResponse",
    "AuditTrailData",
    "AuditTrailResponse",
]
