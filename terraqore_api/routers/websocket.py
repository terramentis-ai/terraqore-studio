"""
WebSocket Router for Real-time Updates
Provides WebSocket endpoints for streaming agent progress and workflow status
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import sys
import os

# Add core_cli to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'core_cli'))

from core.websocket_manager import get_websocket_manager, MessageType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ws", tags=["websocket"])

websocket_manager = get_websocket_manager()


@router.websocket("/projects/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: str
):
    """
    WebSocket endpoint for project-specific real-time updates.
    
    Connect to receive live updates for:
    - Agent start/progress/completion
    - Workflow start/completion
    - Metric updates
    - Errors and notifications
    
    Args:
        websocket: WebSocket connection
        project_id: ID of the project to monitor
    """
    await websocket.accept()
    
    # Register connection with manager
    try:
        websocket_manager.connect(websocket, project_id)
        logger.info(f"WebSocket connected for project {project_id}")
        
        # Send welcome message
        await websocket.send_json({
            "type": "connection_established",
            "project_id": project_id,
            "timestamp": websocket_manager._get_timestamp()
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_json()
                
                # Handle ping messages
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": websocket_manager._get_timestamp()
                    })
                
                # Handle subscription changes
                elif data.get("type") == "subscribe":
                    # Client wants to subscribe to specific message types
                    message_types = data.get("message_types", [])
                    logger.info(f"Client subscribed to types: {message_types}")
                    await websocket.send_json({
                        "type": "subscription_confirmed",
                        "message_types": message_types
                    })
                
                # Echo other messages back for debugging
                else:
                    logger.debug(f"Received message: {data}")
                    
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for project {project_id}")
        websocket_manager.disconnect(websocket)
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        websocket_manager.disconnect(websocket)
        try:
            await websocket.close()
        except:
            pass


@router.get("/stats")
async def websocket_stats():
    """
    Get WebSocket connection statistics.
    
    Returns:
        Dictionary with connection statistics
    """
    manager = get_websocket_manager()
    
    stats = {
        "total_connections": len(manager.active_connections),
        "projects_monitored": len(manager.project_connections),
        "project_details": {}
    }
    
    # Get connection count per project
    for project_id, connections in manager.project_connections.items():
        stats["project_details"][project_id] = {
            "connection_count": len(connections),
            "has_active_connections": len(connections) > 0
        }
    
    return stats


# Example endpoint to test WebSocket broadcasts
@router.post("/test/broadcast/{project_id}")
async def test_broadcast(
    project_id: str,
    message_type: str = Query("test", description="Type of test message"),
    agent_name: str = Query("TestAgent", description="Agent name for test")
):
    """
    Test endpoint to broadcast messages to WebSocket clients.
    
    Args:
        project_id: Project ID to broadcast to
        message_type: Type of message to send
        agent_name: Agent name for the test message
        
    Returns:
        Status of broadcast
    """
    manager = get_websocket_manager()
    
    try:
        if message_type == "agent_start":
            await manager.broadcast_agent_start(
                project_id=project_id,
                agent_name=agent_name,
                task_description="Test task description"
            )
        
        elif message_type == "agent_progress":
            await manager.broadcast_agent_progress(
                project_id=project_id,
                agent_name=agent_name,
                progress_percent=50,
                current_step="Processing data",
                details={"test": True}
            )
        
        elif message_type == "agent_complete":
            await manager.broadcast_agent_complete(
                project_id=project_id,
                agent_name=agent_name,
                success=True,
                output="Test output",
                execution_time_ms=1500
            )
        
        elif message_type == "workflow_start":
            await manager.broadcast_workflow_start(
                project_id=project_id,
                workflow_name="Test Workflow",
                total_phases=5
            )
        
        elif message_type == "workflow_complete":
            await manager.broadcast_workflow_complete(
                project_id=project_id,
                workflow_name="Test Workflow",
                success=True,
                total_time_ms=10000
            )
        
        elif message_type == "metric_update":
            await manager.broadcast_metric_update(
                project_id=project_id,
                metric_name="test_metric",
                value=42,
                unit="operations"
            )
        
        elif message_type == "error":
            await manager.broadcast_error(
                project_id=project_id,
                agent_name=agent_name,
                error_message="Test error message",
                error_type="TestError"
            )
        
        else:
            return {
                "success": False,
                "message": f"Unknown message type: {message_type}"
            }
        
        return {
            "success": True,
            "message": f"Broadcast {message_type} to project {project_id}",
            "connections_notified": len(manager.project_connections.get(project_id, []))
        }
    
    except Exception as e:
        logger.error(f"Error in test broadcast: {e}")
        return {
            "success": False,
            "message": str(e)
        }
