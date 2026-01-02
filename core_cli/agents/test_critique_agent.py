"""
Test Critique Agent - Autonomous Testing Analysis System
Intelligently analyzes the codebase, generates comprehensive test suites,
executes them, and produces visual robustness reports.

Features:
- Phase 1: CodebaseAnalyzer - AST scanning, project structure mapping
- Phase 2: TestGenerator - Generate pytest/unittest suites
- Phase 3: ExecutionEngine - Run tests, collect metrics
- Phase 4: VisualReporter - Dashboard with coverage, pass rates
"""

import logging
import json
import ast
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .base import BaseAgent, AgentContext, AgentResult
from core.llm_client import LLMClient
from core.security_validator import validate_agent_input, SecurityViolation

try:
    from tools.codebase_analyzer import get_codebase_analyzer
except ImportError:
    get_codebase_analyzer = None

try:
    from tools.test_suite_generator import get_test_generator
except ImportError:
    get_test_generator = None

logger = logging.getLogger(__name__)


# ============================================================================
# PHASE 1: CODEBASE ANALYZER
# ============================================================================

@dataclass
class CodebaseAnalysis:
    """Results of codebase analysis."""
    python_files: int = 0
    total_classes: int = 0
    total_functions: int = 0
    total_lines: int = 0
    cyclomatic_complexity: float = 0.0
    modules: Dict[str, Any] = None
    untested_paths: List[str] = None
    high_complexity_functions: List[Dict] = None


class CodebaseAnalyzer:
    """Phase 1: Intelligently scans and understands the project structure."""
    
    def __init__(self, root_path: str = "."):
        """Initialize analyzer with project root.
        
        Args:
            root_path: Root directory of project to analyze
        """
        self.root_path = Path(root_path)
        self.structure = {
            "agents": {},
            "core_modules": {},
            "tests": {},
            "utils": {},
            "other": {}
        }
        self.analysis = CodebaseAnalysis(modules={}, untested_paths=[], high_complexity_functions=[])
    
    def analyze(self) -> CodebaseAnalysis:
        """Main analysis orchestration.
        
        Returns:
            CodebaseAnalysis with project metrics
        """
        logger.info(f"[CodebaseAnalyzer] Scanning project structure: {self.root_path}")
        
        # Map directory structure
        self._map_directory_structure()
        
        # Analyze Python files
        py_files = list(self.root_path.rglob("*.py"))
        self.analysis.python_files = len(py_files)
        logger.info(f"[CodebaseAnalyzer] Found {len(py_files)} Python files")
        
        # AST analysis for each file
        for py_file in py_files:
            try:
                self._analyze_python_file(py_file)
            except Exception as e:
                logger.warning(f"[CodebaseAnalyzer] Could not analyze {py_file}: {e}")
        
        logger.info(f"[CodebaseAnalyzer] Analysis complete: {self.analysis.total_classes} classes, "
                   f"{self.analysis.total_functions} functions")
        
        return self.analysis
    
    def _map_directory_structure(self):
        """Build tree representation of project structure."""
        for path in self.root_path.rglob("*.py"):
            if path.is_file() and "__pycache__" not in str(path):
                rel_path = path.relative_to(self.root_path)
                
                # Categorize by type
                if "agent" in str(rel_path).lower():
                    category = "agents"
                elif "test" in str(rel_path).lower():
                    category = "tests"
                elif "core" in str(rel_path).lower():
                    category = "core_modules"
                elif "util" in str(rel_path).lower() or "tool" in str(rel_path).lower():
                    category = "utils"
                else:
                    category = "other"
                
                self.structure[category][str(rel_path)] = {
                    "path": str(path),
                    "size": path.stat().st_size
                }
    
    def _analyze_python_file(self, file_path: Path):
        """Use AST to understand class and function definitions.
        
        Args:
            file_path: Path to Python file to analyze
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.analysis.total_lines += len(content.split('\n'))
                
                tree = ast.parse(content, filename=str(file_path))
                
                # Extract classes and functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        self.analysis.total_classes += 1
                        # Count methods
                        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                        self.analysis.total_functions += len(methods)
                    
                    elif isinstance(node, ast.FunctionDef) and not isinstance(node, ast.AsyncFunctionDef):
                        self.analysis.total_functions += 1
                        
                        # Calculate cyclomatic complexity (simple estimation)
                        complexity = self._estimate_complexity(node)
                        if complexity > 5:  # High complexity threshold
                            self.analysis.high_complexity_functions.append({
                                "file": str(file_path.relative_to(self.root_path)),
                                "function": node.name,
                                "complexity": complexity,
                                "lines": node.end_lineno - node.lineno if node.end_lineno else 0
                            })
        
        except Exception as e:
            logger.debug(f"[CodebaseAnalyzer] AST parsing failed for {file_path}: {e}")
    
    @staticmethod
    def _estimate_complexity(node: ast.FunctionDef) -> int:
        """Estimate cyclomatic complexity of a function.
        
        Args:
            node: AST function node
            
        Returns:
            Estimated complexity score
        """
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    def get_untested_modules(self) -> List[str]:
        """Identify modules without corresponding test files.
        
        Returns:
            List of untested module paths
        """
        untested = []
        
        for category, files in self.structure.items():
            if category == "tests":
                continue
                
            for file_path in files.keys():
                # Check if corresponding test exists
                test_name = f"test_{Path(file_path).stem}.py"
                test_found = any(test_name in test_file for test_file in self.structure.get("tests", {}).keys())
                
                if not test_found:
                    untested.append(file_path)
        
        self.analysis.untested_paths = untested
        return untested


# ============================================================================
# PHASE 2: TEST GENERATOR
# ============================================================================

class TestGenerator:
    """Phase 2: Generates comprehensive test suites based on analysis."""
    
    def __init__(self, root_path: str = "."):
        """Initialize test generator.
        
        Args:
            root_path: Root directory for test generation
        """
        self.root_path = Path(root_path)
        self.test_templates: Dict[str, str] = {}
    
    def generate_test_suite(self, analysis: CodebaseAnalysis) -> Dict[str, str]:
        """Generate test suite for entire project.
        
        Args:
            analysis: CodebaseAnalysis object
            
        Returns:
            Dictionary of {test_file_path: test_code}
        """
        logger.info(f"[TestGenerator] Generating test suite for {analysis.python_files} files")
        
        tests = {}
        
        # Generate tests for high-complexity functions
        for func_info in analysis.high_complexity_functions[:10]:  # Top 10
            test_code = self._generate_function_test(func_info)
            test_file = f"test_{Path(func_info['file']).stem}.py"
            tests[test_file] = test_code
        
        # Generate tests for untested modules
        for untested_path in analysis.untested_paths[:5]:  # Top 5
            test_code = self._generate_module_test(untested_path)
            test_file = f"test_{Path(untested_path).stem}.py"
            tests[test_file] = test_code
        
        logger.info(f"[TestGenerator] Generated {len(tests)} test files")
        return tests
    
    @staticmethod
    def _generate_function_test(func_info: Dict) -> str:
        """Generate test template for a function.
        
        Args:
            func_info: Function information dict
            
        Returns:
            pytest test code as string
        """
        func_name = func_info['function']
        file_path = func_info['file']
        
        template = f'''"""
Auto-generated tests for {file_path}
Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""

import pytest
from {Path(file_path).stem} import {func_name}


class Test{func_name.title()}:
    """Test suite for {func_name} function."""
    
    def test_{func_name}_basic(self):
        """Test basic functionality of {func_name}."""
        # TODO: Implement basic test case
        assert True
    
    def test_{func_name}_edge_cases(self):
        """Test edge cases for {func_name}."""
        # TODO: Test boundary conditions, None values, empty inputs
        assert True
    
    def test_{func_name}_error_handling(self):
        """Test error handling in {func_name}."""
        # TODO: Test exception handling
        with pytest.raises(Exception):
            pass  # TODO: Replace with actual error condition
    
    @pytest.mark.parametrize("input,expected", [
        # TODO: Add test cases
    ])
    def test_{func_name}_parametrized(self, input, expected):
        """Parametrized tests for {func_name}."""
        # TODO: Implement parametrized test logic
        assert True
'''
        return template
    
    @staticmethod
    def _generate_module_test(module_path: str) -> str:
        """Generate test template for a module.
        
        Args:
            module_path: Path to module
            
        Returns:
            pytest test code as string
        """
        module_name = Path(module_path).stem
        
        template = f'''"""
Auto-generated tests for {module_path}
Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""

import pytest
from {module_name} import *


class Test{module_name.title()}:
    """Test suite for {module_name} module."""
    
    @pytest.fixture
    def setup(self):
        """Setup test fixtures."""
        # TODO: Initialize test data
        return None
    
    def test_imports(self):
        """Test module imports successfully."""
        import {module_name}
        assert {module_name} is not None
    
    def test_module_functions(self, setup):
        """Test module functions."""
        # TODO: Test key functions from module
        assert True
    
    def test_module_integration(self, setup):
        """Test module integration."""
        # TODO: Test interactions with other modules
        assert True
'''
        return template


# ============================================================================
# PHASE 3: EXECUTION ENGINE
# ============================================================================

@dataclass
class TestExecutionResult:
    """Results from test execution."""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    coverage_percent: float = 0.0
    execution_time_seconds: float = 0.0
    errors: List[str] = None


class ExecutionEngine:
    """Phase 3: Executes tests and collects metrics."""
    
    def __init__(self, root_path: str = "."):
        """Initialize execution engine.
        
        Args:
            root_path: Root directory for test execution
        """
        self.root_path = Path(root_path)
        self.result = TestExecutionResult(errors=[])
    
    def run_tests(self, test_directory: str = "tests") -> TestExecutionResult:
        """Run test suite and collect metrics.
        
        Args:
            test_directory: Directory containing tests
            
        Returns:
            TestExecutionResult with metrics
        """
        logger.info(f"[ExecutionEngine] Running tests from {test_directory}")
        
        start_time = time.time()
        test_dir = self.root_path / test_directory
        
        if not test_dir.exists():
            logger.warning(f"[ExecutionEngine] Test directory not found: {test_dir}")
            return self.result
        
        try:
            # Run pytest with coverage
            cmd = [
                sys.executable, "-m", "pytest",
                str(test_dir),
                "-v",
                "--tb=short",
                "--color=yes",
                "-q"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.root_path,
                timeout=300  # 5 minute timeout
            )
            
            # Parse pytest output
            self._parse_pytest_output(result.stdout, result.stderr)
            
            self.result.execution_time_seconds = time.time() - start_time
            logger.info(f"[ExecutionEngine] Test execution complete: "
                       f"{self.result.passed} passed, {self.result.failed} failed")
            
            return self.result
        
        except subprocess.TimeoutExpired:
            logger.error("[ExecutionEngine] Test execution timed out")
            self.result.errors.append("Test execution timed out (5 minutes)")
            return self.result
        
        except Exception as e:
            logger.error(f"[ExecutionEngine] Error running tests: {e}")
            self.result.errors.append(str(e))
            return self.result
    
    def _parse_pytest_output(self, stdout: str, stderr: str):
        """Parse pytest output for metrics.
        
        Args:
            stdout: pytest stdout
            stderr: pytest stderr
        """
        import re
        
        # Parse summary line: "1 passed, 2 failed in 0.50s"
        match = re.search(r'(\d+)\s+passed|(\d+)\s+failed|(\d+)\s+skipped', stdout + stderr)
        
        if match:
            # Extract test counts (simplified parsing)
            if "passed" in stdout:
                self.result.passed = int(re.search(r'(\d+)\s+passed', stdout).group(1) if re.search(r'(\d+)\s+passed', stdout) else 0)
            if "failed" in stdout:
                self.result.failed = int(re.search(r'(\d+)\s+failed', stdout).group(1) if re.search(r'(\d+)\s+failed', stdout) else 0)
            if "skipped" in stdout:
                self.result.skipped = int(re.search(r'(\d+)\s+skipped', stdout).group(1) if re.search(r'(\d+)\s+skipped', stdout) else 0)
        
        self.result.total_tests = self.result.passed + self.result.failed + self.result.skipped
        
        if self.result.total_tests > 0:
            self.result.coverage_percent = (self.result.passed / self.result.total_tests) * 100


# ============================================================================
# PHASE 4: VISUAL REPORTER
# ============================================================================

class VisualReporter:
    """Phase 4: Generates visual reports and dashboards."""
    
    def __init__(self, root_path: str = "."):
        """Initialize reporter.
        
        Args:
            root_path: Root directory
        """
        self.root_path = Path(root_path)
    
    def generate_report(
        self,
        analysis: CodebaseAnalysis,
        test_gen_results: Dict[str, str],
        execution_result: TestExecutionResult
    ) -> str:
        """Generate comprehensive visual report.
        
        Args:
            analysis: CodebaseAnalysis results
            test_gen_results: Generated test code
            execution_result: Test execution results
            
        Returns:
            Formatted report string
        """
        report = ""
        
        # Header
        report += "\n" + "=" * 80 + "\n"
        report += "🧪 TEST CRITIQUE AGENT - COMPREHENSIVE REPORT\n"
        report += "=" * 80 + "\n\n"
        
        # Section 1: Codebase Metrics
        report += "📊 CODEBASE METRICS\n"
        report += "-" * 80 + "\n"
        report += f"  Python Files:              {analysis.python_files}\n"
        report += f"  Classes:                   {analysis.total_classes}\n"
        report += f"  Functions:                 {analysis.total_functions}\n"
        report += f"  Total Lines of Code:       {analysis.total_lines:,}\n"
        report += f"  Untested Modules:          {len(analysis.untested_paths)}\n"
        report += f"  High Complexity Functions: {len(analysis.high_complexity_functions)}\n\n"
        
        # Section 2: High Complexity Functions
        if analysis.high_complexity_functions:
            report += "⚠️  HIGH COMPLEXITY FUNCTIONS (Complexity > 5)\n"
            report += "-" * 80 + "\n"
            for func in analysis.high_complexity_functions[:10]:
                report += f"  • {func['file']}::{func['function']} (C={func['complexity']}, LOC={func['lines']})\n"
            report += "\n"
        
        # Section 3: Test Generation
        report += "🧬 TEST GENERATION RESULTS\n"
        report += "-" * 80 + "\n"
        report += f"  Test Files Generated:      {len(test_gen_results)}\n"
        report += "  Generated Test Files:\n"
        for test_file in sorted(test_gen_results.keys())[:15]:
            report += f"    ✓ {test_file}\n"
        report += "\n"
        
        # Section 4: Test Execution
        report += "🏃 TEST EXECUTION RESULTS\n"
        report += "-" * 80 + "\n"
        report += f"  Total Tests:       {execution_result.total_tests}\n"
        report += f"  Passed:            {execution_result.passed} ✓\n"
        report += f"  Failed:            {execution_result.failed} ✗\n"
        report += f"  Skipped:           {execution_result.skipped} ⊘\n"
        report += f"  Pass Rate:         {execution_result.coverage_percent:.1f}%\n"
        report += f"  Execution Time:    {execution_result.execution_time_seconds:.2f}s\n"
        
        if execution_result.errors:
            report += "  Errors:\n"
            for error in execution_result.errors[:5]:
                report += f"    ⚠️  {error}\n"
        report += "\n"
        
        # Section 5: Recommendations
        report += "🎯 RECOMMENDATIONS\n"
        report += "-" * 80 + "\n"
        
        if execution_result.coverage_percent < 80:
            report += f"  1. Coverage is below target ({execution_result.coverage_percent:.1f}% < 80%)\n"
            report += "     → Implement missing test cases for high-complexity functions\n"
        
        if len(analysis.untested_paths) > 0:
            report += f"  2. {len(analysis.untested_paths)} modules lack test coverage\n"
            report += "     → Review untested modules list above and add tests\n"
        
        if len(analysis.high_complexity_functions) > 5:
            report += f"  3. {len(analysis.high_complexity_functions)} functions have high complexity\n"
            report += "     → Consider refactoring complex functions or add comprehensive tests\n"
        
        report += "\n"
        
        # Footer
        report += "=" * 80 + "\n"
        report += "Generated: " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n"
        report += "=" * 80 + "\n\n"
        
        return report


class TestCritiqueAgent(BaseAgent):
    """Agent that analyzes code and generates test recommendations."""

    PROMPT_PROFILE = {
        "role": "Test Critique Agent — coverage strategist",
        "mission": "Audit repositories, surface risky gaps, and recommend test scaffolding before release.",
        "objectives": [
            "Quantify current coverage and structural complexity",
            "Highlight untested edge cases per module",
            "Recommend concrete unit/integration/security/performance tests",
            "Return actionable steps developers can execute"
        ],
        "guardrails": [
            "Base findings on analyzer output or generator artifacts",
            "Avoid speculation about files not present in metadata",
            "Keep advice implementation-focused"
        ],
        "response_format": "Provide narrative sections: Coverage Assessment, High-Priority Areas, Recommendations, Next Steps.",
        "tone": "Direct staff engineer"
    }

    def __init__(self, llm_client: LLMClient, verbose: bool = False, retriever=None):
        """Initialize test critique agent.
        
        Args:
            llm_client: LLM client for analysis.
            verbose: Verbose logging.
            retriever: RAG retriever for context.
        """
        super().__init__(
            name="TestCritiqueAgent",
            description="Analyzes code and generates test recommendations",
            llm_client=llm_client,
            verbose=verbose,
            retriever=retriever,
            prompt_profile=self.PROMPT_PROFILE
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
        
        # Classify task sensitivity (Phase 5)
        task_sensitivity = self.classify_task_sensitivity(
            task_type="test_critique",
            has_private_data=True,
            has_sensitive_data=False,
            is_security_task=False
        )
        self._log_step(f"Task classified as: {task_sensitivity}")
        
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
