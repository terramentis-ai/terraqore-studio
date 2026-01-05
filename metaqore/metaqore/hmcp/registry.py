"""Skill registry for the Hierarchical Model Chaining Protocol (HMCP)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

from .config_loader import load_hmcp_config


@dataclass(frozen=True)
class SkillDefinition:
    """Immutable definition describing an allowable specialist skill."""

    skill_id: str
    description: str
    parent_agent: str
    max_specialist_size_mb: int
    allowed_teachers: Sequence[str]


class SkillRegistry:
    """In-memory registry that governs which specialist skills may exist."""

    def __init__(
        self,
        skills: Dict[str, SkillDefinition],
        *,
        discovery_policy: str,
        proposal_mechanism: Dict[str, str],
    ) -> None:
        self._skills = skills
        self.discovery_policy = discovery_policy
        self.proposal_mechanism = proposal_mechanism

    @classmethod
    def from_policy(cls) -> "SkillRegistry":
        """Instantiate the registry from the hmcp.json policy file."""

        policy = load_hmcp_config()
        registry_cfg = policy.get("skill_registry", {})
        raw_skills = registry_cfg.get("skills", [])
        skills = {
            entry["skill_id"]: SkillDefinition(
                skill_id=entry["skill_id"],
                description=entry.get("description", ""),
                parent_agent=entry.get("parent_agent", ""),
                max_specialist_size_mb=int(entry.get("max_specialist_size_mb", 0)),
                allowed_teachers=tuple(entry.get("allowed_teachers", [])),
            )
            for entry in raw_skills
        }
        return cls(
            skills,
            discovery_policy=registry_cfg.get("discovery_policy", "registry_only"),
            proposal_mechanism=registry_cfg.get("proposal_mechanism", {}),
        )

    def list_skills(self) -> List[SkillDefinition]:
        return list(self._skills.values())

    def get(self, skill_id: str) -> Optional[SkillDefinition]:
        return self._skills.get(skill_id)

    def is_registered(self, skill_id: str) -> bool:
        return skill_id in self._skills

    def ensure_registered(self, skill_id: str) -> SkillDefinition:
        skill = self.get(skill_id)
        if skill is None:
            raise KeyError(f"Skill '{skill_id}' is not registered with HMCP")
        return skill

    def validate_teachers(self, skill_id: str, teachers: Iterable[str]) -> bool:
        """Return True when all provided teachers are permitted for the skill."""

        skill = self.ensure_registered(skill_id)
        allowed = set(skill.allowed_teachers)
        return all(teacher in allowed for teacher in teachers)

    def allowed_teachers(self, skill_id: str) -> Sequence[str]:
        return self.ensure_registered(skill_id).allowed_teachers

    def get_parent_agent(self, skill_id: str) -> str:
        return self.ensure_registered(skill_id).parent_agent


__all__ = ["SkillDefinition", "SkillRegistry"]
