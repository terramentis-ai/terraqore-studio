"""
Flynt Idea Validator Agent
Validates project ideas for feasibility, complexity, and risk assessment.
"""

import time
import logging
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from agents.base import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger(__name__)


@dataclass
class FeasibilityScore:
    """Feasibility assessment for a project idea."""
    technical_feasibility: float  # 0-10
    timeline_feasibility: float   # 0-10
    resource_feasibility: float   # 0-10
    overall_score: float          # 0-10


@dataclass
class RiskAssessment:
    """Risk identification and mitigation strategies."""
    risk_category: str            # Technical, Timeline, Resources, Dependencies
    risk_description: str
    severity: str                 # Low, Medium, High, Critical
    mitigation_strategy: str
    estimated_impact: str


@dataclass
class IdeaValidation:
    """Complete idea validation result."""
    project_name: str
    is_feasible: bool
    feasibility_score: FeasibilityScore
    risks: List[RiskAssessment]
    scope_analysis: Dict[str, Any]
    technology_recommendations: List[str]
    estimated_effort: str
    recommendation: str
    validation_timestamp: str


class IdeaValidatorAgent(BaseAgent):
    """Agent specialized in validating project ideas and identifying risks.
    
    Capabilities:
    - Assess technical feasibility
    - Evaluate timeline and resource requirements
    - Identify risks and mitigation strategies
    - Recommend technology stacks
    - Scope analysis (MVP vs full feature)
    - Complexity assessment
    """
    
    def __init__(self, llm_client=None, verbose: bool = False):
        """Initialize Idea Validator Agent.
        
        Args:
            llm_client: LLM client for AI interactions.
            verbose: Whether to log detailed execution info.
        """
        super().__init__(
            name="IdeaValidatorAgent",
            description="Validates project feasibility, identifies risks, and assesses complexity",
            llm_client=llm_client,
            verbose=verbose,
            retriever=retriever
        )
        
        # Feasibility rubric
        self.feasibility_rubric = {
            "technical": {
                "well_known_tech": 9,
                "established_frameworks": 7,
                "cutting_edge": 4,
                "experimental": 2
            },
            "timeline": {
                "under_1_month": 9,
                "1_3_months": 7,
                "3_6_months": 5,
                "6_12_months": 3,
                "over_12_months": 1
            },
            "resources": {
                "single_developer": 8,
                "small_team": 6,
                "large_team": 4,
                "enterprise_scale": 2
            }
        }
        
        # Risk categories
        self.risk_categories = [
            "Technical Complexity",
            "Timeline Constraints",
            "Resource Availability",
            "External Dependencies",
            "Scope Creep",
            "Integration Challenges",
            "Performance Requirements"
        ]
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for Idea Validator Agent."""
        return """You are the Idea Validator Agent - an expert in assessing project feasibility and identifying risks.

Your role is to:
1. Assess technical feasibility of the project idea
2. Evaluate timeline and resource requirements
3. Identify potential risks and mitigation strategies
4. Recommend appropriate technology stacks
5. Analyze scope (MVP vs full features)
6. Estimate effort and complexity

When validating ideas:
- Be realistic about complexity
- Consider dependencies and integrations
- Flag scope creep risks
- Suggest MVP approach where appropriate
- Identify skill gaps and resource needs
- Consider emerging technologies vs proven stacks

Feasibility Scoring (0-10):
- 9-10: Highly feasible with standard approaches
- 7-8: Feasible with some challenges
- 5-6: Moderate challenges, needs planning
- 3-4: Significant challenges, high risk
- 0-2: Not feasible or extremely high risk

Risk Assessment should include:
- Risk category (Technical, Timeline, Resources, Dependencies, Scope, Integration, Performance)
- Description of the specific risk
- Severity (Low, Medium, High, Critical)
- Mitigation strategy
- Estimated impact if risk occurs

Output Format:
Return ONLY a valid JSON object with this structure:
{
    "project_name": "Project Name",
    "is_feasible": true,
    "feasibility_score": {
        "technical_feasibility": 8,
        "timeline_feasibility": 7,
        "resource_feasibility": 6,
        "overall_score": 7
    },
    "risks": [
        {
            "risk_category": "Technical Complexity",
            "risk_description": "Specific risk description",
            "severity": "High",
            "mitigation_strategy": "How to mitigate",
            "estimated_impact": "What happens if risk occurs"
        }
    ],
    "scope_analysis": {
        "recommended_mvp": "What to build first",
        "full_features": ["Feature list"],
        "phases": ["Phase breakdown"]
    },
    "technology_recommendations": [
        "Recommended tech/framework",
        "Alternative option"
    ],
    "estimated_effort": "3-6 months with team of 2-3 developers",
    "recommendation": "Clear recommendation on feasibility and next steps",
    "validation_timestamp": "ISO format timestamp"
}"""
    
    def execute(self, context: AgentContext) -> AgentResult:
        """Execute idea validation workflow.
        
        Args:
            context: Agent execution context with project details.
            
        Returns:
            AgentResult with validation output.
        """
        start_time = time.time()
        steps = []
        
        try:
            # Step 1: Extract idea information
            self._log_step("Extracting project idea details")
            idea_info = self._extract_idea_info(context)
            steps.append("Extracted project requirements")
            
            # Step 2: Assess feasibility
            self._log_step("Assessing technical feasibility")
            feasibility = self._assess_feasibility(idea_info, context)
            steps.append("Completed feasibility assessment")
            
            # Step 3: Identify risks
            self._log_step("Identifying risks and challenges")
            risks = self._identify_risks(idea_info, context)
            steps.append(f"Identified {len(risks)} potential risks")
            
            # Step 4: Recommend technologies
            self._log_step("Recommending technology stack")
            tech_recommendations = self._recommend_technologies(idea_info, feasibility)
            steps.append("Generated technology recommendations")
            
            # Step 5: Generate validation report
            self._log_step("Generating validation report")
            validation = self._generate_validation_report(
                idea_info, feasibility, risks, tech_recommendations, context
            )
            steps.append("Validation report complete")
            
            execution_time = time.time() - start_time
            self._log_step(f"Completed in {execution_time:.2f}s")
            
            return self.create_result(
                success=True,
                output=self._format_validation_output(validation),
                execution_time=execution_time,
                metadata={
                    "project_name": validation.project_name,
                    "is_feasible": validation.is_feasible,
                    "overall_score": validation.feasibility_score.overall_score,
                    "risk_count": len(validation.risks),
                    "provider": "idea_validator_agent",
                    "validation": validation.__dict__
                },
                intermediate_steps=steps
            )
            
        except Exception as e:
            error_msg = f"Idea validation failed: {str(e)}"
            logger.error(f"[{self.name}] {error_msg}", exc_info=True)
            
            return self.create_result(
                success=False,
                output=error_msg,
                execution_time=time.time() - start_time,
                metadata={"provider": "idea_validator_agent", "error": str(e)},
                intermediate_steps=steps
            )
    
    def _extract_idea_info(self, context: AgentContext) -> Dict[str, Any]:
        """Extract idea information from context."""
        return {
            "project_name": context.project_name,
            "description": context.project_description or context.user_input,
            "user_input": context.user_input,
            "metadata": context.metadata or {},
            "suggested_tech": context.metadata.get("suggested_tech") if context.metadata else None,
            "timeline": context.metadata.get("timeline") if context.metadata else None,
        }
    
    def _assess_feasibility(self, idea_info: Dict[str, Any], context: AgentContext) -> FeasibilityScore:
        """Assess project feasibility across multiple dimensions."""
        # Use LLM for intelligent assessment if available
        if self.llm_client:
            prompt = f"""Assess the feasibility of this project idea:
            
Project: {idea_info['project_name']}
Description: {idea_info['description']}

Evaluate on a scale of 0-10:
1. Technical Feasibility - Can this be built with current technology?
2. Timeline Feasibility - Is this achievable in reasonable time?
3. Resource Feasibility - Can a small team build this?

Respond with ONLY a JSON object:
{{"technical_feasibility": <0-10>, "timeline_feasibility": <0-10>, "resource_feasibility": <0-10>}}"""
            
            response = self.llm_client.generate(prompt)
            if response.success:
                try:
                    scores = json.loads(response.content)
                    return FeasibilityScore(
                        technical_feasibility=scores.get("technical_feasibility", 5),
                        timeline_feasibility=scores.get("timeline_feasibility", 5),
                        resource_feasibility=scores.get("resource_feasibility", 5),
                        overall_score=(
                            (scores.get("technical_feasibility", 5) +
                             scores.get("timeline_feasibility", 5) +
                             scores.get("resource_feasibility", 5)) / 3
                        )
                    )
                except json.JSONDecodeError:
                    pass
        
        # Fallback to heuristic scoring
        return FeasibilityScore(
            technical_feasibility=7,
            timeline_feasibility=6,
            resource_feasibility=6,
            overall_score=6.3
        )
    
    def _identify_risks(self, idea_info: Dict[str, Any], context: AgentContext) -> List[RiskAssessment]:
        """Identify potential risks in the project."""
        risks = []
        description = idea_info["description"].lower()
        
        # Heuristic risk detection
        risk_patterns = {
            "integration": ["api", "third party", "external", "integrate"],
            "complexity": ["machine learning", "ai", "real-time", "distributed"],
            "timeline": ["urgent", "asap", "quick", "yesterday"],
            "scope": ["everything", "full platform", "complete", "all features"],
        }
        
        for category, keywords in risk_patterns.items():
            if any(kw in description for kw in keywords):
                if category == "integration":
                    risks.append(RiskAssessment(
                        risk_category="Integration Challenges",
                        risk_description="Project involves external integrations that may have API changes or downtime",
                        severity="Medium",
                        mitigation_strategy="Design abstraction layer for integrations, have fallbacks",
                        estimated_impact="Delays in development if APIs change"
                    ))
                elif category == "complexity":
                    risks.append(RiskAssessment(
                        risk_category="Technical Complexity",
                        risk_description="Project involves advanced technologies with steep learning curve",
                        severity="High",
                        mitigation_strategy="Allocate more time for research and prototyping",
                        estimated_impact="Longer development timeline, need specialized expertise"
                    ))
                elif category == "timeline":
                    risks.append(RiskAssessment(
                        risk_category="Timeline Constraints",
                        risk_description="Project has unrealistic timeline expectations",
                        severity="Critical",
                        mitigation_strategy="Negotiate timeline or scope reduction",
                        estimated_impact="Quality issues, technical debt, team burnout"
                    ))
                elif category == "scope":
                    risks.append(RiskAssessment(
                        risk_category="Scope Creep",
                        risk_description="Project description suggests trying to build everything at once",
                        severity="High",
                        mitigation_strategy="Define clear MVP scope, plan phases",
                        estimated_impact="Project never launches, resources exhausted"
                    ))
        
        # Always include common risks
        if not risks:
            risks.append(RiskAssessment(
                risk_category="Resource Availability",
                risk_description="General risk of resource constraints",
                severity="Low",
                mitigation_strategy="Plan resource allocation carefully",
                estimated_impact="Potential delays if resources unavailable"
            ))
        
        return risks[:5]  # Return top 5 risks
    
    def _recommend_technologies(self, idea_info: Dict[str, Any], 
                               feasibility: FeasibilityScore) -> List[str]:
        """Recommend appropriate technologies for the project."""
        description = idea_info["description"].lower()
        recommendations = []
        
        # Technology recommendations based on keywords
        if "api" in description or "backend" in description:
            if feasibility.technical_feasibility >= 7:
                recommendations.append("FastAPI (modern, high-performance)")
                recommendations.append("Django + DRF (proven, full-featured)")
            else:
                recommendations.append("Flask (lightweight, easy to learn)")
        
        if "web" in description or "frontend" in description:
            recommendations.append("React (large ecosystem, flexible)")
            recommendations.append("Vue.js (lightweight, gentle learning curve)")
        
        if "database" in description or "data" in description:
            recommendations.append("PostgreSQL (reliable, feature-rich)")
            recommendations.append("MongoDB (flexible, scalable)")
        
        if "real-time" in description:
            recommendations.append("WebSocket infrastructure")
            recommendations.append("Redis for caching")
        
        if not recommendations:
            recommendations = [
                "Python + FastAPI (general purpose backend)",
                "React (if frontend needed)",
                "PostgreSQL (data persistence)"
            ]
        
        return recommendations
    
    def _generate_validation_report(self, 
                                   idea_info: Dict[str, Any],
                                   feasibility: FeasibilityScore,
                                   risks: List[RiskAssessment],
                                   recommendations: List[str],
                                   context: AgentContext) -> IdeaValidation:
        """Generate comprehensive validation report."""
        from datetime import datetime
        
        is_feasible = feasibility.overall_score >= 5
        
        scope_analysis = {
            "recommended_mvp": f"Core features of {idea_info['project_name']}",
            "full_features": ["Authentication", "Data Management", "API Endpoints"],
            "phases": ["Phase 1: MVP", "Phase 2: Enhanced Features", "Phase 3: Polish & Scale"]
        }
        
        return IdeaValidation(
            project_name=idea_info["project_name"],
            is_feasible=is_feasible,
            feasibility_score=feasibility,
            risks=risks,
            scope_analysis=scope_analysis,
            technology_recommendations=recommendations,
            estimated_effort="2-4 weeks with 1-2 developers" if is_feasible else "Not recommended",
            recommendation=(
                f"Project is feasible with score {feasibility.overall_score:.1f}/10. "
                f"Focus on {risks[0].risk_category if risks else 'planning'} as main risk area."
            ),
            validation_timestamp=datetime.now().isoformat()
        )
    
    def _format_validation_output(self, validation: IdeaValidation) -> str:
        """Format validation report as readable output."""
        output = f"""
IDEA VALIDATION REPORT
{'='*70}

Project: {validation.project_name}
Status: {'FEASIBLE' if validation.is_feasible else 'NOT RECOMMENDED'}

FEASIBILITY SCORES (0-10)
{'-'*70}
Technical Feasibility:  {validation.feasibility_score.technical_feasibility:.1f}/10
Timeline Feasibility:   {validation.feasibility_score.timeline_feasibility:.1f}/10
Resource Feasibility:   {validation.feasibility_score.resource_feasibility:.1f}/10
Overall Score:         {validation.feasibility_score.overall_score:.1f}/10

IDENTIFIED RISKS ({len(validation.risks)} found)
{'-'*70}
"""
        for risk in validation.risks:
            output += f"""
Risk: {risk.risk_category}
  Description: {risk.risk_description}
  Severity: {risk.severity}
  Mitigation: {risk.mitigation_strategy}
"""
        
        output += f"""
SCOPE ANALYSIS
{'-'*70}
Recommended MVP: {validation.scope_analysis.get('recommended_mvp')}
Phases: {', '.join(validation.scope_analysis.get('phases', []))}

TECHNOLOGY RECOMMENDATIONS
{'-'*70}
"""
        for tech in validation.technology_recommendations:
            output += f"  • {tech}\n"
        
        output += f"""
ESTIMATE & RECOMMENDATION
{'-'*70}
Estimated Effort: {validation.estimated_effort}
Recommendation: {validation.recommendation}

Validation Time: {validation.validation_timestamp}
"""
        return output
    
    def _log_step(self, message: str):
        """Log an execution step."""
        if self.verbose:
            logger.info(f"[{self.name}] {message}")
