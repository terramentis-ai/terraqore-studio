"""
Task 6 Self-Marketing API Routes
Handles attribution, achievements, and project exports
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import sys
from pathlib import Path

# Add core_clli to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'core_clli'))

from core.attribution_system import (
    get_attribution_system,
    CodeArtifactType,
    AttributionLevel,
    AttributionMetadata
)
from core.achievement_system import get_achievement_tracker, AchievementType
from core.export_system import get_export_manager, ExportFormat, ExportOptions

router = APIRouter(prefix="/api/task6", tags=["task6-marketing"])


# Request/Response Models
class AttributeCodeRequest(BaseModel):
    """Request to track code artifact"""
    artifact_name: str
    artifact_type: str  # From CodeArtifactType enum
    attribution_level: str  # From AttributionLevel enum
    project_id: int
    project_name: str
    agent_responsible: str
    quality_score: Optional[float] = None
    test_coverage: Optional[float] = None
    dependencies: Optional[List[str]] = None


class AttributionResponse(BaseModel):
    """Response with attribution metadata"""
    artifact_id: str
    artifact_name: str
    artifact_type: str
    attribution_level: str
    project_id: int
    project_name: str
    agent_responsible: str
    generation_timestamp: str
    quality_score: Optional[float]
    test_coverage: Optional[float]
    header_comment: str


class AchievementCheckRequest(BaseModel):
    """Request to check and award achievement"""
    achievement_type: str  # From AchievementType enum
    project_id: int
    project_name: str
    context_data: Optional[Dict[str, Any]] = None


class ExportProjectRequest(BaseModel):
    """Request to export project"""
    project_id: int
    project_name: str
    format: str = "markdown"  # markdown, json, html
    include_artifacts: bool = True
    include_achievements: bool = True
    include_metrics: bool = True


# Routes
@router.post("/attribute-code")
async def attribute_code(request: AttributeCodeRequest) -> AttributionResponse:
    """Track and attribute a code artifact"""
    try:
        attribution_system = get_attribution_system()
        
        # Convert string enums to actual enums
        artifact_type = CodeArtifactType(request.artifact_type)
        attribution_level = AttributionLevel(request.attribution_level)
        
        # Generate unique artifact ID
        artifact_id = f"{request.project_id}_{request.artifact_name}_{artifact_type.value}"
        
        # Track the artifact
        metadata = attribution_system.track_artifact(
            artifact_id=artifact_id,
            artifact_name=request.artifact_name,
            artifact_type=artifact_type,
            attribution_level=attribution_level,
            project_id=request.project_id,
            project_name=request.project_name,
            agent_responsible=request.agent_responsible,
            quality_score=request.quality_score,
            test_coverage=request.test_coverage,
            dependencies=request.dependencies
        )
        
        # Generate header comment
        header_comment = attribution_system.generate_header_comment(
            artifact_type=artifact_type,
            metadata=metadata
        )
        
        return AttributionResponse(
            artifact_id=metadata.artifact_id,
            artifact_name=metadata.artifact_name,
            artifact_type=metadata.artifact_type.value,
            attribution_level=metadata.attribution_level.value,
            project_id=metadata.project_id,
            project_name=metadata.project_name,
            agent_responsible=metadata.agent_responsible,
            generation_timestamp=metadata.generation_timestamp,
            quality_score=metadata.quality_score,
            test_coverage=metadata.test_coverage,
            header_comment=header_comment
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to attribute code: {str(e)}")


@router.get("/project-attributions/{project_id}")
async def get_project_attributions(project_id: int) -> Dict[str, Any]:
    """Get all attributions for a project"""
    try:
        attribution_system = get_attribution_system()
        attributions = attribution_system.get_project_attributions(project_id)
        
        return {
            'project_id': project_id,
            'total_attributions': len(attributions),
            'attributions': [attr.to_dict() for attr in attributions]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-achievement")
async def check_achievement(request: AchievementCheckRequest) -> Dict[str, Any]:
    """Check and potentially award an achievement"""
    try:
        achievement_tracker = get_achievement_tracker()
        
        # Convert string to enum
        achievement_type = AchievementType(request.achievement_type)
        
        # Check and award achievement
        achievement = achievement_tracker.check_achievement(
            achievement_type=achievement_type,
            project_id=request.project_id,
            project_name=request.project_name,
            context_data=request.context_data
        )
        
        if achievement:
            return {
                'success': True,
                'achievement': {
                    'type': achievement.achievement_type.value,
                    'name': achievement.badge_name,
                    'description': achievement.description,
                    'icon': achievement.icon,
                    'points': achievement.points,
                    'achieved_at': achievement.achieved_at
                }
            }
        else:
            return {
                'success': False,
                'message': 'Achievement not awarded'
            }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid achievement type: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project-achievements/{project_id}")
async def get_project_achievements(project_id: int) -> Dict[str, Any]:
    """Get all achievements and progress for a project"""
    try:
        achievement_tracker = get_achievement_tracker()
        progress = achievement_tracker.get_achievement_progress(project_id)
        
        return progress
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-project")
async def export_project(request: ExportProjectRequest) -> Dict[str, Any]:
    """Export project with achievements and attributions"""
    try:
        # This is a mock implementation
        # In production, would fetch actual project data
        
        project_data = {
            'id': request.project_id,
            'name': request.project_name,
            'status': 'in_progress',
            'completion_percentage': 75,
            'task_count': 12,
            'created_at': '2025-12-26T00:00:00Z',
            'description': f'Project: {request.project_name}'
        }
        
        attribution_system = get_attribution_system()
        achievement_tracker = get_achievement_tracker()
        export_manager = get_export_manager()
        
        # Get attributions and achievements
        attributions = attribution_system.get_project_attributions(request.project_id)
        attribution_summary = attribution_system.generate_project_summary(request.project_id)
        achievements = achievement_tracker.get_project_achievements(request.project_id)
        
        # Convert achievements to dict format
        achievement_dicts = [
            {
                'icon': a.icon,
                'badge_name': a.badge_name,
                'description': a.description,
                'achieved_at': a.achieved_at,
                'points': a.points
            }
            for a in achievements
        ]
        
        # Generate export
        export_format = ExportFormat(request.format)
        export_options = ExportOptions(
            format=export_format,
            include_artifacts=request.include_artifacts,
            include_achievements=request.include_achievements,
            include_metrics=request.include_metrics
        )
        
        export_content = export_manager.export_project_summary(
            project_data=project_data,
            attribution_summary=attribution_summary,
            achievements=achievement_dicts,
            options=export_options
        )
        
        return {
            'success': True,
            'project_id': request.project_id,
            'format': request.format,
            'content': export_content,
            'filename': f"{request.project_name.replace(' ', '_')}_export.{request.format}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project-summary/{project_id}")
async def get_project_summary(project_id: int) -> Dict[str, Any]:
    """Get complete project summary with all metadata"""
    try:
        attribution_system = get_attribution_system()
        achievement_tracker = get_achievement_tracker()
        
        attribution_summary = attribution_system.generate_project_summary(project_id)
        achievements = achievement_tracker.get_project_achievements(project_id)
        achievement_progress = achievement_tracker.get_achievement_progress(project_id)
        
        return {
            'project_id': project_id,
            'attribution_summary': attribution_summary['attribution_summary'],
            'achievements': {
                'earned': achievement_progress['achievements'],
                'available': achievement_progress['available_achievements'],
                'total_points': achievement_progress['total_points'],
                'completion_percentage': achievement_progress['completion_percentage']
            },
            'artifacts_count': len(attribution_summary.get('artifacts', []))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
