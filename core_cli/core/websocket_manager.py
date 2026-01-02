"""
WebSocket Manager for Real-Time Updates
Handles live streaming of agent progress and system metrics.
"""

import json
import asyncio
import logging
from typing import Dict, List, Callable, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types."""
    AGENT_START = "agent_start"
    AGENT_PROGRESS = "agent_progress"
    AGENT_COMPLETE = "agent_complete"
    AGENT_ERROR = "agent_error"
    WORKFLOW_START = "workflow_start"
    WORKFLOW_COMPLETE = "workflow_complete"
    METRIC_UPDATE = "metric_update"
    STATUS_UPDATE = "status_update"
    NOTIFICATION = "notification"


@dataclass
class WebSocketMessage:
    """A WebSocket message."""
    type: MessageType
    data: Dict[str, Any]
    timestamp: str = None
    project_id: int = None
    
    def __post_init__(self):
        """Set defaults."""
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "project_id": self.project_id
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> "WebSocketMessage":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls(
            type=MessageType[data.get("type", "").upper().replace("-", "_")],
            data=data.get("data", {}),
            timestamp=data.get("timestamp"),
            project_id=data.get("project_id")
        )


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        """Initialize WebSocket manager."""
        self.active_connections: Dict[int, Set] = {}  # project_id -> set of connections
        self.connection_metadata: Dict[Any, Dict[str, Any]] = {}  # connection -> metadata
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.callbacks: List[Callable] = []
    
    async def connect(self, websocket: Any, project_id: int) -> None:
        """Register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection object.
            project_id: Project ID for this connection.
        """
        await websocket.accept()
        
        if project_id not in self.active_connections:
            self.active_connections[project_id] = set()
        
        self.active_connections[project_id].add(websocket)
        self.connection_metadata[websocket] = {
            "project_id": project_id,
            "connected_at": datetime.now().isoformat(),
            "messages_received": 0,
            "messages_sent": 0
        }
        
        logger.info(f"WebSocket connected for project {project_id}. "
                   f"Total connections: {len(self.active_connections[project_id])}")
        
        # Send welcome message
        await self.send_message(
            WebSocketMessage(
                type=MessageType.STATUS_UPDATE,
                data={"status": "connected", "message": "Connected to TerraQore"},
                project_id=project_id
            ),
            websocket
        )
    
    async def disconnect(self, websocket: Any) -> None:
        """Unregister a WebSocket connection.
        
        Args:
            websocket: WebSocket connection object.
        """
        metadata = self.connection_metadata.get(websocket, {})
        project_id = metadata.get("project_id")
        
        if project_id and project_id in self.active_connections:
            self.active_connections[project_id].discard(websocket)
            
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
        
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        
        logger.info(f"WebSocket disconnected for project {project_id}")
    
    async def send_message(
        self,
        message: WebSocketMessage,
        websocket: Any = None
    ) -> None:
        """Send a message to one or more connections.
        
        Args:
            message: WebSocketMessage to send.
            websocket: Optional specific connection. If None, broadcast to project.
        """
        try:
            message_json = message.to_json()
            
            if websocket:
                # Send to specific connection
                await websocket.send_text(message_json)
                metadata = self.connection_metadata.get(websocket, {})
                metadata["messages_sent"] = metadata.get("messages_sent", 0) + 1
            else:
                # Broadcast to all connections for project
                if message.project_id in self.active_connections:
                    for conn in self.active_connections[message.project_id]:
                        try:
                            await conn.send_text(message_json)
                            metadata = self.connection_metadata.get(conn, {})
                            metadata["messages_sent"] = metadata.get("messages_sent", 0) + 1
                        except Exception as e:
                            logger.error(f"Error sending message to connection: {e}")
            
            # Call registered callbacks
            for callback in self.callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    logger.error(f"Error in WebSocket callback: {e}")
        
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
    
    async def broadcast_agent_start(
        self,
        project_id: int,
        agent_name: str,
        task_description: str
    ) -> None:
        """Broadcast agent start event.
        
        Args:
            project_id: Project ID.
            agent_name: Name of agent starting.
            task_description: Description of task.
        """
        message = WebSocketMessage(
            type=MessageType.AGENT_START,
            data={
                "agent_name": agent_name,
                "task_description": task_description,
                "status": "started"
            },
            project_id=project_id
        )
        await self.send_message(message)
    
    async def broadcast_agent_progress(
        self,
        project_id: int,
        agent_name: str,
        progress_percent: int,
        current_step: str,
        details: Dict[str, Any] = None
    ) -> None:
        """Broadcast agent progress update.
        
        Args:
            project_id: Project ID.
            agent_name: Name of agent.
            progress_percent: Progress percentage (0-100).
            current_step: Current step description.
            details: Optional additional details.
        """
        message = WebSocketMessage(
            type=MessageType.AGENT_PROGRESS,
            data={
                "agent_name": agent_name,
                "progress_percent": progress_percent,
                "current_step": current_step,
                "details": details or {}
            },
            project_id=project_id
        )
        await self.send_message(message)
    
    async def broadcast_agent_complete(
        self,
        project_id: int,
        agent_name: str,
        success: bool,
        output: str = None,
        execution_time_ms: float = None
    ) -> None:
        """Broadcast agent completion event.
        
        Args:
            project_id: Project ID.
            agent_name: Name of agent.
            success: Whether agent succeeded.
            output: Optional output from agent.
            execution_time_ms: Optional execution time.
        """
        message = WebSocketMessage(
            type=MessageType.AGENT_COMPLETE,
            data={
                "agent_name": agent_name,
                "success": success,
                "output": output or "",
                "execution_time_ms": execution_time_ms or 0
            },
            project_id=project_id
        )
        await self.send_message(message)
    
    async def broadcast_workflow_start(
        self,
        project_id: int,
        workflow_name: str,
        total_phases: int
    ) -> None:
        """Broadcast workflow start.
        
        Args:
            project_id: Project ID.
            workflow_name: Name of workflow.
            total_phases: Total number of phases.
        """
        message = WebSocketMessage(
            type=MessageType.WORKFLOW_START,
            data={
                "workflow_name": workflow_name,
                "total_phases": total_phases,
                "status": "started"
            },
            project_id=project_id
        )
        await self.send_message(message)
    
    async def broadcast_workflow_complete(
        self,
        project_id: int,
        workflow_name: str,
        success: bool,
        total_time_ms: float = None
    ) -> None:
        """Broadcast workflow completion.
        
        Args:
            project_id: Project ID.
            workflow_name: Name of workflow.
            success: Whether workflow succeeded.
            total_time_ms: Optional total execution time.
        """
        message = WebSocketMessage(
            type=MessageType.WORKFLOW_COMPLETE,
            data={
                "workflow_name": workflow_name,
                "success": success,
                "total_time_ms": total_time_ms or 0
            },
            project_id=project_id
        )
        await self.send_message(message)
    
    async def broadcast_metric_update(
        self,
        project_id: int,
        metric_name: str,
        value: Any,
        unit: str = None
    ) -> None:
        """Broadcast metric update.
        
        Args:
            project_id: Project ID.
            metric_name: Name of metric.
            value: Metric value.
            unit: Optional unit of measurement.
        """
        message = WebSocketMessage(
            type=MessageType.METRIC_UPDATE,
            data={
                "metric_name": metric_name,
                "value": value,
                "unit": unit or ""
            },
            project_id=project_id
        )
        await self.send_message(message)
    
    async def broadcast_error(
        self,
        project_id: int,
        agent_name: str,
        error_message: str,
        error_type: str = None
    ) -> None:
        """Broadcast error event.
        
        Args:
            project_id: Project ID.
            agent_name: Name of agent.
            error_message: Error description.
            error_type: Optional error type.
        """
        message = WebSocketMessage(
            type=MessageType.AGENT_ERROR,
            data={
                "agent_name": agent_name,
                "error_message": error_message,
                "error_type": error_type or "unknown"
            },
            project_id=project_id
        )
        await self.send_message(message)
    
    def get_connection_count(self, project_id: int = None) -> int:
        """Get count of active connections.
        
        Args:
            project_id: Optional project ID to filter.
            
        Returns:
            Number of active connections.
        """
        if project_id:
            return len(self.active_connections.get(project_id, set()))
        return sum(len(conns) for conns in self.active_connections.values())
    
    def get_connection_stats(self, project_id: int = None) -> Dict[str, Any]:
        """Get connection statistics.
        
        Args:
            project_id: Optional project ID to filter.
            
        Returns:
            Connection statistics.
        """
        total_connections = self.get_connection_count(project_id)
        
        messages_sent = 0
        messages_received = 0
        
        for conn, metadata in self.connection_metadata.items():
            if project_id is None or metadata.get("project_id") == project_id:
                messages_sent += metadata.get("messages_sent", 0)
                messages_received += metadata.get("messages_received", 0)
        
        return {
            "active_connections": total_connections,
            "total_messages_sent": messages_sent,
            "total_messages_received": messages_received,
            "project_id": project_id
        }
    
    def register_callback(self, callback: Callable) -> None:
        """Register a callback for all messages.
        
        Args:
            callback: Async or sync callable that receives WebSocketMessage.
        """
        self.callbacks.append(callback)
        logger.info(f"Registered WebSocket callback: {callback.__name__}")


# Global WebSocket manager instance
_ws_manager: WebSocketManager = None


def get_websocket_manager() -> WebSocketManager:
    """Get or create global WebSocket manager.
    
    Returns:
        WebSocketManager instance.
    """
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketManager()
    return _ws_manager
