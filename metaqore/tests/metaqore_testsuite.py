#!/usr/bin/env python3
"""MetaQore comprehensive test orchestrator."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MetaQoreTest")


class TestPhase(Enum):
    CORE_LOGIC = 1
    INTEGRATION = 2
    PERFORMANCE = 3
    VALIDATION = 4  # Reserved for future remote validation


class LLMMode(str, Enum):
    MOCK = "mock"
    OLLAMA = "ollama"


@dataclass
class PhaseCommand:
    name: str
    cmd: Sequence[str]
    cwd: Path = PROJECT_ROOT
    env: Mapping[str, str] | None = None
    optional: bool = False
    skip_reason: str | None = None


def _tests_exist(relative_folder: str) -> bool:
    folder = PROJECT_ROOT / "tests" / relative_folder
    return folder.exists() and any(folder.glob("test_*.py"))


def _base_llm_env(llm_mode: LLMMode) -> dict[str, str]:
    env = {"METAQORE_LLM_MODE": llm_mode.value}
    if llm_mode is LLMMode.MOCK:
        env["METAQORE_USE_MOCK_LLM"] = "1"
        env.setdefault("TEST_MODEL_UNIT", "mock-llm")
    return env


def _phase_commands(phase: TestPhase, llm_mode: LLMMode) -> list[PhaseCommand]:
    commands: list[PhaseCommand] = []
    base_env = _base_llm_env(llm_mode)

    if phase is TestPhase.CORE_LOGIC:
        if llm_mode is LLMMode.MOCK:
            smoke_script = (
                "from metaqore.mock_llm import MockLLMClient\n"
                "client = MockLLMClient(default_mode='summary')\n"
                "resp = client.generate('Describe PSMP checkpoints', agent_name='TestAgent')\n"
                "print(resp.content)\n"
            )
            commands.append(
                PhaseCommand(
                    name="MockLLM smoke test",
                    cmd=[sys.executable, "-c", smoke_script],
                    env=base_env.copy(),
                )
            )

        commands.append(
            PhaseCommand(
                name="Pytest unit suite",
                cmd=[sys.executable, "-m", "pytest", "tests/unit", "-q"],
                env=base_env.copy(),
            )
        )

    elif phase is TestPhase.INTEGRATION:
        if not _tests_exist("integration"):
            commands.append(
                PhaseCommand(
                    name="Integration suite",
                    cmd=[],
                    skip_reason="No integration tests detected",
                    optional=True,
                )
            )
        else:
            env_overrides: dict[str, str] = {}
            if "OLLAMA_BASE_URL" not in os.environ:
                env_overrides["OLLAMA_BASE_URL"] = "http://localhost:11434"
            env_overrides = {**base_env, **env_overrides}
            commands.append(
                PhaseCommand(
                    name="Pytest integration suite",
                    cmd=[sys.executable, "-m", "pytest", "tests/integration", "-q"],
                    env=env_overrides,
                )
            )

    elif phase is TestPhase.PERFORMANCE:
        benchmark = REPO_ROOT / "scripts" / "benchmark_throughput_test.py"
        if not benchmark.exists():
            commands.append(
                PhaseCommand(
                    name="Throughput benchmark",
                    cmd=[],
                    skip_reason="Benchmark script not found",
                    optional=True,
                )
            )
        else:
            commands.append(
                PhaseCommand(
                    name="Throughput benchmark",
                    cmd=[sys.executable, str(benchmark)],
                    cwd=REPO_ROOT,
                    env=base_env.copy(),
                    optional=True,
                )
            )

    elif phase is TestPhase.VALIDATION:
        commands.append(
            PhaseCommand(
                name="Validation suite",
                cmd=[],
                skip_reason="Phase reserved for premium validation flows",
                optional=True,
            )
        )

    return commands


async def _run_command(spec: PhaseCommand) -> tuple[bool, str]:
    if spec.skip_reason:
        logger.info("SKIP %s: %s", spec.name, spec.skip_reason)
        return True, spec.skip_reason

    env = os.environ.copy()
    if spec.env:
        env.update(spec.env)

    logger.info("▶ %s", spec.name)
    logger.debug("Command: %s", " ".join(spec.cmd))
    proc = await asyncio.create_subprocess_exec(*spec.cmd, cwd=str(spec.cwd), env=env)
    returncode = await proc.wait()
    success = returncode == 0
    if success:
        logger.info("✔ %s", spec.name)
    else:
        logger.error("✖ %s (exit %s)", spec.name, returncode)
    return success, f"exit={returncode}"


async def run_test_phase(phase: TestPhase, llm_mode: LLMMode) -> bool:
    logger.info("\n%s", "=" * 60)
    logger.info("BEGINNING TEST PHASE %s - %s", phase.value, phase.name)
    logger.info("%s", "=" * 60)

    commands = _phase_commands(phase, llm_mode)
    phase_success = True

    for spec in commands:
        success, _ = await _run_command(spec)
        if success:
            continue
        if spec.optional:
            logger.warning("Optional command '%s' failed; continuing", spec.name)
            continue
        phase_success = False
        break

    if phase_success:
        logger.info("Phase %s complete", phase.value)
    else:
        logger.error("Phase %s failed", phase.value)
    return phase_success


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run the MetaQore test suite.")
    parser.add_argument(
        "--phase",
        type=int,
        choices=[phase.value for phase in TestPhase],
        help="Run a specific test phase (1-4). Runs core phases (1-3) if omitted.",
    )
    parser.add_argument(
        "--llm-mode",
        type=str,
        choices=[mode.value for mode in LLMMode],
        default=LLMMode.MOCK.value,
        help="Select the backing LLM mode (mock or ollama). Defaults to mock for offline CI.",
    )
    args = parser.parse_args()

    llm_mode = LLMMode(args.llm_mode)

    start_time = datetime.now()
    phases_to_run = [TestPhase(args.phase)] if args.phase else list(TestPhase)[:3]

    for phase in phases_to_run:
        phase_passed = await run_test_phase(phase, llm_mode)
        if not phase_passed:
            logger.error("Halting suite after phase %s failure", phase.value)
            duration = datetime.now() - start_time
            logger.error("Test suite halted after %s", duration)
            sys.exit(1)

    duration = datetime.now() - start_time
    logger.info("\n%s", "=" * 60)
    logger.info("SUCCESS: All requested phases completed in %s", duration)
    logger.info("%s", "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())