"""Event type definitions for MetaQore streaming."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4


class EventType(str, Enum):
    """Rich event types covering MetaQore lifecycle."""

    # Project events
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"
    PROJECT_STATUS_CHANGED = "project.status_changed"

    # Artifact events
    ARTIFACT_CREATED = "artifact.created"
    ARTIFACT_UPDATED = "artifact.updated"
    ARTIFACT_DELETED = "artifact.deleted"
    ARTIFACT_BLOCKED = "artifact.blocked"
    ARTIFACT_UNBLOCKED = "artifact.unblocked"

    # Task events
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    # Conflict events
    CONFLICT_DETECTED = "conflict.detected"
    CONFLICT_RESOLVED = "conflict.resolved"
    CONFLICT_ESCALATED = "conflict.escalated"

    # Checkpoint events
    CHECKPOINT_CREATED = "checkpoint.created"
    CHECKPOINT_RESTORED = "checkpoint.restored"

    # Governance events
    POLICY_VIOLATION = "governance.policy_violation"
    VETO_APPLIED = "governance.veto_applied"
    COMPLIANCE_AUDIT = "governance.compliance_audit"

    # Streaming events
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"


class EventCategory(str, Enum):
    """Event categorization for filtering."""

    PROJECTS = "projects"
    ARTIFACTS = "artifacts"
    TASKS = "tasks"
    CONFLICTS = "conflicts"
    GOVERNANCE = "governance"
    CHECKPOINT = "checkpoint"
    SUBSCRIPTION = "subscription"


@dataclass(slots=True)
class Event:
    """Represents a single MetaQore event."""

    event_id: str = field(default_factory=lambda: f"evt_{uuid4().hex[:12]}")
    event_type: EventType = field(default=EventType.PROJECT_CREATED)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resource_id: str = ""
    resource_type: str = ""
    project_id: Optional[str] = None
    actor: Optional[str] = None
    changes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "project_id": self.project_id,
            "actor": self.actor,
            "changes": self.changes,
            "metadata": self.metadata,
            "severity": self.severity,
        }

    def to_message(self) -> Dict[str, Any]:
        """Serialize event to WebSocket message format."""
        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Event:
        """Deserialize event from dictionary."""
        data = data.copy()
        if "event_type" in data and isinstance(data["event_type"], str):
            data["event_type"] = EventType(data["event_type"])
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

    def matches_subscription(self, patterns: list[str]) -> bool:
        """Check if event matches any subscription pattern (wildcard support)."""
        event_type_value = self.event_type.value
        for pattern in patterns:
            if pattern == "*":
                return True
            if pattern == f"{self.resource_type}.*":
                return True
            if pattern == event_type_value:
                return True
        return False


# Backward compatibility alias
StreamingEvent = Event

__all__ = ["EventType", "EventCategory", "Event", "StreamingEvent"]
