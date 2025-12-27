"""
Code Executor Tool - Safely executes and tests generated code with sandboxed limits.

Features:
- Sandbox quotas via docker_runtime_limits presets
- Dangerous output detection with halt
- Execution transcript logging
- Timeout and soft resource limits (best-effort on POSIX)
"""

import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

try:
    import resource  # POSIX-only; used for soft limits
except ImportError:  # pragma: no cover - Windows/non-POSIX
    resource = None

from core.docker_runtime_limits import (
    SandboxSpecification,
    ExecutionTranscript,
    RollbackMetadata,
    get_preset_configuration,
)

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
    transcript: Optional[ExecutionTranscript] = None
    rollback: Optional[RollbackMetadata] = None


@dataclass
class ExecutionPolicy:
    """Execution sandbox policy (best-effort, POSIX limits when available)."""

    timeout: int = 30
    memory_mb: Optional[int] = None  # Soft limit; POSIX only
    cpu_seconds: Optional[int] = None  # Soft limit; POSIX only
    log_path: Optional[Path] = None


class CodeExecutor:
    """Safely executes and tests code with sandbox limits and auditing."""

    def __init__(
        self,
        project_root: str,
        sandbox_spec: Optional[SandboxSpecification] = None,
        policy: Optional[ExecutionPolicy] = None,
        dangerous_patterns: Optional[List[str]] = None,
        use_docker: bool = False,
        docker_image_map: Optional[Dict[str, str]] = None,
    ):
        self.project_root = Path(project_root)
        self.sandbox_spec = sandbox_spec or get_preset_configuration("standard_coding") or SandboxSpecification()
        timeout = self.sandbox_spec.timeout.execution_timeout_seconds
        self.policy = policy or ExecutionPolicy(
            timeout=timeout,
            memory_mb=self.sandbox_spec.memory.max_memory_mb,
            cpu_seconds=self.sandbox_spec.cpu.cpu_time_seconds,
        )
        self.execution_history: List[ExecutionResult] = []
        self.dangerous_patterns = dangerous_patterns or [
            "rm -rf /",
            "os.system",
            "subprocess.run",
            "curl http://169.254",
            "aws_metadata",
            "chmod 777",
            "sudo ",
        ]
        self.use_docker = bool(use_docker and shutil.which("docker"))
        self.docker_image_map = docker_image_map or {
            "python": "python:3.11-slim",
            "javascript": "node:18-alpine",
            "test": "python:3.11-slim",
            "default": "python:3.11-slim",
        }

    # Public APIs -----------------------------------------------------
    def execute_python(self, file_path: str, args: Optional[List[str]] = None, env: Optional[Dict[str, str]] = None) -> ExecutionResult:
        container_cmd = ["python", f"/workspace/{file_path.replace(os.sep, '/')}" ]
        return self._run_command(
            language="python",
            cmd=[sys.executable, str(self.project_root / file_path)],
            container_cmd=container_cmd,
            file_path=file_path,
            args=args,
            env=env,
        )

    def execute_javascript(self, file_path: str, args: Optional[List[str]] = None, env: Optional[Dict[str, str]] = None) -> ExecutionResult:
        container_cmd = ["node", f"/workspace/{file_path.replace(os.sep, '/')}" ]
        return self._run_command(
            language="javascript",
            cmd=["node", str(self.project_root / file_path)],
            container_cmd=container_cmd,
            file_path=file_path,
            args=args,
            env=env,
        )

    def run_tests(self, test_file_or_dir: str, framework: str = "pytest") -> ExecutionResult:
        if framework == "pytest":
            cmd = [sys.executable, "-m", "pytest", str(self.project_root / test_file_or_dir), "-v"]
            container_cmd = ["python", "-m", "pytest", f"/workspace/{test_file_or_dir.replace(os.sep, '/')}", "-v"]
        elif framework == "unittest":
            cmd = [sys.executable, "-m", "unittest", str(self.project_root / test_file_or_dir)]
            container_cmd = ["python", "-m", "unittest", f"/workspace/{test_file_or_dir.replace(os.sep, '/')}"]
        elif framework in ["jest", "mocha"]:
            cmd = ["npm", "test", "--", str(test_file_or_dir)]
            container_cmd = ["npm", "test", "--", f"/workspace/{test_file_or_dir.replace(os.sep, '/')}" ]
        else:
            return self._record_execution(
                ExecutionResult(
                    success=False,
                    language="test",
                    file_path=test_file_or_dir,
                    stdout="",
                    stderr=f"Unknown test framework: {framework}",
                    return_code=1,
                    execution_time=0,
                    validation_passed=False,
                    errors=[f"Unknown framework: {framework}"],
                    warnings=[],
                )
            )

        return self._run_command(language="test", cmd=cmd, container_cmd=container_cmd, file_path=test_file_or_dir)

    def install_dependencies(self, requirements_file: str, package_manager: str = "pip") -> Tuple[bool, str]:
        full_path = self.project_root / requirements_file
        if not full_path.exists():
            return False, f"Requirements file not found: {full_path}"

        if package_manager == "pip":
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(full_path)]
        elif package_manager == "npm":
            cmd = ["npm", "install"]
        elif package_manager == "yarn":
            cmd = ["yarn", "install"]
        else:
            return False, f"Unknown package manager: {package_manager}"

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=str(self.project_root))
            if result.returncode == 0:
                return True, f"Successfully installed dependencies from {requirements_file}"
            return False, (result.stderr or result.stdout)
        except subprocess.TimeoutExpired:
            return False, "Dependency installation timeout"
        except Exception as exc:  # pragma: no cover - safety
            return False, f"Error installing dependencies: {exc}"

    def get_execution_history(self) -> List[ExecutionResult]:
        return self.execution_history.copy()

    def format_result(self, result: ExecutionResult) -> str:
        output = f"""
CODE EXECUTION RESULT
=====================
File: {result.file_path}
Language: {result.language}
Success: {result.success}
Return Code: {result.return_code}
Execution Time: {result.execution_time:.2f}s

STDOUT:
{result.stdout if result.stdout else '(no output)'}

STDERR:
{result.stderr if result.stderr else '(no errors)'}

Validation: {'✓ PASSED' if result.validation_passed else '✗ FAILED'}
"""

        if result.errors:
            output += "\nErrors:\n" + "\n".join(f"  • {err}" for err in result.errors)
        if result.warnings:
            output += "\nWarnings:\n" + "\n".join(f"  • {warn}" for warn in result.warnings)
        if result.transcript:
            output += f"\nTranscript ID: {result.transcript.execution_id}"
            if result.transcript.halt_reason:
                output += f"\nHalt Reason: {result.transcript.halt_reason}"
        return output

    # Internal helpers ------------------------------------------------
    def _run_command(
        self,
        language: str,
        cmd: List[str],
        container_cmd: Optional[List[str]],
        file_path: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> ExecutionResult:
        full_path = self.project_root / file_path
        if not full_path.exists() and language != "test":
            return self._record_execution(
                ExecutionResult(
                    success=False,
                    language=language,
                    file_path=file_path,
                    stdout="",
                    stderr=f"File not found: {full_path}",
                    return_code=1,
                    execution_time=0,
                    validation_passed=False,
                    errors=[f"File not found: {full_path}"],
                    warnings=[],
                )
            )

        if args:
            cmd = cmd + args
            if container_cmd:
                container_cmd = container_cmd + args

        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        selected_cmd = container_cmd if (self.use_docker and container_cmd) else cmd
        final_cmd, used_docker = self._build_command(selected_cmd, language)

        started = time.perf_counter()
        try:
            proc = subprocess.run(
                final_cmd,
                capture_output=True,
                text=True,
                timeout=self.policy.timeout,
                cwd=str(self.project_root),
                env=exec_env,
                preexec_fn=self._build_preexec_fn(),
            )
            stdout, stderr, return_code = proc.stdout, proc.stderr, proc.returncode
            execution_time = time.perf_counter() - started
        except subprocess.TimeoutExpired:
            return self._record_execution(
                ExecutionResult(
                    success=False,
                    language=language,
                    file_path=file_path,
                    stdout="",
                    stderr=f"Execution timeout ({self.policy.timeout}s exceeded)",
                    return_code=-1,
                    execution_time=self.policy.timeout,
                    validation_passed=False,
                    errors=["Timeout"],
                    warnings=[],
                )
            )
        except Exception as exc:  # pragma: no cover - safety
            return self._record_execution(
                ExecutionResult(
                    success=False,
                    language=language,
                    file_path=file_path,
                    stdout="",
                    stderr=str(exc),
                    return_code=1,
                    execution_time=0,
                    validation_passed=False,
                    errors=[str(exc)],
                    warnings=[],
                )
            )

        errors: List[str] = []
        warnings: List[str] = []
        validation_passed = return_code == 0

        if return_code != 0:
            errors.append(f"Process exited with code {return_code}")
            if stderr:
                errors.append(stderr)

        # Detect dangerous output and halt
        dangerous, patterns = self._detect_dangerous_output(stdout, stderr)

        transcript = self._build_transcript(
            language=language,
            file_path=file_path,
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
            execution_time=execution_time,
            dangerous=bool(dangerous),
            patterns=patterns,
            command_line=" ".join(final_cmd),
            working_directory="/workspace" if used_docker else str(self.project_root),
            environment_variables={k: v for k, v in (env or {}).items()},
        )

        if dangerous:
            errors.append("Dangerous output detected; execution halted")
            validation_passed = False
            return_code = return_code if return_code != 0 else 1

        result = ExecutionResult(
            success=(return_code == 0 and not dangerous),
            language=language,
            file_path=file_path,
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
            execution_time=execution_time,
            validation_passed=validation_passed,
            errors=errors,
            warnings=warnings,
            transcript=transcript,
            rollback=None,
        )

        return self._record_execution(result)

    def _build_command(self, cmd: List[str], language: str) -> Tuple[List[str], bool]:
        if not self.use_docker:
            return cmd, False

        image = self.docker_image_map.get(language) or self.docker_image_map.get("default", "python:3.11-slim")
        docker_cmd: List[str] = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{self.project_root}:/workspace",
            "-w",
            "/workspace",
        ]
        docker_cmd.extend(self.sandbox_spec.to_docker_run_args())
        docker_cmd.append(image)
        docker_cmd.extend(cmd)
        return docker_cmd, True

    def _build_preexec_fn(self) -> Optional[Callable[[], None]]:
        """Create a pre-exec hook that applies soft resource limits on POSIX."""

        if platform.system().lower().startswith("win"):
            return None
        if resource is None:
            return None

        mem_bytes = self.policy.memory_mb * 1024 * 1024 if self.policy.memory_mb else None
        cpu_seconds = self.policy.cpu_seconds

        def _setter():  # pragma: no cover - executed in child
            if mem_bytes:
                try:
                    resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
                except Exception:
                    pass
            if cpu_seconds:
                try:
                    resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
                except Exception:
                    pass

        return _setter

    def _detect_dangerous_output(self, stdout: str, stderr: str) -> Tuple[bool, List[str]]:
        combined = (stdout or "") + "\n" + (stderr or "")
        matched = [p for p in self.dangerous_patterns if p.lower() in combined.lower()]
        return (len(matched) > 0), matched

    def _build_transcript(
        self,
        language: str,
        file_path: str,
        stdout: str,
        stderr: str,
        return_code: int,
        execution_time: float,
        dangerous: bool,
        patterns: List[str],
        command_line: str,
        working_directory: str,
        environment_variables: Dict[str, str],
    ) -> ExecutionTranscript:
        return ExecutionTranscript(
            execution_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            language=language,
            file_path=file_path,
            environment_variables=environment_variables,
            command_line=command_line,
            working_directory=working_directory,
            cpu_time_seconds=execution_time,
            memory_peak_mb=0.0,
            wall_time_seconds=execution_time,
            stdout=stdout or "",
            stderr=stderr or "",
            exit_code=return_code,
            quotas_applied=self.sandbox_spec.to_dict(),
            dangerous_output_detected=dangerous,
            dangerous_patterns=patterns,
            halt_reason="Dangerous output detected" if dangerous else None,
        )

    def _record_execution(self, result: ExecutionResult) -> ExecutionResult:
        self.execution_history.append(result)

        log_path = self.policy.log_path
        if log_path:
            try:
                log_path.parent.mkdir(parents=True, exist_ok=True)
                with log_path.open("a", encoding="utf-8") as fh:
                    json.dump(
                        {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "language": result.language,
                            "file": result.file_path,
                            "success": result.success,
                            "return_code": result.return_code,
                            "execution_time": result.execution_time,
                            "errors": result.errors,
                            "warnings": result.warnings,
                            "dangerous_output": result.transcript.dangerous_output_detected if result.transcript else False,
                            "halt_reason": result.transcript.halt_reason if result.transcript else None,
                        },
                        fh,
                    )
                    fh.write("\n")
            except Exception as log_err:  # pragma: no cover - best effort
                logger.debug(f"Failed to write execution log: {log_err}")

        return result
