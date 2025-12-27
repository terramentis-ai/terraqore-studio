"""
Tests for sandbox-aware CodeExecutor: dangerous output halt and docker command building.
"""

import sys
from pathlib import Path

import pytest

# Ensure core_cli package is importable when running from repo root
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.docker_runtime_limits import get_preset_configuration
from tools.code_executor import CodeExecutor


class TestDangerousOutput:
    def test_dangerous_output_triggers_halt(self, tmp_path):
        script = tmp_path / "danger.py"
        script.write_text("print('rm -rf /')\n", encoding="utf-8")

        executor = CodeExecutor(project_root=str(tmp_path))
        result = executor.execute_python(script.name)

        assert result.success is False
        assert result.validation_passed is False
        assert any("Dangerous output" in err for err in result.errors)
        assert result.transcript is not None
        assert result.transcript.dangerous_output_detected is True
        assert "rm -rf /" in " ".join(result.transcript.dangerous_patterns)

    def test_transcript_includes_quotas(self, tmp_path):
        script = tmp_path / "safe.py"
        script.write_text("print('hello')\n", encoding="utf-8")

        executor = CodeExecutor(project_root=str(tmp_path))
        result = executor.execute_python(script.name)

        assert result.success is True
        assert result.transcript is not None
        quotas = result.transcript.quotas_applied
        assert isinstance(quotas, dict)
        assert quotas.get("cpu") is not None
        assert quotas.get("memory") is not None


class TestDockerCommandBuilder:
    def test_build_command_uses_sandbox_args(self, tmp_path):
        spec = get_preset_configuration("test_execution")
        executor = CodeExecutor(project_root=str(tmp_path), sandbox_spec=spec, use_docker=True)
        # Force docker usage for test environments without docker installed
        executor.use_docker = True

        cmd, used = executor._build_command(["python", "/workspace/app.py"], language="python")

        assert used is True
        assert cmd[0] == "docker"
        assert any(arg.startswith("--cpus=") for arg in cmd)
        assert any(arg.startswith("--memory=") for arg in cmd)
        assert any(str(tmp_path) in arg for arg in cmd)
        assert spec.to_docker_run_args()[0] in cmd


if __name__ == "__main__":
    pytest.main([__file__])
