# Unified Agents Architecture - TerraQore Studio v1.2.1

## Overview

TerraQore Studio implements a **hybrid unified agent architecture** that combines:
- **PROMPT_PROFILE-based LLM decision-making** for intelligent, context-aware planning
- **Template-based code generation** for reliable, battle-tested scaffolding
- **Modular design** for maintainability and extensibility

This document explains the unification approach and how the three specialized agents work.

---

## Architecture Pattern

### Traditional Approach (Before)
```
Template Agents (data_science_agent.py, mlops_agent.py, devops_agent.py)
├── MLProjectGenerator (472 lines)
├── DeploymentTemplates (568 lines)
└── InfrastructureTemplates (842 lines)
   [Non-BaseAgent utility classes, inflexible, hard to customize]

LLM Agents (ds_agent.py, mlo_agent.py, do_agent.py)
├── PROMPT_PROFILE system
├── LLM-based generation
└── Flexible but no template backing
   [Could hallucinate, no pre-tested patterns]
```

### Unified Approach (After)
```
Unified Specialized Agents
├── DSAgent (Data Science)
│   ├── Step 1: LLM analyzes ML project requirements
│   ├── Step 2: Recommends framework, project type, data type (JSON)
│   ├── Step 3: Generates comprehensive architecture
│   └── Step 4: Templates available via MLProjectGenerator
│
├── MLOAgent (MLOps)
│   ├── Step 1: LLM analyzes deployment requirements
│   ├── Step 2: Recommends serving framework, monitoring stack (JSON)
│   ├── Step 3: Designs complete MLOps infrastructure
│   └── Step 4: Templates available via existing mlops configs
│
└── DOAgent (DevOps)
    ├── Step 1: LLM analyzes infrastructure requirements
    ├── Step 2: Recommends cloud provider, IaC tool, CI/CD (JSON)
    ├── Step 3: Designs complete infrastructure
    └── Step 4: Templates available via existing devops configs
```

---

## Implementation Details

### 1. DSAgent (Data Science)

**File**: `core_cli/agents/ds_agent.py`

**Key Features**:
- Imports `MLProjectGenerator` from existing `data_science_agent.py`
- Two-stage generation:
  1. **Architecture Recommendation**: LLM outputs JSON with framework choice
  2. **Comprehensive Plan**: Full ML project architecture document

**Execution Flow**:
```python
# Stage 1: Get LLM recommendation (JSON)
recommendation = {
    "project_type": "classification|regression|nlp|computer_vision|time_series|clustering",
    "framework": "pytorch|tensorflow|scikit_learn|xgboost|lightgbm|huggingface",
    "data_type": "tabular|image|text|audio|time_series|mixed",
    "justification": "Why this choice",
    "key_considerations": ["item1", "item2"]
}

# Stage 2: Generate full architecture leveraging recommendation
architecture = LLM.generate(
    f"Based on {recommendation}, generate complete ML architecture"
)

# Stage 3: Return comprehensive plan with metadata
return Result(
    success=True,
    output=architecture,
    metadata={"recommendation": recommendation, "templates_available": True}
)
```

**Benefits**:
- LLM flexibility for novel use cases
- Fallback to templates if JSON parsing fails
- 472 lines of ML domain knowledge accessible
- ~31s execution time

---

### 2. MLOAgent (MLOps)

**File**: `core_cli/agents/mlo_agent.py`

**Key Features**:
- Imports `DeploymentEnvironment`, `MonitoringMetricType`, `ModelStrategy` from existing configs
- Three-stage planning:
  1. **Deployment Analysis**: Recommendation JSON for serving framework, monitoring
  2. **MLOps Infrastructure**: Full deployment, monitoring, CI/CD design
  3. **Fallback**: Uses recommendation if full generation fails

**Execution Flow**:
```python
# Stage 1: Analyze deployment type and tools
recommendation = {
    "deployment_type": "batch|real-time|edge|hybrid",
    "expected_throughput": "requests/sec",
    "serving_framework": "mlflow|tensorflow_serving|torchserve|kserve|seldon",
    "monitoring_needs": ["performance", "drift", "latency", "throughput"],
    "experiment_tracking": "mlflow|wandb|neptune|comet"
}

# Stage 2-4: Generate comprehensive MLOps plan
mlops_plan = LLM.generate(
    f"""
    Deployment Strategy:
    - Type: {recommendation['deployment_type']}
    - Framework: {recommendation['serving_framework']}
    
    Monitoring & Observability:
    - Metrics: {recommendation['monitoring_needs']}
    
    Experiment Tracking:
    - Tool: {recommendation['experiment_tracking']}
    
    CI/CD Pipeline, Retraining Automation, Implementation Roadmap...
    """
)

return Result(output=mlops_plan, metadata={"recommendation": recommendation})
```

**Benefits**:
- Intelligent framework selection (considering throughput, drift, latency)
- Comprehensive monitoring strategy
- Automated retraining pipeline design
- ~25s execution time

---

### 3. DOAgent (DevOps)

**File**: `core_cli/agents/do_agent.py`

**Key Features**:
- Imports `InfrastructureType`, `CloudProvider`, `CIPlatform`, `MonitoringStack` from existing configs
- Multi-stage infrastructure design:
  1. **Infrastructure Analysis**: Cloud provider, IaC tool, CI/CD platform recommendation
  2. **Comprehensive IaC Plan**: Full architecture with Terraform/CloudFormation examples
  3. **Integrated Security**: IAM, secrets, encryption, compliance

**Execution Flow**:
```python
# Stage 1: Analyze infrastructure needs
recommendation = {
    "cloud_provider": "aws|azure|gcp|onpremise|multi",
    "infrastructure_type": "docker_compose|kubernetes|terraform|cloudformation|ansible",
    "ci_platform": "github_actions|gitlab_ci|jenkins|circleci|azure_pipelines",
    "monitoring_stack": "prometheus_grafana|datadog|elk_stack|cloudwatch",
    "expected_scale": "small|medium|large|enterprise"
}

# Stage 2-4: Generate complete DevOps infrastructure
infra_plan = LLM.generate(
    f"""
    Cloud Architecture ({recommendation['cloud_provider']}):
    - Compute, Storage, Networking design
    
    Infrastructure-as-Code ({recommendation['infrastructure_type']}):
    - VPC, Auto-scaling, Load Balancing
    
    CI/CD Pipeline ({recommendation['ci_platform']}):
    - Build, Test, Deploy stages
    
    Monitoring ({recommendation['monitoring_stack']}):
    - Application, Infrastructure, Security monitoring
    
    Security, Cost Optimization, Deployment Workflow...
    """
)

return Result(output=infra_plan, metadata={"recommendation": recommendation})
```

**Benefits**:
- Multi-cloud aware infrastructure design
- Comprehensive IaC generation (Terraform with examples)
- Security-first (IAM, secrets, encryption, compliance)
- Cost optimization strategies
- ~39s execution time

---

## Design Advantages

### 1. **Flexibility + Reliability**
| Aspect | Template-Only | LLM-Only | Unified |
|--------|--------------|----------|---------|
| Novel Use Cases | ❌ Limited | ✅ Excellent | ✅ Excellent |
| Hallucination Risk | ❌ None | ✅ High | ✅ Mitigated |
| Pre-Tested Patterns | ✅ Yes | ❌ No | ✅ Yes |
| Maintenance Burden | ❌ High | ✅ Low | ✅ Low |

### 2. **Cost Efficiency**
- LLM used only for **decisions** (JSON generation)
- Templates provide **scaffolding** (no additional LLM calls)
- Fallback mechanism prevents failures
- ~30-40s total execution vs instantaneous templates
- **Sweet spot**: flexibility without excessive API calls

### 3. **Maintainability**
- Single agent per domain (DSAgent, MLOAgent, DOAgent)
- 472/568/842 lines of existing domain knowledge preserved
- PROMPT_PROFILE system enables easy prompt tuning
- Template fallback prevents agent failures
- Clear separation of concerns

### 4. **Quality Assurance**
- JSON recommendations are deterministic and structured
- LLM-generated plans are grounded in real patterns
- Templates provide validation and best practices
- Metadata tracking enables quality monitoring

---

## Integration Points

### Existing Template Classes (Preserved)
```python
# Data Science templates (core_cli/agents/data_science_agent.py)
from agents.data_science_agent import MLProjectGenerator
generator = MLProjectGenerator()
project = generator.generate_project(
    project_type=ProjectType.CLASSIFICATION,
    framework=MLFramework.PYTORCH
)

# MLOps configurations (core_cli/agents/mlops_agent.py)
from agents.mlops_agent import (
    DeploymentEnvironment, MonitoringMetricType, ModelStrategy
)

# DevOps infrastructure (core_cli/agents/devops_agent.py)
from agents.devops_agent import (
    InfrastructureType, CloudProvider, CIPlatform, MonitoringStack
)
```

### Unified Agent Pattern
```python
class SpecializedAgent(BaseAgent):
    PROMPT_PROFILE = {...}  # PROMPT_PROFILE system
    
    def __init__(self, llm_client, ...):
        super().__init__(...)
        self.template_generator = TemplateClass()  # Initialize templates
    
    def execute(self, context: AgentContext) -> AgentResult:
        # Step 1: LLM decision-making (JSON recommendation)
        recommendation = self._get_recommendation(context)
        
        # Step 2: LLM-based generation (comprehensive plan)
        full_plan = self._generate_full_plan(recommendation, context)
        
        # Step 3: Optionally use templates
        template = self.template_generator.get_template(recommendation)
        
        # Step 4: Return unified result
        return self.create_result(
            success=True,
            output=full_plan,
            metadata={"recommendation": recommendation, "template": template}
        )
```

---

## Testing Results

### Full Test Suite
```
======================================================================
                 SPECIALIZED AGENTS TEST SUITE
======================================================================

✅ DSAgent (Data Science)
   Execution Time: 30.82s
   Test Case: Sentiment analysis for 100K+ reviews
   Output: Comprehensive ML architecture with BERT, PyTorch, FastAPI
   Status: PASSED

✅ MLOAgent (MLOps)
   Execution Time: 25.28s
   Test Case: Fraud detection model deployment (10K req/sec)
   Output: MLflow serving, Kubernetes scaling, drift monitoring
   Status: PASSED

✅ DOAgent (DevOps)
   Execution Time: 38.90s
   Test Case: E-commerce microservices (8 services, multi-cloud)
   Output: Terraform IaC, Kubernetes configs, GitHub Actions CI/CD
   Status: PASSED

🎯 Overall: 3/3 PASSED
======================================================================
```

---

## Future Enhancements

1. **Template Auto-Selection**
   - Parse LLM recommendation to automatically select best template
   - Combine template scaffolding with LLM-generated customizations

2. **Hybrid Execution Modes**
   - `template-only`: Fast, pre-tested (instant)
   - `llm-only`: Flexible, creative (slow, expensive)
   - `hybrid`: Best of both (current implementation)

3. **Feedback Loop Integration**
   - Track agent recommendation quality
   - Use feedback to refine PROMPT_PROFILE
   - Improve template selection over time

4. **Collaborative Agents**
   - DSAgent → generates architecture
   - CoderAgent → uses architecture to generate project files
   - MLOAgent → uses code artifacts to design deployment

5. **Template Versioning**
   - Keep multiple template versions
   - LLM recommends version based on project requirements
   - Track template performance metrics

---

## Summary

The **unified agent architecture** in TerraQore Studio v1.2.1 represents a best-practice pattern for combining:
- **AI Flexibility** (LLM-based decision making via PROMPT_PROFILE)
- **Engineering Reliability** (pre-tested template scaffolding)
- **Maintainability** (single source of truth per domain)
- **Cost Efficiency** (LLM for decisions only)

This approach scales to additional domains (DataEngineer, SecurityArchitect, etc.) while maintaining the quality standards that make TerraQore suitable for production environments.

---

**Last Updated**: January 2, 2026  
**Version**: 1.2.1-UNIFIED  
**Status**: Production Ready
