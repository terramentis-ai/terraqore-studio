"""
TerraQore Data Science Agent
Specialized agent for ML/data science project planning and architecture.
"""

import logging
from typing import Dict, Any, Optional
import json

from agents.base import BaseAgent, AgentContext, AgentResult
from core.llm_client import LLMClient
from core.security_validator import validate_agent_input, SecurityViolation

logger = logging.getLogger(__name__)


class DSAgent(BaseAgent):
    """Agent specialized in data science and ML project architecture.
    
    Capabilities:
    - Design ML pipelines and workflows
    - Recommend appropriate frameworks and tools
    - Plan data processing strategies
    - Define model evaluation metrics
    """

    PROMPT_PROFILE = {
        "role": "Data Science Agent — ML architecture specialist",
        "mission": "Design comprehensive ML/data science project architectures with appropriate frameworks, pipelines, and evaluation strategies.",
        "objectives": [
            "Analyze project requirements and recommend suitable ML frameworks (PyTorch, TensorFlow, Scikit-learn, XGBoost)",
            "Design data processing pipelines including scaling, encoding, and feature engineering",
            "Define model training strategies with hyperparameter optimization",
            "Establish evaluation metrics and validation approaches",
            "Create project scaffolding with best practices"
        ],
        "guardrails": [
            "Recommend frameworks based on project scale and complexity",
            "Include data validation and quality checks",
            "Ensure reproducibility with random seeds and versioning",
            "Plan for model explainability and monitoring"
        ],
        "response_structure": [
            "Project Analysis",
            "Recommended Framework & Tools",
            "Data Pipeline Architecture",
            "Model Training Strategy",
            "Evaluation Framework",
            "Project Structure"
        ],
        "response_format": (
            "Use Markdown with clear sections. Include:\n"
            "- Framework selection with justification\n"
            "- Data processing steps (cleaning, scaling, encoding)\n"
            "- Model architecture recommendations\n"
            "- Hyperparameter search strategy\n"
            "- Evaluation metrics (primary and secondary)\n"
            "- File structure and module organization"
        ),
        "tone": "Technical, precise, and pragmatic"
    }
    
    def __init__(self, llm_client: LLMClient, verbose: bool = True, retriever: object = None):
        """Initialize DS Agent.
        
        Args:
            llm_client: LLM client for AI interactions.
            verbose: Whether to log detailed execution info.
            retriever: Optional retriever for context.
        """
        super().__init__(
            name="DSAgent",
            description="Designs ML/data science project architectures and pipelines",
            llm_client=llm_client,
            verbose=verbose,
            retriever=retriever,
            prompt_profile=self.PROMPT_PROFILE
        )
    
    def execute(self, context: AgentContext) -> AgentResult:
        """Execute data science architecture planning.
        
        Args:
            context: Agent execution context containing project requirements.
            
        Returns:
            AgentResult with ML architecture recommendations.
        """
        try:
            # Security validation
            validate_agent_input(context.user_input)
            
            # Build comprehensive prompt
            prompt = f"""
Project Requirements:
{context.user_input}

Additional Context:
{context.metadata.get('additional_context', 'None')}

Generate a comprehensive data science project architecture including:
1. Framework and tool recommendations
2. Data pipeline design
3. Model training strategy
4. Evaluation framework
5. Project structure

Focus on:
- Scalability and maintainability
- Best practices for ML workflows
- Reproducibility and versioning
- Production deployment considerations
"""
            
            # Generate architecture plan
            response = self._generate_response(prompt, context)
            
            if not response.success:
                return AgentResult(
                    success=False,
                    output="",
                    error=f"Architecture generation failed: {response.error}",
                    metadata={"raw_error": response.error},
                    execution_time=0.0
                )
            
            # Parse and structure the response
            architecture_plan = response.content
            
            # Extract structured information if possible
            metadata = {
                "architecture_length": len(architecture_plan),
                "has_framework_rec": "framework" in architecture_plan.lower(),
                "has_pipeline": "pipeline" in architecture_plan.lower(),
                "has_evaluation": "evaluation" in architecture_plan.lower(),
                "model": response.model,
                "provider": response.provider
            }
            
            execution_time = response.usage.get("total_time", 0.0) if response.usage else 0.0
            return self.create_result(
                success=True,
                output=architecture_plan,
                execution_time=execution_time,
                metadata=metadata
            )
            
        except SecurityViolation as e:
            logger.error(f"Security violation in DSAgent: {e}")
            return self.create_result(
                success=False,
                output="",
                execution_time=0.0,
                error=f"Security violation: {str(e)}",
                metadata={"security_error": True}
            )
        except Exception as e:
            logger.error(f"DSAgent execution failed: {e}", exc_info=True)
            return self.create_result(
                success=False,
                output="",
                execution_time=0.0,
                error=f"Execution failed: {str(e)}",
                metadata={"exception_type": type(e).__name__}
            )
