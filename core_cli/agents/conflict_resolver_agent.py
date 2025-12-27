"""
Conflict Resolver Agent - Automatically attempts to resolve dependency conflicts.

This specialized agent analyzes blocked projects and suggests/implements resolutions.
"""

import logging
import time
from typing import Dict, Any, Optional

from agents.base import BaseAgent, AgentContext, AgentResult
from core.security_validator import validate_agent_input, SecurityViolation
from core.llm_client import LLMClient
from core.psmp import get_psmp_service

logger = logging.getLogger(__name__)


class ConflictResolverAgent(BaseAgent):
    """
    Agent specialized in resolving dependency conflicts.
    
    When a project is BLOCKED due to dependency conflicts, this agent:
    1. Analyzes the conflicts
    2. Suggests resolutions
    3. Optionally applies automated resolution
    4. Updates project state
    """
    
    def __init__(self, llm_client: LLMClient, verbose: bool = True, retriever: object = None):
        """Initialize Conflict Resolver Agent.
        
        Args:
            llm_client: LLM client for generating resolution strategies.
            verbose: Whether to log detailed execution info.
        """
        super().__init__(
            name="ConflictResolverAgent",
            description="Analyzes and resolves dependency conflicts in blocked projects",
            llm_client=llm_client,
            verbose=verbose,
            retriever=retriever
        )
        self.psmp = get_psmp_service()
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for Conflict Resolver Agent."""
        return """You are the Conflict Resolver Agent - an expert in resolving dependency version conflicts.

Your role is to:
1. Analyze dependency conflicts between agents
2. Suggest practical resolution strategies
3. Provide technical justification for each option
4. Recommend the best path forward

When analyzing conflicts:
- Consider version compatibility ranges
- Look for common intermediate versions
- Suggest architectural changes if needed (e.g., service isolation)
- Prioritize runtime dependencies over dev dependencies
- Consider maintenance burden vs. technical debt

Provide your response in this format:
1. **Conflict Summary**: What's conflicting and why
2. **Analysis**: Technical assessment of compatibility
3. **Options**: 2-3 resolution strategies ranked by feasibility
4. **Recommendation**: Best option with implementation steps
5. **Risk Assessment**: Potential issues and mitigation
"""
    
    def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute conflict resolution workflow.
        
        Args:
            context: Agent execution context. metadata should contain:
                - project_id: Project with conflicts
                - conflicts: List of DependencyConflict objects
        
        Returns:
            AgentResult with resolution analysis and recommendations.
        """
        # Validate input for security violations
        try:
            validate_agent_input(lambda self, ctx: None)(self, context)
        except SecurityViolation as e:
            logger.error(f"[{self.name}] Security validation failed: {str(e)}")
            return self.create_result(
                success=False,
                output="",
                execution_time=0,
                error=f"Security validation failed: {str(e)}"
            )
        
        start_time = time.time()
        steps = []
        
        try:
            # Validate context
            if not self.validate_context(context):
                return self.create_result(
                    success=False,
                    output="Invalid context provided",
                    execution_time=time.time() - start_time,
                    error="Missing required context fields"
                )
            
            project_id = context.metadata.get("project_id")
            if not project_id:
                return self.create_result(
                    success=False,
                    output="No project_id in context metadata",
                    execution_time=time.time() - start_time,
                    error="Missing project_id"
                )
            
            self.execution_count += 1
            self._log_step("Starting conflict resolution analysis")
            steps.append("Initialized conflict resolver")
            
            # Get current conflicts
            self._log_step("Retrieving project conflicts")
            conflicts = self.psmp.get_blocking_conflicts(project_id)
            
            if not conflicts:
                self._log_step("No conflicts found - project may already be resolved")
                return self.create_result(
                    success=True,
                    output="No active conflicts to resolve",
                    execution_time=time.time() - start_time,
                    metadata={"project_id": project_id, "conflict_count": 0},
                    intermediate_steps=steps
                )
            
            steps.append(f"Found {len(conflicts)} conflict(s)")
            
            # Analyze each conflict
            self._log_step("Analyzing conflicts")
            analyses = {}
            
            for conflict in conflicts:
                analysis = self._analyze_conflict(conflict, project_id)
                analyses[conflict.library] = analysis
            
            steps.append(f"Analyzed {len(analyses)} unique conflicts")
            
            # Generate resolution recommendations
            self._log_step("Generating resolution strategies")
            recommendations = self._generate_recommendations(conflicts, analyses)
            steps.append("Generated resolution recommendations")
            
            # Format output
            output = self._format_resolution_report(
                project_id, 
                conflicts, 
                analyses, 
                recommendations
            )
            
            execution_time = time.time() - start_time
            self._log_step(f"Completed in {execution_time:.2f}s")
            
            return self.create_result(
                success=True,
                output=output,
                execution_time=execution_time,
                metadata={
                    "project_id": project_id,
                    "conflict_count": len(conflicts),
                    "analyses": analyses,
                    "recommendations": recommendations
                },
                intermediate_steps=steps
            )
            
        except Exception as e:
            error_msg = f"Conflict resolution failed: {str(e)}"
            logger.error(f"[{self.name}] {error_msg}", exc_info=True)
            
            return self.create_result(
                success=False,
                output="",
                execution_time=time.time() - start_time,
                error=error_msg,
                intermediate_steps=steps
            )
    
    def _analyze_conflict(
        self, 
        conflict: Any,  # DependencyConflict
        project_id: int
    ) -> Dict[str, Any]:
        """Analyze a single conflict using LLM."""
        
        prompt = f"""Analyze this dependency conflict and provide a technical assessment:

Library: {conflict.library}
Severity: {conflict.severity}

Conflicting Requirements:
"""
        
        for req in conflict.requirements:
            prompt += f"- {req['agent']}: {req['needs']}"
            if 'purpose' in req and req['purpose']:
                prompt += f" (for {req['purpose']})"
            prompt += "\n"
        
        prompt += f"""
Suggested Resolutions:
{chr(10).join([f"- {r}" for r in conflict.suggested_resolutions[:3]])}

Provide a brief technical analysis (3-4 sentences) of the conflict and compatibility options.
"""
        
        response = self._generate_response(prompt)
        
        if response.success:
            return {
                "library": conflict.library,
                "severity": conflict.severity,
                "analysis": response.content,
                "requirements": conflict.requirements
            }
        else:
            return {
                "library": conflict.library,
                "severity": conflict.severity,
                "analysis": "Unable to generate analysis",
                "requirements": conflict.requirements,
                "error": response.error
            }
    
    def _generate_recommendations(
        self, 
        conflicts: list, 
        analyses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate resolution recommendations for all conflicts."""
        
        # For now, return structured recommendations
        # In production, would use LLM to generate more sophisticated strategies
        
        recommendations = {}
        
        for conflict in conflicts:
            lib = conflict.library
            analysis = analyses.get(lib, {})
            
            # Simple heuristic-based recommendations
            if conflict.severity == "critical":
                strategy = "Priority: Requires immediate resolution to unblock project"
            elif len(conflict.requirements) == 2:
                strategy = "Consider finding intermediate version satisfying both constraints"
            else:
                strategy = "May require architectural change to isolate dependency"
            
            recommendations[lib] = {
                "priority": conflict.severity,
                "strategy": strategy,
                "agents_involved": [r['agent'] for r in conflict.requirements],
                "options": conflict.suggested_resolutions
            }
        
        return recommendations
    
    def _format_resolution_report(
        self,
        project_id: int,
        conflicts: list,
        analyses: Dict[str, Any],
        recommendations: Dict[str, Any]
    ) -> str:
        """Format resolution analysis as readable report."""
        
        report = f"""# Dependency Conflict Resolution Report

## Project Status
- **Project ID**: {project_id}
- **Status**: BLOCKED
- **Total Conflicts**: {len(conflicts)}

---

## Conflict Analysis

"""
        
        for conflict in conflicts:
            lib = conflict.library
            analysis = analyses.get(lib, {})
            rec = recommendations.get(lib, {})
            
            report += f"""### {lib}
**Severity**: {conflict.severity.upper()}

**Conflicting Requirements**:
"""
            for req in conflict.requirements:
                report += f"- `{req['agent']}` requires `{req['needs']}`\n"
            
            report += f"""
**Technical Analysis**:
{analysis.get('analysis', 'N/A')}

**Recommended Strategy**:
{rec.get('strategy', 'N/A')}

**Resolution Options**:
"""
            for i, option in enumerate(rec.get('options', [])[:3], 1):
                report += f"{i}. {option}\n"
            
            report += "\n---\n\n"
        
        report += """## Next Steps
1. Review the resolution options above
2. Choose the best option based on your project constraints
3. Contact the relevant agents to implement the solution
4. Once resolved, use `TerraQore resolve-conflict` to unblock the project
"""
        
        return report
