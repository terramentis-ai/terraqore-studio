"""
TerraQore DevOps Agent
Specialized agent for infrastructure automation and deployment orchestration.

Unified Agent: Combines PROMPT_PROFILE-based LLM decision making with
Infrastructure templates and best practices for modern deployment.
"""

import logging
from typing import Dict, Any, Optional
import json
import time

from agents.base import BaseAgent, AgentContext, AgentResult
from core.llm_client import LLMClient
from core.security_validator import validate_agent_input, SecurityViolation
from agents.devops_agent import InfrastructureType, CloudProvider, CIPlatform, MonitoringStack

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
        """Execute DevOps infrastructure planning with template integration.
        
        Step 1: Analyze infrastructure requirements and cloud provider
        Step 2: Recommend infrastructure architecture and tools
        Step 3: Design complete deployment pipeline
        Step 4: Create IaC templates and CI/CD workflows
        
        Args:
            context: Agent execution context containing project requirements.
            
        Returns:
            AgentResult with infrastructure IaC configurations and deployment workflows.
        """
        start_time = time.time()
        try:
            # Security validation
            validate_agent_input(context.user_input)
            
            # Classify task sensitivity (Phase 5)
            task_sensitivity = self.classify_task_sensitivity(
                task_type="devops_planning",
                has_private_data=False,
                has_sensitive_data=False,
                is_security_task=False
            )
            self._log_step(f"Task classified as: {task_sensitivity}")
            
            # Step 1: Analyze infrastructure requirements
            analysis_prompt = f"""
Given this infrastructure requirement:
{context.user_input}

Application context:
{context.metadata.get('app_info', 'TBD')}

Provide a JSON response with:
{{
  "cloud_provider": "aws|azure|gcp|onpremise|multi",
  "infrastructure_type": "docker_compose|kubernetes|terraform|cloudformation|ansible",
  "ci_platform": "github_actions|gitlab_ci|jenkins|circleci|azure_pipelines",
  "monitoring_stack": "prometheus_grafana|datadog|elk_stack|cloudwatch",
  "expected_scale": "small|medium|large|enterprise",
  "key_requirements": ["item1", "item2", "item3"]
}}

Be concise and JSON-valid.
"""
            
            response = self._generate_response(analysis_prompt, context)
            
            if not response.success:
                return self.create_result(
                    success=False,
                    output="",
                    execution_time=time.time() - start_time,
                    error=f"Infrastructure analysis failed: {response.error}",
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
                logger.warning(f"Could not parse infrastructure recommendation: {e}")
                recommendation = self._parse_recommendation_fallback(response.content)
            
            # Step 2-4: Generate comprehensive infrastructure plan
            infra_prompt = f"""
Based on this infrastructure requirement:
{context.user_input}

And this infrastructure analysis:
{json.dumps(recommendation, indent=2)}

Generate a comprehensive DevOps infrastructure plan with:

# Cloud Architecture
- Cloud Provider: {recommendation.get('cloud_provider', 'AWS')}
- Architecture Overview (compute, storage, networking)
- Scaling Strategy
- High Availability & Disaster Recovery
- Security Zones and Network Segmentation

# Infrastructure-as-Code
- Primary Tool: {recommendation.get('infrastructure_type', 'Terraform')}
- VPC/Network Configuration
- Compute Resources (EC2/AKS/GKE, auto-scaling groups)
- Storage Solutions (RDS, S3/Blob, ElastiCache)
- Load Balancing and Traffic Management
- Cost Optimization Strategies

# Containerization
- Docker Strategy and Best Practices
- Container Registry Setup
- Image Building and Scanning
- Kubernetes Deployment (if applicable)
  - Namespaces and Resource Quotas
  - Ingress and Service Configuration
  - StatefulSets and DaemonSets
  - Pod Security Policies

# CI/CD Pipeline
- Platform: {recommendation.get('ci_platform', 'GitHub Actions')}
- Source Control Integration
- Build Automation
- Testing Stages (unit, integration, smoke)
- Artifact Management
- Deployment Stages (dev, staging, production)
- Automated Rollback Procedures
- Release Management

# Monitoring, Logging & Alerting
- Monitoring Stack: {recommendation.get('monitoring_stack', 'Prometheus + Grafana')}
- Application Performance Monitoring
- Infrastructure Metrics (CPU, memory, disk)
- Log Aggregation and Centralization
- Alert Rules and Escalation
- Dashboard Setup
- SLA/SLO Definition

# Security & Compliance
- Identity and Access Management (IAM)
- Secrets Management (Vault, AWS Secrets Manager)
- Data Encryption (at-rest and in-transit)
- Network Security (firewalls, WAF, DDoS protection)
- Compliance Requirements (HIPAA, GDPR, PCI)
- Security Scanning and Vulnerability Management
- Audit Logging and Compliance Reporting

# Cost Optimization
- Reserved Instances/Commitments
- Auto-scaling Policies
- Resource Tagging Strategy
- Cost Monitoring and Alerts
- Optimization Recommendations

# Deployment Workflow
- Development Environment Setup
- Staging Environment Setup
- Production Deployment Procedures
- Blue-Green or Canary Deployment Strategy
- Automated Testing Before Production
- Rollback Procedures
- Maintenance and Patching Strategy

# Key Requirements
{json.dumps(recommendation.get('key_requirements', []))}
"""
            
            infra_response = self._generate_response(infra_prompt, context)
            
            if not infra_response.success:
                logger.warning("Could not generate full infrastructure plan, using analysis")
                final_output = json.dumps(recommendation, indent=2)
            else:
                final_output = infra_response.content
            
            metadata = {
                "plan_length": len(final_output),
                "recommendation": recommendation,
                "has_iac": any(term in final_output.lower() for term in ["terraform", "cloudformation", "pulumi"]),
                "has_containers": any(term in final_output.lower() for term in ["docker", "kubernetes", "k8s"]),
                "has_cicd": any(term in final_output.lower() for term in ["ci/cd", "github", "gitlab", "jenkins"]),
                "has_monitoring": any(term in final_output.lower() for term in ["prometheus", "grafana", "cloudwatch"]),
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
            logger.error(f"Security violation in DOAgent: {e}")
            return self.create_result(
                success=False,
                output="",
                execution_time=time.time() - start_time,
                error=f"Security violation: {str(e)}",
                metadata={"security_error": True}
            )
        except Exception as e:
            logger.error(f"DOAgent execution failed: {e}", exc_info=True)
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
            "cloud_provider": "aws",
            "infrastructure_type": "terraform",
            "ci_platform": "github_actions",
            "monitoring_stack": "prometheus_grafana",
            "justification": "Fallback recommendation",
            "raw_content": content
        }
