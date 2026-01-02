"""
Metrics API Router
Provides REST endpoints for accessing execution metrics and benchmarking data.
Integrates with StateManager to expose performance analytics.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.state import get_state_manager

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


# Pydantic models for API responses
class ExecutionMetricResponse(BaseModel):
    """Single execution metric record."""
    id: int
    project_id: int
    agent_name: str
    task_type: str
    execution_time_ms: float
    success: bool
    quality_score: Optional[float] = None
    output_tokens: Optional[int] = None
    input_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    timestamp: str


class AgentMetricSummary(BaseModel):
    """Summary metrics for a single agent."""
    agent_name: str
    execution_count: int
    avg_execution_time_ms: float
    success_count: int
    success_rate: float
    avg_quality_score: Optional[float] = None


class MetricsSummary(BaseModel):
    """Overall metrics summary for a project."""
    total_executions: int
    total_execution_time_ms: float
    avg_execution_time_ms: float
    successful_executions: int
    success_rate: float
    avg_quality_score: float
    total_cost_usd: float
    metrics_by_agent: List[AgentMetricSummary]


class MetricsResponse(BaseModel):
    """Response wrapper for metrics queries."""
    data: Any
    count: int = 0
    timestamp: str


@router.get("/health", tags=["health"])
async def health_check():
    """Check metrics API health.
    
    Returns:
        Health status.
    """
    return {
        "status": "healthy",
        "service": "metrics",
        "version": "1.0"
    }


@router.get("/summary/{project_id}")
async def get_metrics_summary(project_id: int) -> Dict[str, Any]:
    """Get aggregate metrics summary for a project.
    
    Args:
        project_id: Project ID.
        
    Returns:
        Metrics summary with per-agent breakdowns.
        
    Raises:
        HTTPException: If project not found or metrics unavailable.
    """
    try:
        state_manager = get_state_manager()
        
        # Verify project exists
        project = state_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get summary metrics
        summary = state_manager.get_execution_metrics_summary(project_id)
        
        return {
            "project_id": project_id,
            "project_name": project.name,
            "metrics": summary
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")


@router.get("/executions/{project_id}")
async def get_execution_metrics(
    project_id: int,
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    order_by: str = Query("DESC", description="Sort order (ASC or DESC)")
) -> Dict[str, Any]:
    """Get execution metrics for a project.
    
    Args:
        project_id: Project ID.
        agent_name: Optional filter by agent name.
        limit: Maximum number of records to return.
        order_by: Sort order (ASC or DESC).
        
    Returns:
        List of execution metrics.
        
    Raises:
        HTTPException: If project not found or query fails.
    """
    try:
        state_manager = get_state_manager()
        
        # Verify project exists
        project = state_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Normalize order_by
        if order_by.upper() not in ("ASC", "DESC"):
            order_by = "DESC"
        
        # Get metrics
        metrics = state_manager.get_execution_metrics(
            project_id=project_id,
            agent_name=agent_name,
            limit=limit,
            order_by=order_by
        )
        
        return {
            "project_id": project_id,
            "project_name": project.name,
            "agent_filter": agent_name,
            "count": len(metrics),
            "metrics": metrics
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")


@router.get("/agents/{project_id}")
async def get_agent_performance(
    project_id: int,
    min_executions: int = Query(1, ge=1, description="Minimum execution count")
) -> Dict[str, Any]:
    """Get per-agent performance metrics.
    
    Args:
        project_id: Project ID.
        min_executions: Minimum number of executions to include.
        
    Returns:
        Agent performance breakdown.
        
    Raises:
        HTTPException: If project not found or query fails.
    """
    try:
        state_manager = get_state_manager()
        
        # Verify project exists
        project = state_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get summary and filter agents
        summary = state_manager.get_execution_metrics_summary(project_id)
        
        # Filter by minimum executions
        filtered_agents = [
            agent for agent in summary["metrics_by_agent"]
            if agent["execution_count"] >= min_executions
        ]
        
        # Sort by execution count descending
        filtered_agents.sort(key=lambda x: x["execution_count"], reverse=True)
        
        return {
            "project_id": project_id,
            "project_name": project.name,
            "total_agents": len(filtered_agents),
            "agents": filtered_agents
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agent metrics: {str(e)}")


@router.get("/timeline/{project_id}")
async def get_execution_timeline(
    project_id: int,
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    hours: int = Query(24, ge=1, le=720, description="Last N hours")
) -> Dict[str, Any]:
    """Get execution timeline showing performance over time.
    
    Args:
        project_id: Project ID.
        agent_name: Optional filter by agent name.
        hours: Number of hours to include in timeline.
        
    Returns:
        Timeline of executions grouped by hour.
        
    Raises:
        HTTPException: If project not found or query fails.
    """
    try:
        state_manager = get_state_manager()
        
        # Verify project exists
        project = state_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get all metrics
        metrics = state_manager.get_execution_metrics(
            project_id=project_id,
            agent_name=agent_name,
            limit=10000,
            order_by="ASC"
        )
        
        # Group by hour
        timeline = {}
        for metric in metrics:
            # Parse timestamp (ISO format)
            timestamp = metric["timestamp"]
            hour_key = timestamp[:13]  # YYYY-MM-DDTHH format
            
            if hour_key not in timeline:
                timeline[hour_key] = {
                    "hour": hour_key,
                    "count": 0,
                    "successful": 0,
                    "failed": 0,
                    "avg_time_ms": 0.0,
                    "total_time_ms": 0.0,
                    "total_quality": 0.0
                }
            
            timeline[hour_key]["count"] += 1
            if metric["success"]:
                timeline[hour_key]["successful"] += 1
            else:
                timeline[hour_key]["failed"] += 1
            
            timeline[hour_key]["total_time_ms"] += metric["execution_time_ms"]
            if metric["quality_score"] is not None:
                timeline[hour_key]["total_quality"] += metric["quality_score"]
        
        # Calculate averages
        for hour_data in timeline.values():
            if hour_data["count"] > 0:
                hour_data["avg_time_ms"] = hour_data["total_time_ms"] / hour_data["count"]
                if hour_data["count"] > 0:
                    hour_data["avg_quality"] = hour_data["total_quality"] / hour_data["count"]
                else:
                    hour_data["avg_quality"] = 0.0
                del hour_data["total_time_ms"]
                del hour_data["total_quality"]
        
        # Return sorted timeline
        sorted_timeline = sorted(timeline.items(), key=lambda x: x[0])
        
        return {
            "project_id": project_id,
            "project_name": project.name,
            "agent_filter": agent_name,
            "hours": hours,
            "timeline": [hour_data for _, hour_data in sorted_timeline]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve timeline: {str(e)}")


@router.get("/comparison/{project_id}")
async def compare_agents(
    project_id: int,
    metric: str = Query("success_rate", description="Metric to compare (success_rate, avg_time, quality, count)")
) -> Dict[str, Any]:
    """Compare agent performance across selected metric.
    
    Args:
        project_id: Project ID.
        metric: Metric to compare (success_rate, avg_time, quality, count).
        
    Returns:
        Ranked comparison of agents.
        
    Raises:
        HTTPException: If project not found or invalid metric.
    """
    valid_metrics = ["success_rate", "avg_time", "quality", "count"]
    
    if metric not in valid_metrics:
        raise HTTPException(status_code=400, detail=f"Invalid metric. Must be one of: {valid_metrics}")
    
    try:
        state_manager = get_state_manager()
        
        # Verify project exists
        project = state_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get summary metrics
        summary = state_manager.get_execution_metrics_summary(project_id)
        agents = summary["metrics_by_agent"]
        
        # Sort by requested metric
        if metric == "success_rate":
            agents.sort(key=lambda x: x["success_rate"], reverse=True)
        elif metric == "avg_time":
            agents.sort(key=lambda x: x["avg_execution_time_ms"])
        elif metric == "quality":
            agents.sort(key=lambda x: x["avg_quality_score"] or 0, reverse=True)
        elif metric == "count":
            agents.sort(key=lambda x: x["execution_count"], reverse=True)
        
        # Add ranking
        for rank, agent in enumerate(agents, 1):
            agent["rank"] = rank
        
        return {
            "project_id": project_id,
            "project_name": project.name,
            "comparison_metric": metric,
            "agents": agents
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare agents: {str(e)}")


@router.post("/log")
async def log_metric(
    project_id: int,
    agent_name: str,
    task_type: str,
    execution_time_ms: float,
    success: bool,
    quality_score: Optional[float] = None,
    output_tokens: Optional[int] = None,
    input_tokens: Optional[int] = None,
    cost_usd: Optional[float] = None
) -> Dict[str, Any]:
    """Log an execution metric.
    
    Args:
        project_id: Project ID.
        agent_name: Name of executing agent.
        task_type: Type of task executed.
        execution_time_ms: Execution time in milliseconds.
        success: Whether execution succeeded.
        quality_score: Optional quality score (0-10).
        output_tokens: Optional output token count.
        input_tokens: Optional input token count.
        cost_usd: Optional cost in USD.
        
    Returns:
        Created metric record.
        
    Raises:
        HTTPException: If logging fails.
    """
    try:
        state_manager = get_state_manager()
        
        # Log metric
        metric_id = state_manager.log_execution_metric(
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
        
        return {
            "metric_id": metric_id,
            "project_id": project_id,
            "agent_name": agent_name,
            "task_type": task_type,
            "execution_time_ms": execution_time_ms,
            "success": success,
            "status": "logged"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log metric: {str(e)}")
