"""
PSMP Integration Tests
Tests the integration of PSMP with the orchestrator and CLI.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.psmp import (
    get_psmp_service,
    DependencySpec,
    DependencyScope,
    ProjectBlockedException,
)
from core.psmp_orchestrator_bridge import get_psmp_bridge
from core.state import get_state_manager, Project, ProjectStatus
from agents.base import AgentContext, AgentResult


class TestPSMPIntegration:
    """Integration tests for PSMP with orchestrator."""
    
    @pytest.fixture
    def setup_test_project(self):
        """Create a test project for PSMP testing."""
        state_mgr = get_state_manager()
        
        # Create test project
        project = Project(
            name="test_psmp_project",
            description="PSMP integration test",
            status=ProjectStatus.INITIALIZED.value,
            created_at="2024-01-01T00:00:00"
        )
        
        project_id = state_mgr.create_project(project)
        yield project_id
        
        # Cleanup
        state_mgr.delete_project(project_id)
    
    def test_psmp_service_initialization(self):
        """Test PSMP service initializes correctly."""
        psmp = get_psmp_service()
        assert psmp is not None
        assert psmp.get_psmp_service() == psmp  # Singleton
    
    def test_psmp_bridge_initialization(self):
        """Test PSMP bridge initializes correctly."""
        bridge = get_psmp_bridge()
        assert bridge is not None
        assert bridge.psmp is not None
    
    def test_project_not_blocked_initially(self, setup_test_project):
        """Test project is not blocked when newly created."""
        bridge = get_psmp_bridge()
        is_blocked, reason = bridge.check_project_blocked(setup_test_project)
        assert not is_blocked
    
    def test_artifact_declaration_without_conflicts(self, setup_test_project):
        """Test declaring artifact without dependency conflicts."""
        bridge = get_psmp_bridge()
        
        # Create a simple agent result
        result = AgentResult(
            success=True,
            output="Generated some code",
            agent_name="TestAgent",
            execution_time=1.0,
            error=None
        )
        
        # Declare artifact with safe dependencies
        success, conflicts = bridge.declare_agent_artifact(
            project_id=setup_test_project,
            agent_name="CoderAgent",
            artifact_type="code",
            result=result,
            dependencies=[
                DependencySpec(
                    name="requests",
                    version_constraint=">=2.28.0",
                    scope=DependencyScope.RUNTIME,
                    declared_by_agent="CoderAgent",
                    purpose="HTTP requests"
                )
            ]
        )
        
        assert success
        assert conflicts is None
    
    def test_artifact_declaration_with_conflicts(self, setup_test_project):
        """Test declaring conflicting artifacts blocks project."""
        bridge = get_psmp_bridge()
        psmp = get_psmp_service()
        
        # First agent declares pandas>=2.0
        result1 = AgentResult(
            success=True,
            output="Generated pandas 2.0 code",
            agent_name="CoderAgent",
            execution_time=1.0,
            error=None
        )
        
        success1, conflicts1 = bridge.declare_agent_artifact(
            project_id=setup_test_project,
            agent_name="CoderAgent",
            artifact_type="code",
            result=result1,
            dependencies=[
                DependencySpec(
                    name="pandas",
                    version_constraint=">=2.0",
                    scope=DependencyScope.RUNTIME,
                    declared_by_agent="CoderAgent",
                    purpose="data processing"
                )
            ]
        )
        
        assert success1
        assert conflicts1 is None
        
        # Second agent declares pandas<2.0
        result2 = AgentResult(
            success=True,
            output="Legacy model code",
            agent_name="DataScienceAgent",
            execution_time=1.0,
            error=None
        )
        
        success2, conflicts2 = bridge.declare_agent_artifact(
            project_id=setup_test_project,
            agent_name="DataScienceAgent",
            artifact_type="data_science",
            result=result2,
            dependencies=[
                DependencySpec(
                    name="pandas",
                    version_constraint="<2.0",
                    scope=DependencyScope.RUNTIME,
                    declared_by_agent="DataScienceAgent",
                    purpose="legacy model compatibility"
                )
            ]
        )
        
        # Second declaration should fail with conflicts
        assert not success2
        assert conflicts2 is not None
        assert len(conflicts2) > 0
        
        # Project should now be blocked
        is_blocked, _ = bridge.check_project_blocked(setup_test_project)
        assert is_blocked
        
        # Verify blocking report
        report = bridge.get_blocking_report(setup_test_project)
        assert "BLOCKED" in report
        assert "pandas" in report
    
    def test_project_blocking_prevents_further_artifacts(self, setup_test_project):
        """Test that blocked projects prevent artifact declarations."""
        bridge = get_psmp_bridge()
        
        # Declare conflicting artifacts (will block project)
        result1 = AgentResult(
            success=True,
            output="Code 1",
            agent_name="Agent1",
            execution_time=1.0,
            error=None
        )
        
        bridge.declare_agent_artifact(
            project_id=setup_test_project,
            agent_name="Agent1",
            artifact_type="code",
            result=result1,
            dependencies=[
                DependencySpec(
                    name="lib1",
                    version_constraint=">=1.0",
                    scope=DependencyScope.RUNTIME,
                    declared_by_agent="Agent1",
                    purpose="test"
                )
            ]
        )
        
        result2 = AgentResult(
            success=True,
            output="Code 2",
            agent_name="Agent2",
            execution_time=1.0,
            error=None
        )
        
        bridge.declare_agent_artifact(
            project_id=setup_test_project,
            agent_name="Agent2",
            artifact_type="code",
            result=result2,
            dependencies=[
                DependencySpec(
                    name="lib1",
                    version_constraint="<1.0",
                    scope=DependencyScope.RUNTIME,
                    declared_by_agent="Agent2",
                    purpose="test"
                )
            ]
        )
        
        # Now project is blocked
        is_blocked, _ = bridge.check_project_blocked(setup_test_project)
        assert is_blocked
        
        # Trying to declare another artifact should raise exception
        result3 = AgentResult(
            success=True,
            output="Code 3",
            agent_name="Agent3",
            execution_time=1.0,
            error=None
        )
        
        with pytest.raises(ProjectBlockedException):
            bridge.declare_agent_artifact(
                project_id=setup_test_project,
                agent_name="Agent3",
                artifact_type="code",
                result=result3,
                dependencies=[]
            )
    
    def test_manifest_generation(self, setup_test_project):
        """Test unified manifest generation."""
        bridge = get_psmp_bridge()
        psmp = get_psmp_service()
        
        # Declare some artifacts with dependencies
        result = AgentResult(
            success=True,
            output="Generated code",
            agent_name="CoderAgent",
            execution_time=1.0,
            error=None
        )
        
        bridge.declare_agent_artifact(
            project_id=setup_test_project,
            agent_name="CoderAgent",
            artifact_type="code",
            result=result,
            dependencies=[
                DependencySpec(
                    name="requests",
                    version_constraint=">=2.28.0",
                    scope=DependencyScope.RUNTIME,
                    declared_by_agent="CoderAgent",
                    purpose="HTTP"
                ),
                DependencySpec(
                    name="pytest",
                    version_constraint=">=7.0",
                    scope=DependencyScope.DEV,
                    declared_by_agent="CoderAgent",
                    purpose="Testing"
                )
            ]
        )
        
        # Generate manifest
        manifest = psmp.get_unified_manifest(setup_test_project)
        
        assert manifest is not None
        assert "requests" in manifest
        assert "pytest" in manifest


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
