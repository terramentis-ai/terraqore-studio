# Critical Unblocking Tasks - Integration Guide

**For**: Development Team  
**Date**: December 27, 2025  
**Purpose**: Quick start guide for using the newly implemented security components

---

## Quick Start

### 1. Using Security Validator

#### Import in your agent:
```python
from core.security_validator import validate_agent_input, SecurityViolation

class MyAgent(BaseAgent):
    def execute(self, context: AgentContext) -> AgentResult:
        # Validate input for security violations
        try:
            validate_agent_input(lambda self, ctx: None)(self, context)
        except SecurityViolation as e:
            logger.error(f"Security violation: {e}")
            return self.create_result(success=False, error=str(e))
        
        # Proceed with safe execution...
```

#### Or use directly:
```python
from core.security_validator import validate_prompt, validate_conversation

# Single prompt validation
try:
    validate_prompt(user_input)
except SecurityViolation:
    reject_request()

# Conversation history validation
try:
    validate_conversation(chat_history)
except SecurityViolation:
    reject_conversation()
```

### 2. Using Hallucination Detector

#### In code validator agent:
```python
from agents.hallucination_detector import detect_hallucinations, ValidationSpec

# Detect hallucinations in code
code = generated_code
result = detect_hallucinations(code, language="python")

if not result.safe_to_deploy:
    print(result.summary())
    for finding in result.findings:
        print(f"{finding.severity}: {finding.description}")
```

#### With specification validation:
```python
spec = ValidationSpec(
    language="python",
    expected_functions=["process", "validate"],
    forbidden_patterns=["os.system", "eval"],
    required_imports=["json", "datetime"],
)

result = detect_hallucinations(code, language="python", spec=spec)
```

### 3. Using Docker Runtime Limits

#### Get a preset configuration:
```python
from core.docker_runtime_limits import (
    get_preset_configuration,
    SandboxSpecification,
    ResourceQuotaLevel,
)

# Use preset
spec = get_preset_configuration("standard_coding")

# Or create custom
spec = SandboxSpecification(
    level=ResourceQuotaLevel.STANDARD,
    cpu=None,  # Use defaults
    memory=None,
    timeout=None,
)

# Validate configuration
is_valid, errors = spec.validate()

# Get Docker run arguments
docker_args = spec.to_docker_run_args()
# Returns: ['--cpus=1.0', '--cpu-shares=1024', '--memory=2048m', ...]
```

#### Create execution transcript:
```python
from core.docker_runtime_limits import ExecutionTranscript
from datetime import datetime

transcript = ExecutionTranscript(
    execution_id="exec_12345",
    timestamp=datetime.now(),
    language="python",
    file_path="src/main.py",
    command_line="python src/main.py",
    working_directory="/workspace",
    cpu_time_seconds=5.2,
    memory_peak_mb=256.5,
    wall_time_seconds=5.5,
    exit_code=0,
    stdout="Process completed",
    stderr="",
    dangerous_output_detected=False,
)

# For JSON serialization
import json
transcript_dict = transcript.to_dict()
json_str = json.dumps(transcript_dict, indent=2)
```

---

## Testing

### Run prompt injection tests:
```bash
cd core_cli/tests/security
pytest test_prompt_injection.py -v
```

### Run hallucination detection tests:
```bash
cd core_cli/tests/security
pytest test_hallucination_detector.py -v
```

### Run with coverage:
```bash
pytest test_prompt_injection.py --cov=core.security_validator
pytest test_hallucination_detector.py --cov=agents.hallucination_detector
```

---

## Common Patterns

### Pattern 1: Secure Agent Execution
```python
from core.security_validator import validate_agent_input
from agents.hallucination_detector import detect_hallucinations

class SecureAgent(BaseAgent):
    def execute(self, context: AgentContext) -> AgentResult:
        # 1. Input validation
        try:
            validate_agent_input(lambda self, ctx: None)(self, context)
        except SecurityViolation as e:
            return self.error_result(f"Input validation failed: {e}")
        
        # 2. Execute with context
        try:
            result = self.do_work(context)
        except Exception as e:
            return self.error_result(f"Execution failed: {e}")
        
        # 3. Validate output if it's code
        if isinstance(result, str) and result.startswith("def "):
            hallucination_result = detect_hallucinations(result, "python")
            if not hallucination_result.safe_to_deploy:
                return self.error_result(hallucination_result.summary())
        
        return self.success_result(result)
```

### Pattern 2: Testing with Malicious Samples
```python
from tests.security.malicious_samples import get_all_samples
from core.docker_runtime_limits import SandboxSpecification

samples = get_all_samples()

for category, sample_dict in samples.items():
    print(f"Testing {category}...")
    for name, code in sample_dict.items():
        # Test with sandbox spec
        spec = SandboxSpecification()
        is_valid, errors = spec.validate()
        
        if not is_valid:
            print(f"  ✗ {name}: {errors}")
        else:
            print(f"  ✓ {name}: Spec valid")
```

### Pattern 3: Comprehensive Code Validation
```python
from agents.code_validator_agent import CodeValidationAgent
from core.security_validator import validate_agent_input
from agents.hallucination_detector import ValidationSpec

validator = CodeValidationAgent(llm_client=client)

# Create context with generated code
context = AgentContext(
    project_id=1,
    project_name="MyProject",
    project_description="Test project",
    user_input="Generate a calculator",
    metadata={
        "code_generation": {
            "files": [
                {
                    "path": "calculator.py",
                    "content": generated_code,
                    "language": "python",
                }
            ]
        },
        "language": "python",
    },
)

# Execute validation
result = validator.execute(context)

print(f"Validation passed: {result.success}")
print(f"Issues found: {result.metadata.get('issues_count')}")
for issue in result.metadata.get('validation', {}).get('issues_found', []):
    print(f"  - {issue['severity']}: {issue['description']}")
```

---

## Configuration Reference

### Sandbox Specification Presets

```python
# Test Execution (minimal resources)
test_spec = get_preset_configuration("test_execution")
# CPU: 0.5, Memory: 512MB, Timeout: 10s

# Standard Coding (default)
standard_spec = get_preset_configuration("standard_coding")
# CPU: 1.0, Memory: 2GB, Timeout: 30s

# Data Processing (intensive)
intensive_spec = get_preset_configuration("data_processing")
# CPU: 4.0, Memory: 8GB, Timeout: 300s

# Trusted Code (enhanced)
trusted_spec = get_preset_configuration("trusted_code")
# CPU: 2.0, Memory: 4GB, Timeout: 300s
```

### Injection Pattern Categories

1. **Command Injection** (ignore instructions, system override, etc.)
2. **File System** (delete, remove, unlink operations)
3. **Credentials** (access secrets, passwords, API keys)
4. **Database** (DROP TABLE, TRUNCATE, DELETE)
5. **System Control** (shutdown, restart, kill)
6. **Privilege Escalation** (sudo, root, admin access)

### Hallucination Categories

1. **SYNTAX_ERROR** - Invalid language grammar
2. **UNDEFINED_REFERENCE** - Undefined var/function
3. **TYPE_MISMATCH** - Type incompatibility
4. **LOGIC_ERROR** - Illogical code flow
5. **SPEC_VIOLATION** - Violates requirements
6. **SECURITY_ISSUE** - Dangerous patterns
7. **PERFORMANCE_ISSUE** - Inefficient code
8. **HALLUCINATED_API** - Non-existent API

---

## Troubleshooting

### Issue: SecurityViolation raised on legitimate input
**Solution**: Review the pattern that triggered it. The default patterns are conservative. You can:
1. Create a custom ValidationSpec with fewer patterns
2. Sanitize input before validation
3. Whitelist known-good input patterns

### Issue: Hallucination detector has false positives
**Solution**: 
1. Increase confidence threshold check
2. Use specific ValidationSpec instead of auto-detection
3. Add builtin functions to whitelist if needed

### Issue: Docker specs not generating proper args
**Solution**:
1. Call `spec.validate()` first
2. Check error messages for invalid configuration
3. Use preset configurations as starting point

---

## Security Best Practices

### Do's ✅
- Always validate input at agent boundaries
- Run hallucination detection on generated code
- Use appropriate sandbox specs for workload type
- Log all validation attempts
- Review findings before deployment
- Test with malicious samples regularly

### Don'ts ❌
- Skip validation for "trusted" input
- Ignore critical/high severity findings
- Use UNRESTRICTED preset for untrusted code
- Execute code without resource limits
- Disable security features for convenience
- Hardcode patterns or skip detection

---

## Integration Checklist

- [ ] Import security_validator in all agents
- [ ] Add validate_agent_input to execute() methods
- [ ] Import HallucinationDetector in code validator
- [ ] Configure SandboxSpecification for execution
- [ ] Add execution logging with ExecutionTranscript
- [ ] Run security tests in CI/CD pipeline
- [ ] Document security measures in README
- [ ] Review findings in deployment process
- [ ] Train team on security patterns
- [ ] Establish monitoring for violations

---

## API Reference

### security_validator.py
```python
# Classes
class SecurityViolation(Exception)
class PromptInjectionDefense
class SecurityContext

# Functions
def validate_prompt(text: Optional[str]) -> None
def validate_conversation(history: Optional[Iterable[dict]]) -> None
def validate_context_fields(*fields: Optional[str]) -> None
def validate_agent_input(func: Callable) -> Callable
```

### hallucination_detector.py
```python
# Classes
class HallucinationDetector
class ValidationSpec
class HallucinationFinding
class HallucinationDetectionResult

# Functions
def detect_hallucinations(
    code: str,
    language: str = "python",
    spec: Optional[ValidationSpec] = None,
    verbose: bool = False,
) -> HallucinationDetectionResult
```

### docker_runtime_limits.py
```python
# Classes
class CPUQuota
class MemoryQuota
class TimeoutQuota
class NetworkQuota
class FilesystemQuota
class SecurityQuota
class SandboxSpecification
class ExecutionTranscript
class RollbackMetadata

# Functions
def get_preset_configuration(preset_name: str) -> Optional[SandboxSpecification]

# Enums
class ResourceQuotaLevel
class ExecutionEnvironment
```

---

## Support

For questions or issues:
1. Check test files for usage examples
2. Review docstrings in implementation files
3. Run tests with `-v` flag for detailed output
4. Check PHASED_ROLLOUT_SCHEDULE.md for architecture

---

**Document Version**: 1.0  
**Last Updated**: December 27, 2025  
**Status**: Ready for Phase 1 Execution

