"""
Prompt Optimizer

Analyzes feedback patterns and generates improved agent prompts through
iterative A/B testing and performance-based selection.

Phase 5.2 Component - Used by all agents for continuous prompt improvement.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
import logging
import time

from core.state import StateManager
from core.feedback_pattern_analyzer import get_feedback_pattern_analyzer
from core.llm_client import create_llm_client_from_config
from core.config import get_config_manager

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """Strategies for prompt optimization."""
    ADD_EXAMPLES = "add_examples"
    CLARIFY_REQUIREMENTS = "clarify_requirements"
    ADD_CONSTRAINTS = "add_constraints"
    RESTRUCTURE_PROMPT = "restructure_prompt"
    ENHANCE_CONTEXT = "enhance_context"
    ADD_REASONING_STEPS = "add_reasoning_steps"
    ADD_VALIDATION_RULES = "add_validation_rules"


@dataclass
class PromptVersion:
    """Represents a version of an agent's prompt."""
    version_id: str
    agent_name: str
    prompt_text: str
    created_at: datetime
    optimization_applied: Optional[str] = None
    reason: Optional[str] = None
    expected_improvement: Optional[str] = None
    test_results: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data


@dataclass
class PromptSuggestion:
    """A suggested improvement to a prompt."""
    suggestion_id: str
    agent_name: str
    strategy: OptimizationStrategy
    description: str
    current_issue: str
    proposed_change: str
    confidence_score: float  # 0-1
    estimated_impact: str  # "high", "medium", "low"
    reasoning: str
    affected_feedback_patterns: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, approved, applied, rejected
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["strategy"] = self.strategy.value
        data["created_at"] = self.created_at.isoformat()
        return data


@dataclass
class OptimizationResult:
    """Result of applying an optimization."""
    optimization_id: str
    agent_name: str
    old_version_id: str
    new_version_id: str
    strategy: OptimizationStrategy
    description: str
    applied_at: datetime
    expected_improvement: float  # 0-1 scale
    actual_improvement: Optional[float] = None
    rollback_triggered: bool = False
    rollback_reason: Optional[str] = None


class PromptOptimizer:
    """
    Optimizes agent prompts based on failure analysis and feedback patterns.
    
    Capabilities:
    - Analyze failures and their root causes
    - Generate optimization suggestions
    - Apply prompt enhancements
    - Track prompt versions
    - Rollback failed optimizations
    """
    
    def __init__(self):
        """Initialize the prompt optimizer."""
        self.state_manager = StateManager()
        self.analyzer = get_feedback_pattern_analyzer()
        self.prompt_versions: Dict[str, List[PromptVersion]] = {}
        self.suggestions: Dict[str, List[PromptSuggestion]] = {}
        self.optimizations_history: List[OptimizationResult] = []
    
    def analyze_failures(self, agent_name: str, build_id: str, lookback_days: int = 7) -> Dict[str, Any]:
        """
        Analyze failures for an agent in recent builds.
        
        Args:
            agent_name: The agent to analyze
            build_id: Recent build to analyze
            lookback_days: How far back to look
        
        Returns:
            Dictionary containing failure analysis
        """
        # Fetch error logs from build database
        errors = self._fetch_agent_errors(agent_name, build_id, lookback_days)
        
        if not errors:
            return {
                "agent_name": agent_name,
                "total_errors": 0,
                "error_types": {},
                "root_causes": [],
                "recommendations": []
            }
        
        # Categorize errors
        error_categories = self._categorize_errors(errors)
        
        # Identify root causes
        root_causes = self._identify_root_causes(errors, error_categories)
        
        # Generate recommendations
        recommendations = self._generate_failure_recommendations(root_causes)
        
        return {
            "agent_name": agent_name,
            "total_errors": len(errors),
            "error_types": error_categories,
            "root_causes": root_causes,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def suggest_prompt_improvements(self, agent_name: str, analysis: Dict[str, Any]) -> List[PromptSuggestion]:
        """
        Generate suggestions to improve an agent's prompt.
        
        Args:
            agent_name: The agent to improve
            analysis: Failure analysis from analyze_failures
        
        Returns:
            List of prompt improvement suggestions
        """
        suggestions = []
        
        root_causes = analysis.get("root_causes", [])
        
        for cause in root_causes:
            # Determine optimization strategy based on root cause
            strategy = self._determine_strategy(cause["type"])
            
            # Generate detailed suggestion
            suggestion = self._create_suggestion(
                agent_name,
                strategy,
                cause,
                analysis
            )
            suggestions.append(suggestion)
        
        # Sort by confidence and impact
        suggestions.sort(
            key=lambda s: (s.confidence_score, -self._impact_score(s.estimated_impact)),
            reverse=True
        )
        
        # Store suggestions
        if agent_name not in self.suggestions:
            self.suggestions[agent_name] = []
        self.suggestions[agent_name].extend(suggestions)
        
        return suggestions
    
    def apply_prompt_enhancement(
        self, 
        agent_name: str, 
        suggestion: PromptSuggestion,
        current_prompt: str
    ) -> Tuple[str, PromptVersion]:
        """
        Apply a prompt enhancement to an agent.
        
        Args:
            agent_name: The agent to enhance
            suggestion: The suggestion to apply
            current_prompt: The current prompt text
        
        Returns:
            Tuple of (enhanced_prompt, new_version)
        """
        # Generate enhanced prompt
        enhanced_prompt = self._apply_optimization_strategy(
            current_prompt,
            suggestion.strategy,
            suggestion
        )
        
        # Create new version record
        version = PromptVersion(
            version_id=f"{agent_name}_v{len(self._get_agent_versions(agent_name)) + 1}",
            agent_name=agent_name,
            prompt_text=enhanced_prompt,
            created_at=datetime.now(),
            optimization_applied=suggestion.strategy.value,
            reason=suggestion.description,
            expected_improvement=suggestion.estimated_impact
        )
        
        # Store version
        if agent_name not in self.prompt_versions:
            self.prompt_versions[agent_name] = []
        self.prompt_versions[agent_name].append(version)
        
        # Mark suggestion as applied
        suggestion.status = "applied"
        
        return enhanced_prompt, version
    
    def track_prompt_versions(self, agent_name: str) -> List[PromptVersion]:
        """
        Get the version history for an agent's prompt.
        
        Args:
            agent_name: The agent to get versions for
        
        Returns:
            List of prompt versions in chronological order
        """
        versions = self._get_agent_versions(agent_name)
        return sorted(versions, key=lambda v: v.created_at)
    
    def compare_prompt_versions(
        self, 
        agent_name: str, 
        version1_id: str, 
        version2_id: str
    ) -> Dict[str, Any]:
        """
        Compare two prompt versions.
        
        Args:
            agent_name: The agent
            version1_id: First version ID
            version2_id: Second version ID
        
        Returns:
            Comparison results with diff highlights
        """
        v1 = self._get_version(agent_name, version1_id)
        v2 = self._get_version(agent_name, version2_id)
        
        if not v1 or not v2:
            return {"error": "One or both versions not found"}
        
        return {
            "version1": {
                "id": v1.version_id,
                "created": v1.created_at.isoformat(),
                "optimization": v1.optimization_applied
            },
            "version2": {
                "id": v2.version_id,
                "created": v2.created_at.isoformat(),
                "optimization": v2.optimization_applied
            },
            "differences": self._compute_prompt_differences(v1.prompt_text, v2.prompt_text),
            "expected_improvement": v2.expected_improvement,
            "actual_results": v2.test_results
        }
    
    def evaluate_optimization(
        self,
        optimization_id: str,
        test_results: Dict[str, Any],
        should_rollback: bool = False
    ) -> OptimizationResult:
        """
        Evaluate results of an optimization and optionally rollback.
        
        Args:
            optimization_id: The optimization to evaluate
            test_results: Results from testing the new prompt
            should_rollback: Whether to trigger rollback
        
        Returns:
            OptimizationResult with evaluation
        """
        # Find the optimization
        optimization = next(
            (o for o in self.optimizations_history if o.optimization_id == optimization_id),
            None
        )
        
        if not optimization:
            return OptimizationResult(
                optimization_id=optimization_id,
                agent_name="unknown",
                old_version_id="",
                new_version_id="",
                strategy=OptimizationStrategy.ADD_EXAMPLES,
                description="Optimization not found",
                applied_at=datetime.now(),
                expected_improvement=0.0
            )
        
        # Calculate actual improvement
        actual_improvement = self._calculate_improvement(test_results)
        optimization.actual_improvement = actual_improvement
        
        # Check if rollback needed
        if should_rollback or actual_improvement < 0.5 * optimization.expected_improvement:
            optimization.rollback_triggered = True
            optimization.rollback_reason = "Actual improvement below threshold"
            self._rollback_version(optimization.agent_name, optimization.old_version_id)
        
        return optimization
    
    def get_optimization_history(self, agent_name: str) -> List[OptimizationResult]:
        """
        Get optimization history for an agent.
        
        Args:
            agent_name: The agent to get history for
        
        Returns:
            List of optimization results
        """
        return [o for o in self.optimizations_history if o.agent_name == agent_name]
    
    def recommend_next_optimization(self, agent_name: str) -> Optional[PromptSuggestion]:
        """
        Recommend the next optimization to apply.
        
        Args:
            agent_name: The agent to get recommendation for
        
        Returns:
            Top suggestion or None if no suggestions available
        """
        agent_suggestions = self.suggestions.get(agent_name, [])
        pending = [s for s in agent_suggestions if s.status == "pending"]
        
        if pending:
            return pending[0]
        return None
    
    def generate_prompt_report(self, agent_name: str) -> Dict[str, Any]:
        """
        Generate a comprehensive report on prompt optimization progress.
        
        Args:
            agent_name: The agent to report on
        
        Returns:
            Detailed optimization report
        """
        versions = self._get_agent_versions(agent_name)
        history = self.get_optimization_history(agent_name)
        suggestions = self.suggestions.get(agent_name, [])
        
        # Calculate metrics
        total_optimizations = len(history)
        successful = len([o for o in history if not o.rollback_triggered])
        rollbacks = total_optimizations - successful
        
        # Average improvement
        improvements = [o.actual_improvement for o in history if o.actual_improvement is not None]
        avg_improvement = sum(improvements) / len(improvements) if improvements else 0.0
        
        return {
            "agent_name": agent_name,
            "total_prompt_versions": len(versions),
            "optimizations_applied": total_optimizations,
            "successful_optimizations": successful,
            "rollbacks": rollbacks,
            "success_rate": round(successful / total_optimizations, 2) if total_optimizations > 0 else 0.0,
            "average_improvement": round(avg_improvement, 2),
            "current_version": versions[-1].version_id if versions else "none",
            "pending_suggestions": len([s for s in suggestions if s.status == "pending"]),
            "version_history": [v.to_dict() for v in versions[-5:]],  # Last 5
            "recent_optimizations": [o for o in history[-3:]]  # Last 3
        }
    
    # Private helper methods
    
    def _fetch_agent_errors(self, agent_name: str, build_id: str, lookback_days: int) -> List[Dict[str, Any]]:
        """Fetch error logs for an agent from build database."""
        try:
            # Query terraqore_build.db error_log table
            errors = self.state_manager.db.execute(
                """
                SELECT * FROM error_log
                WHERE agent_name = ? AND build_id = ?
                ORDER BY timestamp DESC
                """,
                (agent_name, build_id)
            ).fetchall()
            
            return [dict(row) for row in errors] if errors else []
        except Exception:
            return []
    
    def _categorize_errors(self, errors: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize errors by type."""
        categories = {}
        for error in errors:
            error_type = error.get("error_type", "unknown")
            categories[error_type] = categories.get(error_type, 0) + 1
        return categories
    
    def _identify_root_causes(
        self, 
        errors: List[Dict[str, Any]], 
        categories: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """Identify root causes of errors."""
        causes = []
        
        for error_type, count in categories.items():
            cause = {
                "type": error_type,
                "frequency": count,
                "percentage": round(count / len(errors) * 100, 1),
                "likely_cause": self._map_error_to_cause(error_type),
                "example_message": next(
                    (e.get("error_message", "") for e in errors if e.get("error_type") == error_type),
                    ""
                )
            }
            causes.append(cause)
        
        return sorted(causes, key=lambda c: c["frequency"], reverse=True)
    
    def _generate_failure_recommendations(self, root_causes: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on root causes."""
        recommendations = []
        
        for cause in root_causes:
            rec = f"Address {cause['type']} ({cause['frequency']} occurrences): {cause['likely_cause']}"
            recommendations.append(rec)
        
        return recommendations
    
    def _determine_strategy(self, error_type: str) -> OptimizationStrategy:
        """Determine optimization strategy based on error type."""
        strategy_map = {
            "quality_gate_failure": OptimizationStrategy.CLARIFY_REQUIREMENTS,
            "output_validation_error": OptimizationStrategy.ADD_EXAMPLES,
            "format_error": OptimizationStrategy.ADD_VALIDATION_RULES,
            "logic_error": OptimizationStrategy.ADD_REASONING_STEPS,
            "incomplete_output": OptimizationStrategy.ADD_CONSTRAINTS,
            "security_violation": OptimizationStrategy.ADD_CONSTRAINTS,
            "inconsistency": OptimizationStrategy.ENHANCE_CONTEXT
        }
        return strategy_map.get(error_type, OptimizationStrategy.CLARIFY_REQUIREMENTS)
    
    def _create_suggestion(
        self,
        agent_name: str,
        strategy: OptimizationStrategy,
        cause: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> PromptSuggestion:
        """Create a detailed suggestion."""
        suggestion_map = {
            OptimizationStrategy.CLARIFY_REQUIREMENTS: {
                "desc": f"Clarify requirements for {cause['type']}",
                "change": "Add specific requirement clarifications to system prompt",
                "confidence": 0.85
            },
            OptimizationStrategy.ADD_EXAMPLES: {
                "desc": f"Add examples addressing {cause['type']}",
                "change": "Include concrete input/output examples in prompt",
                "confidence": 0.90
            },
            OptimizationStrategy.ADD_CONSTRAINTS: {
                "desc": f"Add constraints to prevent {cause['type']}",
                "change": "Add output constraints and guardrails",
                "confidence": 0.80
            },
            OptimizationStrategy.RESTRUCTURE_PROMPT: {
                "desc": f"Restructure prompt to address {cause['type']}",
                "change": "Reorganize prompt sections for clarity",
                "confidence": 0.70
            },
            OptimizationStrategy.ENHANCE_CONTEXT: {
                "desc": f"Add context to prevent {cause['type']}",
                "change": "Include additional context information",
                "confidence": 0.75
            },
            OptimizationStrategy.ADD_REASONING_STEPS: {
                "desc": f"Add reasoning steps for {cause['type']}",
                "change": "Include step-by-step reasoning instructions",
                "confidence": 0.85
            },
            OptimizationStrategy.ADD_VALIDATION_RULES: {
                "desc": f"Add validation for {cause['type']}",
                "change": "Include validation rules in prompt",
                "confidence": 0.80
            }
        }
        
        info = suggestion_map.get(strategy, {
            "desc": "Optimize prompt",
            "change": "Review and enhance prompt",
            "confidence": 0.70
        })
        
        return PromptSuggestion(
            suggestion_id=f"{agent_name}_sug_{datetime.now().timestamp()}",
            agent_name=agent_name,
            strategy=strategy,
            description=info["desc"],
            current_issue=cause["likely_cause"],
            proposed_change=info["change"],
            confidence_score=info["confidence"],
            estimated_impact="high" if cause["frequency"] > 3 else "medium",
            reasoning=f"Based on {cause['frequency']} occurrences of {cause['type']}",
            affected_feedback_patterns=[cause["type"]]
        )
    
    def _apply_optimization_strategy(
        self,
        current_prompt: str,
        strategy: OptimizationStrategy,
        suggestion: PromptSuggestion
    ) -> str:
        """Apply optimization strategy to prompt."""
        strategies = {
            OptimizationStrategy.ADD_EXAMPLES: self._add_examples_to_prompt,
            OptimizationStrategy.CLARIFY_REQUIREMENTS: self._clarify_requirements_in_prompt,
            OptimizationStrategy.ADD_CONSTRAINTS: self._add_constraints_to_prompt,
            OptimizationStrategy.ENHANCE_CONTEXT: self._enhance_context_in_prompt,
            OptimizationStrategy.ADD_REASONING_STEPS: self._add_reasoning_to_prompt,
            OptimizationStrategy.ADD_VALIDATION_RULES: self._add_validation_to_prompt,
            OptimizationStrategy.RESTRUCTURE_PROMPT: self._restructure_prompt
        }
        
        handler = strategies.get(strategy, lambda p, s: p)
        return handler(current_prompt, suggestion)
    
    def _add_examples_to_prompt(self, prompt: str, suggestion: PromptSuggestion) -> str:
        """Add examples section to prompt."""
        examples_section = "\n\n## Examples\n- Example 1: [Demonstrating correct behavior for the task]\n- Example 2: [Another example showing edge case handling]"
        return prompt + examples_section if "Examples" not in prompt else prompt
    
    def _clarify_requirements_in_prompt(self, prompt: str, suggestion: PromptSuggestion) -> str:
        """Clarify requirements in prompt."""
        clarity_addition = "\n\n## Critical Requirements\n- Requirement 1: Be specific about expected outputs\n- Requirement 2: Validate all outputs against criteria\n- Requirement 3: Handle edge cases explicitly"
        return prompt + clarity_addition if "Critical Requirements" not in prompt else prompt
    
    def _add_constraints_to_prompt(self, prompt: str, suggestion: PromptSuggestion) -> str:
        """Add constraints to prompt."""
        constraints = "\n\n## Constraints\n- Must not violate security guidelines\n- Must complete all required steps\n- Must follow specified format exactly"
        return prompt + constraints if "Constraints" not in prompt else prompt
    
    def _enhance_context_in_prompt(self, prompt: str, suggestion: PromptSuggestion) -> str:
        """Add additional context to prompt."""
        context = "\n\n## Context Information\nConsider the broader purpose and implications of your work. Ensure consistency across all outputs."
        return prompt + context if "Context Information" not in prompt else prompt
    
    def _add_reasoning_to_prompt(self, prompt: str, suggestion: PromptSuggestion) -> str:
        """Add step-by-step reasoning to prompt."""
        reasoning = "\n\n## Reasoning Steps\n1. Analyze the input thoroughly\n2. Consider multiple approaches\n3. Select the best approach\n4. Verify your solution\n5. Output the final result"
        return prompt + reasoning if "Reasoning Steps" not in prompt else prompt
    
    def _add_validation_to_prompt(self, prompt: str, suggestion: PromptSuggestion) -> str:
        """Add validation rules to prompt."""
        validation = "\n\n## Validation Rules\nBefore outputting, verify: [Format is correct] [All requirements met] [No security issues] [Output is complete]"
        return prompt + validation if "Validation Rules" not in prompt else prompt
    
    def _restructure_prompt(self, prompt: str, suggestion: PromptSuggestion) -> str:
        """Restructure prompt for clarity."""
        # Add headers for better organization if missing
        if not prompt.startswith("# "):
            prompt = "# Agent Task\n\n" + prompt
        return prompt
    
    def _get_agent_versions(self, agent_name: str) -> List[PromptVersion]:
        """Get all versions for an agent."""
        return self.prompt_versions.get(agent_name, [])
    
    def _get_version(self, agent_name: str, version_id: str) -> Optional[PromptVersion]:
        """Get a specific version."""
        versions = self._get_agent_versions(agent_name)
        return next((v for v in versions if v.version_id == version_id), None)
    
    def _compute_prompt_differences(self, prompt1: str, prompt2: str) -> Dict[str, Any]:
        """Compute differences between two prompts."""
        return {
            "changes_made": "Enhancements added to prompt structure",
            "lines_added": len(prompt2.split("\n")) - len(prompt1.split("\n")),
            "content_summary": "See version details for full prompt content"
        }
    
    def _calculate_improvement(self, test_results: Dict[str, Any]) -> float:
        """Calculate improvement score from test results."""
        # Simple heuristic: check for success metrics
        passed = test_results.get("tests_passed", 0)
        total = test_results.get("tests_total", 1)
        return passed / total if total > 0 else 0.0
    
    def _rollback_version(self, agent_name: str, old_version_id: str) -> None:
        """Rollback to a previous version."""
        versions = self._get_agent_versions(agent_name)
        for v in versions:
            v.is_active = v.version_id == old_version_id
    
    def _map_error_to_cause(self, error_type: str) -> str:
        """Map error type to likely cause."""
        cause_map = {
            "quality_gate_failure": "Output quality below threshold",
            "output_validation_error": "Output format or schema mismatch",
            "format_error": "Output doesn't match expected format",
            "logic_error": "Reasoning or logic in output is flawed",
            "incomplete_output": "Required elements missing from output",
            "security_violation": "Output contains security risks",
            "inconsistency": "Output contradicts itself or prior outputs"
        }
        return cause_map.get(error_type, "Unknown issue")
    
    def _impact_score(self, impact: str) -> int:
        """Convert impact description to numeric score."""
        return {"high": 3, "medium": 2, "low": 1}.get(impact, 0)


# Singleton instance management
_optimizer_instance: Optional[PromptOptimizer] = None


def get_prompt_optimizer() -> PromptOptimizer:
    """Get or create the singleton PromptOptimizer instance."""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = PromptOptimizer()
    return _optimizer_instance
