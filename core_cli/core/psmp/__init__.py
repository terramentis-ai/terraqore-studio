"""
TerraQore Project State Management Protocol (PSMP)
Core module for managing project lifecycle, state transitions, and mandatory dependency resolution.
"""

from .models import DependencySpec, ProjectArtifact, PSMPEvent
from .dependency_resolver import DependencyConflictResolver
from .service import PSMPService

__all__ = [
    "DependencySpec",
    "ProjectArtifact",
    "PSMPEvent",
    "DependencyConflictResolver",
    "PSMPService",
]
