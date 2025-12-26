"""
Execution Engine - Orchestrates task execution and code generation workflow.

Responsibilities:
- Task queue management
- Dependency resolution
- Progress tracking
- Human approval checkpoints
- Execution history
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

from core.state import StateManager
from agents.coder_agent import CoderAgent, CodeGeneration, CodeFile
from agents.base import AgentContext
from tools.file_ops import FileOperations
from tools.code_executor import CodeExecutor

logger = logging.getLogger(__name__)


@dataclass
class TaskExecution:
    """Record of a task execution."""
    task_id: int
    task_title: str
    status: str  # pending, in_progress, generated, approved, completed, failed, skipped
    generated_files: List[str]
    execution_notes: str
    errors: List[str]
    created_at: str
    completed_at: Optional[str]
    approved_by: Optional[str]
    approval_time: Optional[str]


class ExecutionEngine:
    """Orchestrates task execution and code generation."""
    
    def __init__(self, project_name: str, state_manager: StateManager, project_root: str, test_mode: bool = False):
        """
        Initialize execution engine.
        
        Args:
            project_name: Name of the project
            state_manager: State management instance
            project_root: Root directory of the project
            test_mode: If True, force deterministic stub generation (no LLM calls)
        """
        self.project_name = project_name
        self.state_manager = state_manager
        self.project_root = Path(project_root)
        
        # Initialize tools
        # Create LLM client from configuration for agents
        from core.config import get_config_manager
        from core.llm_client import create_llm_client_from_config

        config = get_config_manager().load()
        llm_client = create_llm_client_from_config(config)

        # Pass test_mode through to the coder agent
        self.coder_agent = CoderAgent(llm_client=llm_client, test_mode=test_mode)
        self.file_ops = FileOperations(str(self.project_root))
        self.code_executor = CodeExecutor(str(self.project_root))
        
        # Execution tracking
        self.task_executions: Dict[int, TaskExecution] = {}
        self.pending_approvals: Dict[int, CodeGeneration] = {}
        self.execution_log: List[Dict[str, Any]] = []
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Get list of pending tasks for the project."""
        try:
            tasks = self.state_manager.get_project_tasks(
                self.state_manager.get_project_id(self.project_name)
            )
            pending = [t for t in tasks if t.get("status") == "pending"]
            return pending
        except Exception as e:
            logger.error(f"Failed to get pending tasks: {str(e)}")
            return []
    
    def resolve_task_dependencies(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Check if task dependencies are satisfied.
        
        Returns:
            Tuple of (all_satisfied, unsatisfied_dependencies)
        """
        try:
            dependencies = task.get("dependencies", [])
            if not dependencies:
                return True, []
            
            tasks = self.state_manager.get_project_tasks(
                self.state_manager.get_project_id(self.project_name)
            )
            task_titles = {t["title"]: t for t in tasks}
            
            unsatisfied = []
            for dep in dependencies:
                dep_title = str(dep)
                dep_task = task_titles.get(dep_title)
                if not dep_task or dep_task.get("status") != "completed":
                    unsatisfied.append(dep_title)
            
            return len(unsatisfied) == 0, unsatisfied
            
        except Exception as e:
            logger.error(f"Failed to resolve dependencies: {str(e)}")
            return False, [str(d) for d in dependencies]
    
    def generate_code_for_task(self, task: Dict[str, Any]) -> Tuple[bool, Optional[CodeGeneration]]:
        """
        Generate code for a specific task.
        
        Args:
            task: Task dictionary from database
            
        Returns:
            Tuple of (success, CodeGeneration)
        """
        try:
            project_id = self.state_manager.get_project_id(self.project_name)

            # Mark as in progress
            self._mark_task_status(task["id"], "in_progress")
            
            # Prepare context for agent
            # Build AgentContext using the structure expected by BaseAgent
            context = AgentContext(
                project_id=project_id,
                project_name=self.project_name,
                project_description=task.get("description", ""),
                user_input=task.get("description", ""),
                metadata={
                    "task_id": task["id"],
                    "task_title": task["title"],
                    "priority": task.get("priority", 1),
                    "estimated_hours": task.get("estimated_hours", 4),
                    # Normalize dependencies to strings for safe prompting
                    "dependencies": [str(d) for d in task.get("dependencies", [])],
                    "milestone": task.get("milestone", "unknown"),
                    "language_hint": self._get_language_hint(task)
                }
            )
            
            # Generate code
            result = self.coder_agent.execute(context)
            
            if result.success:
                # Parse the code generation payload if present
                cg_payload = result.metadata.get("code_generation")
                if cg_payload:
                    files = []
                    for f in cg_payload.get("files", []) or []:
                        deps_raw = f.get("dependencies") or []
                        deps = [str(d) for d in deps_raw]
                        files.append(
                            CodeFile(
                                path=f.get("path", ""),
                                language=cg_payload.get("language", result.metadata.get("language", "python")),
                                content=f.get("content", ""),
                                description=f.get("description", ""),
                                test_code=f.get("test_code"),
                                dependencies=deps
                            )
                        )
                    code_gen = CodeGeneration(
                        task_id=task["id"],
                        task_title=task["title"],
                        language=cg_payload.get("language", result.metadata.get("language", "python")),
                        files=files,
                        summary=cg_payload.get("summary", result.output[:200] if result.output else "Code generated"),
                        execution_notes=cg_payload.get("execution_notes", ""),
                        validation_passed=cg_payload.get("validation_passed", result.metadata.get("validation_passed", False))
                    )
                else:
                    # Fallback when agent didn't include structured payload
                    code_gen = CodeGeneration(
                        task_id=task["id"],
                        task_title=task["title"],
                        language=result.metadata.get("language", "python"),
                        files=[],  # Would be populated from agent output
                        summary=result.output[:200] if result.output else "Code generated",
                        execution_notes="",
                        validation_passed=result.metadata.get("validation_passed", False)
                    )
                
                # Store pending approval
                self.pending_approvals[task["id"]] = code_gen
                self._mark_task_status(task["id"], "generated")
                
                self._log_execution("code_generated", task["id"], result.metadata)
                
                logger.info(f"Code generated for task: {task['title']}")
                return True, code_gen
            else:
                error_msg = f"Code generation failed: {result.output}"
                self._mark_task_status(task["id"], "failed")
                self._log_execution("code_generation_failed", task["id"], {"error": error_msg})
                
                logger.error(f"FAILED to generate code: {error_msg}")
                return False, None
                
        except Exception as e:
            error_msg = f"Error during code generation: {str(e)}"
            self._mark_task_status(task["id"], "failed")
            self._log_execution("execution_error", task["id"], {"error": error_msg})
            
            logger.error(error_msg)
            return False, None
    
    def approve_and_apply_code(
        self,
        task_id: int,
        approve: bool = True,
        approver: str = "user"
    ) -> Tuple[bool, str]:
        """
        Review, approve, and apply generated code.
        
        Args:
            task_id: ID of the task
            approve: Whether to apply the code
            approver: Name/ID of who approved
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if task_id not in self.pending_approvals:
                return False, f"No pending code for task {task_id}"
            
            code_gen = self.pending_approvals[task_id]
            
            if not approve:
                del self.pending_approvals[task_id]
                self._mark_task_status(task_id, "pending")
                self._log_execution("code_rejected", task_id, {"approver": approver})
                return True, f"Code rejected for task {task_id}"
            
            # Apply code files
            success_count = 0
            error_msgs = []
            
            for code_file in code_gen.files:
                success, msg = self.file_ops.create_file(
                    code_file.path,
                    code_file.content,
                    force_overwrite=True,
                    description=code_file.description
                )
                
                if success:
                    success_count += 1
                else:
                    error_msgs.append(msg)
            
            # Mark task as approved
            self._mark_task_status(task_id, "approved")
            
            # Log approval
            self._log_execution("code_approved", task_id, {
                "approver": approver,
                "files_applied": success_count
            })
            
            # Clean up
            del self.pending_approvals[task_id]
            
            if error_msgs:
                return False, f"Applied {success_count} files with {len(error_msgs)} errors"
            else:
                logger.info(f"Applied {success_count} files for task {task_id}")
                return True, f"Applied {success_count} files successfully"
                
        except Exception as e:
            error_msg = f"Error applying code: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def execute_task(
        self,
        task_id: int,
        auto_approve: bool = False
    ) -> Tuple[bool, str]:
        """
        Execute complete workflow for a task: generate → approve → apply.
        
        Args:
            task_id: ID of the task
            auto_approve: Whether to auto-approve generated code
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get task
            project_id = self.state_manager.get_project_id(self.project_name)
            task = self._get_task_by_id(project_id, task_id)
            
            if not task:
                return False, f"Task {task_id} not found"
            
            # Check dependencies
            satisfied, unsatisfied = self.resolve_task_dependencies(task)
            if not satisfied:
                msg = f"Unsatisfied dependencies: {', '.join(unsatisfied)}"
                logger.warning(f"Skipping task {task['title']}: {msg}")
                return False, msg
            
            # Generate code
            success, code_gen = self.generate_code_for_task(task)
            if not success:
                return False, "Code generation failed"
            
            # Auto-approve if requested
            if auto_approve:
                success, msg = self.approve_and_apply_code(task_id, approve=True, approver="auto")
                if success:
                    self._mark_task_status(task_id, "completed")
                    return True, msg
                else:
                    return False, msg
            else:
                return True, f"Code generated for {task['title']}, awaiting approval"
                
        except Exception as e:
            error_msg = f"Error executing task: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def execute_all_pending_tasks(self, auto_approve: bool = False) -> Dict[str, Any]:
        """
        Execute all pending tasks in dependency order.
        
        Args:
            auto_approve: Auto-approve all generated code
            
        Returns:
            Summary of execution
        """
        try:
            pending_tasks = self.get_pending_tasks()
            
            if not pending_tasks:
                return {"completed": 0, "failed": 0, "skipped": 0, "message": "No pending tasks"}
            
            # Sort by dependencies (topological sort)
            sorted_tasks = self._topological_sort(pending_tasks)
            
            completed = 0
            failed = 0
            skipped = 0
            
            for task in sorted_tasks:
                success, msg = self.execute_task(task["id"], auto_approve=auto_approve)
                
                if success:
                    completed += 1
                elif "unsatisfied" in msg.lower():
                    skipped += 1
                else:
                    failed += 1
            
            summary = {
                "completed": completed,
                "failed": failed,
                "skipped": skipped,
                "total": len(pending_tasks),
                "message": f"Executed {completed} tasks, {failed} failed, {skipped} skipped"
            }
            
            logger.info(f"Execution summary: {summary['message']}")
            return summary
            
        except Exception as e:
            error_msg = f"Error executing all tasks: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    def get_pending_approvals(self) -> Dict[int, Dict[str, Any]]:
        """Get code awaiting approval."""
        return {
            task_id: {
                "task_id": code_gen.task_id,
                "task_title": code_gen.task_title,
                "language": code_gen.language,
                "files": len(code_gen.files),
                "summary": code_gen.summary
            }
            for task_id, code_gen in self.pending_approvals.items()
        }


import asyncio
from pathlib import Path as _Path


class Executor:
    """Compatibility adapter providing a lightweight async Executor API
    used by the frontend API module. This wraps the existing
    ExecutionEngine and runs execution in a background thread so
    the FastAPI endpoints can `await` the calls.
    """

    def __init__(self):
        self.state_manager = StateManager()
        self._engines: Dict[str, ExecutionEngine] = {}

    async def execute_workflow(self, project_id: str) -> str:
        """Start execution for a project's pending tasks in background.

        Returns a generated execution id immediately.
        """
        try:
            project = self.state_manager.get_project(project_id) or {"name": f"project-{project_id}"}
            project_name = project.get("name", f"project-{project_id}")
            engine = ExecutionEngine(project_name, self.state_manager, project_root=str(_Path.cwd()))
            exec_id = f"exec-{int(datetime.utcnow().timestamp())}"

            # Run the synchronous execution in a background thread
            asyncio.create_task(asyncio.to_thread(engine.execute_all_pending_tasks))

            # Keep a reference if needed for status checks
            self._engines[exec_id] = engine
            return exec_id
        except Exception:
            return "exec-error"

    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Return a simple status for the execution id.

        This is a lightweight implementation which can be extended
        to return real progress information from the engine.
        """
        engine = self._engines.get(execution_id)
        if not engine:
            return {"execution_id": execution_id, "status": "unknown"}

        # Provide a basic summary from the execution engine
        return {
            "execution_id": execution_id,
            "status": "running",
            "pending_approvals": len(engine.get_pending_approvals()),
            "executions_logged": len(engine.execution_log or [])
        }
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get overall execution summary."""
        try:
            project_id = self.state_manager.get_project_id(self.project_name)
            tasks = self.state_manager.get_project_tasks(project_id)
            
            status_counts = {}
            for task in tasks:
                status = task.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            file_summary = self.file_ops.get_summary()
            
            return {
                "project": self.project_name,
                "total_tasks": len(tasks),
                "status_breakdown": status_counts,
                "files_created": file_summary["files_created"],
                "files_modified": file_summary["files_modified"],
                "pending_approvals": len(self.pending_approvals),
                "execution_log_entries": len(self.execution_log)
            }
        except Exception as e:
            logger.error(f"Error getting summary: {str(e)}")
            return {"error": str(e)}
    
    def _get_language_hint(self, task: Dict[str, Any]) -> Optional[str]:
        """Extract language hint from task description."""
        desc = (task.get("title", "") + " " + task.get("description", "")).lower()
        
        if any(word in desc for word in ["python", "django", "flask", "fastapi"]):
            return "python"
        elif any(word in desc for word in ["javascript", "typescript", "node", "react"]):
            return "javascript"
        
        return None
    
    def _mark_task_status(self, task_id: int, status: str) -> None:
        """Update task status in database."""
        try:
            project_id = self.state_manager.get_project_id(self.project_name)
            # Would update database - simplified here
            logger.debug(f"Task {task_id} status: {status}")
        except Exception as e:
            logger.error(f"Failed to update task status: {str(e)}")
    
    def _get_task_by_id(self, project_id: int, task_id: int) -> Optional[Dict[str, Any]]:
        """Get task by ID."""
        try:
            tasks = self.state_manager.get_project_tasks(project_id)
            for task in tasks:
                if task.get("id") == task_id:
                    return task
            return None
        except Exception as e:
            logger.error(f"Failed to get task: {str(e)}")
            return None
    
    def _topological_sort(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort tasks by dependencies (topological sort)."""
        # Simplified - real implementation would use graph algorithms
        return tasks
    
    def _log_execution(self, action: str, task_id: int, metadata: Dict[str, Any]) -> None:
        """Log an execution event."""
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "task_id": task_id,
            "metadata": metadata
        })
    
    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get execution log."""
        return self.execution_log.copy()
