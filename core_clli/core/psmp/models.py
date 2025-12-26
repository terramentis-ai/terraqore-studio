"""
PSMP Models - Data structures for the Project State Management Protocol.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
from datetime import datetime


class DependencyScope(str, Enum):
    """When a dependency is needed."""
    RUNTIME = "runtime"
    DEV = "dev"
    BUILD = "build"


class EventType(str, Enum):
    """Types of events in a project lifecycle."""
    PROJECT_CREATED = "project_created"
    ARTIFACT_DECLARED = "artifact_declared"
    DEPENDENCY_ADDED = "dependency_added"
    CONFLICT_DETECTED = "conflict_detected"
    PROJECT_BLOCKED = "project_blocked"
    CONFLICT_RESOLVED = "conflict_resolved"
    PROJECT_UNBLOCKED = "project_unblocked"
    STATE_TRANSITION = "state_transition"


@dataclass
class DependencySpec:
    """Standard model for an agent to declare a dependency."""
    name: str
    version_constraint: str  # e.g., ">=2.0,<3.0", "==1.5.*"
    scope: DependencyScope  # When is it needed?
    declared_by_agent: str  # Which agent added it?
    purpose: Optional[str] = None  # Why is it needed?
    declared_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version_constraint": self.version_constraint,
            "scope": self.scope.value,
            "declared_by_agent": self.declared_by_agent,
            "purpose": self.purpose,
            "declared_at": self.declared_at.isoformat()
        }


@dataclass
class DependencyConflict:
    """Represents a detected dependency conflict."""
    library: str
    requirements: List[Dict[str, str]]  # [{"agent": "CoderAgent", "needs": "pandas>=2.0"}, ...]
    error: str
    severity: Literal["warning", "error", "critical"] = "error"
    suggested_resolutions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "library": self.library,
            "requirements": self.requirements,
            "error": self.error,
            "severity": self.severity,
            "suggested_resolutions": self.suggested_resolutions
        }


@dataclass
class ProjectArtifact:
    """Artifact declared by an agent during execution."""
    artifact_id: str
    agent_id: str
    project_id: int
    artifact_type: str  # "code", "config", "model", "data"
    content_summary: str
    dependencies: List[DependencySpec] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "artifact_id": self.artifact_id,
            "agent_id": self.agent_id,
            "project_id": self.project_id,
            "artifact_type": self.artifact_type,
            "content_summary": self.content_summary,
            "dependencies": [d.to_dict() for d in self.dependencies],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class PSMPEvent:
    """Event in the project state management audit trail."""
    event_id: str
    event_type: EventType
    project_id: int
    timestamp: datetime = field(default_factory=datetime.now)
    agent_name: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "project_id": self.project_id,
            "timestamp": self.timestamp.isoformat(),
            "agent_name": self.agent_name,
            "details": self.details
        }
