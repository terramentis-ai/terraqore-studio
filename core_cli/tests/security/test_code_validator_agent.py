"""
Tests for CodeValidationAgent hallucination halt and spec presets.
"""

import sys
from pathlib import Path

import pytest

# Ensure core_cli package is importable when running from repo root
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.base import AgentContext
from agents.code_validator_agent import CodeValidationAgent
from tests.security.malicious_samples import COMMAND_INJECTION_SAMPLES


class DummyLLM:
    """Minimal LLM stub to satisfy BaseAgent interface."""

    def generate(self, prompt: str, system: str):
        return type("Resp", (), {"success": True, "content": "ok", "usage": {}})()


def make_context(code: str, language: str = "python") -> AgentContext:
    return AgentContext(
        project_id=1,
        project_name="demo",
        project_description="test",
        user_input="",
        metadata={
            "language": language,
            "code_generation": {
                "files": [
                    {"path": "main.py", "content": code}
                ]
            },
        },
        conversation_history=[],
    )


class TestHallucinationHalt:
    def test_halt_on_high_severity(self):
        agent = CodeValidationAgent(llm_client=DummyLLM(), verbose=False)
        context = make_context("import os\nos.system('ls')")

        result = agent.execute(context)

        assert result.success is False
        assert "Hallucination threshold breached" in result.output
        assert result.metadata.get("hallucination_meta", {}).get("max_severity") in {"high", "critical"}

    def test_halt_on_score_threshold(self):
        agent = CodeValidationAgent(llm_client=DummyLLM(), verbose=False)
        # Only halt on critical by severity; use score gate for high
        agent.hallucination_thresholds = {
            "min_score": 0.95,
            "halt_severities": {"critical"},
        }
        context = make_context("import os\nos.system('ls')")

        result = agent.execute(context)

        assert result.success is False
        meta = result.metadata.get("hallucination_meta", {})
        assert meta.get("min_score", 1.0) < 0.95
        assert meta.get("halt") is True

    def test_metadata_contains_halt_reason(self):
        agent = CodeValidationAgent(llm_client=DummyLLM(), verbose=False)
        context = make_context("import subprocess\nsubprocess.run('ls', shell=True)")

        result = agent.execute(context)

        meta = result.metadata.get("hallucination_meta", {})
        assert meta.get("halt") is True
        assert "max_severity" in meta
        assert "total_findings" in meta

    def test_malicious_sample_triggers_halt(self):
        agent = CodeValidationAgent(llm_client=DummyLLM(), verbose=False)
        code = COMMAND_INJECTION_SAMPLES["shell_injection"]
        context = make_context(code)

        result = agent.execute(context)

        assert result.success is False
        meta = result.metadata.get("hallucination_meta", {})
        assert meta.get("halt") is True


class TestSpecPreset:
    def test_language_preset_applied_when_no_spec(self):
        agent = CodeValidationAgent(llm_client=DummyLLM(), verbose=False)
        spec = agent._build_validation_spec({
            "language": "python",
            "metadata": {},
        })
        assert spec is not None
        assert "os.system" in spec.forbidden_patterns


if __name__ == "__main__":
    pytest.main([__file__])
