"""
TerraQore MLOps Agent
Specialized agent for ML model deployment, monitoring, and lifecycle management.
"""

import logging
from typing import Dict, Any, Optional
import json

from agents.base import BaseAgent, AgentContext, AgentResult
from core.llm_client import LLMClient
from core.security_validator import validate_agent_input, SecurityViolation

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
        """Execute MLOps infrastructure planning.
        
        Args:
            context: Agent execution context containing project requirements.
            
        Returns:
            AgentResult with MLOps architecture and workflows.
        """
        try:
            # Security validation
            validate_agent_input(context.user_input)
            
            # Build comprehensive prompt
            prompt = f"""
Project Requirements:
{context.user_input}

Model Information:
{context.metadata.get('model_info', 'To be determined')}

Deployment Context:
- Target Environment: {context.metadata.get('target_env', 'Cloud (AWS/GCP/Azure)')}
- Expected Load: {context.metadata.get('expected_load', 'Medium (100-1000 req/sec)')}
- SLA Requirements: {context.metadata.get('sla_requirements', 'Standard (99% uptime, <500ms latency)')}

Generate a comprehensive MLOps infrastructure plan including:
1. Model deployment strategy and serving infrastructure
2. Monitoring, logging, and alerting systems
3. Experiment tracking and model registry setup
4. CI/CD pipeline for ML workflows
5. Automated retraining and continuous improvement
6. Implementation roadmap with priorities

Focus on:
- Production reliability and scalability
- Model performance monitoring and drift detection
- Automated testing and validation
- Cost optimization and resource management
"""
            
            # Generate MLOps plan
            response = self._generate_response(prompt, context)
            
            if not response.success:
                return AgentResult(
                    success=False,
                    output="",
                    error=f"MLOps plan generation failed: {response.error}",
                    metadata={"raw_error": response.error},
                    execution_time=0.0
                )
            
            # Parse and structure the response
            mlops_plan = response.content
            
            # Extract structured information
            metadata = {
                "plan_length": len(mlops_plan),
                "has_deployment": "deployment" in mlops_plan.lower(),
                "has_monitoring": "monitoring" in mlops_plan.lower() or "observability" in mlops_plan.lower(),
                "has_cicd": "ci/cd" in mlops_plan.lower() or "pipeline" in mlops_plan.lower(),
                "has_registry": "registry" in mlops_plan.lower(),
                "model": response.model,
                "provider": response.provider
            }
            
            execution_time = response.usage.get("total_time", 0.0) if response.usage else 0.0
            return self.create_result(
                success=True,
                output=mlops_plan,
                execution_time=execution_time,
                metadata=metadata
            )
            
        except SecurityViolation as e:
            logger.error(f"Security violation in MLOAgent: {e}")
            return self.create_result(
                success=False,
                output="",
                execution_time=0.0,
                error=f"Security violation: {str(e)}",
                metadata={"security_error": True}
            )
        except Exception as e:
            logger.error(f"MLOAgent execution failed: {e}", exc_info=True)
            return self.create_result(
                success=False,
                output="",
                execution_time=0.0,
                error=f"Execution failed: {str(e)}",
                metadata={"exception_type": type(e).__name__}
            )
