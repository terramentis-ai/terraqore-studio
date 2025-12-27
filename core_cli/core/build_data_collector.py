"""
Build Data Collector for TerraQore Studio
Captures production phase metrics and execution data for later analysis and testing.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class BuildStage(str, Enum):
    """Build/production stages."""
    INITIALIZATION = "initialization"
    IDEATION = "ideation"
    IDEA_VALIDATION = "idea_validation"
    PLANNING = "planning"
    DEVELOPMENT = "development"
    CODE_VALIDATION = "code_validation"
    SECURITY_SCAN = "security_scan"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    COMPLETION = "completion"


class MetricType(str, Enum):
    """Types of metrics collected."""
    EXECUTION_TIME = "execution_time"
    QUALITY_SCORE = "quality_score"
    ERROR_COUNT = "error_count"
    ITERATION_COUNT = "iteration_count"
    FEEDBACK_COUNT = "feedback_count"
    MEMORY_USAGE = "memory_usage"
    TOKEN_COUNT = "token_count"
    LLM_MODELS_USED = "llm_models_used"

@dataclass
class ExecutionMetric:
    """Single execution metric data point."""
    metric_type: str
    value: float
    agent_name: Optional[str]
    stage: str
    timestamp: str
    context: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StageRecord:
    """Record of a build stage execution."""
    project_id: int
    stage: str
    started_at: str
    completed_at: Optional[str]
    status: str  # started, in_progress, completed, failed
    agent_involved: Optional[str]
    metrics: Dict[str, Any]
    issues: List[str]
    decisions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BuildDataCollector:
    """Collects and persists build/production phase data."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize build data collector.
        
        Args:
            db_path: Path to build database. If None, uses default location.
        """
        self.db_path = db_path or Path.cwd() / "data" / "terraqore_build.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        logger.info(f"BuildDataCollector initialized at {self.db_path}")
    
    def _init_database(self):
        """Initialize build database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS build_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                build_id TEXT UNIQUE NOT NULL,
                project_id INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                total_stages INTEGER DEFAULT 0,
                successful_stages INTEGER DEFAULT 0,
                failed_stages INTEGER DEFAULT 0,
                total_duration_seconds REAL,
                metadata TEXT
            )
        """)
        
        # Stage records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stage_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                build_id TEXT NOT NULL,
                project_id INTEGER NOT NULL,
                stage TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                agent_involved TEXT,
                duration_seconds REAL,
                metrics TEXT,
                issues TEXT,
                decisions TEXT,
                FOREIGN KEY (build_id) REFERENCES build_metadata(build_id)
            )
        """)
        
        # Execution metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                build_id TEXT NOT NULL,
                project_id INTEGER NOT NULL,
                stage TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                value REAL NOT NULL,
                agent_name TEXT,
                timestamp TEXT NOT NULL,
                context TEXT,
                FOREIGN KEY (build_id) REFERENCES build_metadata(build_id)
            )
        """)
        
        # Error log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                build_id TEXT NOT NULL,
                project_id INTEGER NOT NULL,
                stage TEXT NOT NULL,
                agent_name TEXT,
                error_type TEXT NOT NULL,
                error_message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                context TEXT,
                FOREIGN KEY (build_id) REFERENCES build_metadata(build_id)
            )
        """)
        
        # Agent performance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                build_id TEXT NOT NULL,
                project_id INTEGER NOT NULL,
                agent_name TEXT NOT NULL,
                executions INTEGER DEFAULT 0,
                avg_execution_time REAL,
                avg_quality_score REAL,
                total_issues INTEGER DEFAULT 0,
                total_feedback INTEGER DEFAULT 0,
                success_rate REAL,
                last_updated TEXT NOT NULL,
                FOREIGN KEY (build_id) REFERENCES build_metadata(build_id)
            )
        """)
        
        # Test data snapshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                build_id TEXT NOT NULL,
                project_id INTEGER NOT NULL,
                snapshot_type TEXT NOT NULL,
                stage TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (build_id) REFERENCES build_metadata(build_id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Build database schema initialized")
    
    def start_build(self, build_id: str, project_id: int) -> None:
        """Start a new build recording session.
        
        Args:
            build_id: Unique build identifier
            project_id: Associated project ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO build_metadata (
                build_id, project_id, started_at, status, metadata
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            build_id,
            project_id,
            datetime.now().isoformat(),
            "started",
            json.dumps({"system_version": "5.1"})
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Build session started: {build_id} for project {project_id}")
    
    def record_stage(
        self,
        build_id: str,
        project_id: int,
        stage: str,
        status: str,
        agent_involved: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
        issues: Optional[List[str]] = None,
        decisions: Optional[List[str]] = None,
        duration_seconds: Optional[float] = None
    ) -> int:
        """Record a build stage execution.
        
        Args:
            build_id: Build session ID
            project_id: Project ID
            stage: Stage name
            status: Stage status (started, in_progress, completed, failed)
            agent_involved: Agent that executed this stage
            metrics: Dict of metrics for this stage
            issues: List of issues encountered
            decisions: List of decisions made
            duration_seconds: Execution time
            
        Returns:
            Record ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO stage_records (
                build_id, project_id, stage, started_at, status,
                agent_involved, duration_seconds, metrics, issues, decisions
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            build_id,
            project_id,
            stage,
            datetime.now().isoformat(),
            status,
            agent_involved,
            duration_seconds,
            json.dumps(metrics or {}),
            json.dumps(issues or []),
            json.dumps(decisions or [])
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Recorded stage '{stage}' (status={status})")
        return record_id
    
    def record_metric(
        self,
        build_id: str,
        project_id: int,
        metric_type: str,
        value: float,
        stage: str,
        agent_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> int:
        """Record execution metric.
        
        Args:
            build_id: Build session ID
            project_id: Project ID
            metric_type: Type of metric
            value: Metric value
            stage: Current stage
            agent_name: Agent name if applicable
            context: Additional context
            
        Returns:
            Record ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO execution_metrics (
                build_id, project_id, metric_type, value, stage,
                agent_name, timestamp, context
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            build_id,
            project_id,
            metric_type,
            value,
            stage,
            agent_name,
            datetime.now().isoformat(),
            json.dumps(context or {})
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id
    
    def record_error(
        self,
        build_id: str,
        project_id: int,
        stage: str,
        error_type: str,
        error_message: str,
        agent_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> int:
        """Record error occurrence.
        
        Args:
            build_id: Build session ID
            project_id: Project ID
            stage: Stage where error occurred
            error_type: Type of error
            error_message: Error message
            agent_name: Agent involved if applicable
            context: Additional context
            
        Returns:
            Record ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO error_log (
                build_id, project_id, stage, agent_name, error_type,
                error_message, timestamp, context
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            build_id,
            project_id,
            stage,
            agent_name,
            error_type,
            error_message,
            datetime.now().isoformat(),
            json.dumps(context or {})
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.warning(f"Error recorded in stage '{stage}': {error_type}")
        return record_id
    
    def save_test_snapshot(
        self,
        build_id: str,
        project_id: int,
        snapshot_type: str,
        stage: str,
        data: Dict[str, Any]
    ) -> int:
        """Save test data snapshot for later use.
        
        Args:
            build_id: Build session ID
            project_id: Project ID
            snapshot_type: Type of snapshot (agent_output, validation_result, etc)
            stage: Stage associated with snapshot
            data: Data to snapshot
            
        Returns:
            Record ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO test_snapshots (
                build_id, project_id, snapshot_type, stage, data, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            build_id,
            project_id,
            snapshot_type,
            stage,
            json.dumps(data),
            datetime.now().isoformat()
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Saved test snapshot: {snapshot_type}")
        return record_id
    
    def end_build(self, build_id: str, status: str = "completed") -> None:
        """End build recording session.
        
        Args:
            build_id: Build session ID
            status: Final status (completed, failed, etc)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get build start time
        cursor.execute("SELECT started_at FROM build_metadata WHERE build_id = ?", (build_id,))
        row = cursor.fetchone()
        
        if row:
            started = datetime.fromisoformat(row[0])
            now = datetime.now()
            duration = (now - started).total_seconds()
            
            # Count successful and failed stages
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'completed' THEN 1 END),
                    COUNT(CASE WHEN status = 'failed' THEN 1 END),
                    COUNT(*)
                FROM stage_records
                WHERE build_id = ?
            """, (build_id,))
            
            successful, failed, total = cursor.fetchone()
            
            # Update build metadata
            cursor.execute("""
                UPDATE build_metadata
                SET completed_at = ?, status = ?, total_duration_seconds = ?,
                    total_stages = ?, successful_stages = ?, failed_stages = ?
                WHERE build_id = ?
            """, (
                now.isoformat(),
                status,
                duration,
                total,
                successful,
                failed,
                build_id
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Build session ended: {build_id} with status {status}")
    
    def get_build_summary(self, build_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of a build session.
        
        Args:
            build_id: Build session ID
            
        Returns:
            Build summary dict or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT build_id, project_id, started_at, completed_at, status,
                   total_stages, successful_stages, failed_stages, total_duration_seconds
            FROM build_metadata
            WHERE build_id = ?
        """, (build_id,))
        
        row = cursor.fetchone()
        
        if row:
            summary = {
                "build_id": row[0],
                "project_id": row[1],
                "started_at": row[2],
                "completed_at": row[3],
                "status": row[4],
                "total_stages": row[5],
                "successful_stages": row[6],
                "failed_stages": row[7],
                "duration_seconds": row[8]
            }
            
            # Get stage records
            cursor.execute("""
                SELECT stage, status, duration_seconds FROM stage_records
                WHERE build_id = ?
                ORDER BY id
            """, (build_id,))
            
            summary["stages"] = [
                {"name": r[0], "status": r[1], "duration": r[2]}
                for r in cursor.fetchall()
            ]
            
            # Get errors
            cursor.execute("""
                SELECT stage, error_type, error_message FROM error_log
                WHERE build_id = ?
            """, (build_id,))
            
            summary["errors"] = [
                {"stage": r[0], "type": r[1], "message": r[2]}
                for r in cursor.fetchall()
            ]
            
            conn.close()
            return summary
        
        conn.close()
        return None
    
    def get_test_snapshots(
        self,
        build_id: str,
        snapshot_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve test snapshots for a build.
        
        Args:
            build_id: Build session ID
            snapshot_type: Optional filter by type
            
        Returns:
            List of snapshots
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if snapshot_type:
            cursor.execute("""
                SELECT snapshot_type, stage, data, created_at
                FROM test_snapshots
                WHERE build_id = ? AND snapshot_type = ?
            """, (build_id, snapshot_type))
        else:
            cursor.execute("""
                SELECT snapshot_type, stage, data, created_at
                FROM test_snapshots
                WHERE build_id = ?
            """, (build_id,))
        
        snapshots = [
            {
                "type": r[0],
                "stage": r[1],
                "data": json.loads(r[2]),
                "created_at": r[3]
            }
            for r in cursor.fetchall()
        ]
        
        conn.close()
        return snapshots
    
    def export_build_data(self, build_id: str, output_format: str = "json") -> str:
        """Export build data for analysis/testing.
        
        Args:
            build_id: Build session ID
            output_format: Export format (json, csv, etc)
            
        Returns:
            Exported data as string
        """
        summary = self.get_build_summary(build_id)
        snapshots = self.get_test_snapshots(build_id)
        
        if output_format == "json":
            export_data = {
                "build_summary": summary,
                "test_snapshots": snapshots
            }
            return json.dumps(export_data, indent=2)
        
        return json.dumps({"build_summary": summary})


# Singleton instance
_build_collector: Optional[BuildDataCollector] = None


def get_build_data_collector() -> BuildDataCollector:
    """Get or create the global build data collector.
    
    Returns:
        BuildDataCollector singleton instance.
    """
    global _build_collector
    if _build_collector is None:
        _build_collector = BuildDataCollector()
    return _build_collector
