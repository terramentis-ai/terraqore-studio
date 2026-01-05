"""Prompt assembly engine for the MetaQore LLM Gateway."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class PromptProfile:
    """Base prompt profile describing agent behavior."""

    name: str
    template: str
    metadata: Dict[str, object]


@dataclass
class PromptAssemblyResult:
    """Output of the prompt assembly process."""

    prompt: str
    profile_hash: str
    metadata: Dict[str, object]


class PromptAssemblyEngine:
    """Caches agent profiles and assembles runtime prompts."""

    def __init__(self) -> None:
        self._profiles: Dict[str, PromptProfile] = {}

    def register_profile(self, agent_name: str, template: str, *, metadata: Optional[Dict[str, object]] = None) -> None:
        profile = PromptProfile(name=agent_name, template=template, metadata=metadata or {})
        self._profiles[agent_name] = profile

    def has_profile(self, agent_name: str) -> bool:
        return agent_name in self._profiles

    def assemble_prompt(
        self,
        agent_name: str,
        task_context: str,
        *,
        overrides: Optional[Dict[str, object]] = None,
    ) -> PromptAssemblyResult:
        if agent_name not in self._profiles:
            raise KeyError(f"Unknown agent profile '{agent_name}'")

        profile = self._profiles[agent_name]
        prompt = profile.template.format(task_context=task_context)
        metadata = {**profile.metadata, **(overrides or {})}
        profile_hash = self._hash_profile(profile.template, metadata)
        return PromptAssemblyResult(prompt=prompt, profile_hash=profile_hash, metadata=metadata)

    @staticmethod
    def _hash_profile(template: str, metadata: Dict[str, object]) -> str:
        digest = hashlib.sha256()
        digest.update(template.encode("utf-8"))
        for key in sorted(metadata):
            digest.update(f"{key}:{metadata[key]}".encode("utf-8"))
        return digest.hexdigest()[:32]


__all__ = ["PromptAssemblyEngine", "PromptAssemblyResult", "PromptProfile"]
