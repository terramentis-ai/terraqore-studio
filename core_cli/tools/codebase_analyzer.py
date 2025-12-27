"""
Codebase Analyzer
Analyzes Python codebases using AST to identify classes, functions, imports, etc.
"""

import logging
import ast
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CodeElement:
    """Represents a code element (class, function, etc)."""
    name: str
    element_type: str  # class, function, async_function
    line_number: int
    end_line_number: int
    decorators: List[str] = field(default_factory=list)
    is_public: bool = True
    docstring: Optional[str] = None
    complexity: int = 0  # Cyclomatic complexity estimate


@dataclass
class CodebaseAnalysis:
    """Results of codebase analysis."""
    python_files: int
    total_classes: int
    total_functions: int
    total_imports: int
    classes: Dict[str, List[CodeElement]] = field(default_factory=dict)
    functions: Dict[str, List[CodeElement]] = field(default_factory=dict)
    imports: Dict[str, List[str]] = field(default_factory=dict)  # filename -> [imports]
    file_coverage: Dict[str, int] = field(default_factory=dict)  # filename -> line count


class CodebaseAnalyzer:
    """Analyzes Python project structure using AST."""
    
    def __init__(self, project_root: Path):
        """Initialize analyzer with project root."""
        self.project_root = Path(project_root)
        self.analysis = None
    
    def analyze(self, exclude_dirs: Optional[List[str]] = None) -> CodebaseAnalysis:
        """Analyze the entire codebase.
        
        Args:
            exclude_dirs: Directories to exclude (e.g., __pycache__, venv, .git).
            
        Returns:
            CodebaseAnalysis with results.
        """
        if exclude_dirs is None:
            exclude_dirs = ["__pycache__", ".venv", "venv", ".git", ".pytest_cache", "node_modules"]
        
        analysis = CodebaseAnalysis(
            python_files=0,
            total_classes=0,
            total_functions=0,
            total_imports=0
        )
        
        # Find all Python files
        python_files = list(self.project_root.rglob("*.py"))
        analysis.python_files = len(python_files)
        
        for py_file in python_files:
            # Skip excluded directories
            if any(part in exclude_dirs for part in py_file.relative_to(self.project_root).parts):
                continue
            
            try:
                file_analysis = self._analyze_file(py_file)
                
                # Aggregate results
                analysis.total_classes += len(file_analysis['classes'])
                analysis.total_functions += len(file_analysis['functions'])
                analysis.total_imports += len(file_analysis['imports'])
                analysis.file_coverage[str(py_file)] = file_analysis['lines']
                
                # Store per-file data
                rel_path = str(py_file.relative_to(self.project_root))
                analysis.classes[rel_path] = file_analysis['classes']
                analysis.functions[rel_path] = file_analysis['functions']
                analysis.imports[rel_path] = file_analysis['imports']
                
            except SyntaxError as e:
                logger.warning(f"Syntax error in {py_file}: {e}")
            except Exception as e:
                logger.warning(f"Error analyzing {py_file}: {e}")
        
        self.analysis = analysis
        return analysis
    
    def _analyze_file(self, file_path: Path) -> Dict:
        """Analyze a single Python file.
        
        Args:
            file_path: Path to Python file.
            
        Returns:
            Dict with classes, functions, imports, and line count.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        classes = []
        functions = []
        imports = []
        lines = len(content.split('\n'))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                element = CodeElement(
                    name=node.name,
                    element_type="class",
                    line_number=node.lineno,
                    end_line_number=getattr(node, 'end_lineno', node.lineno),
                    decorators=[d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list],
                    is_public=not node.name.startswith('_'),
                    docstring=ast.get_docstring(node),
                    complexity=self._estimate_complexity(node)
                )
                classes.append(element)
            
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                element = CodeElement(
                    name=node.name,
                    element_type="async_function" if isinstance(node, ast.AsyncFunctionDef) else "function",
                    line_number=node.lineno,
                    end_line_number=getattr(node, 'end_lineno', node.lineno),
                    decorators=[d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list],
                    is_public=not node.name.startswith('_'),
                    docstring=ast.get_docstring(node),
                    complexity=self._estimate_complexity(node)
                )
                functions.append(element)
            
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
        
        return {
            "classes": classes,
            "functions": functions,
            "imports": imports,
            "lines": lines
        }
    
    def _estimate_complexity(self, node: ast.AST) -> int:
        """Estimate cyclomatic complexity of a node.
        
        Args:
            node: AST node to analyze.
            
        Returns:
            Estimated complexity score.
        """
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler,
                                  ast.BoolOp)):
                complexity += 1
        return complexity
    
    def get_untested_coverage_areas(self, test_files: List[Path]) -> Dict[str, int]:
        """Identify areas that might need more test coverage.
        
        Args:
            test_files: List of test file paths.
            
        Returns:
            Dict of file paths and estimated untested complexity.
        """
        if self.analysis is None:
            self.analyze()
        
        test_coverage = set()
        
        # Parse test files to see what they import/test
        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    test_tree = ast.parse(f.read())
                
                # Extract test functions
                for node in ast.walk(test_tree):
                    if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                        test_coverage.add(node.name)
            except Exception as e:
                logger.warning(f"Error analyzing test file {test_file}: {e}")
        
        # Find untested areas
        untested = {}
        for filepath, functions in self.analysis.functions.items():
            untested_complexity = 0
            for func in functions:
                if func.is_public and func.name not in test_coverage:
                    untested_complexity += func.complexity
            
            if untested_complexity > 0:
                untested[filepath] = untested_complexity
        
        return dict(sorted(untested.items(), key=lambda x: x[1], reverse=True))
    
    def generate_coverage_report(self) -> str:
        """Generate human-readable coverage report.
        
        Returns:
            Formatted report string.
        """
        if self.analysis is None:
            self.analyze()
        
        report = "📊 CODEBASE ANALYSIS REPORT\n"
        report += "=" * 60 + "\n\n"
        
        report += f"📁 Files: {self.analysis.python_files}\n"
        report += f"🏛️  Classes: {self.analysis.total_classes}\n"
        report += f"🔧 Functions: {self.analysis.total_functions}\n"
        report += f"📦 Imports: {self.analysis.total_imports}\n\n"
        
        # High-complexity functions
        high_complexity = []
        for filepath, functions in self.analysis.functions.items():
            for func in functions:
                if func.complexity > 5:
                    high_complexity.append((filepath, func))
        
        if high_complexity:
            report += "⚠️  HIGH COMPLEXITY FUNCTIONS (>5):\n"
            for filepath, func in sorted(high_complexity, key=lambda x: x[1].complexity, reverse=True)[:5]:
                report += f"  • {filepath}:{func.line_number} - {func.name}() (complexity: {func.complexity})\n"
            report += "\n"
        
        # Top files by line count
        top_files = sorted(self.analysis.file_coverage.items(), key=lambda x: x[1], reverse=True)[:5]
        if top_files:
            report += "📄 LARGEST FILES:\n"
            for filepath, lines in top_files:
                report += f"  • {filepath}: {lines} lines\n"
            report += "\n"
        
        report += "=" * 60 + "\n"
        return report


def get_codebase_analyzer(project_root: Path) -> CodebaseAnalyzer:
    """Get or create codebase analyzer instance.
    
    Args:
        project_root: Root directory of project.
        
    Returns:
        CodebaseAnalyzer instance.
    """
    return CodebaseAnalyzer(project_root)
