"""
PSMP Service - Core orchestration of the Project State Management Protocol.

Responsibilities:
- Project state machine enforcement
- Mandatory artifact declaration with dependency validation
- Conflict detection and project blocking
- Event sourced audit trail
- Unified dependency manifest generation
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from core.state import get_state_manager, ProjectStatus
from .models import ProjectArtifact, DependencySpec, PSMPEvent, EventType, DependencyScope
from .dependency_resolver import get_dependency_resolver, DependencyConflict

logger = logging.getLogger(__name__)


class ProjectBlockedException(Exception):
    """Raised when a project is in BLOCKED state."""
    def __init__(self, project_id: int, conflicts: List[DependencyConflict]):
        self.project_id = project_id
        self.conflicts = conflicts
        super().__init__(
            f"Project {project_id} is BLOCKED due to dependency conflicts"
        )


class PSMPService:
    """
    Core PSMP service that manages project lifecycle, state transitions,
    and mandatory dependency validation.
    """
    
    def __init__(self):
        """Initialize PSMP service."""
        self.state_mgr = get_state_manager()
        self.resolver = get_dependency_resolver()
        self.event_log: List[PSMPEvent] = []
        self.artifacts: Dict[int, List[ProjectArtifact]] = {}  # project_id -> artifacts
        logger.info("PSMP Service initialized")
    
    # =========================================================================
    # STATE MACHINE OPERATIONS
    # =========================================================================
    
    def get_project_state(self, project_id: int) -> str:
        """Get current project state."""
        project = self.state_mgr.get_project(project_id=project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        return project.status
    
    def transition_project_state(
        self,
        project_id: int,
        new_state: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Attempt to transition project to a new state.
        Enforces valid state transitions.
        
        Valid transitions:
        INITIALIZED → PLANNING → IN_PROGRESS → COMPLETED
                  ↗ PLANNING → BLOCKED ↔ RESOLVING ↘ COMPLETED
                  → ARCHIVED (from any state)
        """
        current_state = self.get_project_state(project_id)
        
        # Define valid transitions
        valid_transitions = {
            ProjectStatus.INITIALIZED.value: [
                ProjectStatus.PLANNING.value,
                ProjectStatus.ARCHIVED.value
            ],
            ProjectStatus.PLANNING.value: [
                ProjectStatus.IN_PROGRESS.value,
                ProjectStatus.BLOCKED.value,
                ProjectStatus.ARCHIVED.value
            ],
            ProjectStatus.IN_PROGRESS.value: [
                ProjectStatus.COMPLETED.value,
                ProjectStatus.BLOCKED.value,
                ProjectStatus.ARCHIVED.value
            ],
            ProjectStatus.BLOCKED.value: [
                ProjectStatus.IN_PROGRESS.value,  # After resolution
                ProjectStatus.ARCHIVED.value
            ],
            ProjectStatus.COMPLETED.value: [
                ProjectStatus.ARCHIVED.value
            ],
            ProjectStatus.ARCHIVED.value: []  # Terminal state
        }
        
        if new_state not in valid_transitions.get(current_state, []):
            logger.warning(
                f"Invalid transition: {current_state} → {new_state}"
            )
            return False
        
        # Update project state
        self.state_mgr.update_project(project_id, status=new_state)
        
        # Log event
        event = PSMPEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.STATE_TRANSITION,
            project_id=project_id,
            details={
                "from_state": current_state,
                "to_state": new_state,
                "reason": reason
            }
        )
        self._log_event(event)
        
        logger.info(f"Project {project_id} transitioned: {current_state} → {new_state}")
        return True
    
    # =========================================================================
    # ARTIFACT DECLARATION (MANDATORY)
    # =========================================================================
    
    def declare_artifact(
        self,
        project_id: int,
        agent_id: str,
        artifact_type: str,
        content_summary: str,
        dependencies: Optional[List[DependencySpec]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[ProjectArtifact], Optional[List[DependencyConflict]]]:
        """
        MANDATORY: Agents must call this when producing artifacts.
        
        This enforces:
        1. Artifact declaration with dependencies
        2. Automatic conflict detection
        3. Project blocking if conflicts found
        
        Args:
            project_id: Project ID
            agent_id: Agent declaring the artifact
            artifact_type: Type of artifact (code, config, model, etc.)
            content_summary: Summary of artifact content
            dependencies: List of DependencySpec objects (required!)
            metadata: Optional metadata
        
        Returns:
            Tuple of (success, artifact, conflicts)
            If success=False and conflicts is not None, project is BLOCKED
        """
        # Check if project is already blocked
        current_state = self.get_project_state(project_id)
        if current_state == ProjectStatus.BLOCKED.value:
            raise ProjectBlockedException(
                project_id,
                self.resolver.conflicts_detected
            )
        
        # Create artifact record
        artifact = ProjectArtifact(
            artifact_id=str(uuid.uuid4()),
            agent_id=agent_id,
            project_id=project_id,
            artifact_type=artifact_type,
            content_summary=content_summary,
            dependencies=dependencies or [],
            metadata=metadata or {}
        )
        
        # Store artifact
        if project_id not in self.artifacts:
            self.artifacts[project_id] = []
        self.artifacts[project_id].append(artifact)
        
        logger.info(f"Agent {agent_id} declared artifact: {artifact_type}")
        
        # Register dependencies and check for conflicts
        if dependencies:
            success, conflicts = self.resolver.register_dependencies(
                project_id,
                agent_id,
                dependencies
            )
            
            if not conflicts:
                # No conflicts - log event and return
                event = PSMPEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.ARTIFACT_DECLARED,
                    project_id=project_id,
                    agent_name=agent_id,
                    details={
                        "artifact_id": artifact.artifact_id,
                        "artifact_type": artifact_type,
                        "dependency_count": len(dependencies)
                    }
                )
                self._log_event(event)
                
                return True, artifact, None
            
            else:
                # Conflicts detected - block project
                logger.error(f"Dependency conflicts detected for project {project_id}")
                
                # Transition to BLOCKED state
                self.transition_project_state(
                    project_id,
                    ProjectStatus.BLOCKED.value,
                    reason=f"Dependency conflict in {conflicts[0].library}"
                )
                
                # Log conflict event
                event = PSMPEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.CONFLICT_DETECTED,
                    project_id=project_id,
                    agent_name=agent_id,
                    details={
                        "artifact_id": artifact.artifact_id,
                        "conflicts": [c.to_dict() for c in conflicts]
                    }
                )
                self._log_event(event)
                
                return False, artifact, conflicts
        
        else:
            # No dependencies declared
            event = PSMPEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.ARTIFACT_DECLARED,
                project_id=project_id,
                agent_name=agent_id,
                details={
                    "artifact_id": artifact.artifact_id,
                    "artifact_type": artifact_type,
                    "dependency_count": 0
                }
            )
            self._log_event(event)
            
            return True, artifact, None
    
    # =========================================================================
    # CONFLICT RESOLUTION
    # =========================================================================
    
    def get_blocking_conflicts(self, project_id: int) -> List[DependencyConflict]:
        """Get conflicts that are blocking a project."""
        return self.resolver.conflicts_detected
    
    def generate_conflict_report(
        self,
        project_id: int
    ) -> Dict[str, Any]:
        """Generate human-readable conflict report."""
        conflicts = self.get_blocking_conflicts(project_id)
        
        report = {
            "project_id": project_id,
            "status": "BLOCKED" if conflicts else "OK",
            "timestamp": datetime.now().isoformat(),
            "total_conflicts": len(conflicts),
            "conflicts": [c.to_dict() for c in conflicts]
        }
        
        return report
    
    def resolve_conflict_manual(
        self,
        project_id: int,
        library: str,
        selected_version: str,
        resolver_agent: str = "manual"
    ) -> bool:
        """
        Manually resolve a conflict by selecting a version.
        
        Args:
            project_id: Project ID
            library: Library with conflict
            selected_version: Selected version constraint
            resolver_agent: Agent/user that resolved it
        
        Returns:
            True if resolved, False if cannot resolve
        """
        # Find and remove the conflict
        conflict_found = False
        for conflict in self.resolver.conflicts_detected[:]:
            if conflict.library == library:
                conflict_found = True
                self.resolver.conflicts_detected.remove(conflict)
                
                # Log resolution
                event = PSMPEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.CONFLICT_RESOLVED,
                    project_id=project_id,
                    agent_name=resolver_agent,
                    details={
                        "library": library,
                        "selected_version": selected_version,
                        "resolver_agent": resolver_agent
                    }
                )
                self._log_event(event)
                
                break
        
        # If all conflicts resolved, unblock project
        if conflict_found and not self.resolver.conflicts_detected:
            self.transition_project_state(
                project_id,
                ProjectStatus.IN_PROGRESS.value,
                reason="All dependency conflicts resolved"
            )
            
            event = PSMPEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.PROJECT_UNBLOCKED,
                project_id=project_id,
                agent_name=resolver_agent
            )
            self._log_event(event)
            
            logger.info(f"Project {project_id} unblocked after conflict resolution")
            return True
        
        return conflict_found
    
    # =========================================================================
    # MANIFEST GENERATION
    # =========================================================================
    
    def get_unified_manifest(self) -> Dict[str, str]:
        """
        Generate unified, conflict-free dependency manifest.
        
        Returns dict suitable for requirements.txt or pyproject.toml
        """
        return self.resolver.get_resolved_manifest()
    
    # =========================================================================
    # EVENT LOG & AUDIT TRAIL
    # =========================================================================
    
    def _log_event(self, event: PSMPEvent):
        """Log an event to the audit trail."""
        self.event_log.append(event)
        logger.debug(f"PSMP Event: {event.event_type.value} for project {event.project_id}")
    
    def get_event_log(self, project_id: int) -> List[PSMPEvent]:
        """Get event log for a project."""
        return [e for e in self.event_log if e.project_id == project_id]
    
    def get_artifact_history(self, project_id: int) -> List[ProjectArtifact]:
        """Get all artifacts declared for a project."""
        return self.artifacts.get(project_id, [])


# Global service instance
_service: Optional[PSMPService] = None


def get_psmp_service() -> PSMPService:
    """Get or create the global PSMP service."""
    global _service
    if _service is None:
        _service = PSMPService()
    return _service
