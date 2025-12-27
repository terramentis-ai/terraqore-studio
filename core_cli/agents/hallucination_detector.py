"""
Hallucination Detector for AI-Generated Code

Detects and prevents hallucinations in code generation through:
1. AST validation - ensuring code syntax matches Python/JS grammar
2. Spec matching - validating output matches intended specification  
3. Security scanning - detecting suspicious patterns
4. Consistency checking - verifying logical flow and structure

Author: ML Specialist + Backend Engineer
Timeline: 2-3 days
Status: Foundation interface
"""

import ast
import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class HallucinationSeverity(str, Enum):
    """Severity levels for detected hallucinations."""
    LOW = "low"           # Minor inconsistency
    MEDIUM = "medium"     # Significant issue
    HIGH = "high"         # Major hallucination
    CRITICAL = "critical" # Invalid/dangerous code


class HallucinationCategory(str, Enum):
    """Categories of hallucinations."""
    SYNTAX_ERROR = "syntax_error"           # Invalid syntax
    UNDEFINED_REFERENCE = "undefined_reference"  # Uses undefined var/function
    TYPE_MISMATCH = "type_mismatch"         # Type incompatibility
    LOGIC_ERROR = "logic_error"             # Illogical code flow
    SPEC_VIOLATION = "spec_violation"       # Violates spec
    SECURITY_ISSUE = "security_issue"       # Dangerous patterns
    PERFORMANCE_ISSUE = "performance_issue" # Inefficient code
    HALLUCINATED_API = "hallucinated_api"   # Non-existent API call


@dataclass
class HallucinationFinding:
    """A detected hallucination in generated code."""
    category: HallucinationCategory
    severity: HallucinationSeverity
    line_number: Optional[int]
    column_number: Optional[int]
    description: str
    affected_code: str
    suggestion: Optional[str] = None
    confidence: float = 0.8  # 0-1 confidence score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "description": self.description,
            "affected_code": self.affected_code,
            "suggestion": self.suggestion,
            "confidence": self.confidence,
        }


@dataclass
class ValidationSpec:
    """Specification for code validation."""
    language: str                    # "python", "javascript", "typescript"
    expected_functions: List[str] = field(default_factory=list)  # Functions that must exist
    expected_classes: List[str] = field(default_factory=list)    # Classes that must exist
    forbidden_patterns: List[str] = field(default_factory=list)  # Patterns not allowed
    required_imports: List[str] = field(default_factory=list)    # Required modules
    max_complexity: Optional[int] = None  # Cyclomatic complexity limit
    min_documentation: float = 0.5        # Min documentation coverage (0-1)
    
    def __post_init__(self):
        """Validate spec after initialization."""
        if self.language not in ["python", "javascript", "typescript"]:
            raise ValueError(f"Unsupported language: {self.language}")
        if not (0 <= self.min_documentation <= 1):
            raise ValueError("min_documentation must be 0-1")


@dataclass
class HallucinationDetectionResult:
    """Complete hallucination detection result."""
    code: str
    language: str
    has_hallucinations: bool
    findings: List[HallucinationFinding]
    score: float = 1.0  # 0-1, higher is better (no hallucinations)
    safe_to_deploy: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    
    def summary(self) -> str:
        """Generate a summary of findings."""
        if not self.findings:
            return "✓ No hallucinations detected. Code appears valid."
        
        critical = sum(1 for f in self.findings if f.severity == HallucinationSeverity.CRITICAL)
        high = sum(1 for f in self.findings if f.severity == HallucinationSeverity.HIGH)
        medium = sum(1 for f in self.findings if f.severity == HallucinationSeverity.MEDIUM)
        low = sum(1 for f in self.findings if f.severity == HallucinationSeverity.LOW)
        
        return (
            f"Found {len(self.findings)} hallucinations: "
            f"{critical} critical, {high} high, {medium} medium, {low} low"
        )


class HallucinationDetector:
    """
    Detects hallucinations in AI-generated code.
    
    Validates code through multiple mechanisms:
    1. AST parsing - syntactic correctness
    2. Spec matching - semantic correctness
    3. Pattern detection - suspicious code
    4. Consistency checking - internal logic
    """
    
    def __init__(self, verbose: bool = False):
        """Initialize hallucination detector.
        
        Args:
            verbose: Enable detailed logging
        """
        self.verbose = verbose
        self.python_builtin_functions = {
            "print", "len", "range", "str", "int", "float", "bool",
            "list", "dict", "set", "tuple", "open", "input", "type",
            "isinstance", "issubclass", "super", "property", "staticmethod",
            "classmethod", "zip", "map", "filter", "enumerate", "sum",
            "min", "max", "sorted", "reversed", "all", "any", "abs",
            "round", "pow", "divmod", "hex", "oct", "bin", "ord", "chr",
            "ascii", "repr", "format", "getattr", "setattr", "delattr",
            "hasattr", "callable", "iter", "next", "Exception", "ValueError",
            "TypeError", "RuntimeError", "KeyError", "IndexError", "__name__", "__main__",
        }
        
        self.javascript_global_objects = {
            "console", "JSON", "Math", "Array", "Object", "String",
            "Number", "Boolean", "Date", "RegExp", "Error", "Promise",
            "Map", "Set", "WeakMap", "WeakSet", "Symbol", "Proxy",
            "Reflect", "setTimeout", "setInterval", "clearTimeout",
            "clearInterval", "parseInt", "parseFloat", "isNaN", "isFinite",
            "eval", "encodeURI", "decodeURI", "encodeURIComponent",
            "decodeURIComponent", "require", "module", "exports",
        }
    
    def detect(
        self,
        code: str,
        language: str,
        spec: Optional[ValidationSpec] = None,
    ) -> HallucinationDetectionResult:
        """
        Detect hallucinations in generated code.
        
        Args:
            code: Generated code to validate
            language: Programming language ("python", "javascript", "typescript")
            spec: Optional ValidationSpec for semantic validation
            
        Returns:
            HallucinationDetectionResult with findings
        """
        findings = []
        
        # 1. Syntactic validation
        if language == "python":
            findings.extend(self._validate_python_syntax(code))
        elif language in ["javascript", "typescript"]:
            findings.extend(self._validate_javascript_syntax(code))
        
        # 2. AST analysis
        if language == "python":
            findings.extend(self._analyze_python_ast(code))
        
        # 3. Spec validation
        if spec:
            findings.extend(self._validate_against_spec(code, language, spec))
        
        # 4. Pattern detection
        findings.extend(self._detect_suspicious_patterns(code, language))
        
        # 5. Consistency checks
        findings.extend(self._check_consistency(code, language))
        
        # Calculate score with stronger penalties for critical/high
        has_critical = any(f.severity == HallucinationSeverity.CRITICAL for f in findings)
        has_high = any(f.severity == HallucinationSeverity.HIGH for f in findings)

        severity_weights = {
            HallucinationSeverity.CRITICAL: 0.6,
            HallucinationSeverity.HIGH: 0.3,
            HallucinationSeverity.MEDIUM: 0.15,
            HallucinationSeverity.LOW: 0.05,
        }

        score = 1.0
        for f in findings:
            score -= severity_weights.get(f.severity, 0.1)
        score = max(0.0, score)

        safe_to_deploy = not (has_critical or has_high)
        
        result = HallucinationDetectionResult(
            code=code,
            language=language,
            has_hallucinations=len(findings) > 0,
            findings=findings,
            score=score,
            safe_to_deploy=safe_to_deploy,
        )
        
        if self.verbose:
            logger.info(f"Hallucination detection complete: {result.summary()}")
        
        return result
    
    def _validate_python_syntax(self, code: str) -> List[HallucinationFinding]:
        """Validate Python syntax via AST parsing."""
        findings = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            findings.append(HallucinationFinding(
                category=HallucinationCategory.SYNTAX_ERROR,
                severity=HallucinationSeverity.CRITICAL,
                line_number=e.lineno,
                column_number=e.offset,
                description=f"Syntax error: {e.msg}",
                affected_code=e.text or "",
                suggestion="Fix the syntax error to make code valid Python",
                confidence=1.0,
            ))
        except Exception as e:
            findings.append(HallucinationFinding(
                category=HallucinationCategory.SYNTAX_ERROR,
                severity=HallucinationSeverity.HIGH,
                line_number=None,
                column_number=None,
                description=f"Failed to parse code: {str(e)}",
                affected_code=code[:100],
                confidence=0.9,
            ))
        
        return findings
    
    def _validate_javascript_syntax(self, code: str) -> List[HallucinationFinding]:
        """Validate JavaScript/TypeScript syntax using regex patterns."""
        findings = []
        
        # Check for common syntax errors
        unclosed_braces = code.count("{") - code.count("}")
        unclosed_parens = code.count("(") - code.count(")")
        unclosed_brackets = code.count("[") - code.count("]")
        
        if unclosed_braces != 0:
            findings.append(HallucinationFinding(
                category=HallucinationCategory.SYNTAX_ERROR,
                severity=HallucinationSeverity.CRITICAL,
                line_number=None,
                column_number=None,
                description=f"Unclosed braces: {unclosed_braces} unmatched",
                affected_code="",
                confidence=1.0,
            ))
        
        if unclosed_parens != 0:
            findings.append(HallucinationFinding(
                category=HallucinationCategory.SYNTAX_ERROR,
                severity=HallucinationSeverity.CRITICAL,
                line_number=None,
                column_number=None,
                description=f"Unclosed parentheses: {unclosed_parens} unmatched",
                affected_code="",
                confidence=1.0,
            ))
        
        if unclosed_brackets != 0:
            findings.append(HallucinationFinding(
                category=HallucinationCategory.SYNTAX_ERROR,
                severity=HallucinationSeverity.CRITICAL,
                line_number=None,
                column_number=None,
                description=f"Unclosed brackets: {unclosed_brackets} unmatched",
                affected_code="",
                confidence=1.0,
            ))
        
        return findings
    
    def _analyze_python_ast(self, code: str) -> List[HallucinationFinding]:
        """Analyze Python AST for hallucinations."""
        findings = []
        try:
            tree = ast.parse(code)
            
            # Collect defined names
            defined_names = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    defined_names.add(node.name)
                    if isinstance(node, ast.FunctionDef):
                        for arg in node.args.args:
                            defined_names.add(arg.arg)
                        if node.args.vararg:
                            defined_names.add(node.args.vararg.arg)
                        if node.args.kwarg:
                            defined_names.add(node.args.kwarg.arg)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            defined_names.add(target.id)
            
            # Check for undefined references
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    if node.id not in defined_names and node.id not in self.python_builtin_functions:
                        findings.append(HallucinationFinding(
                            category=HallucinationCategory.UNDEFINED_REFERENCE,
                            severity=HallucinationSeverity.HIGH,
                            line_number=node.lineno,
                            column_number=None,
                            description=f"Undefined name: '{node.id}'",
                            affected_code=node.id,
                            suggestion=f"Define '{node.id}' before using it",
                            confidence=0.8,
                        ))
        except Exception as e:
            if self.verbose:
                logger.error(f"AST analysis failed: {str(e)}")
        
        return findings
    
    def _validate_against_spec(
        self,
        code: str,
        language: str,
        spec: ValidationSpec
    ) -> List[HallucinationFinding]:
        """Validate code against specification."""
        findings = []
        
        # Check for required functions
        for func_name in spec.expected_functions:
            if f"def {func_name}" not in code and f"function {func_name}" not in code:
                findings.append(HallucinationFinding(
                    category=HallucinationCategory.SPEC_VIOLATION,
                    severity=HallucinationSeverity.HIGH,
                    line_number=None,
                    column_number=None,
                    description=f"Expected function '{func_name}' not found",
                    affected_code="",
                    suggestion=f"Add function '{func_name}' as specified",
                    confidence=0.9,
                ))
        
        # Check for required classes
        for class_name in spec.expected_classes:
            if f"class {class_name}" not in code:
                findings.append(HallucinationFinding(
                    category=HallucinationCategory.SPEC_VIOLATION,
                    severity=HallucinationSeverity.HIGH,
                    line_number=None,
                    column_number=None,
                    description=f"Expected class '{class_name}' not found",
                    affected_code="",
                    suggestion=f"Add class '{class_name}' as specified",
                    confidence=0.9,
                ))
        
        # Check for forbidden patterns
        for pattern in spec.forbidden_patterns:
            if pattern in code:
                findings.append(HallucinationFinding(
                    category=HallucinationCategory.SPEC_VIOLATION,
                    severity=HallucinationSeverity.MEDIUM,
                    line_number=None,
                    column_number=None,
                    description=f"Forbidden pattern found: '{pattern}'",
                    affected_code=pattern,
                    suggestion=f"Remove forbidden pattern '{pattern}'",
                    confidence=1.0,
                ))
        
        # Check for required imports using AST (Python only) to ignore comments/text
        python_imports = set()
        if language == "python":
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            python_imports.add((alias.name or "").split(".")[0])
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        python_imports.add((node.module or "").split(".")[0])
            except Exception:
                # Fallback to substring search if AST parse fails
                python_imports = set()

        for import_name in spec.required_imports:
            if language == "python":
                present = import_name in python_imports
            else:
                present = (f"import {import_name}" in code) or (f"from {import_name}" in code)

            if not present:
                findings.append(HallucinationFinding(
                    category=HallucinationCategory.SPEC_VIOLATION,
                    severity=HallucinationSeverity.MEDIUM,
                    line_number=None,
                    column_number=None,
                    description=f"Required import missing: '{import_name}'",
                    affected_code="",
                    suggestion=f"Add 'import {import_name}' or 'from {import_name} import ...'",
                    confidence=0.9,
                ))
        
        return findings
    
    def _detect_suspicious_patterns(self, code: str, language: str) -> List[HallucinationFinding]:
        """Detect suspicious/dangerous patterns."""
        findings = []
        
        # Check for dangerous patterns
        dangerous_patterns = [
            (r"exec\s*\(", "exec() call", HallucinationSeverity.CRITICAL),
            (r"eval\s*\(", "eval() call", HallucinationSeverity.CRITICAL),
            (r"__import__\s*\(", "__import__() call", HallucinationSeverity.HIGH),
            (r"os\.system\s*\(", "os.system() call", HallucinationSeverity.HIGH),
            (r"subprocess\s*\.", "subprocess module", HallucinationSeverity.MEDIUM),
            (r"pickle\s*\.", "pickle module", HallucinationSeverity.HIGH),
        ]
        
        for pattern, description, severity in dangerous_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                findings.append(HallucinationFinding(
                    category=HallucinationCategory.SECURITY_ISSUE,
                    severity=severity,
                    line_number=None,
                    column_number=None,
                    description=f"Potentially dangerous operation: {description}",
                    affected_code=match.group(),
                    suggestion=f"Review and justify use of {description}",
                    confidence=0.9,
                ))
        
        return findings
    
    def _check_consistency(self, code: str, language: str) -> List[HallucinationFinding]:
        """Check code consistency and logic."""
        findings = []
        
        # Check for unreachable code (very basic check)
        lines = code.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("return") or stripped.startswith("raise"):
                base_indent = len(line) - len(line.lstrip(" \t"))
                for next_line in lines[i+1:]:
                    next_indent = len(next_line) - len(next_line.lstrip(" \t"))
                    next_stripped = next_line.strip()
                    if not next_stripped:
                        continue
                    if next_indent < base_indent:
                        break
                    if not next_stripped.startswith(("except", "finally", "def", "class")):
                        findings.append(HallucinationFinding(
                            category=HallucinationCategory.LOGIC_ERROR,
                            severity=HallucinationSeverity.MEDIUM,
                            line_number=i+1,
                            column_number=None,
                            description="Potentially unreachable code",
                            affected_code=next_stripped[:50],
                            suggestion="Remove code after return/raise or restructure",
                            confidence=0.7,
                        ))
                        break
        
        return findings


# Utility function for easy integration
def detect_hallucinations(
    code: str,
    language: str = "python",
    spec: Optional[ValidationSpec] = None,
    verbose: bool = False,
) -> HallucinationDetectionResult:
    """Convenience function to detect hallucinations.
    
    Args:
        code: Generated code to validate
        language: Programming language
        spec: Optional validation spec
        verbose: Enable verbose logging
        
    Returns:
        HallucinationDetectionResult
    """
    detector = HallucinationDetector(verbose=verbose)
    return detector.detect(code, language, spec)


if __name__ == "__main__":
    # Example usage
    sample_code = """
def hello(name):
    print(f"Hello {name}")
    return "done"
    print("This won't execute")

hello("World")
"""
    
    result = detect_hallucinations(sample_code, language="python", verbose=True)
    print(f"\nHallucination Detection Result:")
    print(f"Safe to deploy: {result.safe_to_deploy}")
    print(f"Score: {result.score:.2f}")
    print(f"Summary: {result.summary()}")
    
    for finding in result.findings:
        print(f"\n{finding.category.value} ({finding.severity.value}):")
        print(f"  {finding.description}")
        if finding.suggestion:
            print(f"  Suggestion: {finding.suggestion}")
