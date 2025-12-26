"""
Feedback Pattern Analyzer

Analyzes validation feedback from the collaboration state database to identify
recurring patterns, improvement clusters, and agent-specific improvement trends.

Used by Phase 5.2 Learning System to inform prompt optimization and threshold
adjustment decisions.
"""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
import json
from enum import Enum

from core.state import StateManager


class FeedbackCategory(Enum):
    """Categories of feedback patterns."""
    QUALITY_GATE_FAILURE = "quality_gate_failure"
    OUTPUT_VALIDATION_ERROR = "output_validation_error"
    SECURITY_VIOLATION = "security_violation"
    FORMAT_ERROR = "format_error"
    LOGIC_ERROR = "logic_error"
    INCOMPLETE_OUTPUT = "incomplete_output"
    INCONSISTENCY = "inconsistency"
    STYLE_ISSUE = "style_issue"
    OTHER = "other"


class ImprovementPriority(Enum):
    """Priority levels for improvements."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class FeedbackPattern:
    """Represents a recurring feedback pattern."""
    category: FeedbackCategory
    frequency: int
    agents_affected: List[str]
    common_contexts: List[str]
    suggested_improvements: List[str]
    first_occurrence: datetime
    last_occurrence: datetime
    avg_recurrence_days: float
    priority: ImprovementPriority = field(default=ImprovementPriority.MEDIUM)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "frequency": self.frequency,
            "agents_affected": self.agents_affected,
            "common_contexts": self.common_contexts,
            "suggested_improvements": self.suggested_improvements,
            "first_occurrence": self.first_occurrence.isoformat(),
            "last_occurrence": self.last_occurrence.isoformat(),
            "avg_recurrence_days": round(self.avg_recurrence_days, 2),
            "priority": self.priority.name
        }


@dataclass
class ImprovementCluster:
    """A group of related feedback items."""
    cluster_id: str
    category: FeedbackCategory
    size: int
    agents: List[str]
    feedback_items: List[Dict[str, Any]]
    common_solution: Optional[str] = None
    estimated_impact: float = 0.0  # 0-1 scale
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AgentImprovementTrend:
    """Improvement trend for a specific agent."""
    agent_name: str
    total_feedback_count: int
    feedback_by_category: Dict[str, int]
    trend_direction: str  # "improving", "stable", "degrading"
    recent_pattern_frequency: Dict[str, int]  # Last 7 days
    improvement_rate: float  # Percentage
    top_issues: List[Tuple[str, int]]  # (issue, count)
    last_updated: datetime


class FeedbackPatternAnalyzer:
    """
    Analyzes feedback patterns to identify improvements and trends.
    
    Uses data from the collaboration_state database to:
    - Identify recurring feedback patterns
    - Group similar feedback into improvement clusters
    - Track agent-specific improvement trends
    - Suggest optimizations based on patterns
    """
    
    def __init__(self):
        """Initialize the analyzer with state manager."""
        self.state_manager = StateManager()
        self.patterns_cache: Dict[str, FeedbackPattern] = {}
        self.last_analysis_time: Optional[datetime] = None
    
    def analyze_feedback_history(self, project_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Analyze feedback history for a project.
        
        Args:
            project_id: Project to analyze
            days: Look back this many days (default 30)
        
        Returns:
            Dictionary containing:
            - patterns: List of identified patterns
            - summary: Overall feedback statistics
            - recommendations: Suggested improvements
        """
        # Get all feedback for the project
        feedback_items = self._fetch_project_feedback(project_id, days)
        
        if not feedback_items:
            return {
                "patterns": [],
                "summary": {
                    "total_feedback": 0,
                    "date_range": f"Last {days} days",
                    "analysis_time": datetime.now().isoformat()
                },
                "recommendations": []
            }
        
        # Analyze patterns
        patterns = self._identify_patterns(feedback_items)
        
        # Generate summary statistics
        summary = self._generate_feedback_summary(feedback_items, patterns)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(patterns)
        
        self.last_analysis_time = datetime.now()
        
        return {
            "patterns": [p.to_dict() for p in patterns],
            "summary": summary,
            "recommendations": recommendations
        }
    
    def identify_improvement_clusters(self, feedback: List[Dict[str, Any]]) -> List[ImprovementCluster]:
        """
        Group similar feedback into actionable clusters.
        
        Args:
            feedback: List of feedback dictionaries
        
        Returns:
            List of improvement clusters
        """
        if not feedback:
            return []
        
        clusters: Dict[str, ImprovementCluster] = {}
        
        for idx, item in enumerate(feedback):
            # Categorize feedback
            category = self._categorize_feedback(item)
            category_key = category.value
            
            # Find or create cluster
            if category_key not in clusters:
                clusters[category_key] = ImprovementCluster(
                    cluster_id=f"cluster_{category_key}_{idx}",
                    category=category,
                    size=0,
                    agents=[],
                    feedback_items=[]
                )
            
            cluster = clusters[category_key]
            cluster.size += 1
            cluster.feedback_items.append(item)
            
            agent = item.get("agent_name", "unknown")
            if agent not in cluster.agents:
                cluster.agents.append(agent)
        
        # Calculate solutions and impact for each cluster
        result = []
        for cluster in clusters.values():
            cluster.common_solution = self._suggest_cluster_solution(cluster)
            cluster.estimated_impact = self._estimate_cluster_impact(cluster)
            result.append(cluster)
        
        return result
    
    def get_agent_improvement_trends(self, agent_name: str, days: int = 30) -> AgentImprovementTrend:
        """
        Get improvement trends for a specific agent.
        
        Args:
            agent_name: Name of the agent to analyze
            days: Look back this many days
        
        Returns:
            AgentImprovementTrend with detailed metrics
        """
        # Fetch feedback for this agent
        feedback_items = self._fetch_agent_feedback(agent_name, days)
        
        if not feedback_items:
            return AgentImprovementTrend(
                agent_name=agent_name,
                total_feedback_count=0,
                feedback_by_category={},
                trend_direction="no_data",
                recent_pattern_frequency={},
                improvement_rate=0.0,
                top_issues=[],
                last_updated=datetime.now()
            )
        
        # Count feedback by category
        category_counts = self._count_feedback_by_category(feedback_items)
        
        # Calculate trend direction
        trend_direction = self._calculate_trend_direction(feedback_items)
        
        # Get recent pattern frequency (last 7 days)
        recent_patterns = self._analyze_recent_patterns(feedback_items)
        
        # Calculate improvement rate
        improvement_rate = self._calculate_improvement_rate(feedback_items)
        
        # Identify top issues
        top_issues = self._identify_top_issues(feedback_items, limit=5)
        
        return AgentImprovementTrend(
            agent_name=agent_name,
            total_feedback_count=len(feedback_items),
            feedback_by_category=category_counts,
            trend_direction=trend_direction,
            recent_pattern_frequency=recent_patterns,
            improvement_rate=improvement_rate,
            top_issues=top_issues,
            last_updated=datetime.now()
        )
    
    def get_pattern_context_analysis(self, pattern: FeedbackPattern) -> Dict[str, Any]:
        """
        Analyze the contexts where a pattern occurs.
        
        Args:
            pattern: The pattern to analyze
        
        Returns:
            Analysis of when and why the pattern occurs
        """
        return {
            "pattern_category": pattern.category.value,
            "common_contexts": pattern.common_contexts,
            "affected_agents": pattern.agents_affected,
            "frequency_metric": f"{pattern.frequency} occurrences",
            "recurrence_interval": f"Every {pattern.avg_recurrence_days:.1f} days",
            "suggested_fixes": pattern.suggested_improvements,
            "priority": pattern.priority.name
        }
    
    def predict_next_feedback_patterns(self, agent_name: str, lookback_days: int = 30) -> List[Dict[str, Any]]:
        """
        Predict likely future feedback patterns based on history.
        
        Args:
            agent_name: Agent to predict for
            lookback_days: Historical window
        
        Returns:
            List of likely future patterns with confidence scores
        """
        feedback = self._fetch_agent_feedback(agent_name, lookback_days)
        
        if len(feedback) < 3:
            return []
        
        # Analyze pattern recurrence
        predictions = []
        category_frequencies = self._count_feedback_by_category(feedback)
        
        for category, count in category_frequencies.items():
            confidence = min(count / len(feedback), 1.0)  # Normalize to 0-1
            
            # Calculate likely next occurrence
            times = self._extract_feedback_timestamps(feedback, category)
            if times and len(times) > 1:
                intervals = [
                    (times[i] - times[i-1]).days
                    for i in range(1, len(times))
                ]
                avg_days = sum(intervals) / len(intervals)
                next_expected = datetime.now() + timedelta(days=int(avg_days))
            else:
                next_expected = datetime.now() + timedelta(days=7)
            
            predictions.append({
                "category": category,
                "confidence": round(confidence, 2),
                "likely_next_occurrence": next_expected.isoformat(),
                "preventive_action": self._suggest_preventive_action(category)
            })
        
        return sorted(predictions, key=lambda x: x["confidence"], reverse=True)
    
    # Private helper methods
    
    def _fetch_project_feedback(self, project_id: int, days: int) -> List[Dict[str, Any]]:
        """Fetch feedback items from database."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            feedback = self.state_manager.db.execute(
                """
                SELECT af.* FROM agent_feedback af
                WHERE af.project_id = ? AND af.created_at >= ?
                ORDER BY af.created_at DESC
                """,
                (project_id, cutoff_date.isoformat())
            ).fetchall()
            
            return [dict(row) for row in feedback] if feedback else []
        except Exception:
            return []
    
    def _fetch_agent_feedback(self, agent_name: str, days: int) -> List[Dict[str, Any]]:
        """Fetch feedback for a specific agent."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            feedback = self.state_manager.db.execute(
                """
                SELECT af.* FROM agent_feedback af
                WHERE af.agent_name = ? AND af.created_at >= ?
                ORDER BY af.created_at DESC
                """,
                (agent_name, cutoff_date.isoformat())
            ).fetchall()
            
            return [dict(row) for row in feedback] if feedback else []
        except Exception:
            return []
    
    def _categorize_feedback(self, feedback_item: Dict[str, Any]) -> FeedbackCategory:
        """Categorize a feedback item."""
        feedback_text = feedback_item.get("feedback_text", "").lower()
        feedback_type = feedback_item.get("feedback_type", "").lower()
        
        if "quality" in feedback_text or "quality" in feedback_type:
            return FeedbackCategory.QUALITY_GATE_FAILURE
        elif "validation" in feedback_text or "validation" in feedback_type:
            return FeedbackCategory.OUTPUT_VALIDATION_ERROR
        elif "security" in feedback_text or "security" in feedback_type:
            return FeedbackCategory.SECURITY_VIOLATION
        elif "format" in feedback_text or "format" in feedback_type:
            return FeedbackCategory.FORMAT_ERROR
        elif "logic" in feedback_text or "logic" in feedback_type:
            return FeedbackCategory.LOGIC_ERROR
        elif "incomplete" in feedback_text or "incomplete" in feedback_type:
            return FeedbackCategory.INCOMPLETE_OUTPUT
        elif "inconsistent" in feedback_text or "inconsistency" in feedback_type:
            return FeedbackCategory.INCONSISTENCY
        elif "style" in feedback_text or "style" in feedback_type:
            return FeedbackCategory.STYLE_ISSUE
        else:
            return FeedbackCategory.OTHER
    
    def _identify_patterns(self, feedback_items: List[Dict[str, Any]]) -> List[FeedbackPattern]:
        """Identify recurring patterns."""
        patterns_by_category = defaultdict(list)
        
        for item in feedback_items:
            category = self._categorize_feedback(item)
            patterns_by_category[category].append(item)
        
        patterns = []
        for category, items in patterns_by_category.items():
            if len(items) >= 2:  # Only consider patterns that repeat
                pattern = FeedbackPattern(
                    category=category,
                    frequency=len(items),
                    agents_affected=list(set(i.get("agent_name", "unknown") for i in items)),
                    common_contexts=self._extract_common_contexts(items),
                    suggested_improvements=self._suggest_improvements(category, items),
                    first_occurrence=self._get_timestamp(items[-1]),  # Oldest
                    last_occurrence=self._get_timestamp(items[0]),    # Newest
                    avg_recurrence_days=self._calculate_recurrence_interval(items),
                    priority=self._determine_priority(category, len(items))
                )
                patterns.append(pattern)
        
        return sorted(patterns, key=lambda p: (p.priority.value, -p.frequency))
    
    def _generate_feedback_summary(
        self, 
        feedback_items: List[Dict[str, Any]], 
        patterns: List[FeedbackPattern]
    ) -> Dict[str, Any]:
        """Generate summary statistics."""
        categories = [self._categorize_feedback(f).value for f in feedback_items]
        category_counts = Counter(categories)
        
        return {
            "total_feedback": len(feedback_items),
            "unique_categories": len(category_counts),
            "feedback_by_category": dict(category_counts),
            "recurring_patterns": len(patterns),
            "most_common_issue": category_counts.most_common(1)[0][0] if category_counts else "none",
            "affected_agents": len(set(f.get("agent_name", "unknown") for f in feedback_items)),
            "analysis_time": datetime.now().isoformat()
        }
    
    def _generate_recommendations(self, patterns: List[FeedbackPattern]) -> List[str]:
        """Generate recommendations based on patterns."""
        recommendations = []
        
        for pattern in patterns[:5]:  # Top 5 patterns
            rec = (
                f"Address {pattern.category.value}: "
                f"{pattern.frequency} occurrences affecting {len(pattern.agents_affected)} agent(s). "
                f"Suggested: {pattern.suggested_improvements[0] if pattern.suggested_improvements else 'Monitor'}"
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _count_feedback_by_category(self, feedback_items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count feedback items by category."""
        counts = defaultdict(int)
        for item in feedback_items:
            category = self._categorize_feedback(item)
            counts[category.value] += 1
        return dict(counts)
    
    def _calculate_trend_direction(self, feedback_items: List[Dict[str, Any]]) -> str:
        """Determine if agent is improving, stable, or degrading."""
        if len(feedback_items) < 4:
            return "insufficient_data"
        
        # Split into older and recent feedback
        midpoint = len(feedback_items) // 2
        older = feedback_items[midpoint:]
        recent = feedback_items[:midpoint]
        
        # Calculate severity (placeholder logic)
        older_severity = sum(1 for f in older)
        recent_severity = sum(1 for f in recent)
        
        if recent_severity < older_severity * 0.8:
            return "improving"
        elif recent_severity > older_severity * 1.2:
            return "degrading"
        else:
            return "stable"
    
    def _analyze_recent_patterns(self, feedback_items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze patterns from the last 7 days."""
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent = [f for f in feedback_items if self._get_timestamp(f) >= seven_days_ago]
        return self._count_feedback_by_category(recent)
    
    def _calculate_improvement_rate(self, feedback_items: List[Dict[str, Any]]) -> float:
        """Calculate improvement rate as percentage."""
        if len(feedback_items) < 2:
            return 0.0
        
        trend = self._calculate_trend_direction(feedback_items)
        if trend == "improving":
            return 0.15  # 15% improvement
        elif trend == "stable":
            return 0.0
        else:
            return -0.10  # 10% degradation
    
    def _identify_top_issues(self, feedback_items: List[Dict[str, Any]], limit: int = 5) -> List[Tuple[str, int]]:
        """Identify top issues affecting the agent."""
        category_counts = self._count_feedback_by_category(feedback_items)
        return sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def _extract_common_contexts(self, items: List[Dict[str, Any]]) -> List[str]:
        """Extract common contexts from feedback items."""
        contexts = []
        for item in items:
            context = item.get("feedback_context", "")
            if context:
                contexts.append(context)
        return list(set(contexts))[:3]  # Top 3 unique contexts
    
    def _suggest_improvements(self, category: FeedbackCategory, items: List[Dict[str, Any]]) -> List[str]:
        """Suggest improvements for a category."""
        suggestions = {
            FeedbackCategory.QUALITY_GATE_FAILURE: [
                "Increase prompt specificity about quality requirements",
                "Add example outputs with quality annotations",
                "Implement pre-validation checks"
            ],
            FeedbackCategory.OUTPUT_VALIDATION_ERROR: [
                "Clarify expected output format",
                "Add schema validation to prompt",
                "Provide structured output examples"
            ],
            FeedbackCategory.SECURITY_VIOLATION: [
                "Add security guidelines to system prompt",
                "Implement output sanitization",
                "Review and restrict dangerous patterns"
            ],
            FeedbackCategory.FORMAT_ERROR: [
                "Provide exact format examples",
                "Add format validation",
                "Include format requirements in system message"
            ],
            FeedbackCategory.LOGIC_ERROR: [
                "Clarify reasoning requirements",
                "Add step-by-step examples",
                "Implement logic validation checks"
            ],
            FeedbackCategory.INCOMPLETE_OUTPUT: [
                "Specify required output completeness",
                "Add checklist of required elements",
                "Implement completeness validation"
            ],
            FeedbackCategory.INCONSISTENCY: [
                "Add consistency rules to prompt",
                "Provide examples of consistent outputs",
                "Implement consistency checks"
            ],
            FeedbackCategory.STYLE_ISSUE: [
                "Provide style guide examples",
                "Add style requirements to prompt",
                "Implement style validation"
            ],
        }
        return suggestions.get(category, ["Review feedback and adjust approach"])
    
    def _suggest_cluster_solution(self, cluster: ImprovementCluster) -> Optional[str]:
        """Suggest a solution for an improvement cluster."""
        if not cluster.feedback_items:
            return None
        
        solution_map = {
            "quality_gate_failure": "Enhance prompt with quality criteria and examples",
            "output_validation_error": "Add output format validation and examples",
            "security_violation": "Add security guidelines to agent prompts",
            "format_error": "Provide explicit format specifications",
            "logic_error": "Add step-by-step reasoning requirements",
            "incomplete_output": "Define completeness criteria",
            "inconsistency": "Add consistency rules and examples",
            "style_issue": "Provide style guide in prompt"
        }
        return solution_map.get(cluster.category.value, "Review and enhance agent prompts")
    
    def _estimate_cluster_impact(self, cluster: ImprovementCluster) -> float:
        """Estimate the impact of addressing a cluster (0-1 scale)."""
        # Impact = frequency / total possible feedback × agent count factor
        base_impact = min(cluster.size / 10, 1.0)
        agent_factor = min(len(cluster.agents) / 3, 1.0)
        return round((base_impact + agent_factor) / 2, 2)
    
    def _get_timestamp(self, item: Dict[str, Any]) -> datetime:
        """Extract timestamp from item."""
        ts = item.get("created_at")
        if isinstance(ts, str):
            try:
                return datetime.fromisoformat(ts)
            except:
                return datetime.now()
        return ts if isinstance(ts, datetime) else datetime.now()
    
    def _calculate_recurrence_interval(self, items: List[Dict[str, Any]]) -> float:
        """Calculate average days between occurrences."""
        if len(items) < 2:
            return 0.0
        
        timestamps = sorted([self._get_timestamp(i) for i in items])
        intervals = [(timestamps[i] - timestamps[i-1]).days for i in range(1, len(timestamps))]
        
        return sum(intervals) / len(intervals) if intervals else 0.0
    
    def _determine_priority(self, category: FeedbackCategory, frequency: int) -> ImprovementPriority:
        """Determine priority based on category and frequency."""
        if category in [FeedbackCategory.SECURITY_VIOLATION]:
            return ImprovementPriority.CRITICAL
        elif frequency >= 5:
            return ImprovementPriority.HIGH
        elif frequency >= 3:
            return ImprovementPriority.MEDIUM
        else:
            return ImprovementPriority.LOW
    
    def _extract_feedback_timestamps(self, feedback: List[Dict[str, Any]], category: str) -> List[datetime]:
        """Extract timestamps for a specific category."""
        return [
            self._get_timestamp(f)
            for f in feedback
            if self._categorize_feedback(f).value == category
        ]
    
    def _suggest_preventive_action(self, category: str) -> str:
        """Suggest preventive action for a category."""
        actions = {
            "quality_gate_failure": "Strengthen quality validation in prompt",
            "output_validation_error": "Add schema validation",
            "security_violation": "Review security guidelines",
            "format_error": "Validate output format before submission",
            "logic_error": "Add step-by-step reasoning",
            "incomplete_output": "Verify completeness checklist",
            "inconsistency": "Check consistency before output",
            "style_issue": "Apply style formatter"
        }
        return actions.get(category, "Monitor and review")


# Singleton instance management
_analyzer_instance: Optional[FeedbackPatternAnalyzer] = None


def get_feedback_pattern_analyzer() -> FeedbackPatternAnalyzer:
    """Get or create the singleton FeedbackPatternAnalyzer instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = FeedbackPatternAnalyzer()
    return _analyzer_instance
