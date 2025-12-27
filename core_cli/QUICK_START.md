# Quick Start Guide - Flynt-Studio Fixes

This guide helps you get started with the newly implemented fixes.

## ✅ What Was Fixed

### Critical Fixes (P0)
- ✅ **AgentRegistry** - Complete agent management lifecycle
- ✅ **Input Validation** - Type-safe context validation
- ✅ **LLM Client** - Exponential backoff retry strategy
- ✅ **Configuration** - Comprehensive config validation

### High Priority Fixes (P1)
- ✅ **Error Recovery** - Automatic failure recovery system
- ✅ **Monitoring** - Real-time agent health tracking
- ✅ **Health Endpoints** - REST API for system monitoring
- ✅ **Unit Tests** - Comprehensive test coverage

---

## Installation

```bash
# Update dependencies
pip install -r requirements.txt

# Verify installation
python -c "from core.error_handler import get_error_recovery_manager; print('✅ Error handler installed')"
python -c "from core.monitoring import get_agent_monitor; print('✅ Monitoring installed')"
```

---

## Usage Examples

### 1. Error Recovery in Your Agents

When something goes wrong, the system automatically tries to recover:

```python
from core.error_handler import get_error_recovery_manager, ErrorContext, ErrorType, RecoverySeverity
from datetime import datetime
import asyncio

async def handle_agent_failure(error_message: str, agent_name: str):
    """Handle agent failures with automatic recovery."""
    
    error = ErrorContext(
        error_type=ErrorType.API_ERROR,
        severity=RecoverySeverity.RECOVERABLE,
        message=error_message,
        timestamp=datetime.now(),
        agent_name=agent_name,
        retry_count=0
    )
    
    recovery_mgr = get_error_recovery_manager()
    result = await recovery_mgr.handle_error(error)
    
    if result.success:
        print(f"✅ Recovery succeeded: {result.message}")
        return True
    else:
        print(f"❌ Recovery failed: {result.message}")
        return False
```

### 2. Monitor Agent Health

Track agent execution and get health status:

```python
from core.monitoring import get_agent_monitor, ExecutionMetric
from datetime import datetime
import time

def run_agent_with_monitoring(agent, context):
    """Run agent and track execution metrics."""
    monitor = get_agent_monitor()
    start_time = time.time()
    
    try:
        result = agent.execute(context)
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Track successful execution
        metric = ExecutionMetric(
            agent_name=agent.name,
            execution_time_ms=execution_time_ms,
            success=result.success,
            quality_score=8.5 if result.success else 3.0,
            output_tokens=len(result.output.split())
        )
        monitor.track_execution(metric)
        
        # Check health status
        health = monitor.get_health_status(agent.name)
        print(f"Agent {agent.name} status: {health.value}")
        
        return result
    except Exception as e:
        # Track failed execution
        metric = ExecutionMetric(
            agent_name=agent.name,
            execution_time_ms=(time.time() - start_time) * 1000,
            success=False,
            quality_score=0.0,
            error_message=str(e)
        )
        monitor.track_execution(metric)
        raise
```

### 3. Validate Configuration

Ensure your configuration is correct:

```python
from core.config import get_config_manager

try:
    config_mgr = get_config_manager()
    config = config_mgr.load()
    
    print(f"✅ Primary provider: {config.primary_llm.provider}")
    print(f"✅ Model: {config.primary_llm.model}")
    print(f"✅ Max retries: {config.max_retries}")
    
    if config.fallback_llm:
        print(f"✅ Fallback provider: {config.fallback_llm.provider}")
    else:
        print("⚠️ No fallback provider configured")
        
except ValueError as e:
    print(f"❌ Configuration error: {e}")
```

### 4. Check System Health

Use the new health check endpoints:

```bash
# Simple health check
curl http://localhost:8000/health | jq

# All agents status
curl http://localhost:8000/health/agents | jq

# Specific agent
curl http://localhost:8000/health/agents/CoderAgent | jq

# Error statistics
curl http://localhost:8000/health/errors | jq
```

Health check response example:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-25T10:30:00",
  "llm_health": {
    "primary": {
      "available": true,
      "success": true,
      "message": "OK"
    }
  },
  "agents": {
    "total_agents": 8,
    "overall_success_rate": 0.92,
    "agent_count_by_status": {
      "healthy": 6,
      "degraded": 2
    }
  }
}
```

---

## Running Tests

```bash
# Run all tests
pytest tests/test_core_components.py -v

# Run with coverage
pytest tests/test_core_components.py --cov=core --cov=agents

# Run specific test class
pytest tests/test_core_components.py::TestAgentMonitoring -v

# Run async tests
pytest tests/test_core_components.py -v -m asyncio
```

---

## Key Components

### 1. **Error Recovery** (`core/error_handler.py`)
Automatically recovers from failures:
- **RetryStrategy** - Retries with exponential backoff
- **FallbackStrategy** - Switches to alternative provider
- **CircuitBreakerStrategy** - Prevents cascading failures
- **DeadLetterStrategy** - Stores critical errors for analysis

### 2. **Monitoring** (`core/monitoring.py`)
Tracks agent performance:
- Real-time health status
- Execution metrics (time, success rate, quality)
- Performance trends
- Slowest/unreliable agent ranking

### 3. **Agent Registry** (`agents/base.py`)
Complete agent lifecycle:
- `register()` - Register new agent
- `get()` - Get agent by name
- `list_agents()` - List all agents
- `unregister()` - Remove agent
- `is_registered()` - Check if registered
- `get_all()` - Get all agents as dictionary

### 4. **Configuration** (`core/config.py`)
Validates settings:
- Provider validation
- API key checking
- Parameter clamping (temperature, max_tokens)
- Helpful warning messages

---

## Configuration Checklist

Before deploying, ensure:

```yaml
# config/settings.yaml
llm:
  primary_provider: "gemini"
  fallback_provider: "groq"
  
  gemini:
    model: "gemini-1.5-flash"
    temperature: 0.7
    max_tokens: 4096
  
  groq:
    model: "llama-3.1-70b-versatile"
    temperature: 0.7
    max_tokens: 4096

system:
  max_retries: 3
  timeout: 30
  debug: false
```

Environment variables:
```bash
export GEMINI_API_KEY="your-key"
export GROQ_API_KEY="your-key"
```

---

## Troubleshooting

### Error: "Missing required context field"
**Cause:** Invalid AgentContext passed to agent
**Fix:** Ensure project_id > 0, project_name and user_input are non-empty strings

### Error: "Circuit breaker is OPEN"
**Cause:** Too many consecutive failures
**Fix:** Check LLM provider status, wait 60 seconds for circuit reset

### Error: "No API key for {provider}"
**Cause:** API key environment variable not set
**Fix:** `export PROVIDER_API_KEY="your-key"`

### Slow agent responses
**Solution:** Check agent health status:
```python
monitor = get_agent_monitor()
slow = monitor.get_slowest_agents(top_n=5)
print(slow)  # Lists slowest agents and execution times
```

---

## Monitoring Dashboard

Access system health via HTTP:

```python
import requests

response = requests.get("http://localhost:8000/health")
health = response.json()

print(f"System Status: {health['status']}")
print(f"Total Agents: {health['agents']['total_agents']}")
print(f"Success Rate: {health['agents']['overall_success_rate']*100:.1f}%")
```

---

## Next Steps

1. **Run tests to verify installation:**
   ```bash
   pytest tests/test_core_components.py -v
   ```

2. **Deploy health check endpoints:**
   - Add monitoring/alerting for `/health` endpoint
   - Set up dashboard to display agent metrics

3. **Integrate error recovery:**
   - Update agent execute() methods to use recovery
   - Configure recovery strategies per agent type

4. **Enable monitoring:**
   - Start tracking execution metrics
   - Monitor health trends over time

5. **Set up alerting:**
   - Alert if any agent status becomes DEGRADED
   - Alert if circuit breaker opens
   - Track error patterns

---

## Support

For questions or issues:
1. Check `IMPLEMENTATION_FIXES.md` for detailed documentation
2. Review test cases in `tests/test_core_components.py`
3. Read docstrings in each module

---

**Last Updated:** December 25, 2025  
**Status:** All P0 and P1 fixes implemented ✅
