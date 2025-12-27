"""
TerraQore Agent Monitoring System
Tracks agent health, performance metrics, and generates insights.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Agent health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class ExecutionMetric:
    """Single execution metric."""
    agent_name: str
    execution_time_ms: float
    success: bool
    quality_score: float  # 0-10
    timestamp: datetime = field(default_factory=datetime.now)
    output_tokens: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentHealthMetrics:
    """Aggregated metrics for an agent."""
    agent_name: str
    status: HealthStatus
    success_rate: float          # 0-1
    avg_execution_time_ms: float
    avg_quality_score: float     # 0-10
    error_rate: float            # 0-1
    last_execution: Optional[datetime] = None
    consecutive_failures: int = 0
    total_executions: int = 0
    total_failures: int = 0
    uptime_percent: float = 100.0


class AgentMonitor:
    """Monitors agent performance and health."""
    
    def __init__(self, health_window_minutes: int = 60):
        """Initialize agent monitor.
        
        Args:
            health_window_minutes: Time window for health calculation.
        """
        self.health_window = timedelta(minutes=health_window_minutes)
        self.metrics: Dict[str, List[ExecutionMetric]] = defaultdict(list)
        self.max_metrics_per_agent = 10000  # Keep last N metrics
        self.agent_status_changed_callbacks = []
    
    def track_execution(self, metric: ExecutionMetric) -> None:
        """Track an agent execution.
        
        Args:
            metric: Execution metric to track.
        """
        agent_name = metric.agent_name
        self.metrics[agent_name].append(metric)
        
        # Trim old metrics to prevent memory overflow
        if len(self.metrics[agent_name]) > self.max_metrics_per_agent:
            self.metrics[agent_name] = self.metrics[agent_name][-self.max_metrics_per_agent:]
        
        logger.debug(
            f"Tracked execution for {agent_name}: "
            f"success={metric.success}, time={metric.execution_time_ms}ms, "
            f"quality={metric.quality_score}"
        )
    
    def get_health_status(self, agent_name: str) -> HealthStatus:
        """Get current health status of an agent.
        
        Args:
            agent_name: Agent to check.
            
        Returns:
            HealthStatus enum.
        """
        metrics = self.get_recent_metrics(agent_name)
        if not metrics:
            return HealthStatus.OFFLINE
        
        health = self.get_agent_metrics(agent_name)
        
        # Determine status based on metrics
        if health.success_rate < 0.5 or health.error_rate > 0.5:
            return HealthStatus.UNHEALTHY
        elif health.success_rate < 0.8 or health.error_rate > 0.2:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def get_agent_metrics(self, agent_name: str) -> AgentHealthMetrics:
        """Get aggregated metrics for an agent.
        
        Args:
            agent_name: Agent name.
            
        Returns:
            Aggregated health metrics.
        """
        metrics = self.get_recent_metrics(agent_name)
        
        if not metrics:
            return AgentHealthMetrics(
                agent_name=agent_name,
                status=HealthStatus.OFFLINE,
                success_rate=0.0,
                avg_execution_time_ms=0.0,
                avg_quality_score=0.0,
                error_rate=1.0,
                total_executions=0,
                total_failures=0
            )
        
        # Calculate metrics
        successful = [m for m in metrics if m.success]
        failed = [m for m in metrics if not m.success]
        success_rate = len(successful) / len(metrics) if metrics else 0.0
        error_rate = 1.0 - success_rate
        
        execution_times = [m.execution_time_ms for m in successful] if successful else [0]
        quality_scores = [m.quality_score for m in successful] if successful else [0]
        
        # Count consecutive failures
        consecutive_failures = 0
        for metric in reversed(metrics):
            if not metric.success:
                consecutive_failures += 1
            else:
                break
        
        return AgentHealthMetrics(
            agent_name=agent_name,
            status=self.get_health_status(agent_name),
            success_rate=success_rate,
            avg_execution_time_ms=statistics.mean(execution_times) if execution_times else 0.0,
            avg_quality_score=statistics.mean(quality_scores) if quality_scores else 0.0,
            error_rate=error_rate,
            last_execution=metrics[-1].timestamp if metrics else None,
            consecutive_failures=consecutive_failures,
            total_executions=len(metrics),
            total_failures=len(failed)
        )
    
    def get_recent_metrics(
        self,
        agent_name: str,
        minutes: Optional[int] = None
    ) -> List[ExecutionMetric]:
        """Get recent metrics for an agent.
        
        Args:
            agent_name: Agent name.
            minutes: Optional time window in minutes. Uses default if None.
            
        Returns:
            List of recent metrics.
        """
        all_metrics = self.metrics.get(agent_name, [])
        if not all_metrics:
            return []
        
        if minutes is None:
            window = self.health_window
        else:
            window = timedelta(minutes=minutes)
        
        cutoff_time = datetime.now() - window
        return [m for m in all_metrics if m.timestamp >= cutoff_time]
    
    def get_performance_trends(
        self,
        agent_name: str,
        bucket_minutes: int = 5
    ) -> Dict[str, Any]:
        """Get performance trends over time.
        
        Args:
            agent_name: Agent name.
            bucket_minutes: Size of time buckets.
            
        Returns:
            Trends by metric.
        """
        metrics = self.get_recent_metrics(agent_name)
        if not metrics:
            return {}
        
        # Group metrics into time buckets
        buckets: Dict[int, List[ExecutionMetric]] = defaultdict(list)
        for metric in metrics:
            bucket_index = int(metric.timestamp.timestamp() / (bucket_minutes * 60))
            buckets[bucket_index].append(metric)
        
        # Calculate trend for each bucket
        trends = []
        for bucket_index in sorted(buckets.keys()):
            bucket_metrics = buckets[bucket_index]
            successful = [m for m in bucket_metrics if m.success]
            
            trends.append({
                "timestamp": min(m.timestamp for m in bucket_metrics),
                "success_rate": len(successful) / len(bucket_metrics) if bucket_metrics else 0.0,
                "avg_execution_time_ms": statistics.mean(
                    [m.execution_time_ms for m in bucket_metrics]
                ) if bucket_metrics else 0.0,
                "avg_quality_score": statistics.mean(
                    [m.quality_score for m in successful]
                ) if successful else 0.0,
                "count": len(bucket_metrics)
            })
        
        return {
            "agent_name": agent_name,
            "bucket_minutes": bucket_minutes,
            "trends": trends
        }
    
    def get_all_agent_status(self) -> Dict[str, AgentHealthMetrics]:
        """Get health status for all monitored agents.
        
        Returns:
            Dictionary of agent name to health metrics.
        """
        return {
            agent_name: self.get_agent_metrics(agent_name)
            for agent_name in self.metrics.keys()
        }
    
    def get_slowest_agents(self, top_n: int = 5) -> List[tuple[str, float]]:
        """Get slowest agents by average execution time.
        
        Args:
            top_n: Number of agents to return.
            
        Returns:
            List of (agent_name, avg_time_ms) tuples.
        """
        all_metrics = self.get_all_agent_status()
        sorted_agents = sorted(
            all_metrics.items(),
            key=lambda x: x[1].avg_execution_time_ms,
            reverse=True
        )
        return [(name, metrics.avg_execution_time_ms) for name, metrics in sorted_agents[:top_n]]
    
    def get_least_reliable_agents(self, top_n: int = 5) -> List[tuple[str, float]]:
        """Get agents with lowest success rates.
        
        Args:
            top_n: Number of agents to return.
            
        Returns:
            List of (agent_name, success_rate) tuples.
        """
        all_metrics = self.get_all_agent_status()
        sorted_agents = sorted(
            all_metrics.items(),
            key=lambda x: x[1].success_rate
        )
        return [(name, metrics.success_rate) for name, metrics in sorted_agents[:top_n]]
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring summary.
        
        Returns:
            Summary of all agents and system health.
        """
        all_metrics = self.get_all_agent_status()
        
        # Count agents by status
        status_counts = defaultdict(int)
        for metrics in all_metrics.values():
            status_counts[metrics.status.value] += 1
        
        # Calculate overall statistics
        success_rates = [m.success_rate for m in all_metrics.values()]
        execution_times = [m.avg_execution_time_ms for m in all_metrics.values()]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(all_metrics),
            "agent_count_by_status": dict(status_counts),
            "overall_success_rate": statistics.mean(success_rates) if success_rates else 0.0,
            "overall_avg_execution_time_ms": statistics.mean(execution_times) if execution_times else 0.0,
            "slowest_agents": self.get_slowest_agents(5),
            "least_reliable_agents": self.get_least_reliable_agents(5),
            "agents": {
                name: {
                    "status": metrics.status.value,
                    "success_rate": metrics.success_rate,
                    "avg_execution_time_ms": metrics.avg_execution_time_ms,
                    "avg_quality_score": metrics.avg_quality_score,
                    "error_rate": metrics.error_rate,
                    "total_executions": metrics.total_executions,
                    "last_execution": metrics.last_execution.isoformat() if metrics.last_execution else None
                }
                for name, metrics in all_metrics.items()
            }
        }
    
    def reset_metrics(self, agent_name: Optional[str] = None) -> None:
        """Reset metrics for an agent or all agents.
        
        Args:
            agent_name: Optional agent name. If None, resets all.
        """
        if agent_name is None:
            self.metrics.clear()
            logger.info("Reset all agent metrics")
        else:
            if agent_name in self.metrics:
                self.metrics[agent_name].clear()
                logger.info(f"Reset metrics for agent: {agent_name}")


# Global monitor instance
_agent_monitor: Optional[AgentMonitor] = None


def get_agent_monitor() -> AgentMonitor:
    """Get or create the global agent monitor.
    
    Returns:
        AgentMonitor singleton instance.
    """
    global _agent_monitor
    if _agent_monitor is None:
        _agent_monitor = AgentMonitor()
    return _agent_monitor
