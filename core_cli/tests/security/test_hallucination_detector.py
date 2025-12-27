"""
Unit tests for HallucinationDetector

Tests cover:
- Syntax error detection
- Undefined reference detection  
- Type mismatch detection
- Security issue detection
- Spec compliance validation
- Performance validation
"""

import pytest
from agents.hallucination_detector import (
    HallucinationDetector,
    ValidationSpec,
    HallucinationCategory,
    HallucinationSeverity,
    detect_hallucinations,
)


class TestHallucinationDetectorSyntax:
    """Tests for syntax validation."""
    
    def setup_method(self):
        """Setup for each test."""
        self.detector = HallucinationDetector()
    
    def test_detect_python_syntax_error(self):
        """Test detection of Python syntax errors."""
        invalid_code = '''
def foo(
    print("missing closing paren")
'''
        result = self.detector.detect(invalid_code, "python")
        assert result.has_hallucinations
        assert not result.safe_to_deploy
        assert any(f.severity == HallucinationSeverity.CRITICAL for f in result.findings)
    
    def test_valid_python_syntax(self):
        """Test that valid Python code passes."""
        valid_code = '''
def hello(name):
    print(f"Hello {name}")
    return True

result = hello("World")
'''
        result = self.detector.detect(valid_code, "python")
        syntax_errors = [f for f in result.findings 
                        if f.category == HallucinationCategory.SYNTAX_ERROR]
        assert len(syntax_errors) == 0
    
    def test_detect_javascript_bracket_mismatch(self):
        """Test detection of JavaScript bracket mismatches."""
        invalid_code = '''
function test() {
    console.log("hello"
}
'''
        result = self.detector.detect(invalid_code, "javascript")
        assert result.has_hallucinations
        assert any(f.severity == HallucinationSeverity.CRITICAL for f in result.findings)


class TestHallucinationDetectorUndefinedReferences:
    """Tests for undefined reference detection."""
    
    def setup_method(self):
        """Setup for each test."""
        self.detector = HallucinationDetector()
    
    def test_detect_undefined_variable(self):
        """Test detection of undefined variables."""
        code = '''
def process_data():
    result = my_undefined_function()
    return result
'''
        result = self.detector.detect(code, "python")
        undefined = [f for f in result.findings 
                    if f.category == HallucinationCategory.UNDEFINED_REFERENCE]
        assert len(undefined) > 0
    
    def test_defined_names_not_flagged(self):
        """Test that defined names are not flagged."""
        code = '''
def helper():
    return 42

def process_data():
    result = helper()
    return result
'''
        result = self.detector.detect(code, "python")
        undefined = [f for f in result.findings 
                    if f.category == HallucinationCategory.UNDEFINED_REFERENCE]
        assert len(undefined) == 0
    
    def test_builtin_functions_not_flagged(self):
        """Test that builtin functions are not flagged."""
        code = '''
data = [1, 2, 3]
total = sum(data)
length = len(data)
max_val = max(data)
'''
        result = self.detector.detect(code, "python")
        undefined = [f for f in result.findings 
                    if f.category == HallucinationCategory.UNDEFINED_REFERENCE]
        assert len(undefined) == 0


class TestHallucinationDetectorSecurityPatterns:
    """Tests for security issue detection."""
    
    def setup_method(self):
        """Setup for each test."""
        self.detector = HallucinationDetector()
    
    def test_detect_eval_usage(self):
        """Test detection of eval() usage."""
        code = '''
user_input = "1 + 1"
result = eval(user_input)
'''
        result = self.detector.detect(code, "python")
        security = [f for f in result.findings 
                   if f.category == HallucinationCategory.SECURITY_ISSUE]
        assert len(security) > 0
    
    def test_detect_exec_usage(self):
        """Test detection of exec() usage."""
        code = '''
code_str = "print('hello')"
exec(code_str)
'''
        result = self.detector.detect(code, "python")
        security = [f for f in result.findings 
                   if f.category == HallucinationCategory.SECURITY_ISSUE]
        assert len(security) > 0
    
    def test_detect_subprocess_usage(self):
        """Test detection of subprocess module."""
        code = '''
import subprocess
subprocess.run("ls -la", shell=True)
'''
        result = self.detector.detect(code, "python")
        security = [f for f in result.findings 
                   if f.category == HallucinationCategory.SECURITY_ISSUE]
        assert len(security) > 0
    
    def test_safe_code_no_security_issues(self):
        """Test that safe code doesn't trigger security warnings."""
        code = '''
def calculate_sum(a, b):
    return a + b

result = calculate_sum(1, 2)
print(result)
'''
        result = self.detector.detect(code, "python")
        security = [f for f in result.findings 
                   if f.category == HallucinationCategory.SECURITY_ISSUE]
        assert len(security) == 0


class TestHallucinationDetectorSpecValidation:
    """Tests for specification validation."""
    
    def setup_method(self):
        """Setup for each test."""
        self.detector = HallucinationDetector()
    
    def test_detect_missing_required_function(self):
        """Test detection of missing required functions."""
        spec = ValidationSpec(
            language="python",
            expected_functions=["process", "validate"],
        )
        code = '''
def process(data):
    return data

# validate() is missing
'''
        result = self.detector.detect(code, "python", spec)
        spec_violations = [f for f in result.findings 
                          if f.category == HallucinationCategory.SPEC_VIOLATION]
        assert len(spec_violations) > 0
    
    def test_detect_missing_required_import(self):
        """Test detection of missing required imports."""
        spec = ValidationSpec(
            language="python",
            required_imports=["json", "datetime"],
        )
        code = '''
import json

# missing: import datetime
'''
        result = self.detector.detect(code, "python", spec)
        spec_violations = [f for f in result.findings 
                          if f.category == HallucinationCategory.SPEC_VIOLATION]
        assert len(spec_violations) > 0
    
    def test_detect_forbidden_pattern(self):
        """Test detection of forbidden patterns."""
        spec = ValidationSpec(
            language="python",
            forbidden_patterns=["os.system", "rm -rf"],
        )
        code = '''
import os
os.system("rm -rf /")
'''
        result = self.detector.detect(code, "python", spec)
        spec_violations = [f for f in result.findings 
                          if f.category == HallucinationCategory.SPEC_VIOLATION]
        assert len(spec_violations) > 0


class TestHallucinationDetectorConsistency:
    """Tests for code consistency validation."""
    
    def setup_method(self):
        """Setup for each test."""
        self.detector = HallucinationDetector()
    
    def test_detect_unreachable_code(self):
        """Test detection of unreachable code."""
        code = '''
def process():
    return True
    print("This is unreachable")
'''
        result = self.detector.detect(code, "python")
        logic_errors = [f for f in result.findings 
                       if f.category == HallucinationCategory.LOGIC_ERROR]
        assert len(logic_errors) > 0


class TestHallucinationDetectorScore:
    """Tests for hallucination score calculation."""
    
    def setup_method(self):
        """Setup for each test."""
        self.detector = HallucinationDetector()
    
    def test_score_perfect_code(self):
        """Test that valid code gets high score."""
        code = '''
def add(a, b):
    return a + b

def main():
    result = add(1, 2)
    print(result)

if __name__ == "__main__":
    main()
'''
        result = self.detector.detect(code, "python")
        assert result.score > 0.8
    
    def test_score_code_with_critical_issues(self):
        """Test that code with critical issues gets low score."""
        code = '''
def broken(
    print("no closing paren")
x = undefined_var
'''
        result = self.detector.detect(code, "python")
        assert result.score < 0.5


class TestDetectHallucinationsUtility:
    """Tests for the convenience detect_hallucinations function."""
    
    def test_convenience_function(self):
        """Test the detect_hallucinations utility function."""
        code = '''
def hello():
    print("Hello")
'''
        result = detect_hallucinations(code, language="python")
        assert isinstance(result, dict) or hasattr(result, 'safe_to_deploy')
    
    def test_with_spec(self):
        """Test convenience function with spec."""
        spec = ValidationSpec(
            language="python",
            expected_functions=["hello"],
        )
        code = '''
def hello():
    print("Hello")
'''
        result = detect_hallucinations(code, language="python", spec=spec)
        assert result.safe_to_deploy


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def setup_method(self):
        """Setup for each test."""
        self.detector = HallucinationDetector()
    
    def test_empty_code(self):
        """Test handling of empty code."""
        result = self.detector.detect("", "python")
        # Should not crash
        assert isinstance(result.findings, list)
    
    def test_only_comments(self):
        """Test code with only comments."""
        code = '''
# This is a comment
# Another comment
'''
        result = self.detector.detect(code, "python")
        # Should be valid
        assert len([f for f in result.findings 
                   if f.severity == HallucinationSeverity.CRITICAL]) == 0
    
    def test_multiline_strings(self):
        """Test handling of multiline strings."""
        code = '''
def process():
    text = """
    This is a
    multiline string
    """
    return text
'''
        result = self.detector.detect(code, "python")
        # Should not flag undefined references in strings
        assert len([f for f in result.findings 
                   if f.category == HallucinationCategory.UNDEFINED_REFERENCE]) == 0


if __name__ == "__main__":
    print("Hallucination Detector Tests")
    print("Run with: pytest test_hallucination_detector.py -v")
