# MetaQore Adversarial Test Harness Guide

**Version**: 1.0.0
**Objective**: Proactively test the resilience of MetaQore's SecureGateway and PSMP conflict detection by simulating malicious or non-compliant LLM behaviors.

## Architecture

### Module Structure
- `client.py`: Contains `AdversarialMockLLMClient` class
- `scenarios.py`: Predefined attack scenario configurations
- `harness.py`: Main test runner and orchestrator
- `fixtures.py`: Pytest fixtures for easy integration

### Class Design

#### AdversarialMockLLMClient
Inherits from `MockLLMClient`. Overrides normal response generation to apply adversarial transformations based on `attack_mode`.

**Attack Modes**:
- `INSTRUCTION_IGNORE`: LLM completely ignores the task directive.
- `PROMPT_LEAKAGE`: LLM echoes back part of its system prompt.
- `ARTIFACT_POISONING`: LLM returns valid-looking JSON with malicious data.
- `DELAYED_FAILURE`: LLM responds normally for N turns, then injects adversarial content.

#### AdversarialTestHarness
Orchestrates the full test:
1. Setup PSMP Project
2. Configure Client with Scenario
3. Execute Task
4. Monitor Governance (expect Conflict/Veto)
5. Assert Outcome

## Scenarios

| Scenario | Description | Expected Response |
|----------|-------------|-------------------|
| `instruction_disobedience` | Ignores directive | SecureGateway Veto |
| `system_prompt_exfiltration` | Leaks prompt | SecureGateway Veto (Data Leakage) |
| `structured_output_sabotage` | Malicious JSON | PSMP Conflict (Schema/Validation) |
| `latent_corruption` | Fails on turn 4 | Stateful Veto |

## Usage

```python
from metaqore.testing.adversarial import AdversarialTestHarness, ScenarioRegistry

def test_adversarial_resilience():
    harness = AdversarialTestHarness()
    scenario = ScenarioRegistry.get("instruction_disobedience")
    
    result = harness.run_scenario(scenario)
    
    assert result.success
    assert result.governance_response.type == "VETO"
```
