import sys
import os
import datetime
from pathlib import Path

# Add core to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.attribution_system import get_attribution_system, CodeArtifactType, AttributionLevel
from core.achievement_system import get_achievement_tracker, AchievementType
from core.state import get_state_manager, Project, ProjectStatus

def populate_demo_data():
    print("🎨 Populating Project Gallery with demo data...")
    
    # Initialize systems
    state_manager = get_state_manager()
    attr_system = get_attribution_system()
    ach_tracker = get_achievement_tracker()
    
    # Create a demo project
    project_name = "Flynt Demo Project"
    existing_project = state_manager.get_project(name=project_name)
    
    if existing_project:
        print(f"Project '{project_name}' already exists (ID: {existing_project.id})")
        project_id = existing_project.id
    else:
        print(f"Creating project: {project_name}")
        project = Project(
            id=0, # ID will be assigned by DB
            name=project_name,
            description="A demonstration of the FlyntCore self-marketing capabilities.",
            status=ProjectStatus.COMPLETED,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now()
        )
        project_id = state_manager.create_project(project)
    
    # Add some achievements
    print(f"🏆 Awarding achievements for project {project_id}...")
    achievements = [
        (AchievementType.PROJECT_CREATED, {}),
        (AchievementType.PROJECT_COMPLETED, {"completion_percentage": 100}),
        (AchievementType.ALL_WORKFLOWS, {"workflow_count": 5}),
        (AchievementType.HIGH_QUALITY, {"quality_score": 95}),
        (AchievementType.CODE_GENERATED, {"artifacts": 10})
    ]
    
    for ach_type, context in achievements:
        ach_tracker.check_achievement(project_id, ach_type, context)
        
    # Add some attributed artifacts
    print("📝 Creating attribution records...")
    artifacts = [
        ("main.py", CodeArtifactType.PYTHON_MODULE, "Core application entry point"),
        ("utils.ts", CodeArtifactType.TYPESCRIPT_FILE, "Frontend utility functions"),
        ("App.tsx", CodeArtifactType.REACT_COMPONENT, "Main React component"),
        ("settings.yaml", CodeArtifactType.CONFIG_FILE, "System configuration"),
        ("test_main.py", CodeArtifactType.TEST_FILE, "Main test suite")
    ]
    
    for name, type_, desc in artifacts:
        attr_system.track_artifact(
            artifact_id=f"{project_id}_{name}",
            artifact_name=name,
            artifact_type=type_,
            attribution_level=AttributionLevel.GENERATED,
            project_id=project_id,
            project_name=project_name,
            agent_responsible="CoderAgent",
            custom_metadata={
                "description": desc,
                "generator_model": "gemini-1.5-flash"
            }
        )
        
    print("\n✅ Demo data populated successfully!")
    print("👉 Go to the 'Project Gallery' (G) tab in the UI to see the results.")

if __name__ == "__main__":
    populate_demo_data()
