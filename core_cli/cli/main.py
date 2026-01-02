"""
TerraQore CLI - Main Command Line Interface
Provides intuitive commands for interacting with TerraQore.
"""

import click
import logging
import json
from pathlib import Path
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_config_manager, ConfigManager
from core.state import get_state_manager, Project, ProjectStatus
from core.llm_client import create_llm_client_from_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.cwd() / "logs" / "terraqore.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print TerraQore banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ███████╗██╗  ██╗   ██╗███╗   ██╗████████╗                ║
║   ██╔════╝██║  ╚██╗ ██╔╝████╗  ██║╚══██╔══╝                ║
║   █████╗  ██║   ╚████╔╝ ██╔██╗ ██║   ██║                   ║
║   ██╔══╝  ██║    ╚██╔╝  ██║╚██╗██║   ██║                   ║
║   ██║     ███████╗██║   ██║ ╚████║   ██║                   ║
║   ╚═╝     ╚══════╝╚═╝   ╚═╝  ╚═══╝   ╚═╝                   ║
║                                                              ║
║        Your Personal Developer Assistant                    ║
║        For Agentic AI Projects                              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    click.echo(click.style(banner, fg='cyan', bold=True))


@click.group()
@click.version_option(version='0.1.0', prog_name='Flynt')
def cli():
    """TerraQore - Your Personal Developer Assistant for Agentic AI Projects.
    
    Build agentic AI projects from idea to deployment with AI-powered assistance.
    """
    pass


@cli.command()
def init():
    """Initialize TerraQore in the current directory."""
    print_banner()
    click.echo("\n🚀 Initializing TerraQore...\n")
    
    # Create config manager
    config_mgr = get_config_manager()
    config = config_mgr.load()
    
    # Check if using Ollama (which doesn't need API key) or if API keys are set
    using_ollama = config.primary_llm.provider == "ollama"
    
    if not using_ollama and not config.primary_llm.api_key:
        click.echo(click.style("⚠️  No API keys detected!", fg='yellow', bold=True))
        click.echo(config_mgr.get_api_key_instructions())
        click.echo("\nAfter setting API keys, run 'TerraQore init' again.")
        return
    
    # Initialize state manager
    state_mgr = get_state_manager()
    
    click.echo(click.style("✓", fg='green') + " Configuration loaded")
    click.echo(click.style("✓", fg='green') + " Database initialized")
    click.echo(click.style("✓", fg='green') + f" Primary LLM: {config.primary_llm.model} ({config.primary_llm.provider})")
    
    if config.fallback_llm and config.fallback_llm.api_key:
        click.echo(click.style("✓", fg='green') + f" Fallback LLM: {config.fallback_llm.model}")
    
    click.echo("\n" + click.style("✨ TerraQore is ready!", fg='green', bold=True))
    click.echo("\nNext steps:")
    click.echo("  1. Create a new project: TerraQore new 'My Project Name'")
    click.echo("  2. List projects: TerraQore list")
    click.echo("  3. Get help: TerraQore --help")


@cli.command()
@click.argument('name')
@click.option('--description', '-d', help='Project description')
def new(name: str, description: Optional[str]):
    """Create a new project.
    
    Example: TerraQore new "RAG Chatbot for Job Search"
    """
    click.echo(f"\n🎯 Creating new project: {name}\n")
    
    # Check if TerraQore is initialized
    config_mgr = get_config_manager()
    config = config_mgr.load()
    
    # Check if using Ollama or if API keys are set
    using_ollama = config.primary_llm.provider == "ollama"
    if not using_ollama and not config.primary_llm.api_key:
        click.echo(click.style("⚠️  TerraQore not initialized. Run 'TerraQore init' first.", fg='yellow'))
        return
    
    # Create project
    state_mgr = get_state_manager()
    
    # Check if project already exists
    existing = state_mgr.get_project(name=name)
    if existing:
        click.echo(click.style(f"⚠️  Project '{name}' already exists!", fg='yellow'))
        return
    
    project = Project(
        name=name,
        description=description or "",
        status=ProjectStatus.INITIALIZED.value
    )
    
    project_id = state_mgr.create_project(project)
    
    click.echo(click.style("✓", fg='green') + f" Project created (ID: {project_id})")
    click.echo("\nNext steps:")
    click.echo(f"  1. Start ideation: TerraQore ideate '{name}'")
    click.echo(f"  2. View project: TerraQore show '{name}'")


@cli.command()
@click.option('--status', '-s', help='Filter by status')
def list(status: Optional[str]):
    """List all projects."""
    state_mgr = get_state_manager()
    projects = state_mgr.list_projects(status=status)
    
    if not projects:
        click.echo("\n📭 No projects found.")
        click.echo("Create one with: TerraQore new 'Project Name'\n")
        return
    
    click.echo(f"\n📚 Your Projects ({len(projects)}):\n")
    
    for project in projects:
        status_color = {
            'initialized': 'cyan',
            'planning': 'yellow',
            'in_progress': 'blue',
            'completed': 'green',
            'blocked': 'red',
            'archived': 'white'
        }.get(project.status, 'white')
        
        click.echo(f"  • {click.style(project.name, bold=True)}")
        click.echo(f"    Status: {click.style(project.status, fg=status_color)}")
        if project.description:
            click.echo(f"    {project.description[:80]}...")
        click.echo(f"    Created: {project.created_at.split('T')[0]}")
        click.echo()


@cli.command()
@click.argument('name')
def show(name: str):
    """Show detailed information about a project."""
    state_mgr = get_state_manager()
    project = state_mgr.get_project(name=name)
    
    if not project:
        click.echo(click.style(f"⚠️  Project '{name}' not found.", fg='yellow'))
        return
    
    click.echo(f"\n📋 Project: {click.style(project.name, bold=True)}\n")
    click.echo(f"Status: {click.style(project.status, fg='cyan')}")
    click.echo(f"Created: {project.created_at}")
    click.echo(f"Updated: {project.updated_at}")
    
    if project.description:
        click.echo(f"\nDescription:\n  {project.description}")
    
    # Show tasks
    tasks = state_mgr.get_tasks(project.id)
    if tasks:
        click.echo(f"\n📝 Tasks ({len(tasks)}):")
        for task in tasks:
            status_icon = {
                'pending': '⏳',
                'in_progress': '🔄',
                'completed': '✅',
                'failed': '❌',
                'skipped': '⏭️'
            }.get(task.get('status'), '•')
            click.echo(f"  {status_icon} {task.get('title', 'Unknown')} ({task.get('status', 'unknown')})")


@cli.command()
@click.option('--details', is_flag=True, help='Show detailed provider messages')
def llm_health(details):
    """Run LLM health check and display results."""
    try:
        from core.llm_client import create_llm_client_from_config
        cfg = get_config_manager().load()
        client = create_llm_client_from_config(cfg)
        health = client.health_check()

        p = health.get('primary', {})
        f = health.get('fallback', {})

        if p.get('success'):
            click.echo(click.style(f"Primary provider OK: {p.get('message')}", fg='green'))
        else:
            click.echo(click.style(f"Primary provider issue: {p.get('message')}", fg='yellow'))

        if f.get('available'):
            if f.get('success'):
                click.echo(click.style(f"Fallback provider OK: {f.get('message')}", fg='green'))
            else:
                click.echo(click.style(f"Fallback provider issue: {f.get('message')}", fg='yellow'))
        else:
            click.echo(click.style("No fallback provider configured or available.", fg='yellow'))

        if details:
            click.echo('\nFull health details:')
            click.echo(json.dumps(health, indent=2))

    except Exception as e:
        logger.error(f"LLM health check failed: {e}", exc_info=True)
        click.echo(click.style(f"Error checking LLM health: {e}", fg='red'))


@cli.command()
@click.argument('name')
@click.option('--input', '-i', help='Additional guidance for ideation')
def ideate(name: str, input: Optional[str]):
    """Start ideation phase for a project.
    
    This will use the Idea Agent to research trends, brainstorm variations,
    and create an actionable project plan.
    
    Example: TerraQore ideate "My Project" -i "Focus on simplicity"
    """
    click.echo(f"\n💡 Starting Ideation for: {click.style(name, bold=True)}\n")
    
    state_mgr = get_state_manager()
    project = state_mgr.get_project(name=name)
    
    if not project:
        click.echo(click.style(f"⚠️  Project '{name}' not found.", fg='yellow'))
        click.echo("Create it first with: TerraQore new 'Project Name'")
        return
    
    # Import orchestrator
    from orchestration.orchestrator import get_orchestrator
    
    click.echo("🔍 Researching current trends...")
    click.echo("💭 Generating project variations...")
    click.echo("✨ Refining recommendations...\n")
    
    with click.progressbar(length=100, label='Processing') as bar:
        # Get orchestrator
        orchestrator = get_orchestrator()
        
        # Run ideation
        bar.update(30)
        result = orchestrator.run_ideation(project.id, user_input=input)
        bar.update(70)
    
    click.echo("\n")
    
    if result.success:
        click.echo(click.style("✓ Ideation Complete!", fg='green', bold=True))
        click.echo("\n" + "="*70)
        click.echo(result.output)
        click.echo("="*70)
        
        # Show execution stats
        click.echo(f"\n⏱️  Completed in {result.execution_time:.2f}s")
        click.echo(f"🔎 Research queries: {result.metadata.get('research_count', 0)}")
        
        # Save to file
        output_file = Path.cwd() / f"{name.replace(' ', '_')}_ideation.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.output)
        click.echo(f"\n💾 Saved to: {output_file}")
        
        click.echo("\n" + click.style("Next Steps:", bold=True))
        click.echo(f"  1. Review the ideation results above")
        click.echo(f"  2. Plan tasks: TerraQore plan '{name}' (Coming Soon)")
        click.echo(f"  3. View project: TerraQore show '{name}'")


@cli.command()
@click.argument('name')
@click.option('--input', '-i', help='Additional guidance for planning')
def plan(name: str, input: Optional[str]):
    """Break down project into actionable tasks.
    
    This will use the Planner Agent to create a detailed task breakdown
    with dependencies, milestones, and estimates.
    
    Example: TerraQore plan "My Project" -i "Focus on MVP features only"
    """
    click.echo(f"\n📋 Starting Planning for: {click.style(name, bold=True)}\n")
    
    state_mgr = get_state_manager()
    project = state_mgr.get_project(name=name)
    
    if not project:
        click.echo(click.style(f"⚠️  Project '{name}' not found.", fg='yellow'))
        click.echo("Create it first with: TerraQore new 'Project Name'")
        return
    
    # Import orchestrator
    from orchestration.orchestrator import get_orchestrator
    
    click.echo("🔍 Analyzing project requirements...")
    click.echo("📝 Generating task breakdown...")
    click.echo("🔗 Identifying dependencies...\n")
    
    with click.progressbar(length=100, label='Planning') as bar:
        # Get orchestrator
        orchestrator = get_orchestrator()
        
        # Run planning
        bar.update(30)
        result = orchestrator.run_planning(project.id, user_input=input)
        bar.update(70)
    
    click.echo("\n")
    
    if result.success:
        click.echo(click.style("✓ Planning Complete!", fg='green', bold=True))
        click.echo("\n" + "="*70)
        click.echo(result.output)
        click.echo("="*70)
        
        # Show execution stats
        click.echo(f"\n⏱️  Completed in {result.execution_time:.2f}s")
        click.echo(f"📊 Tasks created: {result.metadata.get('tasks_created', 0)}")
        click.echo(f"🎯 Milestones: {len(result.metadata.get('milestones', []))}")
        click.echo(f"⏰ Total estimated: {result.metadata.get('total_estimated_hours', 0):.1f} hours")
        
        # Save to file
        output_file = Path.cwd() / f"{name.replace(' ', '_')}_plan.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.output)
        click.echo(f"\n💾 Saved to: {output_file}")
        
        click.echo("\n" + click.style("Next Steps:", bold=True))
        click.echo(f"  1. Review the task breakdown above")
        click.echo(f"  2. View tasks: TerraQore tasks '{name}'")
        click.echo(f"  3. Start execution: TerraQore run '{name}' (Coming Soon)")
    else:
        click.echo(click.style("✗ Planning Failed", fg='red', bold=True))
        click.echo(f"Error: {result.error}")
        click.echo("\nTry again or check logs: logs/terraqore.log")


@cli.command()
@click.argument('name')
@click.option('--milestone', '-m', help='Filter by milestone')
@click.option('--status', '-s', help='Filter by status')
def tasks(name: str, milestone: Optional[str], status: Optional[str]):
    """View tasks for a project.
    
    Example: TerraQore tasks "My Project"
    Example: TerraQore tasks "My Project" -m "Setup"
    Example: TerraQore tasks "My Project" -s "pending"
    """
    state_mgr = get_state_manager()
    project = state_mgr.get_project(name=name)
    
    if not project:
        click.echo(click.style(f"⚠️  Project '{name}' not found.", fg='yellow'))
        return
    
    # Get tasks
    if milestone:
        all_tasks = state_mgr.get_tasks_by_milestone(project.id, milestone)
    else:
        all_tasks = state_mgr.get_tasks(project.id, status=status)
    
    if not all_tasks:
        click.echo(f"\n📭 No tasks found for '{name}'")
        if not milestone and not status:
            click.echo(f"\nCreate tasks with: TerraQore plan '{name}'")
        return
    
    click.echo(f"\n📝 Tasks for: {click.style(name, bold=True)}")
    
    # Group by milestone
    milestones = {}
    for task in all_tasks:
        ms = task.milestone or "No Milestone"
        if ms not in milestones:
            milestones[ms] = []
        milestones[ms].append(task)
    
    # Display tasks
    total_hours = 0
    for ms_name, ms_tasks in milestones.items():
        ms_hours = sum(t.estimated_hours or 0 for t in ms_tasks)
        total_hours += ms_hours
        
        click.echo(f"\n🎯 {click.style(ms_name, bold=True)} ({len(ms_tasks)} tasks, ~{ms_hours:.1f}h)")
        
        for task in ms_tasks:
            # Status icon
            status_icon = {
                'pending': '⏳',
                'in_progress': '🔄',
                'completed': '✅',
                'failed': '❌',
                'skipped': '⏭️'
            }.get(task.status, '•')
            
            # Priority color
            priority_icon = {0: "🟢", 1: "🟡", 2: "🔴"}[task.priority]
            
            # Dependencies
            deps_str = ""
            if task.dependencies:
                deps_str = click.style(f" [{len(task.dependencies)} deps]", fg='cyan')
            
            click.echo(f"  {status_icon} {priority_icon} {task.title} (~{task.estimated_hours or 0}h){deps_str}")
            
            if task.description and len(task.description) > 0:
                desc_preview = task.description[:80] + "..." if len(task.description) > 80 else task.description
                click.echo(f"      {click.style(desc_preview, fg='white', dim=True)}")
    
    # Summary
    click.echo(f"\n📊 Summary:")
    click.echo(f"  Total tasks: {len(all_tasks)}")
    click.echo(f"  Total estimated: {total_hours:.1f} hours")
    
    # Show available tasks (no pending dependencies)
    available = state_mgr.get_available_tasks(project.id)
    if available:
        click.echo(f"  ✨ Ready to start: {len(available)} tasks")


@cli.command()
@click.argument('name')
def roadmap(name: str):
    """View project roadmap with milestones.
    
    Example: TerraQore roadmap "My Project"
    """
    state_mgr = get_state_manager()
    project = state_mgr.get_project(name=name)
    
    if not project:
        click.echo(click.style(f"⚠️  Project '{name}' not found.", fg='yellow'))
        return
    
    all_tasks = state_mgr.get_tasks(project.id)
    
    if not all_tasks:
        click.echo(f"\n📭 No tasks found. Create a plan first:")
        click.echo(f"  TerraQore plan '{name}'")
        return
    
    click.echo(f"\n🗺️  Roadmap for: {click.style(name, bold=True)}\n")
    
    # Group by milestone
    milestones = {}
    for task in all_tasks:
        ms = task.milestone or "No Milestone"
        if ms not in milestones:
            milestones[ms] = {
                'tasks': [],
                'completed': 0,
                'total': 0,
                'hours': 0
            }
        milestones[ms]['tasks'].append(task)
        milestones[ms]['total'] += 1
        milestones[ms]['hours'] += task.estimated_hours or 0
        if task.status == 'completed':
            milestones[ms]['completed'] += 1
    
    # Display roadmap
    for ms_name, ms_data in milestones.items():
        progress = (ms_data['completed'] / ms_data['total'] * 100) if ms_data['total'] > 0 else 0
        
        # Progress bar
        bar_length = 30
        filled = int(bar_length * progress / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        status_color = 'green' if progress == 100 else 'yellow' if progress > 0 else 'white'
        
        click.echo(f"🎯 {click.style(ms_name, bold=True)}")
        click.echo(f"   [{bar}] {progress:.0f}%")
        click.echo(f"   {ms_data['completed']}/{ms_data['total']} tasks • ~{ms_data['hours']:.1f}h\n")
    
    # Overall stats
    total_tasks = len(all_tasks)
    completed_tasks = sum(1 for t in all_tasks if t.status == 'completed')
    overall_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    click.echo("="*50)
    click.echo(f"Overall Progress: {overall_progress:.0f}% ({completed_tasks}/{total_tasks} tasks)")
    click.echo("="*50)


@cli.command()
@click.argument('project')
@click.option('--output', '-o', help='Output file for test scaffold')
def test_critique(project, output):
    """Analyze project codebase and generate test recommendations.
    
    Examines code structure, complexity, and identifies areas needing test coverage.
    Generates test scaffolds for critical functions.
    
    Example: TerraQore test-critique "My Project" -o tests/
    """
    try:
        from orchestration.orchestrator import AgentOrchestrator
        from agents.base import AgentContext
        
        state_mgr = get_state_manager()
        project_id = state_mgr.get_project_id(project)
        
        if not project_id:
            click.echo(click.style(f"❌ Project not found: {project}", fg='red'))
            return
        
        click.echo(f"\n🧪 Test Critique for: {click.style(project, bold=True)}\n")
        
        # Get orchestrator and run test critique
        from core.config import get_config_manager
        config = get_config_manager().load()
        llm_client = create_llm_client_from_config(config)
        orchestrator = AgentOrchestrator(llm_client)
        
        # Get test critique agent
        from agents.test_critique_agent import TestCritiqueAgent
        agent = TestCritiqueAgent(llm_client, verbose=True)
        
        click.echo("📊 Analyzing codebase...")
        click.echo("🔍 Scanning classes and functions...")
        click.echo("⚙️  Estimating test coverage...\n")
        
        # Create context
        context = AgentContext(
            project_id=project_id,
            task_id=None,
            user_input="Analyze and critique test coverage",
            previous_output="",
            metadata={
                "project_root": Path.cwd() / "projects" / project
            }
        )
        
        # Run agent
        result = agent.execute(context)
        
        if result.success:
            click.echo(click.style("✓ Analysis Complete!\n", fg='green', bold=True))
            click.echo(result.output)
            
            # Optionally save to file
            if output:
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(result.output)
                click.echo(click.style(f"\n✅ Report saved to: {output_path}", fg='green'))
        else:
            click.echo(click.style(f"❌ Analysis failed: {result.error}", fg='red'))
    
    except Exception as e:
        logger.error(f"Test critique error: {str(e)}", exc_info=True)
        click.echo(click.style(f"❌ Error: {str(e)}", fg='red'))


@cli.command()
def status():
    """Show TerraQore system status."""
    click.echo("\n🔍 TerraQore Status\n")
    
    # Check configuration
    config_mgr = get_config_manager()
    config = config_mgr.load()
    
    click.echo("Configuration:")
    click.echo(f"  Primary LLM: {config.primary_llm.provider} ({config.primary_llm.model})")
    click.echo(f"  API Key Set: {click.style('Yes' if config.primary_llm.api_key else 'No', fg='green' if config.primary_llm.api_key else 'red')}")
    
    if config.fallback_llm:
        click.echo(f"  Fallback LLM: {config.fallback_llm.provider} ({config.fallback_llm.model})")
        click.echo(f"  Fallback Key Set: {click.style('Yes' if config.fallback_llm.api_key else 'No', fg='green' if config.fallback_llm.api_key else 'yellow')}")
    
    # Check projects
    state_mgr = get_state_manager()
    projects = state_mgr.list_projects()
    
    click.echo(f"\nProjects: {len(projects)}")
    if projects:
        status_counts = {}
        for p in projects:
            status_counts[p.status] = status_counts.get(p.status, 0) + 1
        for status, count in status_counts.items():
            click.echo(f"  {status}: {count}")


@cli.command()
def config():
    """Show or edit configuration."""
    config_mgr = get_config_manager()
    config_path = config_mgr.config_path
    
    click.echo(f"\n⚙️  Configuration File: {config_path}\n")
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            content = f.read()
        click.echo(content)
    
    click.echo("\nTo edit configuration:")
    click.echo(f"  1. Open: {config_path}")
    click.echo("  2. Modify settings")
    click.echo("  3. Restart Flynt")
    
    click.echo("\nAPI Key Setup:")
    click.echo(get_config_manager().get_api_key_instructions())


# ============================================================================
# PHASE 4: CODE GENERATION & EXECUTION COMMANDS
# ============================================================================

@cli.command()
@click.argument('project')
@click.option('--task-id', type=int, help='Execute specific task')
@click.option('--auto', is_flag=True, help='Auto-execute all pending tasks')
@click.option('--approve-all', is_flag=True, help='Auto-approve all generated code')
@click.option('--test-mode', is_flag=True, help='Use deterministic stub code generation (no LLM)')
def execute(project, task_id, auto, approve_all, test_mode):
    """Execute tasks and generate code for a project.
    
    Examples:
        TerraQore execute "Project Name"              # Execute next pending task
        TerraQore execute "Project Name" --task-id 5  # Execute specific task
        TerraQore execute "Project Name" --auto       # Auto-execute all tasks
        TerraQore execute "Project Name" --auto --approve-all  # Full automation
    """
    try:
        from orchestration.executor import ExecutionEngine
        
        state_mgr = get_state_manager()
        project_id = state_mgr.get_project_id(project)
        
        if not project_id:
            click.echo(click.style(f"❌ Project not found: {project}", fg='red'))
            return
        
        # Get project root
        project_root = Path.cwd() / "projects" / project
        
        # Create execution engine
        executor = ExecutionEngine(project, state_mgr, str(project_root), test_mode=test_mode)
        
        if auto:
            click.echo(f"\n🚀 Auto-executing all pending tasks for '{project}'...\n")
            summary = executor.execute_all_pending_tasks(auto_approve=approve_all)
            
            if "error" not in summary:
                click.echo(click.style(f"✅ {summary['message']}", fg='green'))
                click.echo(f"  Completed: {summary['completed']}")
                click.echo(f"  Failed: {summary['failed']}")
                click.echo(f"  Skipped: {summary['skipped']}")
            else:
                click.echo(click.style(f"❌ {summary['error']}", fg='red'))
        
        elif task_id:
            click.echo(f"\n⚙️  Executing task {task_id}...\n")
            success, msg = executor.execute_task(task_id, auto_approve=approve_all)
            
            if success:
                click.echo(click.style(f"✅ {msg}", fg='green'))
            else:
                click.echo(click.style(f"❌ {msg}", fg='red'))
        
        else:
            click.echo(f"\n⚙️  Executing next pending task for '{project}'...\n")
            pending = executor.get_pending_tasks()
            
            if not pending:
                click.echo(click.style("✅ No pending tasks!", fg='green'))
                return
            
            # Execute first pending task
            task = pending[0]
            success, msg = executor.execute_task(task["id"], auto_approve=approve_all)
            
            if success:
                click.echo(click.style(f"✅ {msg}", fg='green'))
            else:
                click.echo(click.style(f"❌ {msg}", fg='red'))
        
        # Show pending approvals if not auto-approved
        if not approve_all:
            approvals = executor.get_pending_approvals()
            if approvals:
                click.echo(f"\n⏳ Pending approvals: {len(approvals)}")
                click.echo("Run 'TerraQore review <project>' to review and approve")
    
    except Exception as e:
        logger.error(f"Execution failed: {str(e)}", exc_info=True)
        click.echo(click.style(f"❌ Error: {str(e)}", fg='red'))


@cli.command()
@click.argument('project')
@click.option('--task-id', type=int, help='Generate code for specific task')
@click.option('--test-mode', is_flag=True, help='Use deterministic stub code generation (no LLM)')
def code(project, task_id, test_mode):
    """Generate code for tasks without executing.
    
    Shows generated code for review before applying to project.
    
    Examples:
        TerraQore code "Project Name"            # Show generated code for next task
        TerraQore code "Project Name" --task-id 3  # Show code for specific task
    """
    try:
        from orchestration.executor import ExecutionEngine
        
        state_mgr = get_state_manager()
        project_id = state_mgr.get_project_id(project)
        
        if not project_id:
            click.echo(click.style(f"❌ Project not found: {project}", fg='red'))
            return
        
        project_root = Path.cwd() / "projects" / project
        executor = ExecutionEngine(project, state_mgr, str(project_root), test_mode=test_mode)
        
        if task_id:
            task = executor._get_task_by_id(project_id, task_id)
            if not task:
                click.echo(click.style(f"❌ Task {task_id} not found", fg='red'))
                return
        else:
            pending = executor.get_pending_tasks()
            if not pending:
                click.echo(click.style("✅ No pending tasks", fg='green'))
                return
            task = pending[0]
        
        click.echo(f"\n📝 Generating code for: {task['title']}\n")
        
        success, code_gen = executor.generate_code_for_task(task)
        
        if success and code_gen:
            click.echo(click.style("✅ Code generated successfully!\n", fg='green'))
            click.echo(f"Language: {click.style(code_gen.language.upper(), bold=True)}")
            click.echo(f"Files: {len(code_gen.files)}")
            click.echo(f"\nFiles to be created:")
            
            for file in code_gen.files:
                click.echo(f"  📄 {click.style(file.path, fg='cyan')}")
                click.echo(f"     {file.description}")
            
            click.echo(f"\nSummary: {code_gen.summary}")
            click.echo(f"\nExecution: {code_gen.execution_notes}")
            
            click.echo(f"\n💾 Run 'TerraQore review {project}' to apply code")
        else:
            click.echo(click.style("❌ Code generation failed", fg='red'))
    
    except Exception as e:
        logger.error(f"Code generation failed: {str(e)}", exc_info=True)
        click.echo(click.style(f"❌ Error: {str(e)}", fg='red'))


@cli.command()
@click.argument('project')
@click.option('--approve', is_flag=True, help='Approve and apply all pending code')
@click.option('--reject', is_flag=True, help='Reject pending code')
def review(project, approve, reject):
    """Review and approve generated code.
    
    Examples:
        TerraQore review "Project Name"           # Show pending code
        TerraQore review "Project Name" --approve # Apply all pending code
        TerraQore review "Project Name" --reject  # Reject pending code
    """
    try:
        from orchestration.executor import ExecutionEngine
        
        state_mgr = get_state_manager()
        project_id = state_mgr.get_project_id(project)
        
        if not project_id:
            click.echo(click.style(f"❌ Project not found: {project}", fg='red'))
            return
        
        project_root = Path.cwd() / "projects" / project
        executor = ExecutionEngine(project, state_mgr, str(project_root))
        
        pending = executor.get_pending_approvals()
        
        if not pending:
            click.echo(click.style("✅ No pending code to review", fg='green'))
            return
        
        click.echo(f"\n📋 Pending Code Review ({len(pending)} items)\n")
        
        for task_id, code_info in pending.items():
            click.echo(f"Task #{task_id}: {click.style(code_info['task_title'], bold=True)}")
            click.echo(f"  Language: {code_info['language']}")
            click.echo(f"  Files: {code_info['files']}")
            click.echo(f"  {code_info['summary']}\n")
        
        if approve:
            click.echo("Applying all pending code...\n")
            for task_id in pending.keys():
                success, msg = executor.approve_and_apply_code(task_id, approve=True)
                status = "✅" if success else "❌"
                click.echo(f"{status} Task #{task_id}: {msg}")
            
            click.echo("\n✅ Code applied successfully!")
        
        elif reject:
            click.echo("Rejecting all pending code...\n")
            for task_id in pending.keys():
                success, msg = executor.approve_and_apply_code(task_id, approve=False)
                status = "✅" if success else "❌"
                click.echo(f"{status} Task #{task_id}: {msg}")
            
            click.echo("\n✅ Code rejected")
        
        else:
            click.echo("Use --approve to apply code or --reject to decline")
    
    except Exception as e:
        logger.error(f"Review failed: {str(e)}", exc_info=True)
        click.echo(click.style(f"❌ Error: {str(e)}", fg='red'))


@cli.command()
@click.argument('project')
def history(project):
    """Show execution history for a project.
    
    Displays all code generations, approvals, and task completions.
    """
    try:
        from orchestration.executor import ExecutionEngine
        
        state_mgr = get_state_manager()
        project_id = state_mgr.get_project_id(project)
        
        if not project_id:
            click.echo(click.style(f"❌ Project not found: {project}", fg='red'))
            return
        
        project_root = Path.cwd() / "projects" / project
        executor = ExecutionEngine(project, state_mgr, str(project_root))
        
        log = executor.get_execution_log()
        
        if not log:
            click.echo(click.style("✅ No execution history", fg='green'))
            return
        
        click.echo(f"\n📜 Execution History for '{project}'\n")
        
        for entry in log:
            timestamp = entry['timestamp']
            action = entry['action']
            task_id = entry['task_id']
            
            action_emoji = {
                'code_generated': '✏️',
                'code_approved': '✅',
                'code_applied': '💾',
                'code_rejected': '❌',
                'execution_error': '⚠️'
            }.get(action, '📝')
            
            click.echo(f"{action_emoji} [{timestamp}] Task #{task_id}: {action}")
        
        # Show summary
        summary = executor.get_execution_summary()
        click.echo(f"\n📊 Summary:")
        click.echo(f"  Total Tasks: {summary.get('total_tasks', 0)}")
        click.echo(f"  Files Created: {summary.get('files_created', 0)}")
        click.echo(f"  Files Modified: {summary.get('files_modified', 0)}")
        click.echo(f"  Pending Approvals: {summary.get('pending_approvals', 0)}")
    
    except Exception as e:
        logger.error(f"History retrieval failed: {str(e)}", exc_info=True)
        click.echo(click.style(f"❌ Error: {str(e)}", fg='red'))


@cli.command()
@click.argument('project')
def rollback(project):
    """Rollback last file operation.
    
    Restores files from backup if available.
    """
    try:
        from orchestration.executor import ExecutionEngine
        
        state_mgr = get_state_manager()
        project_id = state_mgr.get_project_id(project)
        
        if not project_id:
            click.echo(click.style(f"❌ Project not found: {project}", fg='red'))
            return
        
        project_root = Path.cwd() / "projects" / project
        executor = ExecutionEngine(project, state_mgr, str(project_root))
        
        success, msg = executor.file_ops.rollback_last_change()
        
        if success:
            click.echo(click.style(f"✅ {msg}", fg='green'))
        else:
            click.echo(click.style(f"❌ {msg}", fg='red'))
    
    except Exception as e:
        logger.error(f"Rollback failed: {str(e)}", exc_info=True)
        click.echo(click.style(f"❌ Error: {str(e)}", fg='red'))


@cli.command()
@click.argument('project')
def conflicts(project):
    """Display dependency conflicts blocking a project.
    
    Shows all dependency conflicts preventing the project from proceeding,
    with suggestions for resolution.
    """
    try:
        from core.psmp_orchestrator_bridge import get_psmp_bridge
        
        state_mgr = get_state_manager()
        project_id = state_mgr.get_project_id(project)
        
        if not project_id:
            click.echo(click.style(f"❌ Project not found: {project}", fg='red'))
            return
        
        bridge = get_psmp_bridge()
        report = bridge.get_blocking_report(project_id)
        
        click.echo(report)
        
    except Exception as e:
        logger.error(f"Error retrieving conflicts: {str(e)}", exc_info=True)
        click.echo(click.style(f"❌ Error: {str(e)}", fg='red'))


@cli.command()
@click.argument('project')
def resolve_conflicts(project):
    """Run the conflict resolver agent to analyze and recommend solutions.
    
    The resolver agent will analyze blocking dependency conflicts and generate
    recommendations for resolution. After running this, review suggestions and
    use 'TerraQore unblock-project' to apply a resolution.
    """
    try:
        from core.psmp_orchestrator_bridge import get_psmp_bridge
        
        state_mgr = get_state_manager()
        project_id = state_mgr.get_project_id(project)
        
        if not project_id:
            click.echo(click.style(f"❌ Project not found: {project}", fg='red'))
            return
        
        bridge = get_psmp_bridge()
        
        # Check if project is blocked
        is_blocked, reason = bridge.check_project_blocked(project_id)
        if not is_blocked:
            click.echo(click.style("✅ Project is not blocked. No resolution needed.", fg='green'))
            return
        
        click.echo(click.style("🔍 Analyzing conflicts...", fg='cyan'))
        
        result_message = bridge.trigger_conflict_resolver(project_id)
        click.echo(result_message)
        
    except Exception as e:
        logger.error(f"Error running conflict resolver: {str(e)}", exc_info=True)
        click.echo(click.style(f"❌ Error: {str(e)}", fg='red'))


@cli.command()
@click.argument('project')
@click.option('--library', '-l', help='Specific library to resolve')
@click.option('--version', '-v', help='Version to use for resolution')
def unblock_project(project, library, version):
    """Manually resolve conflicts and unblock a project.
    
    After running 'TerraQore resolve-conflicts' and reviewing recommendations,
    use this command to apply a resolution and unblock the project.
    
    Examples:
        TerraQore unblock-project MyProject --library pandas --version 2.0
        TerraQore unblock-project MyProject  # Show interactive resolution options
    """
    try:
        from core.psmp import get_psmp_service
        
        state_mgr = get_state_manager()
        project_id = state_mgr.get_project_id(project)
        
        if not project_id:
            click.echo(click.style(f"❌ Project not found: {project}", fg='red'))
            return
        
        psmp = get_psmp_service()
        
        # Check if project is blocked
        from core.psmp_orchestrator_bridge import get_psmp_bridge
        bridge = get_psmp_bridge()
        is_blocked, _ = bridge.check_project_blocked(project_id)
        
        if not is_blocked:
            click.echo(click.style("✅ Project is not blocked.", fg='green'))
            return
        
        # Get conflicts
        conflicts = psmp.get_blocking_conflicts(project_id)
        
        if not conflicts:
            click.echo(click.style("No conflicts found.", fg='yellow'))
            return
        
        # If library and version specified, resolve directly
        if library and version:
            success = psmp.resolve_conflict_manual(project_id, library, version)
            if success:
                click.echo(click.style(f"✅ Conflict resolved: {library}=={version}", fg='green'))
                click.echo(click.style(f"✅ Project unblocked: {project}", fg='green'))
            else:
                click.echo(click.style(f"❌ Failed to resolve conflict for {library}", fg='red'))
        else:
            # Show options and prompt user
            click.echo(click.style("\n📋 Blocking Conflicts:\n", fg='cyan'))
            
            for i, conflict in enumerate(conflicts, 1):
                click.echo(f"\n{i}. {conflict.library}")
                click.echo(f"   Requirements:")
                for req in conflict.requirements:
                    click.echo(f"     • {req['agent']}: {req['needs']} ({req['purpose']})")
                click.echo(f"   Suggestions:")
                for j, suggestion in enumerate(conflict.suggested_resolutions[:3], 1):
                    click.echo(f"     {j}. {suggestion}")
            
            click.echo(click.style("\nTo resolve, use:", fg='yellow'))
            click.echo("  TerraQore unblock-project PROJECT --library LIBRARY --version VERSION")
        
    except Exception as e:
        logger.error(f"Error unblocking project: {str(e)}", exc_info=True)
        click.echo(click.style(f"❌ Error: {str(e)}", fg='red'))


@cli.command()
@click.argument('project')
def manifest(project):
    """Display unified dependency manifest for project.
    
    Shows all dependencies declared by agents, organized by scope (runtime/dev/build).
    Can be used to generate requirements.txt.
    """
    try:
        from core.psmp import get_psmp_service
        
        state_mgr = get_state_manager()
        project_id = state_mgr.get_project_id(project)
        
        if not project_id:
            click.echo(click.style(f"❌ Project not found: {project}", fg='red'))
            return
        
        psmp = get_psmp_service()
        manifest_content = psmp.get_unified_manifest(project_id)
        
        click.echo(click.style("📋 Unified Dependencies Manifest:\n", fg='cyan'))
        click.echo(manifest_content)
        
        # Offer to save to file
        if click.confirm("\nSave to requirements.txt?"):
            output_file = Path.cwd() / "projects" / project / "requirements.txt"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(manifest_content)
            click.echo(click.style(f"✅ Saved to {output_file}", fg='green'))
        
    except Exception as e:
        logger.error(f"Error generating manifest: {str(e)}", exc_info=True)
        click.echo(click.style(f"❌ Error: {str(e)}", fg='red'))


@cli.command()
@click.option('--organization', '-o', help='Organization / tenant for audit logs')
@click.option('--agent', '-a', help='Filter entries by agent name')
@click.option('--limit', '-n', default=20, show_default=True, type=int,
              help='Number of most recent entries to display (0 = all)')
@click.option('--report', is_flag=True, help='Show aggregated compliance report')
@click.option('--json-output', is_flag=True, help='Print raw JSON for each entry')
@click.option('--log-path', help='Override path to audit log file')
def audit(organization, agent, limit, report, json_output, log_path):
    """Inspect SecureGateway compliance audit logs (Phase 5)."""

    org = organization or os.getenv('TERRAQORE_ORGANIZATION', 'default')
    log_file = Path(log_path) if log_path else Path('core_cli') / 'logs' / f'compliance_audit_{org}.jsonl'

    click.echo(click.style("\n🔐 SecureGateway Compliance Audit", fg='cyan', bold=True))
    click.echo(f"Organization: {org}")
    click.echo(f"Audit file: {log_file}\n")

    if not log_file.exists():
        click.echo(click.style("No audit log found yet. Run agent workflows to generate entries.", fg='yellow'))
        return

    try:
        from core.secure_gateway import ComplianceAuditor

        auditor = ComplianceAuditor(organization=org, log_file=str(log_file))
        logs = auditor.get_logs(agent_name=agent)
    except Exception as e:
        logger.error(f"Failed to load compliance audit: {e}", exc_info=True)
        click.echo(click.style(f"❌ Error opening audit log: {e}", fg='red'))
        return

    if not logs:
        if agent:
            click.echo(click.style(f"No audit entries recorded for agent '{agent}'.", fg='yellow'))
        else:
            click.echo(click.style("Audit log is empty.", fg='yellow'))
        return

    limit = max(0, limit or 0)
    selected_entries = logs if limit == 0 else logs[-limit:]
    selected_entries = list(reversed(selected_entries))  # Show newest first

    click.echo(click.style(f"Displaying {len(selected_entries)} entries", fg='green'))

    if json_output:
        for entry in selected_entries:
            click.echo(json.dumps(entry, indent=2))
    else:
        for entry in selected_entries:
            ts = entry.get('timestamp', 'unknown')
            agent_name = entry.get('agent_name', 'unknown')
            task = entry.get('task_type', 'unknown')
            provider = entry.get('selected_provider', 'unknown')
            sensitivity = entry.get('sensitivity', 'unknown')
            decision = entry.get('policy_decision', '')
            residency = entry.get('data_residency', 'unknown')
            click.echo(f"[{ts}] {agent_name} → {provider} ({sensitivity})")
            click.echo(f"  Task: {task}")
            click.echo(f"  Decision: {decision}")
            click.echo(f"  Data Residency: {residency}")
            click.echo(f"  Policy: {entry.get('policy_name', 'unknown')}\n")

    if report:
        summary = auditor.generate_compliance_report()
        click.echo(click.style("📊 Compliance Summary", fg='cyan', bold=True))
        click.echo(f"Total tasks: {summary.get('total_tasks', 0)}")
        click.echo(f"Local tasks: {summary.get('local_tasks', 0)}")
        click.echo(f"Cloud tasks: {summary.get('cloud_tasks', 0)}")
        click.echo(f"Critical tasks: {summary.get('critical_tasks', 0)}")
        click.echo(f"Sensitive tasks: {summary.get('sensitive_tasks', 0)}")
        if summary.get('by_agent'):
            click.echo("\nBy agent:")
            for agent_name, counts in summary['by_agent'].items():
                click.echo(f"  {agent_name}: local={counts.get('local', 0)}, cloud={counts.get('cloud', 0)}")


def main():
    """Main entry point."""
    try:
        # Perform LLM health check at startup and warn if providers are unavailable
        try:
            from core.llm_client import create_llm_client_from_config
            cfg = get_config_manager().load()
            llm_client = create_llm_client_from_config(cfg)
            # create_llm_client_from_config logs health checks already
        except Exception as e:
            logger.warning(f"LLM health check failed during startup: {e}")

        cli()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        click.echo(click.style(f"\n❌ Error: {e}", fg='red'))
        sys.exit(1)


if __name__ == '__main__':
    main()