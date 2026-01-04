"""Custom exception hierarchy for the MetaQore package.

Each exception inherits from :class:`MetaQoreError` so callers can catch a
single base type when needed. Individual exceptions capture relevant metadata
that may be used by audit logging or higher-level error handling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


class MetaQoreError(Exception):
    """Base class for all MetaQore-specific exceptions."""

    def __init__(self, message: str, *, metadata: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.args[0]!r}, metadata={self.metadata!r})"


class GovernanceViolation(MetaQoreError):
    """Raised when a request violates the current governance policy."""


class SignatureValidationError(MetaQoreError):
    """Raised when a signed payload or artifact fails signature validation."""


class ConflictDetectedError(MetaQoreError):
    """Raised when PSMP detects an unresolvable artifact conflict."""


class CheckpointNotFoundError(MetaQoreError):
    """Raised when a requested checkpoint ID cannot be found or restored."""


@dataclass(slots=True)
class VetoExceptionContext:
    """Structured details for veto operations enforced by SecureGateway."""

    agent_name: str
    task_type: str
    reason: str
    policy: str
    severity: str = "critical"


class VetoAppliedError(MetaQoreError):
    """Raised when SecureGateway vetoes an operation and execution must stop."""

    def __init__(self, context: VetoExceptionContext) -> None:
        super().__init__(context.reason, metadata={
            "agent_name": context.agent_name,
            "task_type": context.task_type,
            "policy": context.policy,
            "severity": context.severity,
        })
        self.context = context
