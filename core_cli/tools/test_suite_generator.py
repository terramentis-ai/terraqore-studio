"""
Test Suite Generator
Generates pytest-compatible test files from codebase analysis.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from tools.codebase_analyzer import CodebaseAnalyzer, CodeElement

logger = logging.getLogger(__name__)


@dataclass
class TestTemplate:
    """Template for test file generation."""
    imports: List[str]
    test_cases: List[str]
    fixtures: List[str] = None
    
    def to_string(self) -> str:
        """Convert template to Python code string."""
        code = '"""Auto-generated tests from codebase analysis."""\n\n'
        code += 'import pytest\n'
        
        for imp in self.imports:
            code += f'from {imp} import *\n'
        
        code += '\n'
        
        # Add fixtures
        if self.fixtures:
            code += '# Fixtures\n'
            for fixture in self.fixtures:
                code += fixture + '\n\n'
        
        # Add tests
        code += '# Test Cases\n'
        for test_case in self.test_cases:
            code += test_case + '\n\n'
        
        return code


class TestSuiteGenerator:
    """Generates test suites from code analysis."""
    
    def __init__(self, project_root: Path):
        """Initialize generator."""
        self.project_root = Path(project_root)
        self.analyzer = CodebaseAnalyzer(project_root)
    
    def generate_tests_for_file(self, target_file: Path) -> str:
        """Generate tests for a specific source file.
        
        Args:
            target_file: Source file to generate tests for.
            
        Returns:
            Test file content as string.
        """
        # Analyze the target file
        analysis = self.analyzer._analyze_file(target_file)
        
        code = self._generate_test_header(target_file)
        
        # Generate test functions for each class
        for class_elem in analysis['classes']:
            code += self._generate_class_tests(class_elem)
        
        # Generate test functions for each public function
        for func_elem in analysis['functions']:
            if func_elem.is_public:
                code += self._generate_function_tests(func_elem)
        
        return code
    
    def _generate_test_header(self, source_file: Path) -> str:
        """Generate test file header with imports.
        
        Args:
            source_file: Source file being tested.
            
        Returns:
            Header string.
        """
        rel_path = source_file.relative_to(self.project_root)
        module_path = str(rel_path).replace('/', '.').replace('.py', '')
        
        header = f'''"""
Test Suite for {source_file.name}

Auto-generated test scaffold. Add your test logic here.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from {module_path} import *


'''
        return header
    
    def _generate_class_tests(self, class_elem: CodeElement) -> str:
        """Generate tests for a class.
        
        Args:
            class_elem: Class element to generate tests for.
            
        Returns:
            Test class code string.
        """
        class_name = class_elem.name
        test_class_name = f"Test{class_name}"
        
        code = f'''class {test_class_name}:
    """Test suite for {class_name}."""
    
    @pytest.fixture
    def setup(self):
        """Setup test instance."""
        # TODO: Initialize {class_name} with appropriate parameters
        instance = {class_name}()
        yield instance
    
    def test_initialization(self, setup):
        """Test {class_name} initialization."""
        assert setup is not None
    
    def test_{class_name.lower()}_attributes(self, setup):
        """Test {class_name} has expected attributes."""
        # TODO: Add attribute assertions
        pass


'''
        return code
    
    def _generate_function_tests(self, func_elem: CodeElement) -> str:
        """Generate tests for a function.
        
        Args:
            func_elem: Function element to generate tests for.
            
        Returns:
            Test function code string.
        """
        func_name = func_elem.name
        test_name = f"test_{func_name}"
        
        code = f'''def {test_name}():
    """Test {func_name} function."""
    # TODO: Setup test data
    
    # Call function
    result = {func_name}()
    
    # TODO: Add assertions
    assert result is not None


'''
        return code
    
    def generate_full_test_suite(self) -> Dict[str, str]:
        """Generate complete test suite for entire project.
        
        Returns:
            Dict mapping test file paths to test content.
        """
        self.analyzer.analyze()
        
        test_files = {}
        
        # Generate tests for each source file
        for class_path in self.analyzer.analysis.classes.keys():
            source_path = self.project_root / class_path
            if source_path.exists():
                test_content = self.generate_tests_for_file(source_path)
                
                # Create test file path
                test_path = source_path.parent / f"test_{source_path.stem}.py"
                test_files[str(test_path)] = test_content
        
        return test_files
    
    def generate_critical_tests(self) -> Dict[str, str]:
        """Generate tests for high-complexity functions only.
        
        Returns:
            Dict mapping test file paths to test content.
        """
        self.analyzer.analyze()
        
        test_files = {}
        
        # Find high-complexity items
        for filepath, functions in self.analyzer.analysis.functions.items():
            high_complexity = [f for f in functions if f.complexity > 5 and f.is_public]
            
            if high_complexity:
                source_path = self.project_root / filepath
                code = self._generate_test_header(source_path)
                
                for func in high_complexity:
                    code += f'''
@pytest.mark.priority("high")
def test_{func.name}_edge_cases():
    """Test edge cases for {func.name} (complexity: {func.complexity})."""
    # TODO: Add edge case tests for high-complexity function
    pass


@pytest.mark.priority("high")
def test_{func.name}_performance():
    """Test performance of {func.name}."""
    import time
    
    # TODO: Add performance test
    # Expected: < 1000ms
    pass

'''
                
                test_path = source_path.parent / f"test_{source_path.stem}_critical.py"
                test_files[str(test_path)] = code
        
        return test_files
    
    def estimate_test_coverage(self, existing_tests: Optional[List[Path]] = None) -> Dict:
        """Estimate current and needed test coverage.
        
        Args:
            existing_tests: List of existing test files.
            
        Returns:
            Coverage estimate dictionary.
        """
        self.analyzer.analyze()
        
        # Find test files if not provided
        if existing_tests is None:
            existing_tests = list(self.project_root.rglob("test_*.py")) + \
                            list(self.project_root.rglob("*_test.py"))
        
        untested = self.analyzer.get_untested_coverage_areas(existing_tests)
        
        return {
            "total_functions": self.analyzer.analysis.total_functions,
            "total_complexity": sum(f.complexity for functions in self.analyzer.analysis.functions.values() 
                                   for f in functions),
            "untested_areas": untested,
            "coverage_estimate": f"{len(existing_tests)} test files found",
            "priority_areas": list(untested.keys())[:5]  # Top 5 untested areas
        }


def get_test_generator(project_root: Path) -> TestSuiteGenerator:
    """Get test suite generator instance.
    
    Args:
        project_root: Root directory of project.
        
    Returns:
        TestSuiteGenerator instance.
    """
    return TestSuiteGenerator(project_root)
