"""
MetaQore - Orchestration Governance Engine

A standalone orchestration governance service that enforces PSMP (Project State
Management Protocol) as mandatory governance, with configurable strictness modes
and bounded execution engines for graph and conversation workflows.

Version: 0.1.0 (Development)
Author: MetaQore Development Team
License: MIT
"""

__version__ = "0.1.0"
__author__ = "MetaQore Development Team"

# Core exports (available after implementation)
# from .core.psmp import PSMPEngine
# from .core.models import Artifact, Project, Task, Conflict, Checkpoint
# from .core.state_manager import StateManager
# from .core.security import SecureGateway, TaskSensitivity
# from .config import MetaQoreConfig, GovernanceMode

__all__ = [
    "__version__",
    # "PSMPEngine",
    # "Artifact",
    # "Project",
    # "Task",
    # "StateManager",
    # "SecureGateway",
    # "MetaQoreConfig",
    # "GovernanceMode",
]
