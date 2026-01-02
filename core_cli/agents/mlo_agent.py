"""
TerraQore MLOps Agent
Specialized agent for ML model deployment, monitoring, and lifecycle management.

Unified Agent: Combines PROMPT_PROFILE-based LLM decision making with
MLOps best practices and templates for production ML workflows.
"""

import logging
from typing import Dict, Any, Optional
import json
import time

from agents.base import BaseAgent, AgentContext, AgentResult
from core.llm_client import LLMClient
from core.security_validator import validate_agent_input, SecurityViolation
from agents.mlops_agent import DeploymentEnvironment, MonitoringMetricType, ModelStrategy

logger = logging.getLogger(__name__)


class MLOAgent(BaseAgent):
    """Agent specialized in MLOps and production ML workflows.
    
    Capabilities:
    - Design model deployment strategies
    - Plan monitoring and observability
    - Set up experiment tracking
    - Implement model versioning and registry
    - Create CI/CD for ML pipelines
    """

    PROMPT_PROFILE = {
        "role": "MLOps Agent — production ML lifecycle specialist",
        "mission": "Design robust MLOps infrastructure for model deployment, monitoring, versioning, and continuous improvement.",
        "objectives": [
            "Design deployment strategies (batch, real-time, edge) with appropriate serving infrastructure",
            "Establish comprehensive monitoring for model performance, data drift, and system health",
            "Implement experiment tracking and model registry systems",
            "Create automated retraining pipelines and A/B testing frameworks",
            "Set up CI/CD workflows for ML model updates"
        ],
        "guardrails": [
            "Prioritize model reproducibility and versioning",
            "Include data validation and schema enforcement",
            "Plan for gradual rollouts and rollback mechanisms",
            "Ensure compliance with data privacy regulations"
        ],
        "response_structure": [
            "Deployment Strategy",
            "Model Serving Infrastructure",
            "Monitoring & Observability",
            "Experiment Tracking & Registry",
            "CI/CD Pipeline",
            "Retraining Automation",
            "Implementation Roadmap"
        ],
        "response_format": (
            "Use Markdown with clear sections. Include:\n"
            "- Deployment environment setup (dev/staging/prod)\n"
            "- Model serving options (TensorFlow Serving, TorchServe, MLflow, etc.)\n"
            "- Metrics to monitor (performance, drift, latency, throughput)\n"
            "- Experiment tracking tools (MLflow, Weights & Biases, Neptune)\n"
            "- CI/CD pipeline stages (test, build, deploy)\n"
            "- Automated retraining triggers and schedules\n"
            "- Infrastructure-as-code templates"
        ),
        "tone": "Production-focused, reliability-oriented, and systematic"
    }
    
    def __init__(self, llm_client: LLMClient, verbose: bool = True, retriever: object = None):
        """Initialize MLO Agent.
        
        Args:
            llm_client: LLM client for AI interactions.
            verbose: Whether to log detailed execution info.
            retriever: Optional retriever for context.
        """
        super().__init__(
            name="MLOAgent",
            description="Designs MLOps infrastructure for model deployment and monitoring",
            llm_client=llm_client,
            verbose=verbose,
            retriever=retriever,
            prompt_profile=self.PROMPT_PROFILE
        )
    
    def execute(self, context: AgentContext) -> AgentResult:
        """Execute MLOps infrastructure planning with best-practice templates.
        
        Step 1: Use LLM to analyze deployment requirements
        Step 2: Recommend deployment strategy and serving framework
        Step 3: Design comprehensive monitoring and observability
        Step 4: Create implementation roadmap
        
        Args:
            context: Agent execution context containing project requirements.
            
        Returns:
            AgentResult with MLOps architecture and workflows.
        """
        start_time = time.time()
        try:
            # Security validation
            validate_agent_input(context.user_input)
            
            # Step 1: Analyze deployment requirements
            analysis_prompt = f"""
Given this ML deployment requirement:
{context.user_input}

Model context:
{context.metadata.get('model_info', 'TBD')}

Provide a JSON response with:
{{
  "deployment_type": "batch|real-time|edge|hybrid",
  "expected_throughput": "requests per second or records per batch",
  "serving_framework": "mlflow|tensorflow_serving|torchserve|kserve|seldon",
  "monitoring_needs": ["performance", "drift", "latency", "throughput"],
  "experiment_tracking": "mlflow|wandb|neptune|comet",
  "key_requirements": ["item1", "item2"]
}}

Be concise and JSON-valid.
"""
            
            response = self._generate_response(analysis_prompt, context)
            
            if not response.success:
                return self.create_result(
                    success=False,
                    output="",
                    execution_time=time.time() - start_time,
                    error=f"MLOps analysis failed: {response.error}",
                    metadata={"stage": "analysis", "error": response.error}
                )
            
            # Parse recommendation
            try:
                rec_text = response.content
                if "```json" in rec_text:
                    rec_text = rec_text.split("```json")[1].split("```")[0]
                elif "```" in rec_text:
                    rec_text = rec_text.split("```")[1].split("```")[0]
                
                recommendation = json.loads(rec_text)
            except (json.JSONDecodeError, IndexError) as e:
                logger.warning(f"Could not parse MLOps recommendation: {e}")
                recommendation = self._parse_recommendation_fallback(response.content)
            
            # Step 2-4: Generate comprehensive MLOps infrastructure plan
            mlops_prompt = f"""
Based on this ML deployment requirement:
{context.user_input}

And this deployment analysis:
{json.dumps(recommendation, indent=2)}

Generate a comprehensive MLOps infrastructure plan with:

# Deployment Strategy
- Deployment Type: {recommendation.get('deployment_type', 'real-time')}
- Serving Framework: {recommendation.get('serving_framework', 'MLflow')}
- Environment Setup (Dev/Staging/Prod)
- Gradual Rollout Strategy (canary, A/B testing)
- Rollback Plan

# Model Serving
- Containerization approach (Docker)
- Scaling strategy (auto-scaling policies)
- Load balancing (Kubernetes Ingress)
- API gateway configuration

# Monitoring & Observability
- Model Performance Metrics
- Data Drift Detection (KL divergence, Kolmogorov-Smirnov)
- Prediction Drift Monitoring
- Latency and Throughput Tracking
- System Health Monitoring
- Logging Strategy (Fluentd, ELK, CloudWatch)
- Alerting Rules and Thresholds

# Experiment Tracking & Model Registry
- Tool: {recommendation.get('experiment_tracking', 'MLflow')}
- Model Versioning Strategy
- Artifact Storage
- Model Metadata Management
- Model Promotion Workflow

# CI/CD Pipeline
- Model Testing (unit, integration, performance)
- Automated Deployment Triggers
- Model Registry Integration
- Data Validation Steps
- Production Deployment Steps
- Documentation and Reproducibility

# Automated Retraining
- Retraining Triggers (schedule, performance threshold, data drift)
- Hyperparameter Optimization
- Automated Testing of New Models
- Performance Comparison and Promotion
- Continuous Learning Loop

# Implementation Roadmap
- Phase 1 (Week 1-2): Foundation setup
- Phase 2 (Week 3-4): Deployment infrastructure
- Phase 3 (Week 5-6): Monitoring and observability
- Phase 4 (Week 7+): Continuous improvement automation
"""
            
            mlops_response = self._generate_response(mlops_prompt, context)
            
            if not mlops_response.success:
                logger.warning("Could not generate full MLOps plan, using analysis")
                final_output = json.dumps(recommendation, indent=2)
            else:
                final_output = mlops_response.content
            
            metadata = {
                "plan_length": len(final_output),
                "recommendation": recommendation,
                "has_deployment": "deployment" in final_output.lower(),
                "has_monitoring": "monitoring" in final_output.lower(),
                "has_cicd": "ci/cd" in final_output.lower() or "pipeline" in final_output.lower(),
                "model": response.model,
                "provider": response.provider,
                "stage": "complete"
            }
            
            execution_time = time.time() - start_time
            return self.create_result(
                success=True,
                output=final_output,
                execution_time=execution_time,
                metadata=metadata
            )
            
        except SecurityViolation as e:
            logger.error(f"Security violation in MLOAgent: {e}")
            return self.create_result(
                success=False,
                output="",
                execution_time=time.time() - start_time,
                error=f"Security violation: {str(e)}",
                metadata={"security_error": True}
            )
        except Exception as e:
            logger.error(f"MLOAgent execution failed: {e}", exc_info=True)
            return self.create_result(
                success=False,
                output="",
                execution_time=time.time() - start_time,
                error=f"Unexpected error: {str(e)}",
                metadata={"exception": str(e)}
            )
    
    def _parse_recommendation_fallback(self, content: str) -> Dict[str, Any]:
        """Parse recommendation when JSON parsing fails."""
        return {
            "deployment_type": "real-time",
            "serving_framework": "mlflow",
            "experiment_tracking": "mlflow",
            "justification": "Fallback recommendation",
            "raw_content": content
        }
