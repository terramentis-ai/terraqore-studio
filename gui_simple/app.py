"""
TerraQore Non-Technical UI
Streamlit-based interface for non-technical users.
Provides a wizard-driven, button-focused interface with visual feedback.
"""

import sys
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

import streamlit as st

# Add core_cli to path BEFORE any imports
_current_dir = Path(__file__).parent.resolve()
_parent_dir = _current_dir.parent
_core_cli_path = _parent_dir / "core_cli"

# Insert at beginning of path
sys.path.insert(0, str(_core_cli_path))

# Now import from core_cli modules
from core.state import get_state_manager, Project
from core.llm_client import create_llm_client_from_config
from orchestration.orchestrator import AgentOrchestrator
from templates.template_registry import get_template_registry, TemplateCategory

logger = logging.getLogger(__name__)


# Configure Streamlit page
st.set_page_config(
    page_title="TerraQore - Build with AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for non-technical UI
st.markdown("""
<style>
    /* Main container */
    .main-container {
        max-width: 1000px;
        margin: 0 auto;
        padding: 2rem;
    }
    
    /* Big buttons */
    .big-button {
        padding: 1.5rem;
        font-size: 1.2rem;
        border-radius: 0.5rem;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .big-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    /* Status indicators */
    .status-success {
        color: #10b981;
        font-weight: bold;
    }
    
    .status-pending {
        color: #f59e0b;
        font-weight: bold;
    }
    
    .status-error {
        color: #ef4444;
        font-weight: bold;
    }
    
    /* Progress bar styling */
    .progress-bar {
        height: 30px;
        border-radius: 10px;
        background: linear-gradient(90deg, #3b82f6, #10b981);
    }
    
    /* Template cards */
    .template-card {
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 1rem;
        transition: all 0.3s;
    }
    
    .template-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
    }
</style>
""", unsafe_allow_html=True)


class TerraQoreUIState:
    """Manages UI state for non-technical interface."""
    
    def __init__(self):
        """Initialize UI state."""
        if "page" not in st.session_state:
            st.session_state.page = "welcome"
        if "project_id" not in st.session_state:
            st.session_state.project_id = None
        if "selected_template" not in st.session_state:
            st.session_state.selected_template = None
        if "workflow_status" not in st.session_state:
            st.session_state.workflow_status = {}
    
    @property
    def page(self) -> str:
        """Get current page."""
        return st.session_state.page
    
    @page.setter
    def page(self, value: str) -> None:
        """Set current page."""
        st.session_state.page = value
    
    @property
    def project_id(self) -> Optional[int]:
        """Get current project ID."""
        return st.session_state.project_id
    
    @project_id.setter
    def project_id(self, value: Optional[int]) -> None:
        """Set current project ID."""
        st.session_state.project_id = value


def page_welcome():
    """Welcome page - show greeting and template selection."""
    st.markdown("# 🚀 Welcome to TerraQore")
    st.markdown("### Build Amazing Projects with AI")
    
    st.markdown("""
    TerraQore helps you create professional software projects without coding expertise.
    Just select what you want to build, and AI will handle the technical details.
    """)
    
    # Big call-to-action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📚 Browse Templates", key="browse_templates", use_container_width=True):
            ui_state.page = "templates"
            st.rerun()
    
    with col2:
        if st.button("✨ Start a New Project", key="new_project", use_container_width=True):
            ui_state.page = "wizard"
            st.rerun()
    
    st.markdown("---")
    
    # Show recent projects
    st.markdown("### 📋 Recent Projects")
    
    state_manager = get_state_manager()
    projects = state_manager.get_projects(limit=5)
    
    if projects:
        for project in projects:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{project.name}**")
                st.caption(project.description or "No description")
            with col2:
                status_color = {
                    "INITIALIZED": "🔵",
                    "PLANNING": "🟡",
                    "IN_PROGRESS": "🔵",
                    "COMPLETED": "🟢",
                    "FAILED": "🔴"
                }.get(project.status, "⚪")
                st.markdown(f"{status_color} {project.status}")
            with col3:
                if st.button("Open", key=f"open_{project.id}"):
                    ui_state.project_id = project.id
                    ui_state.page = "project"
                    st.rerun()
    else:
        st.info("No projects yet. Create your first one!")


def page_templates():
    """Templates browse page."""
    st.markdown("# 📚 Project Templates")
    st.markdown("Choose a template to get started")
    
    if st.button("← Back", key="back_from_templates"):
        ui_state.page = "welcome"
        st.rerun()
    
    st.markdown("---")
    
    # Category filter
    registry = get_template_registry()
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.markdown("### Filter by Category")
    with col2:
        category_options = ["All Templates"] + [cat.value.replace("_", " ").title() for cat in TemplateCategory]
        selected_category = st.selectbox("Category", category_options, key="template_category")
    
    # Filter templates
    if selected_category == "All Templates":
        templates = registry.list_templates()
    else:
        category = TemplateCategory[selected_category.upper().replace(" ", "_")]
        templates = registry.list_templates(category)
    
    # Display templates as cards
    st.markdown("---")
    
    for i, template in enumerate(templates):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### {template.name}")
            st.markdown(f"_{template.description}_")
            
            col_diff, col_hours, col_tech = st.columns(3)
            with col_diff:
                difficulty_emoji = {
                    "beginner": "🟢",
                    "intermediate": "🟡",
                    "advanced": "🔴"
                }.get(template.difficulty_level, "⚪")
                st.caption(f"{difficulty_emoji} {template.difficulty_level.title()}")
            with col_hours:
                st.caption(f"⏱️ ~{template.estimated_hours}h")
            with col_tech:
                st.caption(f"🔧 {len(template.technologies)} tech")
            
            st.caption(f"Technologies: {', '.join(template.technologies[:3])}")
        
        with col2:
            if st.button("Select", key=f"select_template_{template.id}", use_container_width=True):
                ui_state.selected_template = template.id
                ui_state.page = "template_details"
                st.rerun()
        
        st.divider()


def page_template_details():
    """Template details page."""
    registry = get_template_registry()
    template = registry.get_template(ui_state.selected_template)
    
    if not template:
        st.error("Template not found")
        return
    
    st.markdown(f"# {template.name}")
    st.markdown(template.description)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("← Back", key="back_from_details"):
            ui_state.page = "templates"
            st.rerun()
    with col2:
        if st.button("🚀 Create Project", key="create_from_template", use_container_width=True):
            # Create project from template
            state_manager = get_state_manager()
            project_name = f"{template.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            project = Project(
                name=project_name,
                description=template.description,
                status="INITIALIZED",
                metadata={
                    "template_id": template.id,
                    "template_name": template.name,
                    "estimated_hours": template.estimated_hours
                }
            )
            
            project_id = state_manager.create_project(project)
            ui_state.project_id = project_id
            ui_state.page = "project"
            st.rerun()
    
    st.markdown("---")
    
    # Template details
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Difficulty", template.difficulty_level.title())
    with col2:
        st.metric("Estimated Time", f"{template.estimated_hours}h")
    with col3:
        st.metric("Technologies", len(template.technologies))
    
    # Phases
    st.markdown("### 📋 Project Phases")
    for phase in template.workflow_phases:
        with st.expander(f"{phase.phase_name} (~{phase.expected_duration_hours}h)"):
            st.markdown(f"**{phase.description}**")
            st.markdown("Tasks:")
            for task in phase.tasks:
                st.markdown(f"- {task}")
    
    # Success criteria
    st.markdown("### ✅ Success Criteria")
    for criterion in template.success_criteria:
        st.markdown(f"- {criterion}")
    
    # Requirements
    st.markdown("### 📦 Requirements")
    for req in template.requirements:
        st.markdown(f"- **{req.package}** ({req.version}): {req.description}")


def page_project():
    """Project management page."""
    if not ui_state.project_id:
        st.error("No project selected")
        return
    
    state_manager = get_state_manager()
    project = state_manager.get_project(ui_state.project_id)
    
    if not project:
        st.error("Project not found")
        return
    
    st.markdown(f"# {project.name}")
    st.markdown(f"_{project.description}_")
    
    if st.button("← Back to Projects", key="back_to_projects"):
        ui_state.page = "welcome"
        st.rerun()
    
    st.markdown("---")
    
    # Project status
    col1, col2, col3 = st.columns(3)
    with col1:
        status_emoji = {
            "INITIALIZED": "🔵",
            "PLANNING": "🟡",
            "IN_PROGRESS": "🔵",
            "COMPLETED": "🟢",
            "FAILED": "🔴"
        }.get(project.status, "⚪")
        st.metric("Status", f"{status_emoji} {project.status}")
    with col2:
        tasks = state_manager.get_tasks(ui_state.project_id)
        completed = sum(1 for t in tasks if t.status == "COMPLETED")
        st.metric("Progress", f"{completed}/{len(tasks)} tasks")
    with col3:
        st.metric("Created", project.created_at[:10])
    
    st.markdown("---")
    
    # Workflow actions
    st.markdown("### 🎯 Workflow Actions")
    
    workflow_col1, workflow_col2, workflow_col3 = st.columns(3)
    
    with workflow_col1:
        if st.button("💡 Ideation", key="action_ideate", use_container_width=True):
            with st.spinner("Generating ideas..."):
                orchestrator = AgentOrchestrator()
                # TODO: Call ideation workflow
                st.success("Ideas generated! ✨")
                st.rerun()
    
    with workflow_col2:
        if st.button("📋 Planning", key="action_plan", use_container_width=True):
            with st.spinner("Creating plan..."):
                orchestrator = AgentOrchestrator()
                # TODO: Call planning workflow
                st.success("Plan created! 📊")
                st.rerun()
    
    with workflow_col3:
        if st.button("💻 Generate Code", key="action_code", use_container_width=True):
            with st.spinner("Generating code..."):
                orchestrator = AgentOrchestrator()
                # TODO: Call code generation workflow
                st.success("Code generated! 🚀")
                st.rerun()
    
    st.markdown("---")
    
    # Tasks list
    st.markdown("### 📝 Tasks")
    
    if tasks:
        for task in tasks:
            status_icon = {
                "PENDING": "⚪",
                "IN_PROGRESS": "🔵",
                "COMPLETED": "✅",
                "FAILED": "❌"
            }.get(task.status, "⚪")
            
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"{status_icon} **{task.title}**")
                if task.description:
                    st.caption(task.description)
            with col2:
                st.caption(task.agent_type or "Unknown")
    else:
        st.info("No tasks yet. Generate a plan to create tasks.")


def main():
    """Main application."""
    global ui_state
    ui_state = TerraQoreUIState()
    
    # Route to appropriate page
    if ui_state.page == "welcome":
        page_welcome()
    elif ui_state.page == "templates":
        page_templates()
    elif ui_state.page == "template_details":
        page_template_details()
    elif ui_state.page == "project":
        page_project()
    else:
        st.error(f"Unknown page: {ui_state.page}")


if __name__ == "__main__":
    main()
