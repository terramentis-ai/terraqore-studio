"""Mock LLM client used for MetaQore and TerraQore development testing.

The goal is to provide a deterministic yet flexible stand-in for real LLM
providers so that we can run local workflows, unit tests, and integration tests
without talking to OpenRouter, Ollama, or any other external service. When the
infra is ready (for example, once an Oracle Cloud Ollama cluster is reachable)
we can swap in the production client without touching the calling code.
"""

from __future__ import annotations

import hashlib
import itertools
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from textwrap import dedent
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

try:  # Optional import so MetaQore can run outside TerraQore
    from core_cli.core.llm_client import LLMResponse as TerraLLMResponse  # type: ignore
except Exception:  # pragma: no cover - TerraQore dependency is optional
    TerraLLMResponse = None  # type: ignore


@dataclass(slots=True)
class MockLLMResponse:
    """Lightweight response object following TerraQore's LLMResponse contract."""

    content: str
    provider: str = "mock-llm"
    model: str = "mock-llm"
    usage: Dict[str, int] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None

    def to_terra_response(self):  # pragma: no cover - only used when TerraQore installed
        """Return a core_cli.core.llm_client.LLMResponse if TerraQore is available."""

        if TerraLLMResponse is None:
            raise RuntimeError("TerraQore LLMResponse is not available in this environment")
        return TerraLLMResponse(
            content=self.content,
            provider=self.provider,
            model=self.model,
            usage=self.usage,
            success=self.success,
            error=self.error,
        )


@dataclass(slots=True)
class MockLLMScenario:
    """Declarative rule describing how to craft a response for matching prompts."""

    name: str
    keywords: Sequence[str] = ()
    template: Optional[str] = None
    static_response: Optional[str] = None
    handler: Optional[Callable[["MockPromptContext"], str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def matches(self, prompt: str, metadata: Dict[str, Any]) -> bool:
        if not self.keywords:
            return True
        prompt_lower = prompt.lower()
        return all(keyword.lower() in prompt_lower for keyword in self.keywords)


@dataclass(slots=True)
class MockPromptContext:
    """Normalized data passed to scenario handlers."""

    prompt: str
    system_prompt: Optional[str]
    agent_name: Optional[str]
    metadata: Dict[str, Any]
    request_id: int
    timestamp: datetime


class MockLLMClient:
    """Configurable mock that emulates the TerraQore LLM client API."""

    def __init__(
        self,
        *,
        model: str = "mock-llm",
        provider_name: str = "mock",
        latency_range: tuple[float, float] = (0.01, 0.05),
        deterministic: bool = True,
        default_mode: str = "echo",
        seed: Optional[int] = 1337,
    ) -> None:
        self.model = model
        self.provider_name = provider_name
        self.latency_range = latency_range
        self.default_mode = default_mode
        self._scenarios: List[MockLLMScenario] = []
        self._counter = itertools.count(1)
        self._rng = random.Random(seed) if deterministic else random.Random()

    # ------------------------------------------------------------------
    # Scenario configuration helpers
    # ------------------------------------------------------------------
    def register_scenario(self, scenario: MockLLMScenario) -> None:
        """Register a scenario that overrides the default echo behavior."""

        self._scenarios.append(scenario)

    def register_template(
        self,
        name: str,
        *,
        keywords: Iterable[str] | None = None,
        template: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.register_scenario(
            MockLLMScenario(name=name, keywords=tuple(keywords or ()), template=template, metadata=metadata or {})
        )

    def register_handler(
        self,
        name: str,
        handler: Callable[[MockPromptContext], str],
        *,
        keywords: Iterable[str] | None = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.register_scenario(
            MockLLMScenario(
                name=name,
                keywords=tuple(keywords or ()),
                handler=handler,
                metadata=metadata or {},
            )
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        agent_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MockLLMResponse:
        """Return a deterministic mock response."""

        request_id = next(self._counter)
        context = MockPromptContext(
            prompt=prompt,
            system_prompt=system_prompt,
            agent_name=agent_name,
            metadata=metadata or {},
            request_id=request_id,
            timestamp=datetime.now(timezone.utc),
        )

        scenario = self._select_scenario(prompt, context.metadata)
        content = self._render_content(scenario, context)
        usage = self._estimate_usage(prompt, content)
        self._simulate_latency()
        return MockLLMResponse(
            content=content,
            provider=self.provider_name,
            model=self.model,
            usage=usage,
            success=True,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _select_scenario(self, prompt: str, metadata: Dict[str, Any]) -> Optional[MockLLMScenario]:
        for scenario in reversed(self._scenarios):  # last wins for overrides
            if scenario.matches(prompt, metadata):
                return scenario
        return None

    def _render_content(self, scenario: Optional[MockLLMScenario], context: MockPromptContext) -> str:
        if scenario:
            if scenario.handler:
                return scenario.handler(context)
            if scenario.template:
                return scenario.template.format(
                    prompt=context.prompt,
                    system_prompt=context.system_prompt or "",
                    agent=context.agent_name or "unknown-agent",
                    request_id=context.request_id,
                    timestamp=self._format_timestamp(context.timestamp),
                    **scenario.metadata,
                )
            if scenario.static_response:
                return scenario.static_response

        if self.default_mode == "echo":
            return self._echo_response(context)
        if self.default_mode == "summary":
            return self._summary_response(context)
        return self._default_response(context)

    def _echo_response(self, context: MockPromptContext) -> str:
        return dedent(
            f"""
            ### Mock Echo ({self.model})
            request_id: {context.request_id}
            agent: {context.agent_name or "unknown"}

            {context.prompt.strip()}
            """.strip()
        )

    def _summary_response(self, context: MockPromptContext) -> str:
        first_line = context.prompt.strip().splitlines()[0][:160] if context.prompt.strip() else ""
        return dedent(
            f"""
            ### Mock Summary ({self.model})
            request_id: {context.request_id}
            summary: {first_line or "No prompt content provided."}
            """.strip()
        )

    def _default_response(self, context: MockPromptContext) -> str:
        digest = hashlib.sha1(context.prompt.encode("utf-8")).hexdigest()[:12]
        return dedent(
            f"""
            ### Mock Completion ({self.model})
            request_id: {context.request_id}
            prompt_hash: {digest}
            timestamp: {self._format_timestamp(context.timestamp)}

            This is a deterministic offline response for development. Replace the mock
            client with a production provider (e.g., Ollama gateway) when ready.
            """.strip()
        )

    @staticmethod
    def _format_timestamp(timestamp: datetime) -> str:
        utc_timestamp = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
        return utc_timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    def _estimate_usage(self, prompt: str, content: str) -> Dict[str, int]:
        prompt_tokens = max(1, int(len(prompt.split()) * 1.2))
        completion_tokens = max(1, int(len(content.split()) * 1.1))
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

    def _simulate_latency(self) -> None:
        if self.latency_range == (0, 0):  # explicit opt-out
            return
        low, high = self.latency_range
        delay = self._rng.uniform(low, high)
        time.sleep(delay)


__all__ = ["MockLLMClient", "MockLLMResponse", "MockLLMScenario", "MockPromptContext"]
