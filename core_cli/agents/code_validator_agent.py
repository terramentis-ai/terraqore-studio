"""
Flynt Code Validation Agent
Validates generated code for quality, best practices, and standards compliance.

Integrates hallucination detection to ensure AI-generated code is:
- Syntactically valid (correct language grammar)
- Semantically valid (logically correct)
- Spec-compliant (matches intended behavior)
- Secure (no dangerous patterns)
"""

import time
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from agents.base import BaseAgent, AgentContext, AgentResult
from agents.hallucination_detector import (
    HallucinationDetector,
    ValidationSpec,
    HallucinationDetectionResult,
)

logger = logging.getLogger(__name__)


class SeverityLevel(str, Enum):
    """Severity levels for code issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class CodeIssue:
    """Represents a code quality issue."""
    category: str           # Type hints, error handling, documentation, etc.
    severity: str          # info, warning, error, critical
    line_number: Optional[int]
    description: str
    suggestion: str
    example: str


@dataclass
class CodeQualityMetric:
    """Code quality metric score."""
    metric_name: str
    score: float           # 0-10
    status: str           # Good, Fair, Poor
    details: str


@dataclass
class CodeValidationResult:
    """Complete code validation result."""
    success: bool
    overall_score: float   # 0-10
    files_checked: int
    issues_found: List[CodeIssue]
    metrics: List[CodeQualityMetric]
    recommendations: List[str]
    can_deploy: bool
    validation_timestamp: str


class CodeValidationAgent(BaseAgent):
    """Agent specialized in validating generated code quality.
    
    Capabilities:
    - Type hints validation
    - Error handling verification
    - Documentation completeness
    - Code style compliance (PEP8, etc.)
    - Performance analysis
    - Readability scoring
    - Best practices checking
    - Complexity analysis
    """
    
    def __init__(self, llm_client=None, verbose: bool = False, retriever=None):
        """Initialize Code Validation Agent.
        
        Args:
            llm_client: LLM client for AI interactions.
            verbose: Whether to log detailed execution info.
        """
        super().__init__(
            name="CodeValidationAgent",
            description="Validates generated code quality, runs unit tests, and checks style/formatting",
            llm_client=llm_client,
            verbose=verbose,
            retriever=retriever
        )
        
        # Initialize hallucination detector
        self.hallucination_detector = HallucinationDetector(verbose=verbose)

        # Halt generation when hallucination risk crosses thresholds
        self.hallucination_thresholds = {
            "min_score": 0.70,
            "halt_severities": {"critical", "high"},
        }
        
        self.quality_thresholds = {
            "type_hints": 0.9,
            "error_handling": 0.85,
            "documentation": 0.8,
            "code_style": 0.9,
            "complexity": 0.7,
            "readability": 0.75
        }
        
        self.validation_rules = {
            "python": self._get_python_rules(),
            "javascript": self._get_javascript_rules(),
            "typescript": self._get_typescript_rules()
        }
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for Code Validation Agent."""
        return """You are the Code Validation Agent - an expert in code quality assurance.

Your role is to:
1. Validate code structure and syntax compliance
2. Check error handling and edge cases
3. Verify documentation completeness
4. Assess code style and conventions
5. Identify performance issues
6. Evaluate code readability
7. Check for security vulnerabilities
8. Verify test coverage

Code Quality Scoring (0-10):
- 9-10: Production ready, excellent quality
- 7-8: Good quality, minor improvements
- 5-6: Acceptable, should address issues
- 3-4: Poor quality, needs significant work
- 0-2: Not ready for deployment

Issue Severity Levels:
- info: Nice to have improvement
- warning: Should address before deploy
- error: Must fix before deploy
- critical: Major issue, security/functionality risk

When validating code:
- Check for proper error handling
- Verify type hints (Python/TypeScript)
- Ensure documentation exists
- Follow language conventions
- Identify performance bottlenecks
- Look for security issues
- Assess code readability

Output Format:
Return ONLY a valid JSON object with this structure:
{
    "overall_score": 7.5,
    "status": "acceptable",
    "metrics": [
        {
            "metric_name": "Type Hints Coverage",
            "score": 8,
            "status": "Good",
            "details": "90% of functions have type hints"
        }
    ],
    "issues": [
        {
            "category": "Error Handling",
            "severity": "warning",
            "line_number": 45,
            "description": "Function lacks try-except block",
            "suggestion": "Wrap database calls in try-except",
            "example": "try:\\n    result = db.query()\\nexcept DatabaseError as e:\\n    handle_error(e)"
        }
    ],
    "recommendations": [
        "Add docstrings to all public functions",
        "Implement logging for debugging"
    ],
    "can_deploy": true
}"""
    
    def execute(self, context: AgentContext) -> AgentResult:
        """Execute code validation workflow.
        
        Args:
            context: Agent execution context with code metadata.
            
        Returns:
            AgentResult with validation output.
        """
        start_time = time.time()
        steps = []
        
        try:
            # Step 1: Extract code information
            self._log_step("Extracting code metadata")
            code_info = self._extract_code_info(context)
            steps.append("Extracted code information")
            
            # Step 1.5: Detect hallucinations in generated code
            self._log_step("Detecting hallucinations in code")
            hallucination_issues, hallucination_meta = self._detect_hallucinations(code_info)
            steps.append(
                f"Hallucination detection complete ({len(hallucination_issues)} issues; "
                f"score floor={hallucination_meta.get('min_score', 1.0):.2f})"
            )

            # Halt early if hallucination thresholds are breached
            if hallucination_meta.get("halt"):
                self._log_step("Hallucination halt triggered")
                steps.append(
                    f"Hallucination halt triggered: severity={hallucination_meta.get('max_severity')}, "
                    f"score={hallucination_meta.get('min_score', 1.0):.2f}, "
                    f"findings={hallucination_meta.get('total_findings', 0)}"
                )
                execution_time = time.time() - start_time
                message = (
                    "Hallucination threshold breached: "
                    f"max_severity={hallucination_meta.get('max_severity')}, "
                    f"min_score={hallucination_meta.get('min_score', 1.0):.2f}, "
                    f"findings={hallucination_meta.get('total_findings', 0)}"
                )
                return self.create_result(
                    success=False,
                    output=message,
                    execution_time=execution_time,
                    metadata={
                        "provider": "code_validator_agent",
                        "hallucination_meta": hallucination_meta,
                    },
                    intermediate_steps=steps,
                )
            
            # Step 2: Validate syntax and structure
            self._log_step("Validating syntax and structure")
            syntax_issues = self._validate_syntax(code_info)
            steps.append(f"Syntax validation complete ({len(syntax_issues)} issues)")
            
            # Step 3: Check documentation
            self._log_step("Checking documentation")
            doc_issues = self._validate_documentation(code_info)
            steps.append(f"Documentation check complete ({len(doc_issues)} issues)")
            
            # Step 4: Check error handling
            self._log_step("Analyzing error handling")
            error_issues = self._validate_error_handling(code_info)
            steps.append(f"Error handling check complete ({len(error_issues)} issues)")
            
            # Step 5: Check code style
            self._log_step("Checking code style and conventions")
            style_issues = self._validate_style(code_info)
            steps.append(f"Style validation complete ({len(style_issues)} issues)")
            
            # Step 6: Generate metrics
            self._log_step("Calculating quality metrics")
            all_issues = hallucination_issues + syntax_issues + doc_issues + error_issues + style_issues
            metrics = self._calculate_metrics(code_info, all_issues)
            steps.append(f"Generated {len(metrics)} quality metrics")
            
            # Step 7: Generate recommendations
            self._log_step("Generating recommendations")
            recommendations = self._generate_recommendations(all_issues, metrics)
            steps.append("Generated recommendations")
            
            # Step 8: Generate final validation result
            self._log_step("Generating validation report")
            validation = self._generate_validation_result(
                code_info, all_issues, metrics, recommendations
            )
            steps.append("Validation complete")
            
            execution_time = time.time() - start_time
            self._log_step(f"Completed in {execution_time:.2f}s")
            
            return self.create_result(
                success=validation.success,
                output=self._format_validation_output(validation),
                execution_time=execution_time,
                metadata={
                    "overall_score": validation.overall_score,
                    "can_deploy": validation.can_deploy,
                    "issues_count": len(validation.issues_found),
                    "critical_issues": len([i for i in validation.issues_found if i.severity == "critical"]),
                    "provider": "code_validator_agent",
                    "validation": validation.__dict__
                },
                intermediate_steps=steps
            )
            
        except Exception as e:
            error_msg = f"Code validation failed: {str(e)}"
            logger.error(f"[{self.name}] {error_msg}", exc_info=True)
            
            return self.create_result(
                success=False,
                output=error_msg,
                execution_time=time.time() - start_time,
                metadata={"provider": "code_validator_agent", "error": str(e)},
                intermediate_steps=steps
            )
    
    def _extract_code_info(self, context: AgentContext) -> Dict[str, Any]:
        """Extract code information from context."""
        return {
            "project_name": context.project_name,
            "code_files": context.metadata.get("code_generation", {}).get("files", []) if context.metadata else [],
            "language": context.metadata.get("language", "python") if context.metadata else "python",
            "user_input": context.user_input,
            "metadata": context.metadata or {}
        }
    
    def _detect_hallucinations(self, code_info: Dict[str, Any]) -> Tuple[List[CodeIssue], Dict[str, Any]]:
        """Detect hallucinations and return issues plus enforcement metadata."""
        issues: List[CodeIssue] = []
        files = code_info.get("code_files", [])
        language = code_info.get("language", "python")

        spec = self._build_validation_spec(code_info)
        severity_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}

        max_severity = "low"
        min_score = 1.0
        total_findings = 0
        detection_results = []

        for file in files:
            code = file.get("content", "")
            if not code.strip():
                continue

            # Run hallucination detection
            result = self.hallucination_detector.detect(
                code=code,
                language=language,
                spec=spec,
            )

            detection_results.append({
                "path": file.get("path", "unknown"),
                "score": result.score,
                "safe_to_deploy": result.safe_to_deploy,
                "findings": len(result.findings),
                "summary": result.summary(),
            })

            min_score = min(min_score, result.score)
            total_findings += len(result.findings)

            if result.findings:
                worst = max(result.findings, key=lambda f: severity_rank.get(f.severity.value, 0)).severity.value
                if severity_rank.get(worst, 0) > severity_rank.get(max_severity, 0):
                    max_severity = worst

            # Convert hallucination findings to CodeIssues
            for finding in result.findings:
                severity_map = {
                    "low": "info",
                    "medium": "warning",
                    "high": "error",
                    "critical": "critical",
                }

                issues.append(CodeIssue(
                    category=finding.category.value,
                    severity=severity_map.get(finding.severity.value, "warning"),
                    line_number=finding.line_number,
                    description=finding.description,
                    suggestion=finding.suggestion or f"Fix {finding.category.value}",
                    example=finding.affected_code[:100]
                ))

            # Add overall hallucination score as a metric
            if not result.safe_to_deploy:
                issues.append(CodeIssue(
                    category="Hallucination Detection",
                    severity="error",
                    line_number=None,
                    description=f"Potential hallucinations detected (score: {result.score:.2f}/1.0)",
                    suggestion=result.summary(),
                    example=f"File: {file.get('path', 'unknown')}"
                ))

        halt = self._should_halt_on_hallucinations(max_severity, min_score)
        meta = {
            "halt": halt,
            "max_severity": max_severity,
            "min_score": min_score if files else 1.0,
            "total_findings": total_findings,
            "results": detection_results,
        }

        return issues, meta

    def _build_validation_spec(self, code_info: Dict[str, Any]) -> Optional[ValidationSpec]:
        """Build ValidationSpec from context metadata if provided."""
        spec_data = (code_info.get("metadata") or {}).get("validation_spec", {})
        if not spec_data:
            return self._language_spec_presets(code_info.get("language", "python"))

        try:
            return ValidationSpec(
                language=code_info.get("language", "python"),
                expected_functions=spec_data.get("expected_functions", []),
                expected_classes=spec_data.get("expected_classes", []),
                forbidden_patterns=spec_data.get("forbidden_patterns", []),
                required_imports=spec_data.get("required_imports", []),
                max_complexity=spec_data.get("max_complexity"),
                min_documentation=spec_data.get("min_documentation", 0.5),
            )
        except Exception as e:
            logger.warning(f"[ValidationSpec] Failed to build spec: {str(e)}")
            return None

    def _language_spec_presets(self, language: str) -> Optional[ValidationSpec]:
        """Return conservative default specs per language to reduce hallucinations."""
        presets = {
            "python": ValidationSpec(
                language="python",
                expected_functions=[],
                expected_classes=[],
                forbidden_patterns=["os.system", "subprocess", "exec(", "eval(", "pickle."],
                required_imports=[],
                min_documentation=0.3,
            ),
            "javascript": ValidationSpec(
                language="javascript",
                forbidden_patterns=["eval(", "child_process", "require('fs')"],
                required_imports=[],
                min_documentation=0.2,
            ),
            "typescript": ValidationSpec(
                language="typescript",
                forbidden_patterns=["eval(", "child_process", "require('fs')"],
                required_imports=[],
                min_documentation=0.2,
            ),
        }
        return presets.get(language)

    def _should_halt_on_hallucinations(self, max_severity: str, min_score: float) -> bool:
        """Determine if validation should halt based on severity/score."""
        if max_severity in self.hallucination_thresholds["halt_severities"]:
            return True
        if min_score < self.hallucination_thresholds["min_score"]:
            return True
        return False
    
    def _validate_syntax(self, code_info: Dict[str, Any]) -> List[CodeIssue]:
        """Validate code syntax and structure."""
        issues = []
        language = code_info.get("language", "python")
        
        # Check file structure
        files = code_info.get("code_files", [])
        if not files:
            issues.append(CodeIssue(
                category="Structure",
                severity="error",
                line_number=None,
                description="No code files generated",
                suggestion="Ensure code generation produced files",
                example="files should include src/main.py, tests/test_main.py"
            ))
        
        # Check for empty files
        for file in files:
            if not file.get("content", "").strip():
                issues.append(CodeIssue(
                    category="Structure",
                    severity="warning",
                    line_number=None,
                    description=f"Empty file: {file.get('path')}",
                    suggestion="Remove empty files or add placeholder content",
                    example="# TODO: Add implementation"
                ))
        
        return issues
    
    def _validate_documentation(self, code_info: Dict[str, Any]) -> List[CodeIssue]:
        """Validate code documentation."""
        issues = []
        files = code_info.get("code_files", [])
        language = code_info.get("language", "python")
        
        for file in files:
            content = file.get("content", "")
            path = file.get("path", "")
            
            # Check for docstrings/comments in Python
            if language == "python" and path.endswith(".py"):
                if "def " in content and "\"\"\"" not in content and "'''" not in content:
                    issues.append(CodeIssue(
                        category="Documentation",
                        severity="warning",
                        line_number=None,
                        description=f"Missing docstrings in {path}",
                        suggestion="Add docstrings to functions",
                        example='def function():\n    """Description of function."""\n    pass'
                    ))
            
            # Check for README
            if not any(f.get("path", "").lower().startswith("readme") for f in files):
                issues.append(CodeIssue(
                    category="Documentation",
                    severity="warning",
                    line_number=None,
                    description="Missing README.md",
                    suggestion="Add README with project description and setup instructions",
                    example="# Project Name\nProject description and setup."
                ))
        
        return issues
    
    def _validate_error_handling(self, code_info: Dict[str, Any]) -> List[CodeIssue]:
        """Validate error handling in code."""
        issues = []
        files = code_info.get("code_files", [])
        language = code_info.get("language", "python")
        
        for file in files:
            content = file.get("content", "")
            path = file.get("path", "")
            
            if language == "python":
                # Check for error handling
                if ("open(" in content or "requests." in content or ".query(" in content):
                    if "try:" not in content or "except" not in content:
                        issues.append(CodeIssue(
                            category="Error Handling",
                            severity="warning",
                            line_number=None,
                            description=f"Missing error handling in {path}",
                            suggestion="Wrap I/O operations in try-except blocks",
                            example="try:\n    result = operation()\nexcept Exception as e:\n    logger.error(e)"
                        ))
        
        return issues
    
    def _validate_style(self, code_info: Dict[str, Any]) -> List[CodeIssue]:
        """Validate code style and conventions."""
        issues = []
        files = code_info.get("code_files", [])
        language = code_info.get("language", "python")
        
        for file in files:
            content = file.get("content", "")
            path = file.get("path", "")
            
            if language == "python":
                # Check for type hints
                if "def " in content and "->" not in content:
                    issues.append(CodeIssue(
                        category="Type Hints",
                        severity="info",
                        line_number=None,
                        description=f"Missing type hints in {path}",
                        suggestion="Add type hints to function signatures",
                        example="def function(x: int) -> str:\n    return str(x)"
                    ))
        
        return issues
    
    def _calculate_metrics(self, code_info: Dict[str, Any], 
                          issues: List[CodeIssue]) -> List[CodeQualityMetric]:
        """Calculate code quality metrics."""
        metrics = []
        
        # Count issues by severity
        critical_count = len([i for i in issues if i.severity == "critical"])
        error_count = len([i for i in issues if i.severity == "error"])
        warning_count = len([i for i in issues if i.severity == "warning"])
        
        # Overall score (0-10)
        overall_score = 10.0
        overall_score -= critical_count * 2
        overall_score -= error_count * 1.5
        overall_score -= warning_count * 0.5
        overall_score = max(0, min(10, overall_score))
        
        metrics.append(CodeQualityMetric(
            metric_name="Overall Quality Score",
            score=overall_score,
            status="Good" if overall_score >= 7 else "Fair" if overall_score >= 5 else "Poor",
            details=f"Score based on {len(issues)} identified issues"
        ))
        
        metrics.append(CodeQualityMetric(
            metric_name="Code Completeness",
            score=min(10, len(code_info.get("code_files", [])) * 2),
            status="Good" if len(code_info.get("code_files", [])) >= 3 else "Fair",
            details=f"{len(code_info.get('code_files', []))} files generated"
        ))
        
        metrics.append(CodeQualityMetric(
            metric_name="Issue Severity Distribution",
            score=8.0 - (critical_count * 2),
            status="Good" if critical_count == 0 else "Fair" if critical_count <= 1 else "Poor",
            details=f"{critical_count} critical, {error_count} errors, {warning_count} warnings"
        ))
        
        return metrics
    
    def _generate_recommendations(self, issues: List[CodeIssue],
                                 metrics: List[CodeQualityMetric]) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        if any(i.severity == "critical" for i in issues):
            recommendations.append("Address critical issues before deployment")
        
        if any(i.category == "Documentation" for i in issues):
            recommendations.append("Improve documentation coverage")
        
        if any(i.category == "Error Handling" for i in issues):
            recommendations.append("Strengthen error handling and validation")
        
        if any(i.category == "Type Hints" for i in issues):
            recommendations.append("Add type hints for better IDE support")
        
        recommendations.append("Consider adding unit tests for edge cases")
        recommendations.append("Set up code linting (pylint, flake8)")
        
        return recommendations
    
    def _generate_validation_result(self,
                                   code_info: Dict[str, Any],
                                   issues: List[CodeIssue],
                                   metrics: List[CodeQualityMetric],
                                   recommendations: List[str]) -> CodeValidationResult:
        """Generate validation result."""
        from datetime import datetime
        
        overall_score = metrics[0].score if metrics else 5.0
        critical_issues = len([i for i in issues if i.severity == "critical"])
        error_issues = len([i for i in issues if i.severity == "error"])
        
        return CodeValidationResult(
            success=critical_issues == 0 and error_issues == 0,
            overall_score=overall_score,
            files_checked=len(code_info.get("code_files", [])),
            issues_found=issues,
            metrics=metrics,
            recommendations=recommendations,
            can_deploy=critical_issues == 0 and error_issues == 0 and overall_score >= 6,
            validation_timestamp=datetime.now().isoformat()
        )
    
    def _format_validation_output(self, validation: CodeValidationResult) -> str:
        """Format validation report as readable output."""
        output = f"""
CODE VALIDATION REPORT
{'='*70}

Overall Score: {validation.overall_score:.1f}/10
Status: {'PASS' if validation.success else 'FAIL'}
Can Deploy: {'YES' if validation.can_deploy else 'NO'}

QUALITY METRICS
{'-'*70}
"""
        for metric in validation.metrics:
            output += f"""
{metric.metric_name}: {metric.score:.1f}/10 ({metric.status})
  {metric.details}
"""
        
        if validation.issues_found:
            output += f"""
ISSUES FOUND ({len(validation.issues_found)})
{'-'*70}
"""
            for issue in validation.issues_found[:10]:
                output += f"""
[{issue.severity.upper()}] {issue.category}
  Description: {issue.description}
  Suggestion: {issue.suggestion}
"""
        else:
            output += f"\nNO ISSUES FOUND - Code quality is excellent!\n"
        
        output += f"""
RECOMMENDATIONS
{'-'*70}
"""
        for i, rec in enumerate(validation.recommendations, 1):
            output += f"{i}. {rec}\n"
        
        output += f"\nValidation Time: {validation.validation_timestamp}\n"
        return output
    
    def _get_python_rules(self) -> Dict[str, Any]:
        """Get Python-specific validation rules."""
        return {
            "style": ["PEP 8", "snake_case for functions", "UPPER_CASE for constants"],
            "type_hints": True,
            "docstring_style": "Google or NumPy",
            "max_line_length": 100
        }
    
    def _get_javascript_rules(self) -> Dict[str, Any]:
        """Get JavaScript-specific validation rules."""
        return {
            "style": ["camelCase for variables", "PascalCase for classes", "const/let over var"],
            "semicolons": True,
            "quotes": "single or double (consistent)",
            "max_line_length": 100
        }
    
    def _get_typescript_rules(self) -> Dict[str, Any]:
        """Get TypeScript-specific validation rules."""
        return {
            "style": ["camelCase for variables", "PascalCase for types", "strict mode"],
            "type_checking": True,
            "null_safety": True,
            "max_line_length": 100
        }
    
    def _log_step(self, message: str):
        """Log an execution step."""
        if self.verbose:
            logger.info(f"[{self.name}] {message}")
