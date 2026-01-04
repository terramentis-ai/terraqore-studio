"""Pydantic data models that power MetaQore's governance layer."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field


def current_utc() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


class MetaQoreModel(BaseModel):
    """Base model with strict field enforcement and helper utilities."""

    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
    }

    def to_dict(self) -> Dict[str, Any]:
        """Shorthand for ``model_dump`` to keep calling code tidy."""

        return self.model_dump()

    def to_json(self, **kwargs: Any) -> str:
        """JSON string representation using Pydantic's serializer."""

        return self.model_dump_json(**kwargs)


class ProjectStatus(str, Enum):
    INITIALIZED = "initialized"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class ConflictSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResolutionStrategy(str, Enum):
    RETRY = "retry"
    OVERRIDE = "override"
    MERGE = "merge"
    ESCALATE = "escalate"


class Conflict(MetaQoreModel):
    """Represents a blocking issue detected by PSMP."""

    id: str = Field(default_factory=lambda: f"conf_{uuid4().hex[:12]}")
    artifact_id: str
    project_id: Optional[str] = None
    description: str
    severity: ConflictSeverity = ConflictSeverity.MEDIUM
    conflict_type: str = Field(default="generic")
    resolution_strategy: ResolutionStrategy = ResolutionStrategy.RETRY
    resolved: bool = False
    created_at: datetime = Field(default_factory=current_utc)
    resolved_at: Optional[datetime] = None

    def mark_resolved(self, strategy: ResolutionStrategy) -> None:
        self.resolution_strategy = strategy
        self.resolved = True
        self.resolved_at = current_utc()


class VetoReason(MetaQoreModel):
    reason: str
    policy_violated: str
    severity: ConflictSeverity = ConflictSeverity.CRITICAL
    details: Dict[str, Any] = Field(default_factory=dict)


class Artifact(MetaQoreModel):
    id: str = Field(default_factory=lambda: f"art_{uuid4().hex[:12]}")
    project_id: str
    artifact_type: str
    version: int = 1
    data: Dict[str, Any]
    created_by: str
    created_at: datetime = Field(default_factory=current_utc)
    depends_on: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    blocked_by: List[Conflict] = Field(default_factory=list)
    provenance: List["Provenance"] = Field(default_factory=list)

    @computed_field  # type: ignore[arg-type]
    @property
    def is_blocked(self) -> bool:
        return any(not conflict.resolved for conflict in self.blocked_by)

    def add_conflict(self, conflict: Conflict) -> None:
        self.blocked_by.append(conflict)

    def add_provenance(self, entry: "Provenance") -> None:
        self.provenance.append(entry)


class Task(MetaQoreModel):
    id: str = Field(default_factory=lambda: f"task_{uuid4().hex[:12]}")
    project_id: str
    title: str
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[str] = None
    depends_on: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=current_utc)
    updated_at: datetime = Field(default_factory=current_utc)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def mark_completed(self) -> None:
        self.status = TaskStatus.COMPLETED
        self.completed_at = current_utc()
        self.updated_at = self.completed_at


class Project(MetaQoreModel):
    id: str = Field(default_factory=lambda: f"proj_{uuid4().hex[:12]}")
    name: str
    description: Optional[str] = None
    owner_id: Optional[str] = None
    status: ProjectStatus = ProjectStatus.INITIALIZED
    created_at: datetime = Field(default_factory=current_utc)
    updated_at: datetime = Field(default_factory=current_utc)
    artifacts: List[Artifact] = Field(default_factory=list)
    tasks: List[Task] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_artifact(self, artifact: Artifact) -> None:
        self.artifacts.append(artifact)
        self.updated_at = current_utc()

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)
        self.updated_at = current_utc()


class Checkpoint(MetaQoreModel):
    id: str = Field(default_factory=lambda: f"chk_{uuid4().hex[:12]}")
    project_id: str
    label: str
    snapshot: Dict[str, Any]
    created_at: datetime = Field(default_factory=current_utc)


class Provenance(MetaQoreModel):
    id: str = Field(default_factory=lambda: f"prov_{uuid4().hex[:12]}")
    artifact_id: str
    actor: str
    action: str
    reason: Optional[str] = None
    signature: Optional[str] = None
    created_at: datetime = Field(default_factory=current_utc)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BlockingReport(MetaQoreModel):
    project_id: str
    conflicts: List[Conflict]
    blocked_artifacts: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=current_utc)

    @classmethod
    def from_artifacts(cls, project_id: str, artifacts: Sequence[Artifact]) -> "BlockingReport":
        blocked = [artifact for artifact in artifacts if artifact.is_blocked]
        conflict_set: List[Conflict] = []
        blocked_ids: List[str] = []
        for artifact in blocked:
            blocked_ids.append(artifact.id)
            conflict_set.extend(conflict for conflict in artifact.blocked_by if not conflict.resolved)
        return cls(
            project_id=project_id,
            conflicts=conflict_set,
            blocked_artifacts=blocked_ids,
        )


__all__ = [
    "MetaQoreModel",
    "ProjectStatus",
    "TaskStatus",
    "ConflictSeverity",
    "ResolutionStrategy",
    "Conflict",
    "VetoReason",
    "Artifact",
    "Task",
    "Project",
    "Checkpoint",
    "Provenance",
    "BlockingReport",
]
