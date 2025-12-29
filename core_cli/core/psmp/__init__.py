"""
TerraQore Project State Management Protocol (PSMP)
Core module for managing project lifecycle, state transitions, and mandatory dependency resolution.
"""

from .models import DependencySpec, ProjectArtifact, PSMPEvent, DependencyConflict
from .dependency_resolver import DependencyConflictResolver
from .service import PSMPService, ProjectBlockedException, get_psmp_service

__all__ = [
    "DependencySpec",
    "ProjectArtifact",
    "PSMPEvent",
    "DependencyConflict",
    "DependencyConflictResolver",
    "PSMPService",
    "ProjectBlockedException",
    "get_psmp_service",
]
