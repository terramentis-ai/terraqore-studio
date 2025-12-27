"""
Unit tests for Flynt base classes and core components.
"""

import pytest
import time
from datetime import datetime
from agents.base import AgentContext, AgentResult, BaseAgent, AgentRegistry
from core.llm_client import LLMResponse
from core.error_handler import (
    ErrorContext, ErrorType, RecoverySeverity, 
    RetryStrategy, CircuitBreakerStrategy, ErrorRecoveryManager
)
from core.monitoring import ExecutionMetric, AgentMonitor, HealthStatus


class TestAgentContext:
    """Tests for AgentContext validation."""
    
    def test_context_creation(self):
        """Test creating valid context."""
        context = AgentContext(
            project_id=1,
            project_name="Test Project",
            project_description="A test project",
            user_input="Do something"
        )
        assert context.project_id == 1
        assert context.project_name == "Test Project"
    
    def test_context_with_metadata(self):
        """Test context with additional metadata."""
        context = AgentContext(
            project_id=1,
            project_name="Test",
            project_description="Test",
            user_input="Test",
            metadata={"custom_key": "custom_value"}
        )
        assert context.metadata["custom_key"] == "custom_value"
    
    def test_context_with_conversation_history(self):
        """Test context with conversation history."""
        context = AgentContext(
            project_id=1,
            project_name="Test",
            project_description="Test",
            user_input="Test",
            conversation_history=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"}
            ]
        )
        assert len(context.conversation_history) == 2


class TestAgentResult:
    """Tests for AgentResult."""
    
    def test_successful_result(self):
        """Test creating successful result."""
        result = AgentResult(
            success=True,
            output="Test output",
            agent_name="TestAgent",
            execution_time=1.5
        )
        assert result.success is True
        assert result.output == "Test output"
    
    def test_failed_result(self):
        """Test creating failed result."""
        result = AgentResult(
            success=False,
            output="",
            agent_name="TestAgent",
            execution_time=0.5,
            error="Something went wrong"
        )
        assert result.success is False
        assert result.error == "Something went wrong"
    
    def test_result_with_metadata(self):
        """Test result with metadata."""
        result = AgentResult(
            success=True,
            output="Test",
            agent_name="TestAgent",
            execution_time=1.0,
            metadata={"tokens": 100}
        )
        assert result.metadata["tokens"] == 100


class TestAgentRegistry:
    """Tests for AgentRegistry."""
    
    def test_register_agent(self):
        """Test registering an agent."""
        registry = AgentRegistry()
        
        # Create mock agent
        class MockAgent(BaseAgent):
            def get_system_prompt(self) -> str:
                return "Mock prompt"
            def execute(self, context: AgentContext) -> AgentResult:
                return AgentResult(True, "mock", "MockAgent", 0.1)
        
        agent = MockAgent(
            name="MockAgent",
            description="A mock agent",
            llm_client=None
        )
        registry.register(agent)
        
        assert registry.is_registered("MockAgent")
        assert registry.get("MockAgent") == agent
    
    def test_list_agents(self):
        """Test listing all agents."""
        registry = AgentRegistry()
        
        class MockAgent(BaseAgent):
            def get_system_prompt(self) -> str:
                return "Mock"
            def execute(self, context: AgentContext) -> AgentResult:
                return AgentResult(True, "", self.name, 0.1)
        
        agent1 = MockAgent("Agent1", "Test 1", None)
        agent2 = MockAgent("Agent2", "Test 2", None)
        
        registry.register(agent1)
        registry.register(agent2)
        
        agents = registry.list_agents()
        assert len(agents) == 2
        assert "Agent1" in agents
        assert "Agent2" in agents
    
    def test_unregister_agent(self):
        """Test unregistering an agent."""
        registry = AgentRegistry()
        
        class MockAgent(BaseAgent):
            def get_system_prompt(self) -> str:
                return "Mock"
            def execute(self, context: AgentContext) -> AgentResult:
                return AgentResult(True, "", "Mock", 0.1)
        
        agent = MockAgent("TestAgent", "Test", None)
        registry.register(agent)
        assert registry.is_registered("TestAgent")
        
        success = registry.unregister("TestAgent")
        assert success is True
        assert not registry.is_registered("TestAgent")
    
    def test_get_all_agents(self):
        """Test getting all agents as dictionary."""
        registry = AgentRegistry()
        
        class MockAgent(BaseAgent):
            def get_system_prompt(self) -> str:
                return "Mock"
            def execute(self, context: AgentContext) -> AgentResult:
                return AgentResult(True, "", self.name, 0.1)
        
        agent1 = MockAgent("Agent1", "Test 1", None)
        agent2 = MockAgent("Agent2", "Test 2", None)
        
        registry.register(agent1)
        registry.register(agent2)
        
        all_agents = registry.get_all()
        assert isinstance(all_agents, dict)
        assert len(all_agents) == 2
        assert "Agent1" in all_agents
        assert "Agent2" in all_agents


class TestBaseAgentValidation:
    """Tests for BaseAgent context validation."""
    
    def test_validate_valid_context(self):
        """Test validation of valid context."""
        class MockAgent(BaseAgent):
            def get_system_prompt(self) -> str:
                return "Mock"
            def execute(self, context: AgentContext) -> AgentResult:
                return AgentResult(True, "", "Mock", 0.1)
        
        agent = MockAgent("TestAgent", "Test", None)
        context = AgentContext(
            project_id=1,
            project_name="Test",
            project_description="Test",
            user_input="Test"
        )
        
        assert agent.validate_context(context) is True
    
    def test_validate_missing_project_id(self):
        """Test validation rejects missing project_id."""
        class MockAgent(BaseAgent):
            def get_system_prompt(self) -> str:
                return "Mock"
            def execute(self, context: AgentContext) -> AgentResult:
                return AgentResult(True, "", "Mock", 0.1)
        
        agent = MockAgent("TestAgent", "Test", None)
        context = AgentContext(
            project_id=0,  # Invalid
            project_name="Test",
            project_description="Test",
            user_input="Test"
        )
        
        assert agent.validate_context(context) is False
    
    def test_validate_empty_project_name(self):
        """Test validation rejects empty project_name."""
        class MockAgent(BaseAgent):
            def get_system_prompt(self) -> str:
                return "Mock"
            def execute(self, context: AgentContext) -> AgentResult:
                return AgentResult(True, "", "Mock", 0.1)
        
        agent = MockAgent("TestAgent", "Test", None)
        context = AgentContext(
            project_id=1,
            project_name="",  # Invalid
            project_description="Test",
            user_input="Test"
        )
        
        assert agent.validate_context(context) is False
    
    def test_validate_empty_user_input(self):
        """Test validation rejects empty user_input."""
        class MockAgent(BaseAgent):
            def get_system_prompt(self) -> str:
                return "Mock"
            def execute(self, context: AgentContext) -> AgentResult:
                return AgentResult(True, "", "Mock", 0.1)
        
        agent = MockAgent("TestAgent", "Test", None)
        context = AgentContext(
            project_id=1,
            project_name="Test",
            project_description="Test",
            user_input=""  # Invalid
        )
        
        assert agent.validate_context(context) is False


class TestErrorRecovery:
    """Tests for error recovery system."""
    
    @pytest.mark.asyncio
    async def test_retry_strategy(self):
        """Test retry strategy."""
        strategy = RetryStrategy(max_retries=3, initial_delay=0.1)
        
        error = ErrorContext(
            error_type=ErrorType.API_ERROR,
            severity=RecoverySeverity.RECOVERABLE,
            message="API failed",
            timestamp=datetime.now(),
            retry_count=0
        )
        
        assert strategy.can_recover(error) is True
        result = await strategy.recover(error)
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_strategy(self):
        """Test circuit breaker pattern."""
        strategy = CircuitBreakerStrategy(failure_threshold=3, reset_timeout=1.0)
        
        error = ErrorContext(
            error_type=ErrorType.API_ERROR,
            severity=RecoverySeverity.RECOVERABLE,
            message="API failed",
            timestamp=datetime.now()
        )
        
        # Simulate failures
        for i in range(3):
            result = await strategy.recover(error)
            assert result.success is True
        
        # Circuit should be open now
        assert strategy.is_open is True
    
    def test_error_context_creation(self):
        """Test creating error context."""
        error = ErrorContext(
            error_type=ErrorType.VALIDATION_ERROR,
            severity=RecoverySeverity.CRITICAL,
            message="Validation failed",
            timestamp=datetime.now(),
            agent_name="TestAgent"
        )
        
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert error.agent_name == "TestAgent"


class TestAgentMonitoring:
    """Tests for agent monitoring system."""
    
    def test_track_execution(self):
        """Test tracking execution metrics."""
        monitor = AgentMonitor()
        
        metric = ExecutionMetric(
            agent_name="TestAgent",
            execution_time_ms=1500.0,
            success=True,
            quality_score=8.5
        )
        
        monitor.track_execution(metric)
        recent = monitor.get_recent_metrics("TestAgent")
        assert len(recent) == 1
        assert recent[0].success is True
    
    def test_agent_health_status(self):
        """Test agent health status calculation."""
        monitor = AgentMonitor()
        
        # Add successful metrics
        for _ in range(8):
            metric = ExecutionMetric(
                agent_name="TestAgent",
                execution_time_ms=1000.0,
                success=True,
                quality_score=8.0
            )
            monitor.track_execution(metric)
        
        # Add failed metrics
        for _ in range(2):
            metric = ExecutionMetric(
                agent_name="TestAgent",
                execution_time_ms=2000.0,
                success=False,
                quality_score=3.0
            )
            monitor.track_execution(metric)
        
        health = monitor.get_agent_metrics("TestAgent")
        assert health.success_rate == 0.8
        assert health.total_executions == 10
        assert health.total_failures == 2
    
    def test_health_status_transitions(self):
        """Test health status transitions."""
        monitor = AgentMonitor()
        
        # Healthy state
        for _ in range(10):
            metric = ExecutionMetric(
                agent_name="TestAgent",
                execution_time_ms=1000.0,
                success=True,
                quality_score=9.0
            )
            monitor.track_execution(metric)
        
        status = monitor.get_health_status("TestAgent")
        assert status == HealthStatus.HEALTHY
        
        # Degrade to degraded
        for _ in range(3):
            metric = ExecutionMetric(
                agent_name="TestAgent",
                execution_time_ms=2000.0,
                success=False,
                quality_score=3.0
            )
            monitor.track_execution(metric)
        
        status = monitor.get_health_status("TestAgent")
        assert status == HealthStatus.DEGRADED
    
    def test_monitoring_summary(self):
        """Test comprehensive monitoring summary."""
        monitor = AgentMonitor()
        
        # Add metrics for multiple agents
        for agent_name in ["Agent1", "Agent2", "Agent3"]:
            for _ in range(5):
                metric = ExecutionMetric(
                    agent_name=agent_name,
                    execution_time_ms=1000.0,
                    success=True,
                    quality_score=8.0
                )
                monitor.track_execution(metric)
        
        summary = monitor.get_monitoring_summary()
        assert summary["total_agents"] == 3
        assert summary["overall_success_rate"] == 1.0


class TestLLMResponseValidation:
    """Tests for LLM response validation."""
    
    def test_successful_response(self):
        """Test successful LLM response."""
        response = LLMResponse(
            content="Generated text",
            provider="gemini",
            model="gemini-1.5-flash",
            usage={"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50},
            success=True
        )
        
        assert response.success is True
        assert response.content == "Generated text"
        assert response.usage["total_tokens"] == 100
    
    def test_failed_response(self):
        """Test failed LLM response."""
        response = LLMResponse(
            content="",
            provider="gemini",
            model="gemini-1.5-flash",
            usage={},
            success=False,
            error="API key invalid"
        )
        
        assert response.success is False
        assert response.error == "API key invalid"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
