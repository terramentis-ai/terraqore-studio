"""
Performance Analytics

Tracks and analyzes agent performance metrics across builds and time.

Part of Phase 5.2 Learning System. Provides comprehensive performance reporting,
degradation detection, and performance forecasting.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import statistics

from core.state import StateManager
from core.build_data_collector import get_build_data_collector


class PerformanceMetric(Enum):
    """Types of performance metrics."""
    EXECUTION_TIME = "execution_time"
    QUALITY_SCORE = "quality_score"
    SUCCESS_RATE = "success_rate"
    ERROR_COUNT = "error_count"
    MEMORY_USAGE = "memory_usage"
    TOKEN_USAGE = "token_usage"
    ITERATIONS_NEEDED = "iterations_needed"
    RETRY_COUNT = "retry_count"


class TrendDirection(Enum):
    """Trend direction indicators."""
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    VOLATILE = "volatile"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class AgentMetrics:
    """Comprehensive metrics for an agent."""
    agent_name: str
    metric_type: PerformanceMetric
    samples: int
    mean: float
    median: float
    stddev: float
    min_value: float
    max_value: float
    p25: float  # 25th percentile
    p75: float  # 75th percentile
    p95: float  # 95th percentile
    measurement_period: str  # "7d", "30d", "all"
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["metric_type"] = self.metric_type.value
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class PerformanceTrend:
    """Represents a performance trend over time."""
    agent_name: str
    metric_type: PerformanceMetric
    period_days: int
    current_value: float
    previous_value: float
    change_percentage: float
    trend_direction: TrendDirection
    volatility: float  # Standard deviation of changes
    projected_value: Optional[float] = None
    confidence: float = 0.0
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["metric_type"] = self.metric_type.value
        data["trend_direction"] = self.trend_direction.value
        data["analysis_timestamp"] = self.analysis_timestamp.isoformat()
        return data


@dataclass
class PerformanceDegradation:
    """Alert for performance degradation."""
    agent_name: str
    metric_type: PerformanceMetric
    severity: str  # "critical", "high", "medium", "low"
    current_value: float
    threshold_value: float
    change_percentage: float
    time_to_threshold_breach: Optional[str] = None
    recommended_action: str = ""
    detected_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["metric_type"] = self.metric_type.value
        data["detected_at"] = self.detected_at.isoformat()
        return data


@dataclass
class PerformanceComparison:
    """Comparison of agent performance."""
    agents: List[str]
    metric_type: PerformanceMetric
    period_days: int
    rankings: List[Tuple[str, float]]  # (agent_name, score)
    best_performer: str
    worst_performer: str
    mean_performance: float
    stddev_performance: float
    comparison_timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agents": self.agents,
            "metric_type": self.metric_type.value,
            "period_days": self.period_days,
            "rankings": [(agent, round(score, 3)) for agent, score in self.rankings],
            "best_performer": self.best_performer,
            "worst_performer": self.worst_performer,
            "mean_performance": round(self.mean_performance, 3),
            "stddev_performance": round(self.stddev_performance, 3),
            "comparison_timestamp": self.comparison_timestamp.isoformat()
        }


class PerformanceAnalytics:
    """
    Comprehensive performance tracking and analysis.
    
    Capabilities:
    - Calculate agent metrics (time, quality, success)
    - Generate performance reports
    - Detect performance degradation
    - Forecast performance trends
    - Compare agent performance
    """
    
    def __init__(self):
        """Initialize performance analytics."""
        self.state_manager = StateManager()
        self.collector = get_build_data_collector()
        self.metrics_cache: Dict[str, List[AgentMetrics]] = {}
        self.trends_cache: Dict[str, List[PerformanceTrend]] = {}
        self.degradation_alerts: List[PerformanceDegradation] = []
    
    def calculate_agent_metrics(
        self,
        agent_name: str,
        build_id: str,
        metric_type: PerformanceMetric,
        period_days: int = 30
    ) -> AgentMetrics:
        """
        Calculate comprehensive metrics for an agent.
        
        Args:
            agent_name: The agent to analyze
            build_id: Build context
            metric_type: Which metric to analyze
            period_days: Historical window
        
        Returns:
            AgentMetrics with statistical analysis
        """
        # Fetch values for this metric
        values = self._fetch_metric_values(agent_name, metric_type, period_days)
        
        if not values:
            return AgentMetrics(
                agent_name=agent_name,
                metric_type=metric_type,
                samples=0,
                mean=0.0,
                median=0.0,
                stddev=0.0,
                min_value=0.0,
                max_value=0.0,
                p25=0.0,
                p75=0.0,
                p95=0.0,
                measurement_period=f"{period_days}d"
            )
        
        # Calculate statistics
        sorted_values = sorted(values)
        mean = statistics.mean(values)
        median = statistics.median(values)
        stddev = statistics.stdev(values) if len(values) > 1 else 0.0
        min_val = min(values)
        max_val = max(values)
        
        # Percentiles
        p25_idx = int(len(values) * 0.25)
        p75_idx = int(len(values) * 0.75)
        p95_idx = int(len(values) * 0.95)
        
        p25 = sorted_values[p25_idx] if p25_idx < len(values) else min_val
        p75 = sorted_values[p75_idx] if p75_idx < len(values) else max_val
        p95 = sorted_values[p95_idx] if p95_idx < len(values) else max_val
        
        metrics = AgentMetrics(
            agent_name=agent_name,
            metric_type=metric_type,
            samples=len(values),
            mean=round(mean, 3),
            median=round(median, 3),
            stddev=round(stddev, 3),
            min_value=round(min_val, 3),
            max_value=round(max_val, 3),
            p25=round(p25, 3),
            p75=round(p75, 3),
            p95=round(p95, 3),
            measurement_period=f"{period_days}d"
        )
        
        # Cache it
        if agent_name not in self.metrics_cache:
            self.metrics_cache[agent_name] = []
        self.metrics_cache[agent_name].append(metrics)
        
        return metrics
    
    def generate_performance_report(self, project_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Generate comprehensive performance report for a project.
        
        Args:
            project_id: Project to report on
            days: Historical window
        
        Returns:
            Detailed performance report
        """
        # Get all agents active in this project
        agents = self._get_project_agents(project_id, days)
        
        if not agents:
            return {
                "project_id": project_id,
                "period_days": days,
                "agents": [],
                "summary": "No performance data available"
            }
        
        # Calculate metrics for each agent
        agent_performance = {}
        for agent in agents:
            agent_performance[agent] = {}
            
            for metric_type in PerformanceMetric:
                metrics = self.calculate_agent_metrics(agent, "", metric_type, days)
                agent_performance[agent][metric_type.value] = metrics.to_dict()
        
        # Calculate project-wide statistics
        project_stats = self._calculate_project_statistics(agents, days)
        
        return {
            "project_id": project_id,
            "period_days": days,
            "agents_analyzed": len(agents),
            "agent_performance": agent_performance,
            "project_statistics": project_stats,
            "report_timestamp": datetime.now().isoformat()
        }
    
    def identify_performance_degradation(self, agent: str, threshold: float = -0.1) -> Optional[PerformanceDegradation]:
        """
        Detect if agent performance is degrading.
        
        Args:
            agent: Agent name
            threshold: Change percentage threshold (-0.1 = 10% decline)
        
        Returns:
            PerformanceDegradation alert or None
        """
        # Analyze trends for all metrics
        worst_degradation = None
        
        for metric_type in PerformanceMetric:
            trend = self._calculate_trend(agent, metric_type, 14)  # Last 2 weeks
            
            if trend and trend.change_percentage < threshold:
                # This metric is degrading
                severity = self._calculate_degradation_severity(
                    metric_type,
                    trend.change_percentage
                )
                
                degradation = PerformanceDegradation(
                    agent_name=agent,
                    metric_type=metric_type,
                    severity=severity,
                    current_value=trend.current_value,
                    threshold_value=trend.previous_value,
                    change_percentage=trend.change_percentage,
                    recommended_action=self._suggest_degradation_fix(metric_type, severity)
                )
                
                self.degradation_alerts.append(degradation)
                
                # Track worst degradation
                if not worst_degradation or severity == "critical":
                    worst_degradation = degradation
        
        return worst_degradation
    
    def forecast_performance(
        self,
        agent: str,
        metric_type: PerformanceMetric,
        forecast_days: int = 7,
        historical_days: int = 30
    ) -> Dict[str, Any]:
        """
        Forecast future performance based on trends.
        
        Args:
            agent: Agent name
            metric_type: Metric to forecast
            forecast_days: Days to forecast ahead
            historical_days: Historical window for trend analysis
        
        Returns:
            Forecast with confidence intervals
        """
        # Get historical values
        values = self._fetch_metric_values(agent, metric_type, historical_days)
        
        if len(values) < 3:
            return {
                "agent": agent,
                "metric_type": metric_type.value,
                "forecast_available": False,
                "reason": "Insufficient historical data"
            }
        
        # Simple linear trend (can be enhanced with more sophisticated models)
        trend = self._calculate_trend(agent, metric_type, historical_days)
        
        if not trend:
            return {
                "agent": agent,
                "metric_type": metric_type.value,
                "forecast_available": False,
                "reason": "Cannot calculate trend"
            }
        
        # Project forward
        current_value = trend.current_value
        change_per_day = (trend.current_value - trend.previous_value) / historical_days
        
        forecast_points = []
        for day in range(1, forecast_days + 1):
            projected_value = current_value + (change_per_day * day)
            forecast_points.append({
                "day": day,
                "projected_value": round(projected_value, 3),
                "confidence": round(max(0.5, 1.0 - (day / forecast_days * 0.5)), 2)
            })
        
        # Check if forecasted value crosses any thresholds
        critical_point = None
        final_forecast = forecast_points[-1]["projected_value"]
        
        if self._would_cross_threshold(metric_type, current_value, final_forecast):
            critical_point = f"Forecasted to cross critical threshold"
        
        return {
            "agent": agent,
            "metric_type": metric_type.value,
            "historical_period_days": historical_days,
            "forecast_period_days": forecast_days,
            "current_value": round(current_value, 3),
            "trend_direction": trend.trend_direction.value,
            "change_per_day": round(change_per_day, 3),
            "forecast_points": forecast_points,
            "final_forecast": round(final_forecast, 3),
            "critical_alert": critical_point,
            "forecast_timestamp": datetime.now().isoformat()
        }
    
    def compare_agent_performance(
        self,
        agents: List[str],
        metric_type: PerformanceMetric,
        period_days: int = 30
    ) -> PerformanceComparison:
        """
        Compare performance across multiple agents.
        
        Args:
            agents: List of agents to compare
            metric_type: Metric to compare on
            period_days: Historical window
        
        Returns:
            PerformanceComparison with rankings
        """
        rankings = []
        
        for agent in agents:
            metrics = self.calculate_agent_metrics(agent, "", metric_type, period_days)
            # Use mean as ranking score (inverted for some metrics)
            score = metrics.mean if metric_type != PerformanceMetric.EXECUTION_TIME else 1 / metrics.mean if metrics.mean > 0 else 0
            rankings.append((agent, score))
        
        # Sort by score
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        scores = [score for _, score in rankings]
        mean_score = statistics.mean(scores) if scores else 0
        stddev_score = statistics.stdev(scores) if len(scores) > 1 else 0
        
        comparison = PerformanceComparison(
            agents=agents,
            metric_type=metric_type,
            period_days=period_days,
            rankings=rankings,
            best_performer=rankings[0][0] if rankings else "none",
            worst_performer=rankings[-1][0] if rankings else "none",
            mean_performance=mean_score,
            stddev_performance=stddev_score
        )
        
        return comparison
    
    def get_performance_summary(self, agent: str, days: int = 30) -> Dict[str, Any]:
        """
        Get a quick performance summary for an agent.
        
        Args:
            agent: Agent name
            days: Historical window
        
        Returns:
            Quick summary of performance
        """
        summary = {
            "agent": agent,
            "period_days": days,
            "metrics": {}
        }
        
        for metric_type in PerformanceMetric:
            metrics = self.calculate_agent_metrics(agent, "", metric_type, days)
            trend = self._calculate_trend(agent, metric_type, days)
            
            summary["metrics"][metric_type.value] = {
                "mean": metrics.mean,
                "current_trend": trend.trend_direction.value if trend else "unknown",
                "change_percent": trend.change_percentage if trend else 0.0
            }
        
        # Overall health
        improving = sum(1 for m in summary["metrics"].values() if m["current_trend"] == "improving")
        degrading = sum(1 for m in summary["metrics"].values() if m["current_trend"] == "degrading")
        
        if degrading > improving:
            health = "degrading"
        elif improving > degrading:
            health = "improving"
        else:
            health = "stable"
        
        summary["overall_health"] = health
        summary["timestamp"] = datetime.now().isoformat()
        
        return summary
    
    # Private helper methods
    
    def _fetch_metric_values(
        self,
        agent_name: str,
        metric_type: PerformanceMetric,
        days: int
    ) -> List[float]:
        """Fetch metric values from database."""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            records = self.state_manager.db.execute(
                """
                SELECT value FROM execution_metrics
                WHERE agent_name = ? AND metric_type = ? AND timestamp >= ?
                ORDER BY timestamp DESC
                """,
                (agent_name, metric_type.value, cutoff_date)
            ).fetchall()
            
            return [row["value"] for row in records] if records else []
        except Exception:
            return []
    
    def _get_project_agents(self, project_id: int, days: int) -> List[str]:
        """Get all agents active in a project."""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            records = self.state_manager.db.execute(
                """
                SELECT DISTINCT agent_name FROM execution_metrics
                WHERE project_id = ? AND timestamp >= ?
                """,
                (project_id, cutoff_date)
            ).fetchall()
            
            return [row["agent_name"] for row in records] if records else []
        except Exception:
            return []
    
    def _calculate_trend(
        self,
        agent: str,
        metric_type: PerformanceMetric,
        period_days: int
    ) -> Optional[PerformanceTrend]:
        """Calculate trend for a metric."""
        values = self._fetch_metric_values(agent, metric_type, period_days)
        
        if len(values) < 2:
            return None
        
        # Split into two periods
        midpoint = len(values) // 2
        older = values[midpoint:]
        recent = values[:midpoint]
        
        if not older or not recent:
            return None
        
        current_mean = statistics.mean(recent)
        previous_mean = statistics.mean(older)
        
        # Calculate change
        if previous_mean != 0:
            change_pct = (current_mean - previous_mean) / previous_mean
        else:
            change_pct = 0
        
        # Determine trend direction
        if abs(change_pct) < 0.05:
            direction = TrendDirection.STABLE
        elif change_pct > 0.1:
            direction = TrendDirection.IMPROVING if metric_type in [
                PerformanceMetric.QUALITY_SCORE,
                PerformanceMetric.SUCCESS_RATE
            ] else TrendDirection.DEGRADING
        elif change_pct < -0.1:
            direction = TrendDirection.DEGRADING if metric_type in [
                PerformanceMetric.QUALITY_SCORE,
                PerformanceMetric.SUCCESS_RATE
            ] else TrendDirection.IMPROVING
        else:
            direction = TrendDirection.STABLE
        
        # Calculate volatility
        all_changes = [abs(values[i] - values[i+1]) for i in range(len(values)-1)]
        volatility = statistics.stdev(all_changes) if len(all_changes) > 1 else 0
        
        return PerformanceTrend(
            agent_name=agent,
            metric_type=metric_type,
            period_days=period_days,
            current_value=current_mean,
            previous_value=previous_mean,
            change_percentage=change_pct,
            trend_direction=direction,
            volatility=volatility
        )
    
    def _calculate_project_statistics(self, agents: List[str], days: int) -> Dict[str, Any]:
        """Calculate project-wide statistics."""
        return {
            "total_agents": len(agents),
            "analysis_period_days": days,
            "metrics_tracked": len(PerformanceMetric),
            "last_updated": datetime.now().isoformat()
        }
    
    def _calculate_degradation_severity(self, metric_type: PerformanceMetric, change_pct: float) -> str:
        """Determine severity of degradation."""
        abs_change = abs(change_pct)
        
        if abs_change > 0.30:
            return "critical"
        elif abs_change > 0.20:
            return "high"
        elif abs_change > 0.10:
            return "medium"
        else:
            return "low"
    
    def _suggest_degradation_fix(self, metric_type: PerformanceMetric, severity: str) -> str:
        """Suggest fix for degradation."""
        fixes = {
            PerformanceMetric.EXECUTION_TIME: "Optimize agent logic or add caching",
            PerformanceMetric.QUALITY_SCORE: "Review and enhance agent prompt",
            PerformanceMetric.SUCCESS_RATE: "Investigate recent failures in build logs",
            PerformanceMetric.ERROR_COUNT: "Debug error patterns and implement guards",
            PerformanceMetric.MEMORY_USAGE: "Optimize data structures or implement cleanup",
            PerformanceMetric.TOKEN_USAGE: "Reduce prompt size or use summarization",
            PerformanceMetric.ITERATIONS_NEEDED: "Improve agent reasoning or add examples",
            PerformanceMetric.RETRY_COUNT: "Fix root causes in output validation"
        }
        
        base_fix = fixes.get(metric_type, "Investigate and fix")
        
        if severity == "critical":
            return f"URGENT: {base_fix}"
        elif severity == "high":
            return f"Priority: {base_fix}"
        else:
            return base_fix
    
    def _would_cross_threshold(self, metric_type: PerformanceMetric, current: float, forecast: float) -> bool:
        """Check if forecast crosses critical threshold."""
        thresholds = {
            PerformanceMetric.QUALITY_SCORE: 5.0,
            PerformanceMetric.SUCCESS_RATE: 0.70,
            PerformanceMetric.ERROR_COUNT: 5.0,
            PerformanceMetric.EXECUTION_TIME: 60.0
        }
        
        threshold = thresholds.get(metric_type)
        if not threshold:
            return False
        
        return (current >= threshold and forecast < threshold) or \
               (current < threshold and forecast >= threshold)


# Singleton instance management
_analytics_instance: Optional[PerformanceAnalytics] = None


def get_performance_analytics() -> PerformanceAnalytics:
    """Get or create the singleton PerformanceAnalytics instance."""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = PerformanceAnalytics()
    return _analytics_instance
