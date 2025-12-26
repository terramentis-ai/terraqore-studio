"""
Code Executor Tool - Safely executes and tests generated code.

Features:
- Sandboxed code execution
- Error capture and reporting
- Test runner integration
- Output validation
- Timeout protection
"""

import subprocess
import logging
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    language: str
    file_path: str
    stdout: str
    stderr: str
    return_code: int
    execution_time: float
    validation_passed: bool
    errors: List[str]
    warnings: List[str]


class CodeExecutor:
    """Safely executes and tests code."""
    
    def __init__(self, project_root: str, timeout: int = 30):
        """
        Initialize code executor.
        
        Args:
            project_root: Root directory of the project
            timeout: Execution timeout in seconds
        """
        self.project_root = Path(project_root)
        self.timeout = timeout
        self.execution_history: List[ExecutionResult] = []
    
    def execute_python(
        self,
        file_path: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None
    ) -> ExecutionResult:
        """
        Execute a Python file.
        
        Args:
            file_path: Relative path to Python file from project root
            args: Optional command-line arguments
            env: Optional environment variables
            
        Returns:
            ExecutionResult with output and status
        """
        try:
            full_path = self.project_root / file_path
            
            if not full_path.exists():
                return ExecutionResult(
                    success=False,
                    language="python",
                    file_path=file_path,
                    stdout="",
                    stderr=f"File not found: {full_path}",
                    return_code=1,
                    execution_time=0,
                    validation_passed=False,
                    errors=[f"File not found: {full_path}"],
                    warnings=[]
                )
            
            # Build command
            cmd = [sys.executable, str(full_path)]
            if args:
                cmd.extend(args)
            
            # Prepare environment
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)
            
            # Execute with timeout
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=str(self.project_root),
                    env=exec_env
                )
                
                stdout = result.stdout
                stderr = result.stderr
                return_code = result.returncode
                execution_time = 0  # Not directly available from subprocess
                
            except subprocess.TimeoutExpired:
                return ExecutionResult(
                    success=False,
                    language="python",
                    file_path=file_path,
                    stdout="",
                    stderr=f"Execution timeout ({self.timeout}s exceeded)",
                    return_code=-1,
                    execution_time=self.timeout,
                    validation_passed=False,
                    errors=["Timeout"],
                    warnings=[]
                )
            
            # Parse results
            errors = []
            warnings = []
            validation_passed = return_code == 0
            
            if return_code != 0:
                errors.append(f"Process exited with code {return_code}")
                if stderr:
                    errors.append(stderr)
            
            if stderr and "Warning" in stderr:
                warnings.append(stderr)
            
            result = ExecutionResult(
                success=return_code == 0,
                language="python",
                file_path=file_path,
                stdout=stdout,
                stderr=stderr,
                return_code=return_code,
                execution_time=0,
                validation_passed=validation_passed,
                errors=errors,
                warnings=warnings
            )
            
            self.execution_history.append(result)
            return result
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                language="python",
                file_path=file_path,
                stdout="",
                stderr=str(e),
                return_code=1,
                execution_time=0,
                validation_passed=False,
                errors=[str(e)],
                warnings=[]
            )
    
    def execute_javascript(
        self,
        file_path: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None
    ) -> ExecutionResult:
        """
        Execute a JavaScript file with Node.js.
        
        Args:
            file_path: Relative path to JavaScript file from project root
            args: Optional command-line arguments
            env: Optional environment variables
            
        Returns:
            ExecutionResult with output and status
        """
        try:
            full_path = self.project_root / file_path
            
            if not full_path.exists():
                return ExecutionResult(
                    success=False,
                    language="javascript",
                    file_path=file_path,
                    stdout="",
                    stderr=f"File not found: {full_path}",
                    return_code=1,
                    execution_time=0,
                    validation_passed=False,
                    errors=[f"File not found: {full_path}"],
                    warnings=[]
                )
            
            # Build command
            cmd = ["node", str(full_path)]
            if args:
                cmd.extend(args)
            
            # Prepare environment
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)
            
            # Execute with timeout
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=str(self.project_root),
                    env=exec_env
                )
                
                stdout = result.stdout
                stderr = result.stderr
                return_code = result.returncode
                
            except subprocess.TimeoutExpired:
                return ExecutionResult(
                    success=False,
                    language="javascript",
                    file_path=file_path,
                    stdout="",
                    stderr=f"Execution timeout ({self.timeout}s exceeded)",
                    return_code=-1,
                    execution_time=self.timeout,
                    validation_passed=False,
                    errors=["Timeout"],
                    warnings=[]
                )
            
            # Parse results
            errors = []
            warnings = []
            validation_passed = return_code == 0
            
            if return_code != 0:
                errors.append(f"Process exited with code {return_code}")
                if stderr:
                    errors.append(stderr)
            
            result = ExecutionResult(
                success=return_code == 0,
                language="javascript",
                file_path=file_path,
                stdout=stdout,
                stderr=stderr,
                return_code=return_code,
                execution_time=0,
                validation_passed=validation_passed,
                errors=errors,
                warnings=warnings
            )
            
            self.execution_history.append(result)
            return result
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                language="javascript",
                file_path=file_path,
                stdout="",
                stderr=str(e),
                return_code=1,
                execution_time=0,
                validation_passed=False,
                errors=[str(e)],
                warnings=[]
            )
    
    def run_tests(
        self,
        test_file_or_dir: str,
        framework: str = "pytest"
    ) -> ExecutionResult:
        """
        Run test suite.
        
        Args:
            test_file_or_dir: Path to test file or directory
            framework: Test framework (pytest, unittest, jest, mocha, etc.)
            
        Returns:
            ExecutionResult with test output
        """
        try:
            full_path = self.project_root / test_file_or_dir
            
            if not full_path.exists():
                return ExecutionResult(
                    success=False,
                    language="test",
                    file_path=test_file_or_dir,
                    stdout="",
                    stderr=f"Test file/directory not found: {full_path}",
                    return_code=1,
                    execution_time=0,
                    validation_passed=False,
                    errors=[f"Not found: {full_path}"],
                    warnings=[]
                )
            
            # Build command based on framework
            if framework == "pytest":
                cmd = [sys.executable, "-m", "pytest", str(full_path), "-v"]
            elif framework == "unittest":
                cmd = [sys.executable, "-m", "unittest", str(full_path)]
            elif framework in ["jest", "mocha"]:
                cmd = ["npm", "test", "--", str(test_file_or_dir)]
            else:
                return ExecutionResult(
                    success=False,
                    language="test",
                    file_path=test_file_or_dir,
                    stdout="",
                    stderr=f"Unknown test framework: {framework}",
                    return_code=1,
                    execution_time=0,
                    validation_passed=False,
                    errors=[f"Unknown framework: {framework}"],
                    warnings=[]
                )
            
            # Execute
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=str(self.project_root)
                )
                
                stdout = result.stdout
                stderr = result.stderr
                return_code = result.returncode
                
            except subprocess.TimeoutExpired:
                return ExecutionResult(
                    success=False,
                    language="test",
                    file_path=test_file_or_dir,
                    stdout="",
                    stderr=f"Test timeout ({self.timeout}s exceeded)",
                    return_code=-1,
                    execution_time=self.timeout,
                    validation_passed=False,
                    errors=["Timeout"],
                    warnings=[]
                )
            
            # Parse results
            errors = []
            if return_code != 0:
                errors.append(f"Tests failed with code {return_code}")
            
            result = ExecutionResult(
                success=return_code == 0,
                language="test",
                file_path=test_file_or_dir,
                stdout=stdout,
                stderr=stderr,
                return_code=return_code,
                execution_time=0,
                validation_passed=return_code == 0,
                errors=errors,
                warnings=[]
            )
            
            self.execution_history.append(result)
            return result
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                language="test",
                file_path=test_file_or_dir,
                stdout="",
                stderr=str(e),
                return_code=1,
                execution_time=0,
                validation_passed=False,
                errors=[str(e)],
                warnings=[]
            )
    
    def install_dependencies(
        self,
        requirements_file: str,
        package_manager: str = "pip"
    ) -> Tuple[bool, str]:
        """
        Install dependencies from requirements file.
        
        Args:
            requirements_file: Path to requirements file (requirements.txt, package.json)
            package_manager: Package manager (pip, npm, yarn, etc.)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            full_path = self.project_root / requirements_file
            
            if not full_path.exists():
                return False, f"Requirements file not found: {full_path}"
            
            # Build command
            if package_manager == "pip":
                cmd = [sys.executable, "-m", "pip", "install", "-r", str(full_path)]
            elif package_manager == "npm":
                cmd = ["npm", "install"]
            elif package_manager == "yarn":
                cmd = ["yarn", "install"]
            else:
                return False, f"Unknown package manager: {package_manager}"
            
            # Execute
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minutes for dependency install
                    cwd=str(self.project_root)
                )
                
                if result.returncode == 0:
                    logger.info(f"Dependencies installed from {requirements_file}")
                    return True, f"Successfully installed dependencies from {requirements_file}"
                else:
                    error_msg = result.stderr or result.stdout
                    logger.error(f"Dependency installation failed: {error_msg}")
                    return False, f"Installation failed: {error_msg}"
                    
            except subprocess.TimeoutExpired:
                return False, "Dependency installation timeout"
            
        except Exception as e:
            error_msg = f"Error installing dependencies: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_execution_history(self) -> List[ExecutionResult]:
        """Get execution history."""
        return self.execution_history.copy()
    
    def format_result(self, result: ExecutionResult) -> str:
        """Format execution result for display."""
        
        status = "✓ SUCCESS" if result.success else "✗ FAILED"
        
        output = f"""
Execution Result: {status}
Language: {result.language}
File: {result.file_path}
Return Code: {result.return_code}

STDOUT:
{result.stdout if result.stdout else '(no output)'}

STDERR:
{result.stderr if result.stderr else '(no errors)'}

Validation: {'✓ PASSED' if result.validation_passed else '✗ FAILED'}
"""
        
        if result.errors:
            output += "\nErrors:\n"
            for error in result.errors:
                output += f"  • {error}\n"
        
        if result.warnings:
            output += "\nWarnings:\n"
            for warning in result.warnings:
                output += f"  • {warning}\n"
        
        return output
