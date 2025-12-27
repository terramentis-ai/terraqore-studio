"""
Agent Collaboration State Management
Tracks agent iterations, feedback loops, and collaborative workflows.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class IterationType(str, Enum):
    """Types of agent iterations."""
    GENERATION = "generation"
    VALIDATION = "validation"
    REFINEMENT = "refinement"
    FEEDBACK = "feedback"


class FeedbackSeverity(str, Enum):
    """Severity levels for feedback."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AgentFeedback:
    """Feedback from one agent to another."""
    source_agent: str
    target_agent: str
    feedback_type: str
    message: str
    severity: FeedbackSeverity
    suggestions: List[str]
    timestamp: str
    iteration_number: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentIteration:
    """Single iteration of an agent execution."""
    project_id: int
    agent_name: str
    iteration_number: int
    iteration_type: IterationType
    input_context: Dict[str, Any]
    output_result: Dict[str, Any]
    quality_score: float  # 0-10
    validation_passed: bool
    feedback_received: List[AgentFeedback]
    timestamp: str
    execution_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "agent_name": self.agent_name,
            "iteration_number": self.iteration_number,
            "iteration_type": self.iteration_type.value,
            "input_context": self.input_context,
            "output_result": self.output_result,
            "quality_score": self.quality_score,
            "validation_passed": self.validation_passed,
            "feedback_received": [f.to_dict() for f in self.feedback_received],
            "timestamp": self.timestamp,
            "execution_time": self.execution_time
        }


@dataclass
class ProjectCollaborationState:
    """State tracking for multi-agent collaboration on a project."""
    project_id: int
    shared_context: Dict[str, Any]
    agent_iterations: Dict[str, List[AgentIteration]]  # agent_name -> iterations
    decision_log: List[Dict[str, Any]]
    feedback_history: List[AgentFeedback]
    current_stage: str
    stage_history: List[str]
    total_iterations: int
    last_updated: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "shared_context": self.shared_context,
            "agent_iterations": {
                agent: [it.to_dict() for it in iterations]
                for agent, iterations in self.agent_iterations.items()
            },
            "decision_log": self.decision_log,
            "feedback_history": [f.to_dict() for f in self.feedback_history],
            "current_stage": self.current_stage,
            "stage_history": self.stage_history,
            "total_iterations": self.total_iterations,
            "last_updated": self.last_updated
        }
    
    def add_iteration(self, iteration: AgentIteration) -> None:
        """Add an agent iteration to the state."""
        agent_name = iteration.agent_name
        if agent_name not in self.agent_iterations:
            self.agent_iterations[agent_name] = []
        
        self.agent_iterations[agent_name].append(iteration)
        self.total_iterations += 1
        self.last_updated = datetime.now().isoformat()
        
        logger.info(
            f"Added iteration for {agent_name} "
            f"(#{iteration.iteration_number}): "
            f"quality={iteration.quality_score:.1f}/10"
        )
    
    def add_feedback(self, feedback: AgentFeedback) -> None:
        """Add feedback between agents."""
        self.feedback_history.append(feedback)
        self.last_updated = datetime.now().isoformat()
        
        logger.info(
            f"Feedback from {feedback.source_agent} "
            f"to {feedback.target_agent}: "
            f"{feedback.severity.value} - {feedback.message}"
        )
    
    def record_decision(self, decision_type: str, details: Dict[str, Any]) -> None:
        """Record a project decision."""
        decision = {
            "type": decision_type,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.decision_log.append(decision)
        self.last_updated = datetime.now().isoformat()
        
        logger.info(f"Decision recorded: {decision_type}")
    
    def update_stage(self, new_stage: str) -> None:
        """Update the current project stage."""
        if new_stage != self.current_stage:
            self.stage_history.append(self.current_stage)
            self.current_stage = new_stage
            self.last_updated = datetime.now().isoformat()
            
            logger.info(f"Project stage updated: {self.current_stage}")
    
    def get_agent_quality_trend(self, agent_name: str) -> List[float]:
        """Get quality score trend for an agent."""
        if agent_name not in self.agent_iterations:
            return []
        
        iterations = self.agent_iterations[agent_name]
        return [it.quality_score for it in iterations]
    
    def get_improvement_rate(self, agent_name: str) -> float:
        """Calculate improvement rate for an agent across iterations."""
        trend = self.get_agent_quality_trend(agent_name)
        
        if len(trend) < 2:
            return 0.0
        
        # Calculate average improvement per iteration
        improvements = [trend[i] - trend[i-1] for i in range(1, len(trend))]
        return sum(improvements) / len(improvements)
    
    def should_iterate_again(self, agent_name: str, min_quality: float = 6.0) -> bool:
        """Determine if agent should iterate again."""
        iterations = self.agent_iterations.get(agent_name, [])
        
        if not iterations:
            return True
        
        last_iteration = iterations[-1]
        
        # Iterate again if quality is below threshold
        if last_iteration.quality_score < min_quality:
            return True
        
        # Iterate again if validation failed
        if not last_iteration.validation_passed:
            return True
        
        return False


class CollaborationStateManager:
    """Manages collaboration state for projects."""
    
    def __init__(self):
        """Initialize collaboration state manager."""
        self.project_states: Dict[int, ProjectCollaborationState] = {}
        logger.info("CollaborationStateManager initialized")
    
    def create_project_state(self, project_id: int) -> ProjectCollaborationState:
        """Create initial collaboration state for a project."""
        state = ProjectCollaborationState(
            project_id=project_id,
            shared_context={},
            agent_iterations={},
            decision_log=[],
            feedback_history=[],
            current_stage="initialization",
            stage_history=[],
            total_iterations=0,
            last_updated=datetime.now().isoformat()
        )
        
        self.project_states[project_id] = state
        logger.info(f"Created collaboration state for project {project_id}")
        
        return state
    
    def get_project_state(self, project_id: int) -> Optional[ProjectCollaborationState]:
        """Get collaboration state for a project."""
        return self.project_states.get(project_id)
    
    def add_iteration(
        self,
        project_id: int,
        iteration: AgentIteration
    ) -> None:
        """Add iteration to project state."""
        state = self.get_project_state(project_id)
        if not state:
            state = self.create_project_state(project_id)
        
        state.add_iteration(iteration)
    
    def add_feedback(
        self,
        project_id: int,
        feedback: AgentFeedback
    ) -> None:
        """Add feedback to project state."""
        state = self.get_project_state(project_id)
        if state:
            state.add_feedback(feedback)
    
    def record_decision(
        self,
        project_id: int,
        decision_type: str,
        details: Dict[str, Any]
    ) -> None:
        """Record decision in project state."""
        state = self.get_project_state(project_id)
        if state:
            state.record_decision(decision_type, details)
    
    def update_stage(self, project_id: int, new_stage: str) -> None:
        """Update project stage."""
        state = self.get_project_state(project_id)
        if state:
            state.update_stage(new_stage)
    
    def get_project_summary(self, project_id: int) -> Dict[str, Any]:
        """Get summary of project collaboration state."""
        state = self.get_project_state(project_id)
        if not state:
            return {}
        
        return {
            "project_id": project_id,
            "current_stage": state.current_stage,
            "total_iterations": state.total_iterations,
            "agents_involved": list(state.agent_iterations.keys()),
            "feedback_count": len(state.feedback_history),
            "decisions_made": len(state.decision_log),
            "last_updated": state.last_updated,
            "quality_trends": {
                agent: state.get_agent_quality_trend(agent)
                for agent in state.agent_iterations.keys()
            },
            "improvement_rates": {
                agent: state.get_improvement_rate(agent)
                for agent in state.agent_iterations.keys()
            }
        }

# Singleton instance
_collaboration_state_manager: Optional[CollaborationStateManager] = None


def get_collaboration_state_manager() -> CollaborationStateManager:
    """Get or create the global collaboration state manager."""
    global _collaboration_state_manager
    if _collaboration_state_manager is None:
        _collaboration_state_manager = CollaborationStateManager()
    return _collaboration_state_manager
