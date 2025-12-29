"""
Simple test to verify TerraQore functionality
"""
import sys
sys.path.insert(0, 'core_cli')

from core.config import get_config_manager
from core.state import get_state_manager, ProjectStatus
from core.llm_client import create_llm_client_from_config
from orchestration.orchestrator import get_orchestrator

def test_initialization():
    """Test that the system initializes"""
    print("="*70)
    print("TERRAQORE SYSTEM TEST")
    print("="*70)
    print()
    
    # Test 1: Config
    print("Test 1: Configuration System")
    try:
        config_mgr = get_config_manager()
        config = config_mgr.load()
        print(f"  ✓ Config loaded")
        print(f"  - Primary Provider: {config.primary_llm.provider}")
        print(f"  - Primary Model: {config.primary_llm.model}")
        print(f"  - API Key Set: {'Yes' if config.primary_llm.api_key else 'No (using Ollama)'}")
    except Exception as e:
        print(f"  ✗ Config failed: {e}")
        return False
    print()
    
    # Test 2: State Manager
    print("Test 2: State Management (Database)")
    try:
        state_mgr = get_state_manager()
        print(f"  ✓ Database connected")
        
        # Create test project with unique name
        import time as time_module
        from core.state import Project
        project_name = f"Test Project {int(time_module.time())}"
        project = Project(
            name=project_name,
            description="Simple test to verify the system works",
            status=ProjectStatus.PLANNING.value
        )
        project_id = state_mgr.create_project(project)
        project.id = project_id
        print(f"  ✓ Created project: {project.name} (ID: {project.id})")
        
        # List projects
        all_projects = state_mgr.list_projects()
        print(f"  ✓ Total projects in DB: {len(all_projects)}")
        
    except Exception as e:
        print(f"  ✗ State management failed: {e}")
        return False
    print()
    
    # Test 3: LLM Client
    print("Test 3: LLM Client")
    try:
        llm_client = create_llm_client_from_config(config)
        print(f"  ✓ LLM client initialized")
        print(f"  - Primary model: {config.primary_llm.model}")
        
        # Try simple completion
        print(f"  - Testing LLM connection...")
        try:
            response = llm_client.complete("Say 'Hello' in one word:")
            print(f"  ✓ LLM Response: {response[:50]}...")
        except Exception as e:
            print(f"  ! LLM test skipped (no API key or Ollama): {str(e)[:80]}")
    except Exception as e:
        print(f"  ! LLM client warning: {str(e)[:100]}")
        # Don't fail the test - LLM might not be configured
        llm_client = None
    print()
    
    # Test 4: Orchestrator
    print("Test 4: Agent Orchestrator")
    try:
        orchestrator = get_orchestrator()
        print(f"  ✓ Orchestrator initialized")
        agents = orchestrator.agent_registry.list_agents()
        print(f"  ✓ Registered agents: {len(agents)}")
        for agent_name in agents:
            print(f"    - {agent_name}")
    except Exception as e:
        print(f"  ✗ Orchestrator failed: {e}")
        return False
    print()
    
    # Test 5: Try ideation on test project
    print("Test 5: Run Ideation Agent")
    try:
        print(f"  - Running ideation for '{project.name}'...")
        result = orchestrator.run_ideation(project.id, user_input="Keep it simple")
        
        if result.success:
            print(f"  ✓ Ideation completed successfully!")
            print(f"  - Execution time: {result.execution_time:.2f}s")
            print(f"  - Output length: {len(result.output)} chars")
            print()
            print("  OUTPUT PREVIEW:")
            print("  " + "="*66)
            preview = result.output[:500] + "..." if len(result.output) > 500 else result.output
            for line in preview.split('\n'):
                print(f"  {line}")
            print("  " + "="*66)
        else:
            print(f"  ✗ Ideation failed: {result.error}")
            
    except Exception as e:
        print(f"  ✗ Ideation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()
    
    print("="*70)
    print("ALL TESTS COMPLETED")
    print("="*70)
    return True

if __name__ == "__main__":
    success = test_initialization()
    sys.exit(0 if success else 1)
