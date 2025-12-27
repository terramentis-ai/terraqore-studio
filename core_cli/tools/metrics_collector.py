"""
Metrics Collection Pipeline

Collects execution metrics from agents and stores them for analysis.
Provides interfaces for real-time monitoring and performance analytics.

Phase 5.2 Component - Used by PerformanceAnalytics and learning system.
"""

import time
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import logging

from core.state import StateManager

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics to collect."""
    EXECUTION_TIME = "execution_time"
    QUALITY_SCORE = "quality_score"
    TOKEN_USAGE = "token_usage"
    COST = "cost"
    SUCCESS_RATE = "success_rate"
    VALIDATION_RESULT = "validation_result"
    FEEDBACK_COUNT = "feedback_count"
    GATE_DECISION = "gate_decision"


class MetricSeverity(Enum):
    """Severity levels for metric anomalies."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


@dataclass
class ExecutionMetric:
    """Represents a single execution metric."""
    project_id: int
    agent_name: str
    task_type: str
    execution_time_ms: int
    success: bool
    quality_score: Optional[float] = None
    output_tokens: Optional[int] = None
    input_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class PerformanceSnapshot:
    """Snapshot of agent performance at a point in time."""
    agent_name: str
    date: str
    tasks_completed: int
    average_quality_score: float
    success_rate: float
    average_execution_time_ms: int
    total_cost_usd: float
    feedback_count: int = 0
    improvement_rate: float = 0.0
    trend_direction: str = "stable"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class MetricAlert:
    """Alert for metric anomalies."""
    metric_type: MetricType
    agent_name: str
    severity: MetricSeverity
    message: str
    expected_value: float
    actual_value: float
    threshold_exceeded: bool
    timestamp: str


class MetricsCollector:
    """
    Collects and stores execution metrics from all agents.
    
    Tracks:
    - Execution time per task
    - Quality scores
    - Token usage and costs
    - Success rates
    - Validation results
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self.state_manager = StateManager()
        self.metric_buffer: List[ExecutionMetric] = []
        self.buffer_size = 100  # Flush after this many metrics
        self.alerts: List[MetricAlert] = []
        self.alert_callbacks: List[Callable[[MetricAlert], None]] = []
    
    def record_execution(
        self,
        project_id: int,
        agent_name: str,
        task_type: str,
        execution_time_ms: int,
        success: bool,
        quality_score: Optional[float] = None,
        output_tokens: Optional[int] = None,
        input_tokens: Optional[int] = None,
        cost_usd: Optional[float] = None
    ) -> ExecutionMetric:
        """
        Record a single execution metric.
        
        Args:
            project_id: Project ID
            agent_name: Name of executing agent
            task_type: Type of task executed
            execution_time_ms: Execution time in milliseconds
            success: Whether execution succeeded
            quality_score: Quality score if available
            output_tokens: Output tokens used
            input_tokens: Input tokens used
            cost_usd: Cost in USD
        
        Returns:
            ExecutionMetric that was recorded
        """
        metric = ExecutionMetric(
            project_id=project_id,
            agent_name=agent_name,
            task_type=task_type,
            execution_time_ms=execution_time_ms,
            success=success,
            quality_score=quality_score,
            output_tokens=output_tokens,
            input_tokens=input_tokens,
            cost_usd=cost_usd
        )
        
        # Add to buffer
        self.metric_buffer.append(metric)
        
        # Check for anomalies
        self._check_anomalies(metric)
        
        # Flush if buffer is full
        if len(self.metric_buffer) >= self.buffer_size:
            self.flush_metrics()
        
        logger.debug(f"Recorded metric for {agent_name}: {task_type} ({execution_time_ms}ms)")
        return metric
    
    def flush_metrics(self) -> int:
        """
        Flush buffered metrics to database.
        
        Returns:
            Number of metrics flushed
        """
        if not self.metric_buffer:
            return 0
        
        try:
            conn = self.state_manager.get_db_connection()
            cursor = conn.cursor()
            
            for metric in self.metric_buffer:
                cursor.execute("""
                    INSERT INTO execution_metrics (
                        project_id, agent_name, task_type, execution_time_ms,
                        success, quality_score, output_tokens, input_tokens,
                        cost_usd, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric.project_id,
                    metric.agent_name,
                    metric.task_type,
                    metric.execution_time_ms,
                    metric.success,
                    metric.quality_score,
                    metric.output_tokens,
                    metric.input_tokens,
                    metric.cost_usd,
                    metric.timestamp
                ))
            
            conn.commit()
            count = len(self.metric_buffer)
            self.metric_buffer = []
            
            logger.info(f"Flushed {count} metrics to database")
            return count
        except Exception as e:
            logger.error(f"Error flushing metrics: {e}")
            return 0
    
    def get_agent_metrics(
        self,
        agent_name: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get aggregated metrics for an agent over a time period.
        
        Args:
            agent_name: Agent to get metrics for
            days: Number of days to look back
        
        Returns:
            Dictionary with aggregated metrics
        """
        try:
            conn = self.state_manager.get_db_connection()
            cursor = conn.cursor()
            
            from datetime import datetime, timedelta
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get metrics
            cursor.execute("""
                SELECT
                    COUNT(*) as task_count,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count,
                    AVG(execution_time_ms) as avg_execution_time,
                    AVG(quality_score) as avg_quality_score,
                    SUM(cost_usd) as total_cost,
                    MIN(execution_time_ms) as min_execution_time,
                    MAX(execution_time_ms) as max_execution_time,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(input_tokens) as total_input_tokens
                FROM execution_metrics
                WHERE agent_name = ? AND timestamp >= ?
            """, (agent_name, cutoff))
            
            row = cursor.fetchone()
            
            if row and row[0] > 0:
                task_count = row[0]
                success_count = row[1] or 0
                success_rate = success_count / task_count if task_count > 0 else 0
                
                return {
                    "agent_name": agent_name,
                    "period_days": days,
                    "task_count": task_count,
                    "success_count": success_count,
                    "success_rate": round(success_rate, 3),
                    "avg_execution_time_ms": round(row[2], 1) if row[2] else 0,
                    "avg_quality_score": round(row[3], 2) if row[3] else 0,
                    "total_cost_usd": round(row[4], 4) if row[4] else 0,
                    "min_execution_time_ms": row[5] or 0,
                    "max_execution_time_ms": row[6] or 0,
                    "total_output_tokens": row[7] or 0,
                    "total_input_tokens": row[8] or 0
                }
            else:
                return {
                    "agent_name": agent_name,
                    "period_days": days,
                    "task_count": 0,
                    "success_count": 0,
                    "success_rate": 0,
                    "avg_execution_time_ms": 0,
                    "avg_quality_score": 0,
                    "total_cost_usd": 0,
                    "min_execution_time_ms": 0,
                    "max_execution_time_ms": 0,
                    "total_output_tokens": 0,
                    "total_input_tokens": 0
                }
        except Exception as e:
            logger.error(f"Error getting agent metrics: {e}")
            return {}
    
    def get_project_metrics(self, project_id: int, days: int = 7) -> Dict[str, Any]:
        """
        Get aggregated metrics for a project over a time period.
        
        Args:
            project_id: Project to get metrics for
            days: Number of days to look back
        
        Returns:
            Dictionary with project-wide metrics
        """
        try:
            conn = self.state_manager.get_db_connection()
            cursor = conn.cursor()
            
            from datetime import datetime, timedelta
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get project-wide metrics
            cursor.execute("""
                SELECT
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_tasks,
                    AVG(execution_time_ms) as avg_execution_time,
                    AVG(quality_score) as avg_quality_score,
                    SUM(cost_usd) as total_cost,
                    COUNT(DISTINCT agent_name) as unique_agents
                FROM execution_metrics
                WHERE project_id = ? AND timestamp >= ?
            """, (project_id, cutoff))
            
            row = cursor.fetchone()
            
            if row and row[0] > 0:
                total = row[0]
                success = row[1] or 0
                
                return {
                    "project_id": project_id,
                    "period_days": days,
                    "total_tasks": total,
                    "successful_tasks": success,
                    "success_rate": round(success / total, 3) if total > 0 else 0,
                    "avg_execution_time_ms": round(row[2], 1) if row[2] else 0,
                    "avg_quality_score": round(row[3], 2) if row[3] else 0,
                    "total_cost_usd": round(row[4], 4) if row[4] else 0,
                    "unique_agents": row[5] or 0
                }
            else:
                return {
                    "project_id": project_id,
                    "period_days": days,
                    "total_tasks": 0,
                    "successful_tasks": 0,
                    "success_rate": 0,
                    "avg_execution_time_ms": 0,
                    "avg_quality_score": 0,
                    "total_cost_usd": 0,
                    "unique_agents": 0
                }
        except Exception as e:
            logger.error(f"Error getting project metrics: {e}")
            return {}
    
    def record_daily_snapshot(self, agent_name: str, snapshot: PerformanceSnapshot) -> bool:
        """
        Record a daily performance snapshot for an agent.
        
        Args:
            agent_name: Agent name
            snapshot: Performance snapshot
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.state_manager.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO agent_performance_history (
                    agent_name, date, tasks_completed, average_quality_score,
                    success_rate, average_execution_time_ms, total_cost_usd,
                    feedback_count, improvement_rate, trend_direction
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.agent_name,
                snapshot.date,
                snapshot.tasks_completed,
                snapshot.average_quality_score,
                snapshot.success_rate,
                snapshot.average_execution_time_ms,
                snapshot.total_cost_usd,
                snapshot.feedback_count,
                snapshot.improvement_rate,
                snapshot.trend_direction
            ))
            
            conn.commit()
            logger.info(f"Recorded daily snapshot for {agent_name}")
            return True
        except Exception as e:
            logger.error(f"Error recording daily snapshot: {e}")
            return False
    
    def get_performance_trend(self, agent_name: str, days: int = 30) -> Dict[str, Any]:
        """
        Get performance trend for an agent over time.
        
        Args:
            agent_name: Agent to analyze
            days: Number of days to look back
        
        Returns:
            Performance trend analysis
        """
        try:
            conn = self.state_manager.get_db_connection()
            cursor = conn.cursor()
            
            from datetime import datetime, timedelta
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute("""
                SELECT
                    date, average_quality_score, success_rate,
                    average_execution_time_ms, total_cost_usd, trend_direction
                FROM agent_performance_history
                WHERE agent_name = ? AND date >= ?
                ORDER BY date ASC
            """, (agent_name, cutoff[:10]))  # Date portion only
            
            rows = cursor.fetchall()
            
            if not rows:
                return {
                    "agent_name": agent_name,
                    "period_days": days,
                    "trend": "no_data",
                    "data_points": []
                }
            
            data_points = []
            for row in rows:
                data_points.append({
                    "date": row[0],
                    "quality_score": row[1],
                    "success_rate": row[2],
                    "execution_time_ms": row[3],
                    "cost_usd": row[4],
                    "trend": row[5]
                })
            
            # Calculate overall trend
            if len(data_points) > 1:
                first_quality = data_points[0]["quality_score"]
                last_quality = data_points[-1]["quality_score"]
                quality_change = last_quality - first_quality
                
                if quality_change > 0.1:
                    overall_trend = "improving"
                elif quality_change < -0.1:
                    overall_trend = "degrading"
                else:
                    overall_trend = "stable"
            else:
                overall_trend = "no_trend"
            
            return {
                "agent_name": agent_name,
                "period_days": days,
                "trend": overall_trend,
                "data_points": data_points,
                "sample_count": len(data_points)
            }
        except Exception as e:
            logger.error(f"Error getting performance trend: {e}")
            return {}
    
    def register_alert_callback(self, callback: Callable[[MetricAlert], None]):
        """
        Register a callback to be called when anomalies are detected.
        
        Args:
            callback: Function to call with MetricAlert
        """
        self.alert_callbacks.append(callback)
    
    def get_recent_alerts(self, limit: int = 10) -> List[MetricAlert]:
        """
        Get recent metric alerts.
        
        Args:
            limit: Maximum number of alerts to return
        
        Returns:
            List of recent alerts
        """
        return self.alerts[-limit:] if self.alerts else []
    
    # Private helper methods
    
    def _check_anomalies(self, metric: ExecutionMetric):
        """Check metric for anomalies."""
        # Check execution time
        if metric.execution_time_ms > 10000:  # 10 seconds
            self._create_alert(
                MetricType.EXECUTION_TIME,
                metric.agent_name,
                MetricSeverity.WARNING,
                f"Execution time {metric.execution_time_ms}ms exceeds threshold",
                5000,
                metric.execution_time_ms
            )
        
        # Check quality score
        if metric.quality_score is not None and metric.quality_score < 5.0:
            self._create_alert(
                MetricType.QUALITY_SCORE,
                metric.agent_name,
                MetricSeverity.WARNING,
                f"Quality score {metric.quality_score} below threshold",
                6.0,
                metric.quality_score
            )
        
        # Check cost
        if metric.cost_usd is not None and metric.cost_usd > 0.50:
            self._create_alert(
                MetricType.COST,
                metric.agent_name,
                MetricSeverity.INFO,
                f"High cost detected: ${metric.cost_usd:.2f}",
                0.10,
                metric.cost_usd
            )
        
        # Check failure
        if not metric.success:
            self._create_alert(
                MetricType.VALIDATION_RESULT,
                metric.agent_name,
                MetricSeverity.WARNING,
                f"Task execution failed for {metric.task_type}",
                1.0,
                0.0
            )
    
    def _create_alert(
        self,
        metric_type: MetricType,
        agent_name: str,
        severity: MetricSeverity,
        message: str,
        expected: float,
        actual: float
    ):
        """Create and notify of an alert."""
        alert = MetricAlert(
            metric_type=metric_type,
            agent_name=agent_name,
            severity=severity,
            message=message,
            expected_value=expected,
            actual_value=actual,
            threshold_exceeded=actual > expected or actual == 0,
            timestamp=datetime.now().isoformat()
        )
        
        self.alerts.append(alert)
        
        # Call registered callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")


# Singleton instance management
_collector_instance: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the singleton MetricsCollector instance."""
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = MetricsCollector()
    return _collector_instance
