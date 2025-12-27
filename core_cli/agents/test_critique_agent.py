"""
Test Critique Agent
Analyzes codebases and generates test recommendations and scaffolds.
"""

import logging
import json
from pathlib import Path
from typing import List
from agents.base import BaseAgent, AgentContext, AgentResult
from core.llm_client import LLMClient
from core.security_validator import validate_agent_input, SecurityViolation
from tools.codebase_analyzer import get_codebase_analyzer
from tools.test_suite_generator import get_test_generator

logger = logging.getLogger(__name__)


class TestCritiqueAgent(BaseAgent):
    """Agent that analyzes code and generates test recommendations."""
    
    def __init__(self, llm_client: LLMClient, verbose: bool = False, retriever=None):
        """Initialize test critique agent.
        
        Args:
            llm_client: LLM client for analysis.
            verbose: Verbose logging.
            retriever: RAG retriever for context.
        """
        super().__init__(
            name="TestCritiqueAgent",
            llm_client=llm_client,
            verbose=verbose,
            retriever=retriever
        )
        self.analyzer = None
        self.generator = None
    
    def validate_context(self, context: AgentContext) -> bool:
        """Validate context has required information.
        
        Args:
            context: Agent context.
            
        Returns:
            True if context is valid.
        """
        return context.project_id is not None or context.metadata.get("project_root") is not None
    
    def _generate_response(self, context: AgentContext) -> str:
        """Generate test critique response.
        
        Args:
            context: Agent context.
            
        Returns:
            Critique response string.
        """
        # Get project root
        project_root = context.metadata.get("project_root")
        if not project_root:
            project_root = Path.cwd() / "projects" / f"project_{context.project_id}"
        else:
            project_root = Path(project_root)
        
        try:
            # Initialize analyzer and generator
            self.analyzer = get_codebase_analyzer(project_root)
            self.generator = get_test_generator(project_root)
            
            # Analyze codebase
            analysis = self.analyzer.analyze()
            
            logger.info(f"Analyzed project: {analysis.python_files} files, "
                       f"{analysis.total_classes} classes, "
                       f"{analysis.total_functions} functions")
            
            # Generate coverage report
            coverage_report = self.analyzer.generate_coverage_report()
            
            # Estimate test coverage
            coverage_estimate = self.generator.estimate_test_coverage()
            
            # Build critique
            critique = self._build_critique(analysis, coverage_estimate, coverage_report)
            
            return critique
            
        except Exception as e:
            logger.error(f"Error in test critique: {e}", exc_info=True)
            return f"Error analyzing codebase: {str(e)}"
    
    def _build_critique(self, analysis, coverage_estimate, coverage_report: str) -> str:
        """Build comprehensive test critique.
        
        Args:
            analysis: Codebase analysis results.
            coverage_estimate: Coverage estimate.
            coverage_report: Human-readable report.
            
        Returns:
            Formatted critique string.
        """
        critique = ""
        critique += coverage_report + "\n"
        
        # Test Coverage Assessment
        critique += "🧪 TEST COVERAGE ASSESSMENT\n"
        critique += "=" * 60 + "\n\n"
        
        critique += f"Total Functions: {coverage_estimate['total_functions']}\n"
        critique += f"Total Complexity: {coverage_estimate['total_complexity']}\n"
        critique += f"Test Files: {coverage_estimate['coverage_estimate']}\n\n"
        
        # Priority areas
        if coverage_estimate['priority_areas']:
            critique += "🔴 HIGH PRIORITY TEST AREAS:\n"
            for i, area in enumerate(coverage_estimate['priority_areas'], 1):
                critique += f"  {i}. {area}\n"
            critique += "\n"
        
        # Untested complexity breakdown
        if coverage_estimate['untested_areas']:
            critique += "⚠️  UNTESTED COMPLEXITY BY FILE:\n"
            for filepath, complexity in list(coverage_estimate['untested_areas'].items())[:5]:
                critique += f"  • {filepath}: {complexity}\n"
            critique += "\n"
        
        # Recommendations
        critique += "📋 TEST GENERATION RECOMMENDATIONS\n"
        critique += "=" * 60 + "\n\n"
        
        # Generate critical tests
        critical_tests = self.generator.generate_critical_tests()
        if critical_tests:
            critique += f"🎯 Generated {len(critical_tests)} critical test files:\n"
            for test_path in list(critical_tests.keys())[:5]:
                critique += f"  • {Path(test_path).name}\n"
            critique += "\n"
            
            critique += "Use these commands to apply generated tests:\n"
            for test_path in list(critical_tests.keys())[:3]:
                critique += f"  TerraQore apply-tests {test_path}\n"
        
        # Action items
        critique += "\n🚀 NEXT STEPS\n"
        critique += "=" * 60 + "\n"
        critique += "1. Review high-priority test areas above\n"
        critique += "2. Run: TerraQore generate-tests <project>  # Generate test scaffold\n"
        critique += "3. Implement specific test logic in generated files\n"
        critique += "4. Run tests: pytest tests/\n"
        critique += "5. Monitor coverage with: TerraQore test-coverage <project>\n"
        
        return critique
    
    def execute(self, context: AgentContext) -> AgentResult:
        """Execute test critique analysis.
        
        Args:
            context: Agent execution context.
            
        Returns:
            AgentResult with critique findings.
        """
        # Validate input for security violations
        try:
            validate_agent_input(lambda self, ctx: None)(self, context)
        except SecurityViolation as e:
            logger.error(f"[{self.name}] Security validation failed: {str(e)}")
            return AgentResult(success=False, output="", agent_name=self.name,
                             error=f"Security validation failed: {str(e)}")
        logger.info(f"TestCritiqueAgent starting analysis for project {context.project_id}")
        
        if not self.validate_context(context):
            return AgentResult(
                success=False,
                output="",
                agent_name=self.name,
                execution_time=0.0,
                error="Invalid context: project_id or project_root required"
            )
        
        import time
        start_time = time.time()
        
        try:
            response = self._generate_response(context)
            execution_time = time.time() - start_time
            
            return AgentResult(
                success=True,
                output=response,
                agent_name=self.name,
                execution_time=execution_time,
                metadata={
                    "analysis_type": "test_critique",
                    "generated_test_templates": True,
                    "priority_count": len(self.generator.estimate_test_coverage().get("priority_areas", []))
                }
            )
        except Exception as e:
            logger.error(f"Test critique failed: {e}", exc_info=True)
            execution_time = time.time() - start_time
            
            return AgentResult(
                success=False,
                output="",
                agent_name=self.name,
                execution_time=execution_time,
                error=str(e)
            )


def get_test_critique_agent(llm_client: LLMClient, verbose: bool = False, retriever=None) -> TestCritiqueAgent:
    """Factory function for test critique agent.
    
    Args:
        llm_client: LLM client.
        verbose: Verbose logging.
        retriever: RAG retriever.
        
    Returns:
        Configured TestCritiqueAgent.
    """
    return TestCritiqueAgent(llm_client, verbose=verbose, retriever=retriever)
