"""
Attribution System for TERRAQORE
Tracks and marks all generated code with TERRAQORE metadata and attribution
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import json
import sqlite3
from pathlib import Path
import hashlib

class AttributionLevel(Enum):
    """Types of code attribution levels"""
    GENERATED = "generated"  # 100% AI generated
    ENHANCED = "enhanced"    # Modified from template
    ASSISTED = "assisted"    # AI-assisted human code
    REVIEWED = "reviewed"    # AI-reviewed human code


class CodeArtifactType(Enum):
    """Types of code artifacts that can be attributed"""
    PYTHON_MODULE = "python_module"
    PYTHON_SCRIPT = "python_script"
    TYPESCRIPT_FILE = "typescript_file"
    REACT_COMPONENT = "react_component"
    CONFIG_FILE = "config_file"
    TEST_FILE = "test_file"
    DOCUMENTATION = "documentation"
    OTHER = "other"


@dataclass
class AttributionMetadata:
    """Metadata for attribution of generated code"""
    artifact_id: str
    artifact_name: str
    artifact_type: CodeArtifactType
    attribution_level: AttributionLevel
    project_id: int
    project_name: str
    agent_responsible: str
    generated_by: str  # "TERRAQORE v1.0"
    generation_timestamp: str
    source_commit: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    license: str = "MIT"  # Default license
    quality_score: Optional[float] = None
    test_coverage: Optional[float] = None
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'artifact_id': self.artifact_id,
            'artifact_name': self.artifact_name,
            'artifact_type': self.artifact_type.value,
            'attribution_level': self.attribution_level.value,
            'project_id': self.project_id,
            'project_name': self.project_name,
            'agent_responsible': self.agent_responsible,
            'generated_by': self.generated_by,
            'generation_timestamp': self.generation_timestamp,
            'source_commit': self.source_commit,
            'dependencies': self.dependencies,
            'license': self.license,
            'quality_score': self.quality_score,
            'test_coverage': self.test_coverage,
            'custom_metadata': self.custom_metadata
        }


class AttributionSystem:
    """
    Manages code attribution across TERRAQORE-generated artifacts.
    Provides headers, tracking, and export functionality.
    """
    
    def __init__(self, db_path: str = "terraqore_attribution.db"):
        """Initialize attribution system"""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for attribution tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artifact_id TEXT UNIQUE NOT NULL,
                artifact_name TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                attribution_level TEXT NOT NULL,
                project_id INTEGER NOT NULL,
                project_name TEXT NOT NULL,
                agent_responsible TEXT NOT NULL,
                generated_by TEXT NOT NULL,
                generation_timestamp TEXT NOT NULL,
                source_commit TEXT,
                dependencies TEXT,
                license TEXT,
                quality_score REAL,
                test_coverage REAL,
                custom_metadata TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS achievement_badges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL UNIQUE,
                project_name TEXT NOT NULL,
                badge_name TEXT NOT NULL,
                description TEXT,
                achieved_at TEXT NOT NULL,
                icon TEXT,
                metadata TEXT,
                FOREIGN KEY (project_id) REFERENCES attributions(project_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def generate_header_comment(
        self,
        artifact_type: CodeArtifactType,
        metadata: AttributionMetadata
    ) -> str:
        """Generate language-appropriate header comment with attribution"""
        
        header = f"""
# ============================================================================
# Generated with TERRAQORE v1.0 - Personal Developer Assistant
# 
# Project: {metadata.project_name} (ID: {metadata.project_id})
# Artifact: {metadata.artifact_name}
# Type: {metadata.artifact_type.value}
# Attribution Level: {metadata.attribution_level.value}
# 
# Generated by: {metadata.agent_responsible}
# Timestamp: {metadata.generation_timestamp}
# License: {metadata.license}
# Quality Score: {metadata.quality_score or 'N/A'}
# Test Coverage: {metadata.test_coverage or 'N/A'}%
#
# This code was generated with AI assistance and reviewed by TERRAQORE.
# See https://github.com/TERRAQORE for more information.
# ============================================================================
"""
        
        # Adjust comment syntax for TypeScript/JavaScript
        if artifact_type in [CodeArtifactType.TYPESCRIPT_FILE, CodeArtifactType.REACT_COMPONENT]:
            header = header.replace('#', '//')
        
        return header.strip()
    
    def track_artifact(
        self,
        artifact_id: str,
        artifact_name: str,
        artifact_type: CodeArtifactType,
        attribution_level: AttributionLevel,
        project_id: int,
        project_name: str,
        agent_responsible: str,
        quality_score: Optional[float] = None,
        test_coverage: Optional[float] = None,
        dependencies: Optional[List[str]] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> AttributionMetadata:
        """Track a generated artifact with full metadata"""
        
        metadata = AttributionMetadata(
            artifact_id=artifact_id,
            artifact_name=artifact_name,
            artifact_type=artifact_type,
            attribution_level=attribution_level,
            project_id=project_id,
            project_name=project_name,
            agent_responsible=agent_responsible,
            generated_by="TERRAQORE v1.0",
            generation_timestamp=datetime.now().isoformat(),
            dependencies=dependencies or [],
            quality_score=quality_score,
            test_coverage=test_coverage,
            custom_metadata=custom_metadata or {}
        )
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO attributions (
                    artifact_id, artifact_name, artifact_type, attribution_level,
                    project_id, project_name, agent_responsible, generated_by,
                    generation_timestamp, dependencies, license, quality_score,
                    test_coverage, custom_metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                artifact_id,
                artifact_name,
                artifact_type.value,
                attribution_level.value,
                project_id,
                project_name,
                agent_responsible,
                metadata.generated_by,
                metadata.generation_timestamp,
                json.dumps(metadata.dependencies),
                metadata.license,
                quality_score,
                test_coverage,
                json.dumps(custom_metadata or {}),
                datetime.now().isoformat()
            ))
            conn.commit()
        finally:
            conn.close()
        
        return metadata
    
    def get_project_attributions(self, project_id: int) -> List[AttributionMetadata]:
        """Get all attributions for a project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM attributions WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,)
            )
            rows = cursor.fetchall()
            
            attributions = []
            for row in rows:
                attr = AttributionMetadata(
                    artifact_id=row[1],
                    artifact_name=row[2],
                    artifact_type=CodeArtifactType(row[3]),
                    attribution_level=AttributionLevel(row[4]),
                    project_id=row[5],
                    project_name=row[6],
                    agent_responsible=row[7],
                    generated_by=row[8],
                    generation_timestamp=row[9],
                    source_commit=row[10],
                    dependencies=json.loads(row[11]),
                    license=row[12],
                    quality_score=row[13],
                    test_coverage=row[14],
                    custom_metadata=json.loads(row[15])
                )
                attributions.append(attr)
            
            return attributions
        finally:
            conn.close()
    
    def record_achievement(
        self,
        project_id: int,
        project_name: str,
        badge_name: str,
        description: str,
        icon: str = "⭐"
    ) -> Dict[str, Any]:
        """Record an achievement badge for a project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        achievement = {
            'project_id': project_id,
            'project_name': project_name,
            'badge_name': badge_name,
            'description': description,
            'achieved_at': datetime.now().isoformat(),
            'icon': icon
        }
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO achievement_badges (
                    project_id, project_name, badge_name, description,
                    achieved_at, icon, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                project_id,
                project_name,
                badge_name,
                description,
                achievement['achieved_at'],
                icon,
                json.dumps({})
            ))
            conn.commit()
        finally:
            conn.close()
        
        return achievement
    
    def get_project_achievements(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all achievements for a project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM achievement_badges WHERE project_id = ? ORDER BY achieved_at DESC",
                (project_id,)
            )
            rows = cursor.fetchall()
            
            achievements = []
            for row in rows:
                achievement = {
                    'project_id': row[2],
                    'project_name': row[3],
                    'badge_name': row[4],
                    'description': row[5],
                    'achieved_at': row[6],
                    'icon': row[7]
                }
                achievements.append(achievement)
            
            return achievements
        finally:
            conn.close()
    
    def generate_project_summary(self, project_id: int) -> Dict[str, Any]:
        """Generate a complete project summary with achievements and attributions"""
        
        attributions = self.get_project_attributions(project_id)
        achievements = self.get_project_achievements(project_id)
        
        summary = {
            'project_id': project_id,
            'attribution_summary': {
                'total_artifacts': len(attributions),
                'by_type': {},
                'by_level': {},
                'by_agent': {},
                'average_quality_score': 0.0,
                'average_test_coverage': 0.0
            },
            'achievements': achievements,
            'artifacts': [attr.to_dict() for attr in attributions]
        }
        
        # Calculate statistics
        if attributions:
            quality_scores = [a.quality_score for a in attributions if a.quality_score]
            test_coverages = [a.test_coverage for a in attributions if a.test_coverage]
            
            if quality_scores:
                summary['attribution_summary']['average_quality_score'] = round(
                    sum(quality_scores) / len(quality_scores), 2
                )
            
            if test_coverages:
                summary['attribution_summary']['average_test_coverage'] = round(
                    sum(test_coverages) / len(test_coverages), 2
                )
            
            # Count by type
            for attr in attributions:
                attr_type = attr.artifact_type.value
                summary['attribution_summary']['by_type'][attr_type] = \
                    summary['attribution_summary']['by_type'].get(attr_type, 0) + 1
            
            # Count by level
            for attr in attributions:
                level = attr.attribution_level.value
                summary['attribution_summary']['by_level'][level] = \
                    summary['attribution_summary']['by_level'].get(level, 0) + 1
            
            # Count by agent
            for attr in attributions:
                agent = attr.agent_responsible
                summary['attribution_summary']['by_agent'][agent] = \
                    summary['attribution_summary']['by_agent'].get(agent, 0) + 1
        
        return summary


# Global singleton instance
_attribution_system: Optional[AttributionSystem] = None


def get_attribution_system() -> AttributionSystem:
    """Get or create the global attribution system instance"""
    global _attribution_system
    if _attribution_system is None:
        _attribution_system = AttributionSystem()
    return _attribution_system
