"""
FastAPI endpoints for TerraQore Studio Frontend Integration

Add these endpoints to your FastAPI main application to enable frontend communication.
"""

from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Generator, Dict, Any
import json
import os
import logging
from datetime import datetime
from core.state import StateManager
from core.llm_client import LLMClient, create_llm_client_from_config
from core.collaboration_state import CollaborationStateManager
from core.monitoring import get_agent_monitor, HealthStatus
from core.error_handler import get_error_recovery_manager
from orchestration.executor import Executor
from core.config import get_config_manager

logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS
# ============================================================================

class ProjectCreate(BaseModel):
    name: str
    description: str

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class WorkflowNode(BaseModel):
    id: str
    type: str
    data: dict
    position: dict

class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    data: Optional[dict] = None

class WorkflowSave(BaseModel):
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]

class CopilotMessage(BaseModel):
    message: str

class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    llm_health: Dict[str, Any]
    agents: Dict[str, Any]
    error_recovery: Dict[str, Any]
    system: Dict[str, Any]


class LLMConfigUpdate(BaseModel):
    """Payload for updating LLM configuration from the frontend."""
    primary_provider: str
    model: str
    api_key: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    fallback_provider: Optional[str] = None
    fallback_model: Optional[str] = None
    fallback_api_key: Optional[str] = None
    fallback_temperature: Optional[float] = 0.7
    fallback_max_tokens: Optional[int] = 4096

class CopilotContext(BaseModel):
    workflow: Optional[dict] = None
    project_context: Optional[dict] = None

class ChatRequest(BaseModel):
    """Request for LLM chat completion."""
    prompt: str
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class TaskPlanRequest(BaseModel):
    """Request for task planning."""
    user_input: str

class AgentExecutionRequest(BaseModel):
    """Request for agent task execution."""
    agent_type: str
    task_description: str
    context: Optional[str] = None

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_state_manager() -> StateManager:
    """Get the state manager instance."""
    return StateManager()

def get_llm_client() -> LLMClient:
    """Get the LLM client instance."""
    # Build LLM client from configured providers
    try:
        config = get_config_manager().load()
        return create_llm_client_from_config(config)
    except Exception:
        # Fallback: re-raise to make the error visible to startup logs
        raise

def get_executor() -> Executor:
    """Get the executor instance."""
    return Executor()

# ============================================================================
# PROJECT ENDPOINTS
# ============================================================================

def setup_project_routes(app: FastAPI):
    """
    Setup project management routes.
    
    Usage:
        app = FastAPI()
        setup_project_routes(app)
    """
    state_manager = get_state_manager()
    
    @app.get("/api/projects")
    async def list_projects():
        """List all projects."""
        try:
            projects = state_manager.list_projects()
            return projects
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/projects")
    async def create_project(project: ProjectCreate):
        """Create a new project."""
        try:
            new_project = state_manager.create_project(
                name=project.name,
                description=project.description
            )
            return new_project
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/projects/{project_id}")
    async def get_project(project_id: str):
        """Get project details."""
        try:
            project = state_manager.get_project(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            return project
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.put("/api/projects/{project_id}")
    async def update_project(project_id: str, updates: ProjectUpdate):
        """Update project."""
        try:
            project = state_manager.update_project(project_id, updates.dict(exclude_unset=True))
            return project
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/api/projects/{project_id}")
    async def delete_project(project_id: str):
        """Delete project."""
        try:
            state_manager.delete_project(project_id)
            return {"status": "deleted"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# WORKFLOW ENDPOINTS
# ============================================================================

def setup_workflow_routes(app: FastAPI):
    """Setup workflow management routes."""
    state_manager = get_state_manager()
    
    @app.get("/api/projects/{project_id}/workflow")
    async def get_workflow(project_id: str):
        """Get project workflow."""
        try:
            workflow = state_manager.get_workflow(project_id)
            return workflow or {"nodes": [], "edges": []}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/projects/{project_id}/workflow")
    async def save_workflow(project_id: str, workflow: WorkflowSave):
        """Save project workflow."""
        try:
            saved = state_manager.save_workflow(
                project_id,
                {
                    "nodes": [node.dict() for node in workflow.nodes],
                    "edges": [edge.dict() for edge in workflow.edges]
                }
            )
            return saved
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# EXECUTION ENDPOINTS
# ============================================================================

def setup_execution_routes(app: FastAPI):
    """Setup workflow execution routes."""
    executor = get_executor()
    
    @app.post("/api/projects/{project_id}/execute")
    async def execute_workflow(project_id: str):
        """Execute workflow."""
        try:
            execution_id = await executor.execute_workflow(project_id)
            return {"execution_id": execution_id, "status": "started"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/projects/{project_id}/executions/{execution_id}")
    async def get_execution_status(project_id: str, execution_id: str):
        """Get execution status."""
        try:
            status = await executor.get_execution_status(execution_id)
            return status
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# CO-PILOT ENDPOINTS
# ============================================================================

def setup_copilot_routes(app: FastAPI):
    """Setup co-pilot AI assistant routes."""
    llm_client = get_llm_client()
    
    @app.post("/api/projects/{project_id}/copilot")
    async def send_copilot_message(project_id: str, message: CopilotMessage):
        """Send message to co-pilot and get response."""
        try:
            response = await llm_client.generate_response(
                prompt=message.message,
                context={
                    "project_id": project_id,
                    "task": "assist_with_workflow_design"
                }
            )
            
            return {
                "response": response,
                "suggestions": extract_suggestions(response)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/projects/{project_id}/copilot/suggestions")
    async def get_copilot_suggestions(project_id: str, context: CopilotContext):
        """Get AI suggestions based on workflow context."""
        try:
            suggestions = await llm_client.generate_suggestions(
                context=context.dict(),
                project_id=project_id
            )
            return {"suggestions": suggestions}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/projects/{project_id}/copilot/stream")
    async def stream_copilot_response(project_id: str, message: str):
        """Stream co-pilot response."""
        async def generate():
            try:
                async for chunk in llm_client.stream_response(message, project_id):
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")

# ============================================================================
# AGENT ENDPOINTS
# ============================================================================

def setup_agent_routes(app: FastAPI):
    """Setup agent information routes."""
    
    @app.get("/api/agents")
    async def list_agents():
        """List available agents."""
        agents = [
            {
                "id": "idea",
                "name": "Idea Agent",
                "description": "Research and brainstorming",
                "icon": "SmartToyIcon",
                "color": "#8b5cf6"
            },
            {
                "id": "coder",
                "name": "Coder Agent",
                "description": "Code generation and architecture",
                "icon": "CodeIcon",
                "color": "#6366f1"
            },
            {
                "id": "data_science",
                "name": "Data Science Agent",
                "description": "ML pipelines and experimentation",
                "icon": "StorageIcon",
                "color": "#10b981"
            },
            {
                "id": "security",
                "name": "Security Agent",
                "description": "Vulnerability scanning and compliance",
                "icon": "SecurityIcon",
                "color": "#ef4444"
            },
            {
                "id": "mlops",
                "name": "MLOps Agent",
                "description": "Pipeline orchestration and versioning",
                "icon": "BuildIcon",
                "color": "#06b6d4"
            },
            {
                "id": "validator",
                "name": "Validator Agent",
                "description": "Quality assurance and compliance",
                "icon": "AnalyticsIcon",
                "color": "#f59e0b"
            },
        ]
        return agents
    
    @app.get("/api/agents/{agent_id}")
    async def get_agent_details(agent_id: str):
        """Get detailed agent information."""
        # TODO: Implement based on actual agent details
        agents = await list_agents()
        agent = next((a for a in agents if a["id"] == agent_id), None)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent

# ============================================================================
# WEBSOCKET ENDPOINTS
# ============================================================================

def setup_websocket_routes(app: FastAPI):
    """Setup WebSocket routes for real-time updates."""
    
    @app.websocket("/api/ws/projects/{project_id}")
    async def websocket_project_updates(websocket: WebSocket, project_id: str):
        """WebSocket for real-time project updates."""
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                # Process data and send updates
                await websocket.send_json({"type": "ack", "message": data})
        except Exception as e:
            await websocket.close(code=1000)
    
    @app.websocket("/api/ws/executions/{execution_id}")
    async def websocket_execution_updates(websocket: WebSocket, execution_id: str):
        """WebSocket for real-time execution updates."""
        await websocket.accept()
        try:
            while True:
                # Stream execution updates
                status = {}  # Get from executor
                await websocket.send_json({"type": "status_update", "data": status})
        except Exception as e:
            await websocket.close(code=1000)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_suggestions(response: str) -> List[str]:
    """Extract suggestions from LLM response."""
    # Parse response for suggested actions
    suggestions = []
    lines = response.split('\n')
    for line in lines:
        if line.startswith('- ') or line.startswith('• '):
            suggestions.append(line[2:].strip())
    return suggestions[:3]  # Return top 3 suggestions

# ============================================================================
# INITIALIZATION FUNCTION
# ============================================================================

def setup_frontend_api(app: FastAPI):
    """
    Initialize all frontend API routes.
    
    Usage:
        from fastapi import FastAPI
        from frontend_api import setup_frontend_api
        
        app = FastAPI()
        setup_frontend_api(app)
    """
    state_manager = get_state_manager()
    llm_client = get_llm_client()
    executor = get_executor()

    @app.get("/api/llm/providers")
    async def list_llm_providers():
        """List supported LLM providers with basic metadata."""
        providers = [
            {"id": "gemini", "name": "Google Gemini", "requires_api_key": True, "default_model": "models/gemini-2.5-flash"},
            {"id": "groq", "name": "Groq", "requires_api_key": True, "default_model": "llama-3.1-70b-versatile"},
            {"id": "openrouter", "name": "OpenRouter", "requires_api_key": True, "default_model": "meta-llama/llama-3.1-70b-instruct"},
            {"id": "ollama", "name": "Ollama (local)", "requires_api_key": False, "default_model": "llama3.2"},
        ]
        return {"providers": providers}

    @app.get("/api/llm/config")
    async def get_llm_config():
        """Return current LLM configuration without exposing raw keys."""
        cfg_mgr = get_config_manager()
        cfg = cfg_mgr.load()
        llm_section = cfg_mgr.config_data.get("llm", {})

        primary_provider = cfg.primary_llm.provider
        primary_settings = llm_section.get(primary_provider, {})
        fallback_provider = llm_section.get("fallback_provider")
        fallback_settings = llm_section.get(fallback_provider, {}) if fallback_provider else {}

        return {
            "primary_provider": primary_provider,
            "primary_model": cfg.primary_llm.model,
            "primary_temperature": cfg.primary_llm.temperature,
            "primary_max_tokens": cfg.primary_llm.max_tokens,
            "primary_api_key_set": bool(primary_settings.get("api_key") or os.getenv(f"{primary_provider.upper()}_API_KEY")),
            "fallback_provider": fallback_provider,
            "fallback_model": cfg.fallback_llm.model if cfg.fallback_llm else None,
            "fallback_temperature": cfg.fallback_llm.temperature if cfg.fallback_llm else None,
            "fallback_max_tokens": cfg.fallback_llm.max_tokens if cfg.fallback_llm else None,
            "fallback_api_key_set": bool(fallback_settings.get("api_key") or (fallback_provider and os.getenv(f"{fallback_provider.upper()}_API_KEY")))
        }

    @app.post("/api/llm/config")
    async def update_llm_config(payload: LLMConfigUpdate):
        """Update LLM provider settings and refresh the in-memory client."""
        nonlocal llm_client

        supported = {"gemini", "groq", "openrouter", "ollama"}
        if payload.primary_provider not in supported:
            raise HTTPException(status_code=400, detail="Unsupported primary provider")
        if payload.fallback_provider and payload.fallback_provider not in supported:
            raise HTTPException(status_code=400, detail="Unsupported fallback provider")

        cfg_mgr = get_config_manager()

        default_models = {
            "gemini": "models/gemini-2.5-flash",
            "groq": "llama-3.1-70b-versatile",
            "openrouter": "meta-llama/llama-3.1-70b-instruct",
            "ollama": "phi3",
        }

        llm_updates: Dict[str, Any] = {
            "primary_provider": payload.primary_provider,
            payload.primary_provider: {
                "model": payload.model or default_models.get(payload.primary_provider),
                "temperature": payload.temperature,
                "max_tokens": payload.max_tokens,
            },
            "fallback_provider": payload.fallback_provider,
        }

        if payload.api_key:
            llm_updates[payload.primary_provider]["api_key"] = payload.api_key
            os.environ[f"{payload.primary_provider.upper()}_API_KEY"] = payload.api_key

        if payload.fallback_provider:
            llm_updates[payload.fallback_provider] = {
                "model": payload.fallback_model or default_models.get(payload.fallback_provider),
                "temperature": payload.fallback_temperature,
                "max_tokens": payload.fallback_max_tokens,
            }
            if payload.fallback_api_key:
                llm_updates[payload.fallback_provider]["api_key"] = payload.fallback_api_key
                os.environ[f"{payload.fallback_provider.upper()}_API_KEY"] = payload.fallback_api_key

        cfg_mgr.update({"llm": llm_updates})
        cfg = cfg_mgr.load()

        # Rebuild LLM client with new settings
        llm_client = create_llm_client_from_config(cfg)
        health = llm_client.health_check()

        return {"status": "ok", "llm_health": health}
    
    @app.post("/api/llm/chat")
    async def llm_chat(request: ChatRequest):
        """Generate LLM completion using the configured provider."""
        try:
            response = llm_client.generate(
                prompt=request.prompt,
                system_prompt=request.system_prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            if not response.success:
                raise HTTPException(status_code=500, detail=response.error or "LLM generation failed")
            
            return {
                "content": response.content,
                "provider": response.provider,
                "model": response.model,
                "usage": response.usage
            }
        except Exception as e:
            logger.error(f"LLM chat error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/llm/plan")
    async def plan_task(request: TaskPlanRequest):
        """Generate task breakdown plan using LLM."""
        try:
            system_prompt = """You are a Meta-Controller AI that breaks down complex tasks into sub-tasks for a multi-agent system.
            
Available agents:
            - Researcher: Gathers information, analyzes requirements, conducts research
            - Engineer: Implements solutions, writes code, handles technical execution
            - Data Analyst: Analyzes data, creates reports, handles data processing
            - Quality Assurance: Tests, validates, ensures quality standards
            
Respond ONLY with valid JSON in this exact format:
            {
              "objective": "clear statement of the main goal",
              "subtasks": [
                {
                  "agentType": "one of: Researcher, Engineer, Data Analyst, Quality Assurance",
                  "description": "specific task description",
                  "priority": 1
                }
              ]
            }"""
            
            prompt = f"""Break down this task into concrete sub-tasks:
            
User Task: {request.user_input}
            
Provide a JSON response with the objective and subtasks array."""
            
            response = llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7
            )
            
            if not response.success:
                raise HTTPException(status_code=500, detail=response.error or "Failed to generate plan")
            
            # Parse JSON response
            import json
            try:
                plan = json.loads(response.content)
                return plan
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', response.content)
                if json_match:
                    plan = json.loads(json_match.group(1))
                    return plan
                else:
                    # Return a fallback structure
                    return {
                        "objective": request.user_input,
                        "subtasks": [{
                            "agentType": "Engineer",
                            "description": request.user_input,
                            "priority": 1
                        }]
                    }
        except Exception as e:
            logger.error(f"Task planning error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/llm/execute")
    async def execute_agent_task(request: AgentExecutionRequest):
        """Execute a specific agent task using LLM."""
        try:
            system_prompt = f"""You are a {request.agent_type} agent in a multi-agent AI system.
            
Your role and responsibilities:
            - Researcher: Gather information, analyze requirements, provide research findings
            - Engineer: Implement solutions, write code, solve technical problems
            - Data Analyst: Analyze data, create insights, generate reports
            - Quality Assurance: Test solutions, validate outputs, ensure quality
            
Provide a concise, actionable response focused on completing the assigned task."""
            
            prompt = f"""Task: {request.task_description}
            
{f'Context from previous steps: {request.context}' if request.context else 'This is the first task in the workflow.'}
            
Provide your output and results."""
            
            response = llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7
            )
            
            if not response.success:
                raise HTTPException(status_code=500, detail=response.error or "Agent execution failed")
            
            return {
                "output": response.content,
                "agent_type": request.agent_type,
                "provider": response.provider,
                "model": response.model
            }
        except Exception as e:
            logger.error(f"Agent execution error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    # Setup health check endpoint
    @app.get("/health", response_model=HealthCheckResponse)
    async def health_check():
        """
        Comprehensive health check endpoint.
        Returns status of all system components.
        """
        # Get LLM health
        try:
            llm_health = llm_client.health_check()
        except Exception as e:
            llm_health = {"error": str(e), "available": False}
        
        # Get agent monitoring stats
        monitor = get_agent_monitor()
        agent_stats = monitor.get_monitoring_summary()
        
        # Get error recovery stats
        recovery_mgr = get_error_recovery_manager()
        error_stats = recovery_mgr.get_error_stats()
        
        # Overall status
        overall_status = "healthy"
        if not llm_health.get("primary", {}).get("success"):
            overall_status = "degraded"
        if agent_stats.get("agent_count_by_status", {}).get("unhealthy", 0) > 0:
            overall_status = "degraded"
        if error_stats.get("total_errors", 0) > 100:
            overall_status = "degraded"
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            llm_health=llm_health,
            agents=agent_stats,
            error_recovery=error_stats,
            system={
                "total_errors_recorded": len(recovery_mgr.error_history),
                "circuit_breaker_status": "monitoring"
            }
        )

    # Alias to match frontend base URL that includes /api
    @app.get("/api/health", response_model=HealthCheckResponse)
    async def health_check_api():
        return await health_check()
    
    @app.get("/health/agents")
    async def agents_health():
        """Get detailed health status for all agents."""
        monitor = get_agent_monitor()
        return monitor.get_monitoring_summary()
    
    @app.get("/health/agents/{agent_name}")
    async def agent_health(agent_name: str):
        """Get health status for a specific agent."""
        monitor = get_agent_monitor()
        metrics = monitor.get_agent_metrics(agent_name)
        return {
            "agent_name": metrics.agent_name,
            "status": metrics.status.value,
            "success_rate": metrics.success_rate,
            "avg_execution_time_ms": metrics.avg_execution_time_ms,
            "avg_quality_score": metrics.avg_quality_score,
            "error_rate": metrics.error_rate,
            "total_executions": metrics.total_executions,
            "last_execution": metrics.last_execution.isoformat() if metrics.last_execution else None
        }
    
    @app.get("/health/errors")
    async def errors_health():
        """Get error statistics and history."""
        recovery_mgr = get_error_recovery_manager()
        return {
            "stats": recovery_mgr.get_error_stats(),
            "recent_errors": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "error_type": e.error_type.value,
                    "severity": e.severity.value,
                    "message": e.message,
                    "agent_name": e.agent_name
                }
                for e in recovery_mgr.error_history[-10:]  # Last 10 errors
            ]
        }
    
    setup_project_routes(app)
    setup_workflow_routes(app)
    setup_execution_routes(app)
    setup_copilot_routes(app)
    setup_agent_routes(app)
    setup_websocket_routes(app)
