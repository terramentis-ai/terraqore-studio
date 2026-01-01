"""
TerraQore DevOps Agent
Specialized agent for infrastructure automation and deployment orchestration.
"""

import logging
from typing import Dict, Any, Optional
import json

from agents.base import BaseAgent, AgentContext, AgentResult
from core.llm_client import LLMClient
from core.security_validator import validate_agent_input, SecurityViolation

logger = logging.getLogger(__name__)


class DOAgent(BaseAgent):
    """Agent specialized in DevOps and infrastructure automation.
    
    Capabilities:
    - Generate Infrastructure-as-Code (Terraform, CloudFormation)
    - Create container configurations (Docker, Kubernetes)
    - Design CI/CD pipelines
    - Plan monitoring and logging infrastructure
    - Set up deployment automation
    """

    PROMPT_PROFILE = {
        "role": "DevOps Agent — infrastructure automation specialist",
        "mission": "Design scalable infrastructure and automated deployment pipelines using modern DevOps practices and Infrastructure-as-Code.",
        "objectives": [
            "Generate Infrastructure-as-Code for multiple cloud providers (AWS, GCP, Azure)",
            "Create container configurations with Docker and Kubernetes manifests",
            "Design comprehensive CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins)",
            "Establish monitoring, logging, and alerting infrastructure",
            "Implement security best practices and compliance requirements"
        ],
        "guardrails": [
            "Follow cloud provider best practices and cost optimization",
            "Include security groups, IAM roles, and network isolation",
            "Ensure secrets management and encryption",
            "Plan for high availability and disaster recovery"
        ],
        "response_structure": [
            "Infrastructure Overview",
            "Cloud Architecture",
            "Container Configuration",
            "CI/CD Pipeline",
            "Monitoring & Logging",
            "Security Configuration",
            "Deployment Workflow",
            "Implementation Files"
        ],
        "response_format": (
            "Use Markdown with clear sections. Include:\n"
            "- Cloud provider selection and architecture diagram\n"
            "- Terraform/CloudFormation templates or pseudo-code\n"
            "- Dockerfile and docker-compose.yml configurations\n"
            "- Kubernetes manifests (Deployment, Service, Ingress)\n"
            "- CI/CD pipeline YAML (GitHub Actions, GitLab CI)\n"
            "- Monitoring setup (Prometheus, Grafana, CloudWatch)\n"
            "- Security configurations (secrets, IAM, network policies)\n"
            "- Step-by-step deployment instructions"
        ),
        "tone": "Systematic, security-conscious, and automation-focused"
    }
    
    def __init__(self, llm_client: LLMClient, verbose: bool = True, retriever: object = None):
        """Initialize DO Agent.
        
        Args:
            llm_client: LLM client for AI interactions.
            verbose: Whether to log detailed execution info.
            retriever: Optional retriever for context.
        """
        super().__init__(
            name="DOAgent",
            description="Designs infrastructure automation and deployment workflows",
            llm_client=llm_client,
            verbose=verbose,
            retriever=retriever,
            prompt_profile=self.PROMPT_PROFILE
        )
    
    def execute(self, context: AgentContext) -> AgentResult:
        """Execute DevOps infrastructure planning.
        
        Args:
            context: Agent execution context containing project requirements.
            
        Returns:
            AgentResult with infrastructure configurations and deployment workflows.
        """
        try:
            # Security validation
            validate_agent_input(context.task)
            
            # Build comprehensive prompt
            prompt = f"""
Project Requirements:
{context.task}

Infrastructure Context:
- Cloud Provider: {context.metadata.get('cloud_provider', 'AWS (default) or multi-cloud')}
- Application Type: {context.metadata.get('app_type', 'Web application / API service')}
- Scale Requirements: {context.metadata.get('scale', 'Auto-scaling (2-10 instances)')}
- Budget Constraints: {context.metadata.get('budget', 'Cost-optimized')}

Generate a comprehensive DevOps infrastructure plan including:
1. Cloud architecture design (compute, storage, networking)
2. Infrastructure-as-Code templates (Terraform/CloudFormation)
3. Container configurations (Docker, Kubernetes)
4. CI/CD pipeline definition
5. Monitoring, logging, and alerting setup
6. Security configurations and best practices
7. Deployment workflow and rollback procedures
8. Cost optimization recommendations

Focus on:
- Scalability and high availability
- Security and compliance
- Automation and reproducibility
- Cost efficiency
- Operational simplicity
"""
            
            # Generate infrastructure plan
            response = self._generate_response(prompt, context)
            
            if not response.success:
                return AgentResult(
                    success=False,
                    output="",
                    error=f"Infrastructure plan generation failed: {response.error}",
                    metadata={"raw_error": response.error},
                    execution_time=0.0
                )
            
            # Parse and structure the response
            infra_plan = response.content
            
            # Extract structured information
            metadata = {
                "plan_length": len(infra_plan),
                "has_iac": any(term in infra_plan.lower() for term in ["terraform", "cloudformation", "pulumi"]),
                "has_containers": any(term in infra_plan.lower() for term in ["docker", "kubernetes", "k8s"]),
                "has_cicd": any(term in infra_plan.lower() for term in ["ci/cd", "github actions", "gitlab", "jenkins"]),
                "has_monitoring": any(term in infra_plan.lower() for term in ["prometheus", "grafana", "cloudwatch", "datadog"]),
                "has_security": any(term in infra_plan.lower() for term in ["security", "iam", "secrets", "encryption"]),
                "model": response.model,
                "provider": response.provider
            }
            
            return AgentResult(
                success=True,
                output=infra_plan,
                metadata=metadata,
                execution_time=response.usage.get("total_time", 0.0) if response.usage else 0.0
            )
            
        except SecurityViolation as e:
            logger.error(f"Security violation in DOAgent: {e}")
            return AgentResult(
                success=False,
                output="",
                error=f"Security violation: {str(e)}",
                metadata={"security_error": True},
                execution_time=0.0
            )
        except Exception as e:
            logger.error(f"DOAgent execution failed: {e}", exc_info=True)
            return AgentResult(
                success=False,
                output="",
                error=f"Execution failed: {str(e)}",
                metadata={"exception_type": type(e).__name__},
                execution_time=0.0
            )
