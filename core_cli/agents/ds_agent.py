"""
TerraQore Data Science Agent
Specialized agent for ML/data science project planning and architecture.

Unified Agent: Combines PROMPT_PROFILE-based LLM decision making with
MLProjectGenerator templates for robust ML project scaffolding.
"""

import logging
from typing import Dict, Any, Optional
import json
import time

from agents.base import BaseAgent, AgentContext, AgentResult
from core.llm_client import LLMClient
from core.security_validator import validate_agent_input, SecurityViolation
from agents.data_science_agent import MLProjectGenerator, ProjectType, MLFramework, DataType

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
        """Initialize DS Agent with integrated templates.
        
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
        # Initialize template generator for code scaffolding
        self.project_generator = MLProjectGenerator()

    
    def execute(self, context: AgentContext) -> AgentResult:
        """Execute data science architecture planning with template integration.
        
        Step 1: Use LLM (PROMPT_PROFILE) to decide architecture (framework, project type)
        Step 2: Select appropriate template from MLProjectGenerator
        Step 3: Enhance template with LLM-specific insights
        Step 4: Return comprehensive project scaffolding
        
        Args:
            context: Agent execution context containing project requirements.
            
        Returns:
            AgentResult with ML architecture + templates scaffolding.
        """
        start_time = time.time()
        try:
            # Security validation
            validate_agent_input(context.user_input)
            
            # Classify task sensitivity (Phase 5)
            task_sensitivity = self.classify_task_sensitivity(
                task_type="data_science_design",
                has_private_data=False,
                has_sensitive_data=False,
                is_security_task=False
            )
            self._log_step(f"Task classified as: {task_sensitivity}")
            
            # Step 1: Generate architecture recommendations using LLM
            architecture_prompt = f"""
Given this ML project requirement:
{context.user_input}

Provide a JSON response with:
{{
  "project_type": "classification|regression|nlp|computer_vision|time_series|clustering",
  "framework": "pytorch|tensorflow|scikit_learn|xgboost|lightgbm|huggingface",
  "data_type": "tabular|image|text|audio|time_series|mixed",
  "suggested_template": "template_key from your framework choice",
  "justification": "why this framework/approach",
  "data_pipeline": {{"scaling": "standard|minmax|robust", "encoding": "onehot|label|target"}},
  "key_considerations": ["item1", "item2", "item3"]
}}

Be concise and JSON-valid.
"""
            
            response = self._generate_response(architecture_prompt, context)
            
            if not response.success:
                return self.create_result(
                    success=False,
                    output="",
                    execution_time=time.time() - start_time,
                    error=f"Architecture recommendation failed: {response.error}",
                    metadata={"stage": "recommendation", "error": response.error}
                )
            
            # Step 2: Parse LLM recommendation
            try:
                rec_text = response.content
                # Extract JSON if wrapped
                if "```json" in rec_text:
                    rec_text = rec_text.split("```json")[1].split("```")[0]
                elif "```" in rec_text:
                    rec_text = rec_text.split("```")[1].split("```")[0]
                
                recommendation = json.loads(rec_text)
            except (json.JSONDecodeError, IndexError) as e:
                logger.warning(f"Could not parse LLM recommendation as JSON: {e}")
                recommendation = self._parse_recommendation_fallback(response.content)
            
            # Step 3: Generate comprehensive architecture documentation
            full_architecture_prompt = f"""
Based on this ML project requirement:
{context.user_input}

And this architecture recommendation:
{json.dumps(recommendation, indent=2)}

Generate a comprehensive ML project architecture document including:

# Project Analysis
- Problem statement
- Success metrics
- Constraints and considerations

# Recommended Framework & Tools
- Framework: {recommendation.get('framework', 'TBD')}
- Justification: {recommendation.get('justification', 'TBD')}
- Key libraries and tools

# Data Pipeline Architecture
- Scaling method: {recommendation.get('data_pipeline', {}).get('scaling', 'standard')}
- Encoding strategy: {recommendation.get('data_pipeline', {}).get('encoding', 'onehot')}
- Data validation steps
- Feature engineering approach

# Model Training Strategy
- Model selection
- Hyperparameter optimization approach
- Validation strategy
- Early stopping criteria

# Evaluation Framework
- Primary metrics
- Secondary metrics
- Testing methodology
- Model explainability approach

# Project Structure
- Recommended file organization
- Module responsibilities
- Configuration management
- Documentation requirements

# Key Considerations
{json.dumps(recommendation.get('key_considerations', []))}
"""
            
            full_response = self._generate_response(full_architecture_prompt, context)
            
            if not full_response.success:
                logger.warning("Could not generate full architecture, using recommendation")
                final_output = json.dumps(recommendation, indent=2)
            else:
                final_output = full_response.content
            
            # Step 4: Build comprehensive metadata
            metadata = {
                "architecture_length": len(final_output),
                "recommendation": recommendation,
                "has_framework_rec": "framework" in final_output.lower(),
                "has_pipeline": "pipeline" in final_output.lower(),
                "has_evaluation": "evaluation" in final_output.lower(),
                "model": response.model,
                "provider": response.provider,
                "stage": "complete",
                "template_available": self._has_template(recommendation)
            }
            
            execution_time = time.time() - start_time
            return self.create_result(
                success=True,
                output=final_output,
                execution_time=execution_time,
                metadata=metadata
            )
            
        except SecurityViolation as e:
            logger.error(f"Security violation in DSAgent: {e}")
            return self.create_result(
                success=False,
                output="",
                execution_time=time.time() - start_time,
                error=f"Security violation: {str(e)}",
                metadata={"security_error": True}
            )
        except Exception as e:
            logger.error(f"DSAgent execution failed: {e}", exc_info=True)
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
            "project_type": "classification",
            "framework": "pytorch",
            "data_type": "tabular",
            "justification": "Fallback recommendation based on content",
            "raw_content": content
        }
    
    def _has_template(self, recommendation: Dict[str, Any]) -> bool:
        """Check if a template exists for the recommendation."""
        try:
            framework = recommendation.get('framework', '').replace('_', '')
            templates = self.project_generator.templates_cache
            for key in templates.keys():
                if framework.lower() in str(key).lower():
                    return True
            return False
        except:
            return False
