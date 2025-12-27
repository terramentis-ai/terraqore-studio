"""
TerraQore State Management Module
Handles project state, memory, and persistence using SQLite.
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ProjectStatus(Enum):
    """Project status enumeration."""
    INITIALIZED = "initialized"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Project:
    """Project data model."""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    status: str = ProjectStatus.INITIALIZED.value
    created_at: str = ""
    updated_at: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()


@dataclass
class Task:
    """Task data model."""
    id: Optional[int] = None
    project_id: int = 0
    title: str = ""
    description: str = ""
    status: str = TaskStatus.PENDING.value
    agent_type: str = ""
    result: Optional[str] = None
    created_at: str = ""
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = None
    priority: int = 0  # NEW: 0=low, 1=medium, 2=high
    milestone: Optional[str] = None  # NEW: Milestone name
    estimated_hours: Optional[float] = None  # NEW: Estimated effort
    dependencies: List[int] = None  # NEW: List of task IDs this depends on
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.dependencies is None:
            self.dependencies = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class StateManager:
    """Manages Flynt's persistent state using SQLite."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize state manager.
        
        Args:
            db_path: Path to SQLite database. If None, uses default location.
        """
        self.db_path = db_path or Path.cwd() / "data" / "terraqore.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
    def _init_database(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                agent_type TEXT,
                result TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                metadata TEXT,
                priority INTEGER DEFAULT 0,
                milestone TEXT,
                estimated_hours REAL,
                dependencies TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)
        
        # Agent execution logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                agent_type TEXT NOT NULL,
                action TEXT NOT NULL,
                input_data TEXT,
                output_data TEXT,
                success BOOLEAN,
                error_message TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        """)
        
        # Session memory
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                key TEXT NOT NULL,
                value TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)
        
        # Code generations (Phase 4)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                language TEXT NOT NULL,
                status TEXT NOT NULL,
                summary TEXT,
                files_count INTEGER,
                generated_at TEXT NOT NULL,
                approved_at TEXT,
                approved_by TEXT,
                applied_at TEXT,
                files_data TEXT,
                validation_passed BOOLEAN,
                errors TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        """)
        
        # Agent iterations (Phase 5.1)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_iterations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                agent_name TEXT NOT NULL,
                iteration_number INTEGER NOT NULL,
                iteration_type TEXT NOT NULL,
                input_context TEXT NOT NULL,
                output_result TEXT NOT NULL,
                quality_score REAL NOT NULL,
                validation_passed BOOLEAN NOT NULL,
                execution_time REAL NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                UNIQUE(project_id, agent_name, iteration_number)
            )
        """)
        
        # Validation results (Phase 5.1)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_iteration_id INTEGER NOT NULL,
                validator_agent TEXT NOT NULL,
                issues TEXT,
                severity TEXT,
                recommendations TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (agent_iteration_id) REFERENCES agent_iterations (id)
            )
        """)
        
        # Agent feedback (Phase 5.1)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                source_agent TEXT NOT NULL,
                target_agent TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT NOT NULL,
                suggestions TEXT,
                iteration_number INTEGER,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)
        
        # Collaboration context (Phase 5.1)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collaboration_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL UNIQUE,
                shared_context TEXT,
                current_stage TEXT,
                stage_history TEXT,
                total_iterations INTEGER DEFAULT 0,
                last_updated TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)
        
        # Execution metrics (Phase 5.2)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                agent_name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                execution_time_ms INTEGER NOT NULL,
                success BOOLEAN NOT NULL,
                quality_score REAL,
                output_tokens INTEGER,
                input_tokens INTEGER,
                cost_usd REAL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_em_project_agent ON execution_metrics(project_id, agent_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_em_timestamp ON execution_metrics(timestamp)")
        
        # Feedback patterns (Phase 5.2)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                agent_name TEXT NOT NULL,
                pattern_category TEXT NOT NULL,
                pattern_frequency INTEGER NOT NULL,
                affected_agents TEXT,
                common_contexts TEXT,
                suggested_improvements TEXT,
                first_occurrence TEXT NOT NULL,
                last_occurrence TEXT NOT NULL,
                avg_recurrence_days REAL,
                priority TEXT,
                analysis_timestamp TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fp_project_agent ON feedback_patterns(project_id, agent_name)")
        
        # Prompt versions (Phase 5.2)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompt_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                prompt_content TEXT NOT NULL,
                performance_baseline REAL,
                performance_achieved REAL,
                improvement_percent REAL,
                test_results TEXT,
                created_at TEXT NOT NULL,
                activated_at TEXT,
                reason_for_change TEXT,
                UNIQUE(agent_name, version_number)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pv_agent ON prompt_versions(agent_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pv_activated ON prompt_versions(activated_at)")
        
        # Quality thresholds (Phase 5.2)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_thresholds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL UNIQUE,
                quality_gate_threshold REAL NOT NULL DEFAULT 6.0,
                feasibility_threshold REAL NOT NULL DEFAULT 5.0,
                security_threshold INTEGER NOT NULL DEFAULT 0,
                performance_threshold_ms INTEGER NOT NULL DEFAULT 5000,
                cost_threshold_usd REAL NOT NULL DEFAULT 0.10,
                last_adjusted TEXT NOT NULL,
                adjustment_reason TEXT,
                adjustment_count INTEGER DEFAULT 0
            )
        """)
        
        # Agent performance history (Phase 5.2)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_performance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                date TEXT NOT NULL,
                tasks_completed INTEGER NOT NULL,
                average_quality_score REAL NOT NULL,
                success_rate REAL NOT NULL,
                average_execution_time_ms INTEGER NOT NULL,
                total_cost_usd REAL NOT NULL,
                feedback_count INTEGER DEFAULT 0,
                improvement_rate REAL DEFAULT 0.0,
                trend_direction TEXT,
                UNIQUE(agent_name, date)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_aph_agent_date ON agent_performance_history(agent_name, date)")
        
        # Learning decisions (Phase 5.2)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                decision_type TEXT NOT NULL,
                agent_name TEXT,
                prompt_version_id INTEGER,
                threshold_adjustment_id INTEGER,
                reason TEXT NOT NULL,
                expected_improvement REAL,
                actual_improvement REAL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (prompt_version_id) REFERENCES prompt_versions (id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ld_status ON learning_decisions(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ld_created ON learning_decisions(created_at)")
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    # Project Operations
    
    def create_project(self, project: Project) -> int:
        """Create a new project.
        
        Args:
            project: Project object to create.
            
        Returns:
            ID of created project.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO projects (name, description, status, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            project.name,
            project.description,
            project.status.value if hasattr(project.status, 'value') else project.status,
            project.created_at,
            project.updated_at,
            json.dumps(project.metadata)
        ))
        
        project_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Created project '{project.name}' with ID {project_id}")
        return project_id
    
    def get_project(self, project_id: Optional[int] = None, name: Optional[str] = None) -> Optional[Project]:
        """Get a project by ID or name.
        
        Args:
            project_id: Project ID.
            name: Project name.
            
        Returns:
            Project object or None if not found.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if project_id:
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        elif name:
            cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
        else:
            conn.close()
            return None
            
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Project(
                id=row[0],
                name=row[1],
                description=row[2],
                status=row[3],
                created_at=row[4],
                updated_at=row[5],
                metadata=json.loads(row[6]) if row[6] else {}
            )
        return None
    
    def list_projects(self, status: Optional[str] = None) -> List[Project]:
        """List all projects, optionally filtered by status.
        
        Args:
            status: Filter by project status.
            
        Returns:
            List of Project objects.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status:
            cursor.execute("SELECT * FROM projects WHERE status = ? ORDER BY updated_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")
            
        rows = cursor.fetchall()
        conn.close()
        
        return [
            Project(
                id=row[0],
                name=row[1],
                description=row[2],
                status=row[3],
                created_at=row[4],
                updated_at=row[5],
                metadata=json.loads(row[6]) if row[6] else {}
            )
            for row in rows
        ]
    
    def update_project(self, project_id: int, **updates):
        """Update project fields.
        
        Args:
            project_id: Project ID to update.
            **updates: Fields to update.
        """
        updates['updated_at'] = datetime.now().isoformat()
        
        if 'metadata' in updates:
            updates['metadata'] = json.dumps(updates['metadata'])
            
        if 'status' in updates and hasattr(updates['status'], 'value'):
            updates['status'] = updates['status'].value
            
        fields = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [project_id]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"UPDATE projects SET {fields} WHERE id = ?", values)
        conn.commit()
        conn.close()
        
        logger.info(f"Updated project {project_id}")
    
    # Task Operations
    
    def create_task(self, task: Task) -> int:
        """Create a new task.
        
        Args:
            task: Task object to create.
            
        Returns:
            ID of created task.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tasks (
                project_id, title, description, status, agent_type, result, 
                created_at, completed_at, metadata, priority, milestone, 
                estimated_hours, dependencies
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.project_id,
            task.title,
            task.description,
            task.status.value if hasattr(task.status, 'value') else task.status,
            task.agent_type,
            task.result,
            task.created_at,
            task.completed_at,
            json.dumps(task.metadata),
            task.priority,
            task.milestone,
            task.estimated_hours,
            json.dumps(task.dependencies)
        ))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Created task '{task.title}' with ID {task_id}")
        return task_id
    
    def get_tasks(self, project_id: int, status: Optional[str] = None) -> List[Task]:
        """Get tasks for a project.
        
        Args:
            project_id: Project ID.
            status: Filter by task status.
            
        Returns:
            List of Task objects.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status:
            cursor.execute(
                "SELECT * FROM tasks WHERE project_id = ? AND status = ? ORDER BY priority DESC, created_at",
                (project_id, status)
            )
        else:
            cursor.execute(
                "SELECT * FROM tasks WHERE project_id = ? ORDER BY priority DESC, created_at",
                (project_id,)
            )
            
        rows = cursor.fetchall()
        conn.close()
        
        return [
            Task(
                id=row[0],
                project_id=row[1],
                title=row[2],
                description=row[3],
                status=row[4],
                agent_type=row[5],
                result=row[6],
                created_at=row[7],
                completed_at=row[8],
                metadata=json.loads(row[9]) if row[9] else {},
                priority=row[10] if len(row) > 10 else 0,
                milestone=row[11] if len(row) > 11 else None,
                estimated_hours=row[12] if len(row) > 12 else None,
                dependencies=json.loads(row[13]) if len(row) > 13 and row[13] else []
            )
            for row in rows
        ]
    
    def update_task(self, task_id: int, **updates):
        """Update task fields.
        
        Args:
            task_id: Task ID to update.
            **updates: Fields to update.
        """
        if 'metadata' in updates:
            updates['metadata'] = json.dumps(updates['metadata'])
        if 'dependencies' in updates:
            updates['dependencies'] = json.dumps(updates['dependencies'])
            
        if 'status' in updates and hasattr(updates['status'], 'value'):
            updates['status'] = updates['status'].value
            
        fields = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [task_id]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"UPDATE tasks SET {fields} WHERE id = ?", values)
        conn.commit()
        conn.close()
        
        logger.info(f"Updated task {task_id}")
    
    def get_tasks_by_milestone(self, project_id: int, milestone: str) -> List[Task]:
        """Get tasks for a specific milestone.
        
        Args:
            project_id: Project ID.
            milestone: Milestone name.
            
        Returns:
            List of Task objects.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM tasks WHERE project_id = ? AND milestone = ? ORDER BY priority DESC, created_at",
            (project_id, milestone)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            Task(
                id=row[0],
                project_id=row[1],
                title=row[2],
                description=row[3],
                status=row[4],
                agent_type=row[5],
                result=row[6],
                created_at=row[7],
                completed_at=row[8],
                metadata=json.loads(row[9]) if row[9] else {},
                priority=row[10] if len(row) > 10 else 0,
                milestone=row[11] if len(row) > 11 else None,
                estimated_hours=row[12] if len(row) > 12 else None,
                dependencies=json.loads(row[13]) if len(row) > 13 and row[13] else []
            )
            for row in rows
        ]

    # Convenience helpers
    def get_project_id(self, name: str) -> Optional[int]:
        """Return the project ID for a given project name."""
        project = self.get_project(name=name)
        return project.id if project else None

    def get_project_tasks(self, project_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return tasks as dictionaries for easier consumption by orchestration code."""
        tasks = self.get_tasks(project_id, status=status)
        result = []
        for t in tasks:
            result.append({
                "id": t.id,
                "project_id": t.project_id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "agent_type": t.agent_type,
                "result": t.result,
                "created_at": t.created_at,
                "completed_at": t.completed_at,
                "metadata": t.metadata,
                "priority": t.priority,
                "milestone": t.milestone,
                "estimated_hours": t.estimated_hours,
                "dependencies": t.dependencies
            })
        return result
    
    def get_available_tasks(self, project_id: int) -> List[Task]:
        """Get tasks that can be started (no pending dependencies).
        
        Args:
            project_id: Project ID.
            
        Returns:
            List of available Task objects.
        """
        all_tasks = self.get_tasks(project_id, status=TaskStatus.PENDING.value)
        completed_task_ids = {t.id for t in self.get_tasks(project_id, status=TaskStatus.COMPLETED.value)}
        
        available = []
        for task in all_tasks:
            # Check if all dependencies are completed
            if all(dep_id in completed_task_ids for dep_id in task.dependencies):
                available.append(task)
        
        return available
    
    # Memory Operations
    
    def store_memory(self, project_id: int, key: str, value: Any):
        """Store a memory entry for a project.
        
        Args:
            project_id: Project ID.
            key: Memory key.
            value: Value to store (will be JSON serialized).
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO memory (project_id, key, value, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            project_id,
            key,
            json.dumps(value),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
    def get_memory(self, project_id: int, key: str) -> Optional[Any]:
        """Retrieve a memory entry.
        
        Args:
            project_id: Project ID.
            key: Memory key.
            
        Returns:
            Stored value or None.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT value FROM memory WHERE project_id = ? AND key = ? ORDER BY created_at DESC LIMIT 1",
            (project_id, key)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        return None
    
    # Agent Iteration Operations (Phase 5.1)
    
    def store_agent_iteration(
        self,
        project_id: int,
        agent_name: str,
        iteration_number: int,
        iteration_type: str,
        input_context: Dict[str, Any],
        output_result: Dict[str, Any],
        quality_score: float,
        validation_passed: bool,
        execution_time: float
    ) -> int:
        """Store an agent iteration result.
        
        Args:
            project_id: Project ID.
            agent_name: Name of the agent.
            iteration_number: Iteration number.
            iteration_type: Type of iteration (generation, validation, etc).
            input_context: Input context for the iteration.
            output_result: Output result from the iteration.
            quality_score: Quality score (0-10).
            validation_passed: Whether validation passed.
            execution_time: Execution time in seconds.
            
        Returns:
            ID of stored iteration.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO agent_iterations (
                project_id, agent_name, iteration_number, iteration_type,
                input_context, output_result, quality_score, validation_passed,
                execution_time, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            agent_name,
            iteration_number,
            iteration_type,
            json.dumps(input_context),
            json.dumps(output_result),
            quality_score,
            validation_passed,
            execution_time,
            datetime.now().isoformat()
        ))
        
        iteration_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(
            f"Stored iteration for {agent_name} #{iteration_number} "
            f"(score={quality_score:.1f}, passed={validation_passed})"
        )
        return iteration_id
    
    def get_agent_iterations(
        self,
        project_id: int,
        agent_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get agent iterations for a project.
        
        Args:
            project_id: Project ID.
            agent_name: Optional filter by agent name.
            
        Returns:
            List of iteration records.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if agent_name:
            cursor.execute("""
                SELECT * FROM agent_iterations
                WHERE project_id = ? AND agent_name = ?
                ORDER BY iteration_number
            """, (project_id, agent_name))
        else:
            cursor.execute("""
                SELECT * FROM agent_iterations
                WHERE project_id = ?
                ORDER BY iteration_number
            """, (project_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "project_id": row[1],
                "agent_name": row[2],
                "iteration_number": row[3],
                "iteration_type": row[4],
                "input_context": json.loads(row[5]),
                "output_result": json.loads(row[6]),
                "quality_score": row[7],
                "validation_passed": row[8],
                "execution_time": row[9],
                "timestamp": row[10]
            }
            for row in rows
        ]
    
    def store_validation_result(
        self,
        agent_iteration_id: int,
        validator_agent: str,
        issues: List[str],
        severity: str,
        recommendations: List[str]
    ) -> int:
        """Store validation result for an agent iteration.
        
        Args:
            agent_iteration_id: ID of the agent iteration.
            validator_agent: Name of the validating agent.
            issues: List of issues found.
            severity: Severity level (info, warning, error, critical).
            recommendations: List of recommendations.
            
        Returns:
            ID of stored validation result.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO validation_results (
                agent_iteration_id, validator_agent, issues, severity,
                recommendations, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            agent_iteration_id,
            validator_agent,
            json.dumps(issues),
            severity,
            json.dumps(recommendations),
            datetime.now().isoformat()
        ))
        
        result_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(
            f"Stored validation result from {validator_agent} "
            f"({severity}): {len(issues)} issues"
        )
        return result_id
    
    def store_feedback(
        self,
        project_id: int,
        source_agent: str,
        target_agent: str,
        feedback_type: str,
        message: str,
        severity: str,
        suggestions: List[str],
        iteration_number: Optional[int] = None
    ) -> int:
        """Store feedback from one agent to another.
        
        Args:
            project_id: Project ID.
            source_agent: Agent providing feedback.
            target_agent: Agent receiving feedback.
            feedback_type: Type of feedback.
            message: Feedback message.
            severity: Severity level.
            suggestions: List of suggestions.
            iteration_number: Optional iteration number.
            
        Returns:
            ID of stored feedback.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO agent_feedback (
                project_id, source_agent, target_agent, feedback_type,
                message, severity, suggestions, iteration_number, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            source_agent,
            target_agent,
            feedback_type,
            message,
            severity,
            json.dumps(suggestions),
            iteration_number,
            datetime.now().isoformat()
        ))
        
        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(
            f"Stored feedback from {source_agent} to {target_agent} "
            f"({severity})"
        )
        return feedback_id
    
    def get_project_feedback(
        self,
        project_id: int,
        target_agent: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get feedback for a project.
        
        Args:
            project_id: Project ID.
            target_agent: Optional filter by target agent.
            
        Returns:
            List of feedback records.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if target_agent:
            cursor.execute("""
                SELECT * FROM agent_feedback
                WHERE project_id = ? AND target_agent = ?
                ORDER BY timestamp DESC
            """, (project_id, target_agent))
        else:
            cursor.execute("""
                SELECT * FROM agent_feedback
                WHERE project_id = ?
                ORDER BY timestamp DESC
            """, (project_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "project_id": row[1],
                "source_agent": row[2],
                "target_agent": row[3],
                "feedback_type": row[4],
                "message": row[5],
                "severity": row[6],
                "suggestions": json.loads(row[7]),
                "iteration_number": row[8],
                "timestamp": row[9]
            }
            for row in rows
        ]
    
    def init_collaboration_context(
        self,
        project_id: int,
        shared_context: Dict[str, Any]
    ) -> None:
        """Initialize collaboration context for a project.
        
        Args:
            project_id: Project ID.
            shared_context: Initial shared context.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO collaboration_context (
                project_id, shared_context, current_stage, stage_history,
                total_iterations, last_updated
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            json.dumps(shared_context),
            "initialization",
            json.dumps(["initialization"]),
            0,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Initialized collaboration context for project {project_id}")
    
    def update_collaboration_stage(self, project_id: int, new_stage: str) -> None:
        """Update collaboration stage for a project.
        
        Args:
            project_id: Project ID.
            new_stage: New stage name.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current stage history
        cursor.execute(
            "SELECT stage_history FROM collaboration_context WHERE project_id = ?",
            (project_id,)
        )
        row = cursor.fetchone()
        
        if row:
            stage_history = json.loads(row[0]) if row[0] else []
            stage_history.append(new_stage)
            
            cursor.execute("""
                UPDATE collaboration_context
                SET current_stage = ?, stage_history = ?, last_updated = ?
                WHERE project_id = ?
            """, (
                new_stage,
                json.dumps(stage_history),
                datetime.now().isoformat(),
                project_id
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Updated collaboration stage to '{new_stage}'")
    
    def get_collaboration_context(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get collaboration context for a project.
        
        Args:
            project_id: Project ID.
            
        Returns:
            Collaboration context or None.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM collaboration_context WHERE project_id = ?",
            (project_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "project_id": row[1],
                "shared_context": json.loads(row[2]) if row[2] else {},
                "current_stage": row[3],
                "stage_history": json.loads(row[4]) if row[4] else [],
                "total_iterations": row[5],
                "last_updated": row[6]
            }
        return None


# Singleton instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get or create the global state manager.
    
    Returns:
        StateManager singleton instance.
    """
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager