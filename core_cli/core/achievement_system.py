"""
Achievement System for FlyntCore
Tracks project milestones, completion badges, and contributor statistics
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class AchievementType(Enum):
    """Types of achievements that can be earned"""
    PROJECT_CREATED = "project_created"
    PROJECT_COMPLETED = "project_completed"
    FIRST_WORKFLOW = "first_workflow"
    ALL_WORKFLOWS = "all_workflows"  # Ideate, Plan, Execute, Review
    ZERO_CONFLICTS = "zero_conflicts"
    TESTS_ADDED = "tests_added"
    HIGH_QUALITY = "high_quality"  # Quality score > 8
    FULL_COVERAGE = "full_coverage"  # Test coverage > 95%
    QUICK_EXECUTION = "quick_execution"  # Execution time < 30s
    CODE_GENERATED = "code_generated"  # At least 500 lines
    MULTI_AGENT = "multi_agent"  # Used 5+ different agents


@dataclass
class Achievement:
    """Represents a single achievement"""
    achievement_type: AchievementType
    project_id: int
    project_name: str
    achieved_at: str
    description: str
    icon: str
    points: int = 10
    badge_name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.badge_name:
            self.badge_name = self.achievement_type.value.replace('_', ' ').title()


class AchievementTracker:
    """
    Tracks achievements and milestones for projects
    """
    
    # Achievement definitions
    ACHIEVEMENT_DEFINITIONS = {
        AchievementType.PROJECT_CREATED: {
            "icon": "🎯",
            "name": "Project Founder",
            "description": "Created your first FlyntCore project",
            "points": 10
        },
        AchievementType.PROJECT_COMPLETED: {
            "icon": "🏆",
            "name": "Completion Master",
            "description": "Completed a project (100% of tasks)",
            "points": 50
        },
        AchievementType.FIRST_WORKFLOW: {
            "icon": "🚀",
            "name": "Workflow Explorer",
            "description": "Executed your first workflow",
            "points": 15
        },
        AchievementType.ALL_WORKFLOWS: {
            "icon": "⚡",
            "name": "Workflow Guru",
            "description": "Executed all 4 workflow types (Ideate, Plan, Execute, Review)",
            "points": 40
        },
        AchievementType.ZERO_CONFLICTS: {
            "icon": "✅",
            "name": "Dependency Master",
            "description": "Completed a project with zero dependency conflicts",
            "points": 30
        },
        AchievementType.TESTS_ADDED: {
            "icon": "✓",
            "name": "Test Pioneer",
            "description": "Added comprehensive tests using Test Critique Agent",
            "points": 25
        },
        AchievementType.HIGH_QUALITY: {
            "icon": "💎",
            "name": "Quality Enthusiast",
            "description": "Achieved code quality score > 8.0",
            "points": 35
        },
        AchievementType.FULL_COVERAGE: {
            "icon": "🛡️",
            "name": "Coverage Champion",
            "description": "Achieved 95%+ test coverage",
            "points": 45
        },
        AchievementType.QUICK_EXECUTION: {
            "icon": "⚡",
            "name": "Speed Demon",
            "description": "Completed workflow in under 30 seconds",
            "points": 20
        },
        AchievementType.CODE_GENERATED: {
            "icon": "📝",
            "name": "Code Generator",
            "description": "Generated 500+ lines of code",
            "points": 30
        },
        AchievementType.MULTI_AGENT: {
            "icon": "👥",
            "name": "Agent Orchestrator",
            "description": "Used 5+ different AI agents in a project",
            "points": 40
        },
    }
    
    def __init__(self):
        """Initialize achievement tracker"""
        self.achievements: Dict[int, List[Achievement]] = {}  # project_id -> achievements
    
    def check_achievement(
        self,
        achievement_type: AchievementType,
        project_id: int,
        project_name: str,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Achievement]:
        """Check if an achievement should be awarded"""
        
        if achievement_type not in self.ACHIEVEMENT_DEFINITIONS:
            return None
        
        definition = self.ACHIEVEMENT_DEFINITIONS[achievement_type]
        
        achievement = Achievement(
            achievement_type=achievement_type,
            project_id=project_id,
            project_name=project_name,
            achieved_at=datetime.now().isoformat(),
            description=definition["description"],
            icon=definition["icon"],
            points=definition["points"],
            badge_name=definition["name"],
            metadata=context_data or {}
        )
        
        if project_id not in self.achievements:
            self.achievements[project_id] = []
        
        self.achievements[project_id].append(achievement)
        return achievement
    
    def get_project_achievements(self, project_id: int) -> List[Achievement]:
        """Get all achievements for a project"""
        return self.achievements.get(project_id, [])
    
    def get_total_points(self, project_id: int) -> int:
        """Calculate total achievement points for a project"""
        achievements = self.get_project_achievements(project_id)
        return sum(a.points for a in achievements)
    
    def get_achievement_progress(
        self,
        project_id: int
    ) -> Dict[str, Any]:
        """Get achievement progress summary for a project"""
        
        achievements = self.get_project_achievements(project_id)
        achieved_types = {a.achievement_type for a in achievements}
        
        progress = {
            'project_id': project_id,
            'total_achievements': len(achievements),
            'total_points': self.get_total_points(project_id),
            'completion_percentage': (len(achieved_types) / len(AchievementType)) * 100,
            'achievements': [
                {
                    'type': a.achievement_type.value,
                    'name': a.badge_name,
                    'icon': a.icon,
                    'points': a.points,
                    'achieved_at': a.achieved_at,
                    'description': a.description
                }
                for a in achievements
            ],
            'available_achievements': [
                {
                    'type': at.value,
                    'name': self.ACHIEVEMENT_DEFINITIONS[at]["name"],
                    'icon': self.ACHIEVEMENT_DEFINITIONS[at]["icon"],
                    'points': self.ACHIEVEMENT_DEFINITIONS[at]["points"],
                    'description': self.ACHIEVEMENT_DEFINITIONS[at]["description"],
                    'earned': at in achieved_types
                }
                for at in AchievementType
            ]
        }
        
        return progress


# Global singleton instance
_achievement_tracker: Optional[AchievementTracker] = None


def get_achievement_tracker() -> AchievementTracker:
    """Get or create the global achievement tracker instance"""
    global _achievement_tracker
    if _achievement_tracker is None:
        _achievement_tracker = AchievementTracker()
    return _achievement_tracker
