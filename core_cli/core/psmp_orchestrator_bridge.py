"""
PSMP Orchestrator Bridge
Integrates PSMP state management with orchestrator workflows.
"""

import logging
from typing import Tuple, Optional, List
from agents.base import AgentResult
from core.psmp import (
    get_psmp_service,
    DependencySpec,
    ProjectBlockedException,
    DependencyConflict
)

logger = logging.getLogger(__name__)


class PSMPOrchestrationBridge:
    """Bridge between PSMP service and orchestrator agent execution."""
    
    def __init__(self):
        """Initialize the bridge."""
        self.psmp = get_psmp_service()
    
    def check_project_blocked(self, project_id: int) -> Tuple[bool, Optional[str]]:
        """Check if project is in BLOCKED state.
        
        Args:
            project_id: Project ID to check.
            
        Returns:
            Tuple of (is_blocked, reason).
        """
        try:
            state = self.psmp.get_project_state(project_id)
            if state == "BLOCKED":
                conflicts = self.psmp.get_blocking_conflicts(project_id)
                reason = f"Project blocked due to {len(conflicts)} dependency conflict(s)"
                return True, reason
            return False, None
        except Exception as e:
            logger.error(f"Error checking project state: {e}")
            return False, None
    
    def declare_agent_artifact(
        self,
        project_id: int,
        agent_name: str,
        artifact_type: str,
        result: AgentResult,
        dependencies: Optional[List[DependencySpec]] = None
    ) -> Tuple[bool, Optional[List[DependencyConflict]]]:
        """Declare an artifact produced by an agent.
        
        This is the mandatory artifact declaration that triggers conflict detection.
        
        Args:
            project_id: Project ID.
            agent_name: Name of the agent that produced the artifact.
            artifact_type: Type of artifact (code, plan, analysis, etc).
            result: AgentResult from agent execution.
            dependencies: Optional list of dependencies extracted from artifact.
            
        Returns:
            Tuple of (success, conflicts). If success is False and conflicts is not None,
            the project has been blocked.
            
        Raises:
            ProjectBlockedException: If trying to declare artifact on BLOCKED project.
        """
        try:
            # Check if already blocked
            is_blocked, _ = self.check_project_blocked(project_id)
            if is_blocked:
                raise ProjectBlockedException(
                    project_id,
                    "Cannot declare artifact on blocked project"
                )
            
            # Extract dependencies from result if not provided
            if dependencies is None:
                dependencies = self._extract_dependencies_from_result(result)
            
            # Declare artifact
            success, artifact, conflicts = self.psmp.declare_artifact(
                project_id=project_id,
                agent_id=agent_name,
                artifact_type=artifact_type,
                content_summary=result.output[:200] if result.output else "",
                dependencies=dependencies,
                metadata={
                    "execution_time": result.execution_time,
                    "error": result.error
                }
            )
            
            if not success and conflicts:
                logger.warning(
                    f"Conflicts detected after artifact from {agent_name}: {len(conflicts)} conflict(s)"
                )
                return False, conflicts
            
            logger.info(f"Artifact declared successfully for {agent_name}")
            return True, None
            
        except ProjectBlockedException as e:
            logger.error(f"Cannot declare artifact: {e}")
            raise
        except Exception as e:
            logger.error(f"Error declaring artifact: {e}")
            return False, None
    
    def handle_conflict_blocking(
        self,
        project_id: int,
        conflicts: List[DependencyConflict]
    ) -> str:
        """Generate user-friendly message for conflict blocking.
        
        Args:
            project_id: Project ID that is now blocked.
            conflicts: List of conflicts that caused blocking.
            
        Returns:
            Formatted message describing the block and next steps.
        """
        message = f"\n🚫 PROJECT BLOCKED: Dependency Conflicts Detected\n"
        message += f"Project ID: {project_id}\n"
        message += f"Total conflicts: {len(conflicts)}\n\n"
        
        for i, conflict in enumerate(conflicts, 1):
            message += f"Conflict #{i}: {conflict.library}\n"
            message += f"  Requirements:\n"
            for req in conflict.requirements:
                message += f"    - {req['agent']}: {req['library']} {req['needs']} ({req['purpose']})\n"
            message += f"  Suggested resolutions:\n"
            for j, resolution in enumerate(conflict.suggested_resolutions[:2], 1):
                message += f"    {j}. {resolution}\n"
            message += "\n"
        
        message += "Next steps:\n"
        message += "  1. Review the conflicts above\n"
        message += "  2. Run: flynt resolve-conflicts <project>\n"
        message += "  3. Select a resolution strategy\n"
        message += "  4. Run: flynt unblock-project <project>\n"
        
        return message
    
    def _extract_dependencies_from_result(
        self,
        result: AgentResult
    ) -> List[DependencySpec]:
        """Extract dependencies from agent result.
        
        This is a simple heuristic; can be enhanced with AST analysis or LLM parsing.
        
        Args:
            result: AgentResult to analyze.
            
        Returns:
            List of detected dependencies.
        """
        # TODO: Implement dependency extraction from code/metadata
        # For now, return empty list; dependencies should be explicitly provided
        return []
    
    def get_blocking_report(self, project_id: int) -> str:
        """Generate full blocking report for display to user.
        
        Args:
            project_id: Project ID.
            
        Returns:
            Formatted report.
        """
        try:
            conflicts = self.psmp.get_blocking_conflicts(project_id)
            if not conflicts:
                return "✅ Project is not blocked."
            
            return self.handle_conflict_blocking(project_id, conflicts)
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return f"Error retrieving block status: {e}"
    
    def trigger_conflict_resolver(self, project_id: int) -> str:
        """Trigger the conflict resolver agent.
        
        Args:
            project_id: Project ID that is blocked.
            
        Returns:
            Result message from resolver agent.
        """
        from core.state import get_state_manager
        from agents.conflict_resolver_agent import ConflictResolverAgent
        from agents.base import AgentContext
        from core.llm_client import create_llm_client_from_config
        from core.config import get_config_manager
        
        try:
            state_mgr = get_state_manager()
            conflicts = self.psmp.get_blocking_conflicts(project_id)
            
            if not conflicts:
                return "✅ No conflicts to resolve."
            
            # Create resolver agent
            config = get_config_manager().load()
            llm_client = create_llm_client_from_config(config)
            resolver = ConflictResolverAgent(llm_client, verbose=True)
            
            # Create context
            context = AgentContext(
                project_id=project_id,
                task_id=None,
                user_input=f"Resolve {len(conflicts)} dependency conflicts",
                previous_output="",
                metadata={
                    "conflicts": [c.to_dict() for c in conflicts],
                    "project_state": "BLOCKED"
                }
            )
            
            # Execute resolver
            result = resolver.execute(context)
            
            if result.success:
                logger.info(f"Conflict resolver completed for project {project_id}")
                return result.output
            else:
                return f"Conflict resolution failed: {result.error}"
                
        except Exception as e:
            logger.error(f"Error triggering conflict resolver: {e}")
            return f"Error running conflict resolver: {e}"


def get_psmp_bridge() -> PSMPOrchestrationBridge:
    """Get singleton instance of PSMP orchestration bridge.
    
    Returns:
        PSMPOrchestrationBridge instance.
    """
    if not hasattr(get_psmp_bridge, "_instance"):
        get_psmp_bridge._instance = PSMPOrchestrationBridge()
    return get_psmp_bridge._instance
