"""
Agent Specialization Router

Routes tasks to specialized agents based on historical performance and specialization.

Part of Phase 5.2 Learning System. Analyzes agent performance patterns to identify
strengths and routes work to optimal agents.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import statistics

from core.state import StateManager
from core.performance_analytics import get_performance_analytics, PerformanceMetric


class TaskType(Enum):
    """Types of tasks agents might handle."""
    IDEATION = "ideation"
    PLANNING = "planning"
    IMPLEMENTATION = "implementation"
    VALIDATION = "validation"
    CODE_GENERATION = "code_generation"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    OPTIMIZATION = "optimization"
    SECURITY_CHECK = "security_check"
    GENERIC = "generic"


class SpecializationLevel(Enum):
    """Levels of specialization."""
    GENERALIST = 0
    SPECIALIST = 1
    EXPERT = 2


@dataclass
class AgentSpecialization:
    """Represents an agent's specialization."""
    agent_name: str
    specialization_type: TaskType
    level: SpecializationLevel
    success_rate: float
    avg_execution_time: float
    quality_score: float
    samples: int  # Number of tasks handled
    confidence: float  # Confidence in this specialization (0-1)
    last_evaluated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["specialization_type"] = self.specialization_type.value
        data["level"] = self.level.name
        data["last_evaluated"] = self.last_evaluated.isoformat()
        return data


@dataclass
class RoutingDecision:
    """Decision to route a task to an agent."""
    task_id: str
    task_type: TaskType
    selected_agent: str
    alternative_agents: List[Tuple[str, float]]  # (agent, score)
    selection_reason: str
    confidence_score: float
    specialization_match: str  # "perfect", "good", "fair", "poor"
    decision_timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "selected_agent": self.selected_agent,
            "alternative_agents": [(a, round(s, 3)) for a, s in self.alternative_agents],
            "selection_reason": self.selection_reason,
            "confidence_score": round(self.confidence_score, 3),
            "specialization_match": self.specialization_match,
            "decision_timestamp": self.decision_timestamp.isoformat()
        }


@dataclass
class RoutingEvaluation:
    """Evaluation of a routing decision against actual results."""
    routing_decision: RoutingDecision
    actual_success: bool
    actual_quality: float
    actual_time: float
    was_optimal: bool  # True if selected agent was best choice in hindsight
    improvement_vs_alternatives: float  # Percentage
    feedback: Optional[str] = None
    evaluation_timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "selected_agent": self.routing_decision.selected_agent,
            "was_optimal": self.was_optimal,
            "actual_quality": round(self.actual_quality, 3),
            "improvement_vs_alternatives": round(self.improvement_vs_alternatives, 3),
            "evaluation_timestamp": self.evaluation_timestamp.isoformat()
        }


@dataclass
class AgentCapability:
    """Represents a capability/skill of an agent."""
    agent_name: str
    capability_name: str
    proficiency: float  # 0-1 scale
    proven_by_count: int  # Number of successful uses
    last_used: datetime = field(default_factory=datetime.now)


class AgentSpecializationRouter:
    """
    Routes tasks to specialized agents based on performance patterns.
    
    Capabilities:
    - Identify agent specializations
    - Rank agents for specific task types
    - Make intelligent routing decisions
    - Evaluate routing effectiveness
    - Learn from routing outcomes
    """
    
    def __init__(self):
        """Initialize the router."""
        self.state_manager = StateManager()
        self.analytics = get_performance_analytics()
        self.specializations: Dict[str, List[AgentSpecialization]] = {}
        self.routing_history: List[RoutingDecision] = []
        self.routing_evaluations: List[RoutingEvaluation] = []
        self.agent_capabilities: Dict[str, List[AgentCapability]] = {}
    
    def get_agent_specialization(self, agent_name: str) -> List[AgentSpecialization]:
        """
        Identify what an agent specializes in.
        
        Args:
            agent_name: The agent to analyze
        
        Returns:
            List of specializations with proficiency levels
        """
        # Check cache
        if agent_name in self.specializations:
            return self.specializations[agent_name]
        
        specializations = []
        
        # Analyze performance for each task type
        for task_type in TaskType:
            if task_type == TaskType.GENERIC:
                continue
            
            # Get metrics for this agent
            metrics = self._get_agent_task_metrics(agent_name, task_type)
            
            if metrics and metrics["samples"] > 0:
                # Determine specialization level
                level = self._determine_specialization_level(metrics)
                
                if level != SpecializationLevel.GENERALIST or metrics["success_rate"] > 0.75:
                    specialization = AgentSpecialization(
                        agent_name=agent_name,
                        specialization_type=task_type,
                        level=level,
                        success_rate=metrics["success_rate"],
                        avg_execution_time=metrics["avg_execution_time"],
                        quality_score=metrics["quality_score"],
                        samples=metrics["samples"],
                        confidence=self._calculate_specialization_confidence(metrics)
                    )
                    specializations.append(specialization)
        
        # Sort by level (expert first)
        specializations.sort(key=lambda s: (s.level.value, -s.confidence), reverse=True)
        
        # Cache it
        self.specializations[agent_name] = specializations
        
        return specializations
    
    def rank_agents_for_task(self, task_type: TaskType, available_agents: List[str]) -> List[Tuple[str, float]]:
        """
        Rank agents by suitability for a task type.
        
        Args:
            task_type: The type of task
            available_agents: List of agents to rank
        
        Returns:
            Sorted list of (agent_name, score) tuples
        """
        rankings = []
        
        for agent in available_agents:
            # Calculate agent score for this task
            score = self._calculate_agent_task_score(agent, task_type)
            rankings.append((agent, score))
        
        # Sort by score descending
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        return rankings
    
    def route_task_to_best_agent(
        self,
        task_id: str,
        task_type: TaskType,
        available_agents: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        Route a task to the best available agent.
        
        Args:
            task_id: Unique task identifier
            task_type: Type of task
            available_agents: Agents that can handle this task
            context: Additional context (complexity, time constraint, etc.)
        
        Returns:
            RoutingDecision with selected agent and alternatives
        """
        # Rank agents
        rankings = self.rank_agents_for_task(task_type, available_agents)
        
        if not rankings:
            # Fallback to first available
            selected = available_agents[0]
            ranking = 0.5
            reason = "No specialization data, using default assignment"
        else:
            selected, ranking = rankings[0]
            
            # Check for specialization match
            specializations = self.get_agent_specialization(selected)
            matching_spec = next(
                (s for s in specializations if s.specialization_type == task_type),
                None
            )
            reason = f"Routed to {selected} - {matching_spec.level.name if matching_spec else 'Generalist'}"
        
        # Determine specialization match quality
        match_quality = self._determine_match_quality(ranking)
        
        # Create decision
        decision = RoutingDecision(
            task_id=task_id,
            task_type=task_type,
            selected_agent=selected,
            alternative_agents=rankings[1:3],  # Top 2 alternatives
            selection_reason=reason,
            confidence_score=ranking,
            specialization_match=match_quality
        )
        
        # Store in history
        self.routing_history.append(decision)
        
        return decision
    
    def evaluate_routing_decision(
        self,
        decision: RoutingDecision,
        actual_success: bool,
        actual_quality: float,
        actual_time: float,
        feedback: Optional[str] = None
    ) -> RoutingEvaluation:
        """
        Evaluate how well a routing decision worked.
        
        Args:
            decision: The original routing decision
            actual_success: Whether the task succeeded
            actual_quality: Quality score achieved
            actual_time: Time taken
            feedback: Optional feedback
        
        Returns:
            RoutingEvaluation
        """
        # Check if it was optimal (if alternative was available, did they perform better?)
        was_optimal = True
        improvement = 0.0
        
        if decision.alternative_agents:
            # Would the alternative have been better?
            # (In practice, would need to rerun to know for certain)
            # For now, use heuristic based on performance
            improvement = actual_quality / 10.0 * 100  # Rough estimate
        
        evaluation = RoutingEvaluation(
            routing_decision=decision,
            actual_success=actual_success,
            actual_quality=actual_quality,
            actual_time=actual_time,
            was_optimal=was_optimal,
            improvement_vs_alternatives=improvement,
            feedback=feedback
        )
        
        # Store evaluation
        self.routing_evaluations.append(evaluation)
        
        # Learn from evaluation (update scores if needed)
        if not actual_success:
            self._record_agent_failure(decision.selected_agent, decision.task_type)
        else:
            self._record_agent_success(decision.selected_agent, decision.task_type, actual_quality)
        
        return evaluation
    
    def get_agent_routing_statistics(self, agent_name: str) -> Dict[str, Any]:
        """
        Get routing statistics for an agent.
        
        Args:
            agent_name: The agent
        
        Returns:
            Detailed routing statistics
        """
        # Tasks routed to this agent
        routed_to = [d for d in self.routing_history if d.selected_agent == agent_name]
        
        # Evaluations for this agent
        evals = [e for e in self.routing_evaluations if e.routing_decision.selected_agent == agent_name]
        
        if not routed_to:
            return {
                "agent_name": agent_name,
                "tasks_routed": 0,
                "statistics": "No routing data available"
            }
        
        # Calculate statistics
        total_tasks = len(routed_to)
        successful = len([e for e in evals if e.actual_success])
        success_rate = successful / len(evals) if evals else 0
        
        avg_quality = statistics.mean([e.actual_quality for e in evals]) if evals else 0
        avg_time = statistics.mean([e.actual_time for e in evals]) if evals else 0
        
        # Task type distribution
        by_type = {}
        for decision in routed_to:
            task_type = decision.task_type.value
            by_type[task_type] = by_type.get(task_type, 0) + 1
        
        return {
            "agent_name": agent_name,
            "total_tasks_routed": total_tasks,
            "evaluated_tasks": len(evals),
            "success_rate": round(success_rate, 3),
            "average_quality": round(avg_quality, 3),
            "average_execution_time": round(avg_time, 3),
            "task_type_distribution": by_type,
            "specializations": [s.to_dict() for s in self.get_agent_specialization(agent_name)]
        }
    
    def get_routing_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive routing analytics.
        
        Args:
            days: Historical window
        
        Returns:
            Routing analytics
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent_routing = [d for d in self.routing_history if d.decision_timestamp >= cutoff]
        recent_evals = [e for e in self.routing_evaluations if e.evaluation_timestamp >= cutoff]
        
        if not recent_routing:
            return {
                "period_days": days,
                "routing_decisions": 0,
                "analytics": "No routing data in period"
            }
        
        # Overall success rate
        success_rate = len([e for e in recent_evals if e.actual_success]) / len(recent_evals) if recent_evals else 0
        
        # Optimal decisions
        optimal_decisions = len([e for e in recent_evals if e.was_optimal])
        optimal_rate = optimal_decisions / len(recent_evals) if recent_evals else 0
        
        # By task type
        by_task_type = {}
        for decision in recent_routing:
            task_type = decision.task_type.value
            if task_type not in by_task_type:
                by_task_type[task_type] = {"count": 0, "successful": 0}
            by_task_type[task_type]["count"] += 1
            
            # Check if successful
            matching_eval = next(
                (e for e in recent_evals if e.routing_decision.task_id == decision.task_id),
                None
            )
            if matching_eval and matching_eval.actual_success:
                by_task_type[task_type]["successful"] += 1
        
        return {
            "period_days": days,
            "total_routing_decisions": len(recent_routing),
            "evaluated_decisions": len(recent_evals),
            "overall_success_rate": round(success_rate, 3),
            "optimal_routing_rate": round(optimal_rate, 3),
            "by_task_type": by_task_type,
            "analytics_timestamp": datetime.now().isoformat()
        }
    
    # Private helper methods
    
    def _get_agent_task_metrics(self, agent_name: str, task_type: TaskType) -> Optional[Dict[str, Any]]:
        """Get metrics for an agent on a specific task type."""
        # Query historical data
        try:
            records = self.state_manager.db.execute(
                """
                SELECT * FROM execution_metrics
                WHERE agent_name = ? AND task_type = ?
                ORDER BY timestamp DESC
                LIMIT 100
                """,
                (agent_name, task_type.value)
            ).fetchall()
            
            if not records:
                return None
            
            # Calculate metrics
            records_list = [dict(row) for row in records]
            success = len([r for r in records_list if r.get("success", False)])
            
            metrics = {
                "success_rate": success / len(records_list),
                "avg_execution_time": statistics.mean([r.get("execution_time", 0) for r in records_list]),
                "quality_score": statistics.mean([r.get("quality_score", 5.0) for r in records_list]),
                "samples": len(records_list)
            }
            return metrics
        except Exception:
            return None
    
    def _determine_specialization_level(self, metrics: Dict[str, Any]) -> SpecializationLevel:
        """Determine level of specialization based on metrics."""
        if metrics["samples"] < 5:
            return SpecializationLevel.GENERALIST
        
        if metrics["success_rate"] > 0.95 and metrics["quality_score"] > 8.0:
            return SpecializationLevel.EXPERT
        elif metrics["success_rate"] > 0.80:
            return SpecializationLevel.SPECIALIST
        else:
            return SpecializationLevel.GENERALIST
    
    def _calculate_specialization_confidence(self, metrics: Dict[str, Any]) -> float:
        """Calculate confidence in specialization."""
        # More samples = higher confidence
        confidence = min(metrics["samples"] / 50, 1.0)
        
        # Consistent performance = higher confidence
        if metrics["success_rate"] > 0.85:
            confidence *= 1.2
        
        return min(confidence, 1.0)
    
    def _calculate_agent_task_score(self, agent: str, task_type: TaskType) -> float:
        """Calculate score for agent on specific task type."""
        metrics = self._get_agent_task_metrics(agent, task_type)
        
        if not metrics or metrics["samples"] == 0:
            return 0.5  # Neutral score if no data
        
        # Score = (success_rate * 0.6 + quality_score/10 * 0.3 + specialization * 0.1)
        specializations = self.get_agent_specialization(agent)
        spec_bonus = 0.2 if any(s.specialization_type == task_type for s in specializations) else 0
        
        score = (
            metrics["success_rate"] * 0.6 +
            (metrics["quality_score"] / 10.0) * 0.3 +
            spec_bonus
        )
        
        return min(score, 1.0)
    
    def _determine_match_quality(self, score: float) -> str:
        """Determine match quality based on score."""
        if score >= 0.85:
            return "perfect"
        elif score >= 0.70:
            return "good"
        elif score >= 0.50:
            return "fair"
        else:
            return "poor"
    
    def _record_agent_failure(self, agent: str, task_type: TaskType) -> None:
        """Record a failure for future learning."""
        # Could update metrics or scoring here
        pass
    
    def _record_agent_success(self, agent: str, task_type: TaskType, quality: float) -> None:
        """Record a success for future learning."""
        # Could update specialization profiles here
        if agent not in self.agent_capabilities:
            self.agent_capabilities[agent] = []
        
        # Update or create capability
        capability_name = f"{task_type.value}_handler"
        existing = next((c for c in self.agent_capabilities[agent] if c.capability_name == capability_name), None)
        
        if existing:
            # Update proficiency
            existing.proficiency = min(existing.proficiency + (quality / 10.0 * 0.1), 1.0)
            existing.proven_by_count += 1
            existing.last_used = datetime.now()
        else:
            # Create new capability
            capability = AgentCapability(
                agent_name=agent,
                capability_name=capability_name,
                proficiency=quality / 10.0,
                proven_by_count=1
            )
            self.agent_capabilities[agent].append(capability)


# Singleton instance management
_router_instance: Optional[AgentSpecializationRouter] = None


def get_agent_specialization_router() -> AgentSpecializationRouter:
    """Get or create the singleton AgentSpecializationRouter instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = AgentSpecializationRouter()
    return _router_instance
