"""
TerraQore Idea Agent
Specialized agent for project ideation, research, and concept refinement.
"""

import time
import logging
from typing import Dict, Any, List, Optional
import json

from agents.base import BaseAgent, AgentContext, AgentResult
from tools.research import get_research_tool, SearchResult
from core.llm_client import LLMClient
from core.security_validator import validate_agent_input, SecurityViolation

logger = logging.getLogger(__name__)


class IdeaAgent(BaseAgent):
    """Agent specialized in project ideation and research.
    
    Capabilities:
    - Research current trends and technologies
    - Brainstorm project variations
    - Refine concepts based on feasibility
    - Generate actionable project plans
    """
    
    def __init__(self, llm_client: LLMClient, verbose: bool = True, retriever: object = None):
        """Initialize Idea Agent.
        
        Args:
            llm_client: LLM client for AI interactions.
            verbose: Whether to log detailed execution info.
        """
        super().__init__(
            name="IdeaAgent",
            description="Researches trends, brainstorms ideas, and refines project concepts",
            llm_client=llm_client,
            verbose=verbose,
            retriever=retriever
        )
        self.research_tool = get_research_tool()
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for Idea Agent."""
        return """You are the Idea Agent - an expert in project ideation and research for agentic AI projects.

Your role is to:
1. Research current trends and technologies in the project domain
2. Brainstorm creative and feasible project variations
3. Refine concepts based on technical feasibility and user goals
4. Generate clear, actionable project plans

You have access to web research capabilities. Use them to stay current with the latest developments.

When brainstorming:
- Be creative but practical
- Consider technical constraints
- Think about MVP (Minimum Viable Product) scope
- Suggest modern tools and frameworks
- Focus on deliverable prototypes

Format your responses clearly with sections for:
- Research Findings
- Project Variations (3-5 options)
- Recommended Approach
- Next Steps

Be enthusiastic but realistic. Help users turn vague ideas into concrete plans."""
    
    def execute(self, context: AgentContext) -> AgentResult:
        """Execute ideation workflow.
        
        Args:
            context: Agent execution context.
            
        Returns:
            AgentResult with ideation output.
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
        
        # Validate context
        if not self.validate_context(context):
            return self.create_result(
                success=False,
                output="Invalid context provided",
                execution_time=time.time() - start_time,
                error="Missing required context fields"
            )
        
        self.execution_count += 1
        self._log_step("Starting ideation workflow")
        steps.append("Workflow started")
        
        try:
            # Step 1: Research current trends
            self._log_step("Researching current trends")
            research_results = self._research_trends(context)
            steps.append(f"Researched trends: {len(research_results)} results found")
            
            # Step 2: Generate ideas with research context
            self._log_step("Generating project variations")
            ideas = self._generate_ideas(context, research_results)
            steps.append("Generated project variations")
            
            # Step 3: Refine and recommend
            self._log_step("Refining recommendations")
            final_output = self._refine_recommendations(context, ideas, research_results)
            steps.append("Refined recommendations")
            
            execution_time = time.time() - start_time
            self._log_step(f"Completed in {execution_time:.2f}s")
            
            return self.create_result(
                success=True,
                output=final_output,
                execution_time=execution_time,
                metadata={
                    "research_count": len(research_results),
                    "provider": "idea_agent"
                },
                intermediate_steps=steps
            )
            
        except Exception as e:
            error_msg = f"Ideation failed: {str(e)}"
            logger.error(f"[{self.name}] {error_msg}", exc_info=True)
            
            return self.create_result(
                success=False,
                output="",
                execution_time=time.time() - start_time,
                error=error_msg,
                intermediate_steps=steps
            )
    
    def _research_trends(self, context: AgentContext) -> List[SearchResult]:
        """Research current trends related to the project.
        
        Args:
            context: Agent context.
            
        Returns:
            List of search results.
        """
        # Extract key terms from project description
        project_topic = context.project_name
        
        # Search for relevant trends
        queries = [
            f"{project_topic} latest developments",
            f"{project_topic} best practices 2024",
            f"agentic AI {project_topic}"
        ]
        
        all_results = []
        for query in queries[:2]:  # Limit to 2 queries to stay within free tier
            results = self.research_tool.search(query, max_results=3)
            all_results.extend(results)
            if self.verbose:
                logger.info(f"[{self.name}] Found {len(results)} results for: {query}")
        
        return all_results
    
    def _generate_ideas(
        self, 
        context: AgentContext, 
        research_results: List[SearchResult]
    ) -> str:
        """Generate project variations based on research.
        
        Args:
            context: Agent context.
            research_results: Research findings.
            
        Returns:
            Generated ideas as string.
        """
        # Format research for LLM
        research_summary = self.research_tool.format_results(research_results)
        
        prompt = f"""Based on this project idea and current research, brainstorm 3-5 variations:

PROJECT:
{self._format_context(context)}

CURRENT RESEARCH:
{research_summary}

Generate creative but feasible project variations. For each variation:
1. Give it a catchy name
2. Describe the core concept (2-3 sentences)
3. List key features (3-5 bullet points)
4. Suggest tech stack
5. Estimate complexity (Simple/Medium/Complex)

Format as clear sections with headers."""
        
        response = self._generate_response(prompt)
        
        if response.success:
            return response.content
        else:
            return "Error generating ideas. Please try again."
    
    def _refine_recommendations(
        self,
        context: AgentContext,
        ideas: str,
        research_results: List[SearchResult]
    ) -> str:
        """Refine ideas into actionable recommendations.
        
        Args:
            context: Agent context.
            ideas: Generated ideas.
            research_results: Research findings.
            
        Returns:
            Final refined output.
        """
        prompt = f"""Review these project variations and provide a final recommendation:

PROJECT CONTEXT:
{self._format_context(context)}

GENERATED VARIATIONS:
{ideas}

Provide:
1. **Research Summary**: Key findings from current trends (3-4 bullet points)
2. **Recommended Approach**: Which variation is best and why (1 paragraph)
3. **MVP Scope**: What to build first for a working prototype (5-7 bullet points)
4. **Tech Stack**: Specific tools/frameworks to use
5. **Next Steps**: Immediate actions to start (3-5 steps)

Be specific and actionable. Focus on getting to a working prototype quickly."""
        
        response = self._generate_response(prompt)
        
        if response.success:
            # Format final output
            final_output = f"""# 💡 Ideation Results for: {context.project_name}

## 🔍 Research Phase
Found {len(research_results)} relevant sources on current trends and best practices.

---

{response.content}

---

## 📊 Execution Stats
- Research queries: 2
- Results analyzed: {len(research_results)}
- Variations generated: 3-5
- Time to complete: ~{self.execution_count * 30}s

✨ Ready to move to the planning phase!
"""
            return final_output
        else:
            return f"Error refining recommendations: {response.error}"
    
    def quick_research(self, topic: str) -> str:
        """Quick research on a specific topic.
        
        Args:
            topic: Topic to research.
            
        Returns:
            Research summary.
        """
        results = self.research_tool.search(topic, max_results=5)
        
        if not results:
            return f"No results found for: {topic}"
        
        summary_prompt = f"""Summarize these research findings about "{topic}":

{self.research_tool.format_results(results)}

Provide:
1. Key Takeaways (3-5 bullets)
2. Current State of Technology
3. Recommended Tools/Frameworks
4. Getting Started Tips

Keep it concise and actionable."""
        
        response = self._generate_response(summary_prompt)
        
        if response.success:
            return response.content
        else:
            return self.research_tool.format_results(results)