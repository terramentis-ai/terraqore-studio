"""
Learning Threshold Engine

Dynamically adjusts quality thresholds based on agent performance patterns.

Part of Phase 5.2 Learning System. Analyzes build metrics to determine adaptive
thresholds that improve agent quality while reducing false negatives.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import statistics

from core.state import StateManager
from core.build_data_collector import get_build_data_collector


class ThresholdMetricType(Enum):
    """Types of metrics used for thresholds."""
    QUALITY_SCORE = "quality_score"
    CONFIDENCE_SCORE = "confidence_score"
    COMPLETION_RATE = "completion_rate"
    SUCCESS_RATE = "success_rate"
    ERROR_COUNT = "error_count"
    EXECUTION_TIME = "execution_time"
    OUTPUT_VALIDITY = "output_validity"


@dataclass
class ThresholdConfig:
    """Configuration for a quality threshold."""
    metric_type: ThresholdMetricType
    current_value: float
    minimum_value: float
    maximum_value: float
    description: str
    agent_name: Optional[str] = None
    stage_name: Optional[str] = None
    context_tags: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    adjustment_history: List[Tuple[float, str, datetime]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["metric_type"] = self.metric_type.value
        data["last_updated"] = self.last_updated.isoformat()
        data["adjustment_history"] = [
            {
                "old_value": adj[0],
                "reason": adj[1],
                "timestamp": adj[2].isoformat()
            }
            for adj in self.adjustment_history
        ]
        return data


@dataclass
class ThresholdEffectiveness:
    """Measures how effective a threshold is."""
    threshold_config: ThresholdConfig
    sample_size: int
    true_positives: int  # Correctly identified
    true_negatives: int  # Correctly rejected
    false_positives: int  # Incorrectly accepted
    false_negatives: int  # Incorrectly rejected
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    last_evaluated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "threshold_value": self.threshold_config.current_value,
            "metric_type": self.threshold_config.metric_type.value,
            "accuracy": round(self.accuracy, 3),
            "precision": round(self.precision, 3),
            "recall": round(self.recall, 3),
            "f1_score": round(self.f1_score, 3),
            "sample_size": self.sample_size,
            "last_evaluated": self.last_evaluated.isoformat()
        }


@dataclass
class ThresholdRecommendation:
    """Recommendation to adjust a threshold."""
    current_threshold: float
    recommended_threshold: float
    reason: str
    expected_impact: Dict[str, Any]
    confidence: float  # 0-1
    related_metrics: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, approved, applied, rejected
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class LearningThresholdEngine:
    """
    Dynamically adjusts quality thresholds based on agent performance.
    
    Capabilities:
    - Calculate adaptive thresholds per agent/stage
    - Track threshold effectiveness
    - Recommend threshold adjustments
    - Analyze threshold-related metrics
    - Prevent threshold drift
    """
    
    def __init__(self):
        """Initialize the threshold engine."""
        self.state_manager = StateManager()
        self.collector = get_build_data_collector()
        self.thresholds: Dict[str, ThresholdConfig] = {}
        self.effectiveness_history: List[ThresholdEffectiveness] = []
        self.recommendations: List[ThresholdRecommendation] = []
    
    def calculate_adaptive_threshold(
        self, 
        agent: str, 
        stage: str, 
        metric_type: ThresholdMetricType,
        context: Optional[Dict[str, Any]] = None,
        lookback_days: int = 14
    ) -> float:
        """
        Calculate an adaptive threshold for an agent/stage/metric.
        
        Uses historical performance data to determine optimal threshold that:
        - Maintains quality standards
        - Minimizes false rejections
        - Accounts for agent specialization
        
        Args:
            agent: Agent name
            stage: Pipeline stage
            metric_type: Type of metric
            context: Additional context (task type, complexity)
            lookback_days: Historical window
        
        Returns:
            Recommended threshold value
        """
        # Fetch historical metrics
        metrics = self._fetch_agent_metrics(agent, stage, metric_type, lookback_days)
        
        if not metrics:
            return self._get_default_threshold(metric_type)
        
        # Calculate statistics
        values = [m["value"] for m in metrics]
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0
        
        # Apply context-aware adjustment
        context_tags = self._extract_context_tags(context) if context else []
        adjustment = self._get_context_adjustment(context_tags)
        
        # Calculate threshold using adaptive formula
        # Threshold = mean - (stdev * confidence_factor) * adjustment
        confidence_factor = 1.5  # Aim for ~93% acceptance
        base_threshold = mean - (stdev * confidence_factor)
        
        # Apply bounds
        threshold = self._apply_threshold_bounds(base_threshold, metric_type, adjustment)
        
        # Store configuration
        threshold_key = f"{agent}_{stage}_{metric_type.value}"
        self.thresholds[threshold_key] = ThresholdConfig(
            metric_type=metric_type,
            current_value=threshold,
            minimum_value=self._get_min_threshold(metric_type),
            maximum_value=self._get_max_threshold(metric_type),
            description=f"Adaptive threshold for {agent} at {stage}",
            agent_name=agent,
            stage_name=stage,
            context_tags=context_tags
        )
        
        return threshold
    
    def track_threshold_effectiveness(
        self,
        threshold: float,
        metric_type: ThresholdMetricType,
        results: List[Dict[str, Any]],
        agent_name: Optional[str] = None,
        stage_name: Optional[str] = None
    ) -> ThresholdEffectiveness:
        """
        Measure how effectively a threshold classifies outputs.
        
        Args:
            threshold: The threshold value
            metric_type: Type of metric
            results: Results with actual values and expected labels
            agent_name: Optional agent name
            stage_name: Optional stage name
        
        Returns:
            ThresholdEffectiveness measurement
        """
        if not results:
            return ThresholdEffectiveness(
                threshold_config=ThresholdConfig(
                    metric_type=metric_type,
                    current_value=threshold,
                    minimum_value=0,
                    maximum_value=100,
                    description="Empty results"
                ),
                sample_size=0,
                true_positives=0,
                true_negatives=0,
                false_positives=0,
                false_negatives=0,
                accuracy=0,
                precision=0,
                recall=0,
                f1_score=0
            )
        
        # Calculate confusion matrix
        tp, tn, fp, fn = 0, 0, 0, 0
        
        for result in results:
            value = result.get("value", 0)
            expected = result.get("expected_quality", True)  # True = should pass
            
            predicted = value >= threshold
            
            if predicted and expected:
                tp += 1
            elif not predicted and not expected:
                tn += 1
            elif predicted and not expected:
                fp += 1
            elif not predicted and expected:
                fn += 1
        
        # Calculate metrics
        total = len(results)
        accuracy = (tp + tn) / total if total > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        config = ThresholdConfig(
            metric_type=metric_type,
            current_value=threshold,
            minimum_value=self._get_min_threshold(metric_type),
            maximum_value=self._get_max_threshold(metric_type),
            description=f"Evaluated threshold for {metric_type.value}",
            agent_name=agent_name,
            stage_name=stage_name
        )
        
        effectiveness = ThresholdEffectiveness(
            threshold_config=config,
            sample_size=total,
            true_positives=tp,
            true_negatives=tn,
            false_positives=fp,
            false_negatives=fn,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1
        )
        
        self.effectiveness_history.append(effectiveness)
        
        return effectiveness
    
    def recommend_threshold_adjustment(
        self,
        agent: str,
        stage: Optional[str] = None,
        metric_type: Optional[ThresholdMetricType] = None,
        lookback_days: int = 14
    ) -> Optional[ThresholdRecommendation]:
        """
        Recommend a threshold adjustment based on effectiveness analysis.
        
        Args:
            agent: Agent name
            stage: Optional stage filter
            metric_type: Optional metric type filter
            lookback_days: Historical window for analysis
        
        Returns:
            ThresholdRecommendation or None
        """
        # Find relevant thresholds
        relevant_thresholds = [
            t for threshold_key, t in self.thresholds.items()
            if t.agent_name == agent and (not stage or t.stage_name == stage)
        ]
        
        if not relevant_thresholds:
            return None
        
        # Analyze effectiveness of current threshold
        recent_effectiveness = [
            e for e in self.effectiveness_history
            if e.threshold_config.agent_name == agent and
            (datetime.now() - e.last_evaluated).days <= lookback_days
        ]
        
        if not recent_effectiveness:
            return None
        
        # Find the threshold with lowest effectiveness
        worst = min(recent_effectiveness, key=lambda e: e.f1_score)
        
        # Determine adjustment
        if worst.false_negatives > worst.false_positives:
            # Too strict, lower threshold
            new_threshold = worst.threshold_config.current_value * 0.9
            reason = f"Threshold too strict (missing {worst.false_negatives} valid outputs)"
        elif worst.false_positives > worst.false_negatives:
            # Too lenient, raise threshold
            new_threshold = worst.threshold_config.current_value * 1.1
            reason = f"Threshold too lenient (accepting {worst.false_positives} invalid outputs)"
        else:
            # Balanced, minor adjustment
            new_threshold = worst.threshold_config.current_value
            reason = "Threshold performing well"
        
        # Apply bounds
        new_threshold = self._apply_threshold_bounds(
            new_threshold,
            worst.threshold_config.metric_type,
            1.0
        )
        
        # Calculate expected impact
        expected_impact = {
            "current_f1": round(worst.f1_score, 3),
            "estimated_improvement": round((worst.f1_score * 1.05) if new_threshold != worst.threshold_config.current_value else worst.f1_score, 3),
            "false_positive_reduction": worst.false_positives,
            "false_negative_reduction": worst.false_negatives
        }
        
        recommendation = ThresholdRecommendation(
            current_threshold=worst.threshold_config.current_value,
            recommended_threshold=new_threshold,
            reason=reason,
            expected_impact=expected_impact,
            confidence=0.85,
            related_metrics=[worst.threshold_config.metric_type.value]
        )
        
        self.recommendations.append(recommendation)
        
        return recommendation
    
    def apply_threshold_adjustment(
        self,
        recommendation: ThresholdRecommendation,
        agent: str,
        stage: Optional[str] = None
    ) -> ThresholdConfig:
        """
        Apply a threshold adjustment.
        
        Args:
            recommendation: The recommendation to apply
            agent: Agent name
            stage: Optional stage name
        
        Returns:
            Updated ThresholdConfig
        """
        # Find the threshold to update
        threshold_key = None
        for key, config in self.thresholds.items():
            if config.agent_name == agent and (not stage or config.stage_name == stage):
                threshold_key = key
                break
        
        if not threshold_key:
            # Create new threshold
            threshold_key = f"{agent}_{stage}_{recommendation.related_metrics[0]}"
            self.thresholds[threshold_key] = ThresholdConfig(
                metric_type=ThresholdMetricType.QUALITY_SCORE,
                current_value=recommendation.recommended_threshold,
                minimum_value=0,
                maximum_value=100,
                description=f"Applied threshold for {agent}"
            )
        
        # Update threshold
        old_value = self.thresholds[threshold_key].current_value
        self.thresholds[threshold_key].current_value = recommendation.recommended_threshold
        self.thresholds[threshold_key].adjustment_history.append(
            (old_value, recommendation.reason, datetime.now())
        )
        self.thresholds[threshold_key].last_updated = datetime.now()
        
        # Mark recommendation as applied
        recommendation.status = "applied"
        
        return self.thresholds[threshold_key]
    
    def get_threshold_analytics(self, agent: str) -> Dict[str, Any]:
        """
        Get comprehensive threshold analytics for an agent.
        
        Args:
            agent: Agent name
        
        Returns:
            Detailed analytics
        """
        agent_thresholds = [
            t for t in self.thresholds.values()
            if t.agent_name == agent
        ]
        
        agent_effectiveness = [
            e for e in self.effectiveness_history
            if e.threshold_config.agent_name == agent
        ]
        
        return {
            "agent_name": agent,
            "total_thresholds": len(agent_thresholds),
            "thresholds": [t.to_dict() for t in agent_thresholds],
            "effectiveness_evaluations": len(agent_effectiveness),
            "average_accuracy": round(
                sum(e.accuracy for e in agent_effectiveness) / len(agent_effectiveness)
                if agent_effectiveness else 0,
                3
            ),
            "average_f1": round(
                sum(e.f1_score for e in agent_effectiveness) / len(agent_effectiveness)
                if agent_effectiveness else 0,
                3
            ),
            "recent_adjustments": [
                {
                    "timestamp": adj[2].isoformat(),
                    "from": adj[0],
                    "reason": adj[1]
                }
                for t in agent_thresholds
                for adj in t.adjustment_history[-3:]  # Last 3 per threshold
            ]
        }
    
    def detect_threshold_drift(self, agent: str, days: int = 7) -> Optional[Dict[str, Any]]:
        """
        Detect if thresholds are drifting (performance degrading).
        
        Args:
            agent: Agent name
            days: Look back this many days
        
        Returns:
            Drift alert or None
        """
        # Get recent effectiveness data
        cutoff_date = datetime.now() - timedelta(days=days)
        recent = [
            e for e in self.effectiveness_history
            if e.threshold_config.agent_name == agent and
            e.last_evaluated >= cutoff_date
        ]
        
        if len(recent) < 2:
            return None
        
        # Check for declining F1 scores
        f1_scores = [e.f1_score for e in recent]
        trend = f1_scores[-1] - f1_scores[0]
        
        if trend < -0.1:  # Declining more than 10%
            return {
                "agent_name": agent,
                "drift_detected": True,
                "f1_trend": round(trend, 3),
                "current_f1": round(f1_scores[-1], 3),
                "previous_f1": round(f1_scores[0], 3),
                "recommendation": "Review and adjust thresholds",
                "alert_level": "high" if trend < -0.2 else "medium"
            }
        
        return None
    
    def prevent_threshold_creep(self, agent: str) -> Dict[str, Any]:
        """
        Prevent thresholds from gradually becoming too loose/strict.
        
        Args:
            agent: Agent name
        
        Returns:
            Analysis and recommendations
        """
        agent_thresholds = [
            t for t in self.thresholds.values()
            if t.agent_name == agent
        ]
        
        creep_analysis = {
            "agent": agent,
            "thresholds_checked": len(agent_thresholds),
            "creep_detected": False,
            "recommendations": []
        }
        
        for threshold in agent_thresholds:
            if len(threshold.adjustment_history) > 3:
                # Check if thresholds are monotonically increasing/decreasing
                recent_adjustments = threshold.adjustment_history[-3:]
                values = [adj[0] for adj in recent_adjustments]
                
                is_increasing = all(values[i] <= values[i+1] for i in range(len(values)-1))
                is_decreasing = all(values[i] >= values[i+1] for i in range(len(values)-1))
                
                if is_increasing or is_decreasing:
                    creep_analysis["creep_detected"] = True
                    direction = "increasing" if is_increasing else "decreasing"
                    creep_analysis["recommendations"].append(
                        f"Threshold {threshold.metric_type.value} shows {direction} creep. "
                        f"Reset to baseline and apply smaller adjustments."
                    )
        
        return creep_analysis
    
    # Private helper methods
    
    def _fetch_agent_metrics(
        self,
        agent: str,
        stage: str,
        metric_type: ThresholdMetricType,
        lookback_days: int
    ) -> List[Dict[str, Any]]:
        """Fetch historical metrics from build database."""
        try:
            cutoff_date = (datetime.now() - timedelta(days=lookback_days)).isoformat()
            
            metrics = self.state_manager.db.execute(
                """
                SELECT * FROM execution_metrics
                WHERE agent_name = ? AND stage = ? AND metric_type = ? AND timestamp >= ?
                ORDER BY timestamp DESC
                """,
                (agent, stage, metric_type.value, cutoff_date)
            ).fetchall()
            
            return [dict(row) for row in metrics] if metrics else []
        except Exception:
            return []
    
    def _get_default_threshold(self, metric_type: ThresholdMetricType) -> float:
        """Get default threshold for metric type."""
        defaults = {
            ThresholdMetricType.QUALITY_SCORE: 6.0,
            ThresholdMetricType.CONFIDENCE_SCORE: 0.7,
            ThresholdMetricType.COMPLETION_RATE: 0.95,
            ThresholdMetricType.SUCCESS_RATE: 0.85,
            ThresholdMetricType.ERROR_COUNT: 1.0,
            ThresholdMetricType.EXECUTION_TIME: 30.0,
            ThresholdMetricType.OUTPUT_VALIDITY: 0.9
        }
        return defaults.get(metric_type, 0.5)
    
    def _extract_context_tags(self, context: Dict[str, Any]) -> List[str]:
        """Extract context tags for adjustment."""
        tags = []
        if context.get("complexity") == "high":
            tags.append("complex")
        if context.get("task_type") == "critical":
            tags.append("critical")
        if context.get("time_sensitive"):
            tags.append("time_sensitive")
        return tags
    
    def _get_context_adjustment(self, context_tags: List[str]) -> float:
        """Get adjustment factor based on context tags."""
        adjustment = 1.0
        if "complex" in context_tags:
            adjustment *= 0.85  # Lower threshold for complex tasks
        if "critical" in context_tags:
            adjustment *= 0.90  # Lower threshold for critical tasks
        if "time_sensitive" in context_tags:
            adjustment *= 1.05  # Slightly higher threshold for time-sensitive
        return adjustment
    
    def _apply_threshold_bounds(
        self,
        threshold: float,
        metric_type: ThresholdMetricType,
        adjustment: float
    ) -> float:
        """Apply minimum and maximum bounds to threshold."""
        min_val = self._get_min_threshold(metric_type)
        max_val = self._get_max_threshold(metric_type)
        
        bounded = max(min_val, min(max_val, threshold))
        return round(bounded, 2)
    
    def _get_min_threshold(self, metric_type: ThresholdMetricType) -> float:
        """Get minimum threshold for metric type."""
        minimums = {
            ThresholdMetricType.QUALITY_SCORE: 1.0,
            ThresholdMetricType.CONFIDENCE_SCORE: 0.1,
            ThresholdMetricType.COMPLETION_RATE: 0.0,
            ThresholdMetricType.SUCCESS_RATE: 0.0,
            ThresholdMetricType.ERROR_COUNT: 0.0,
            ThresholdMetricType.EXECUTION_TIME: 0.1,
            ThresholdMetricType.OUTPUT_VALIDITY: 0.0
        }
        return minimums.get(metric_type, 0.0)
    
    def _get_max_threshold(self, metric_type: ThresholdMetricType) -> float:
        """Get maximum threshold for metric type."""
        maximums = {
            ThresholdMetricType.QUALITY_SCORE: 10.0,
            ThresholdMetricType.CONFIDENCE_SCORE: 1.0,
            ThresholdMetricType.COMPLETION_RATE: 1.0,
            ThresholdMetricType.SUCCESS_RATE: 1.0,
            ThresholdMetricType.ERROR_COUNT: 100.0,
            ThresholdMetricType.EXECUTION_TIME: 300.0,
            ThresholdMetricType.OUTPUT_VALIDITY: 1.0
        }
        return maximums.get(metric_type, 100.0)


# Singleton instance management
_engine_instance: Optional[LearningThresholdEngine] = None


def get_learning_threshold_engine() -> LearningThresholdEngine:
    """Get or create the singleton LearningThresholdEngine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = LearningThresholdEngine()
    return _engine_instance
