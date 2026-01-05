"""Hierarchical chaining policy enforcement for HMCP specialists."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Sequence, Tuple, Union

from .config_loader import load_hmcp_config


NumberLike = Union[int, float]


class ChainingPolicyError(RuntimeError):
    """Raised when the hierarchical chaining policy cannot be applied."""


@dataclass(frozen=True)
class SpawnTrigger:
    """Configuration describing when a specialist may spawn a child."""

    condition: str
    threshold: float
    isolation_requirement: str


@dataclass(frozen=True)
class ChainingLevel:
    """Immutable representation of a policy-defined level in the hierarchy."""

    index: int
    key: str
    level_type: str
    example: str
    max_parameters: int
    raw_max_size: str
    can_spawn: bool

    def describe(self) -> str:
        return f"Level {self.index} ({self.level_type})"


@dataclass(frozen=True)
class SpawnDecision:
    """Result of evaluating whether a child specialist may be spawned."""

    allowed: bool
    reasons: Sequence[str]
    next_level: Optional[ChainingLevel]


class HierarchicalChainingPolicy:
    """Loads and enforces HMCP hierarchical chaining rules."""

    def __init__(
        self,
        levels: Sequence[ChainingLevel],
        trigger: SpawnTrigger,
        depth: int,
    ) -> None:
        if not levels:
            raise ChainingPolicyError("Policy must define at least one level")

        self._levels = list(levels)
        self._levels_by_key: Dict[str, ChainingLevel] = {level.key: level for level in levels}
        self._levels_by_index: Dict[int, ChainingLevel] = {level.index: level for level in levels}
        self._trigger = trigger
        self._depth = depth

    @classmethod
    def from_policy(cls) -> "HierarchicalChainingPolicy":
        policy = load_hmcp_config()
        section = policy.get("hierarchical_chaining_policy")
        if not section:
            raise ChainingPolicyError("Missing 'hierarchical_chaining_policy' section in hmcp.json")

        depth = int(section.get("chaining_depth", 0))
        if depth <= 0:
            raise ChainingPolicyError("Chaining depth must be positive")

        levels = []
        for idx in range(1, depth + 1):
            key = f"level_{idx}"
            raw_level = section.get(key)
            if not raw_level:
                raise ChainingPolicyError(f"Missing definition for {key}")
            max_size = raw_level.get("max_size")
            if not max_size:
                raise ChainingPolicyError(f"Level {key} missing 'max_size'")

            level = ChainingLevel(
                index=idx,
                key=key,
                level_type=raw_level.get("type", "unknown"),
                example=raw_level.get("example", ""),
                max_parameters=_parse_parameter_budget(max_size),
                raw_max_size=max_size,
                can_spawn=bool(raw_level.get("can_spawn", False)),
            )
            levels.append(level)

        trigger_cfg = section.get("spawning_trigger", {})
        trigger = SpawnTrigger(
            condition=trigger_cfg.get("condition", "unspecified"),
            threshold=float(trigger_cfg.get("threshold", 1.0)),
            isolation_requirement=trigger_cfg.get("isolation_requirement", "unknown"),
        )
        return cls(levels, trigger=trigger, depth=depth)

    @property
    def depth(self) -> int:
        return self._depth

    @property
    def spawn_trigger(self) -> SpawnTrigger:
        return self._trigger

    def iter_levels(self) -> Iterable[ChainingLevel]:
        return iter(self._levels)

    def get_level(self, identifier: Union[int, str]) -> ChainingLevel:
        if isinstance(identifier, int):
            level = self._levels_by_index.get(identifier)
        else:
            level = self._levels_by_key.get(identifier)
        if not level:
            raise ChainingPolicyError(f"Unknown hierarchy level: {identifier}")
        return level

    def next_level(self, identifier: Union[int, str]) -> Optional[ChainingLevel]:
        current = self.get_level(identifier)
        return self._levels_by_index.get(current.index + 1)

    def validate_model_size(self, identifier: Union[int, str], parameter_count: NumberLike) -> None:
        """Ensure a specialist fits within the configured parameter budget."""

        level = self.get_level(identifier)
        params = int(parameter_count)
        if params > level.max_parameters:
            raise ChainingPolicyError(
                f"Specialist exceeds max size for {level.describe()}: "
                f"{params:,} params > allowed {level.max_parameters:,}"
            )

    def evaluate_spawn_request(
        self,
        identifier: Union[int, str],
        *,
        confidence: float,
        task_isolation_passed: bool,
        candidate_parameter_count: Optional[NumberLike] = None,
    ) -> SpawnDecision:
        """Evaluate whether the specialist at `identifier` can spawn a child."""

        reasons: list[str] = []
        allowed = True

        current = self.get_level(identifier)
        next_level = self.next_level(current.index)

        if not current.can_spawn:
            allowed = False
            reasons.append(f"{current.describe()} is not allowed to spawn child specialists")

        if not next_level:
            allowed = False
            reasons.append("Maximum chaining depth reached; no child level defined")

        if confidence < self._trigger.threshold:
            allowed = False
            reasons.append(
                f"Confidence {confidence:.2f} below spawn threshold {self._trigger.threshold:.2f}"
            )

        if not task_isolation_passed:
            allowed = False
            reasons.append(
                "Isolation requirement not satisfied: "
                f"{self._trigger.isolation_requirement}"
            )

        if candidate_parameter_count is not None and next_level is not None:
            params = int(candidate_parameter_count)
            if params > next_level.max_parameters:
                allowed = False
                reasons.append(
                    "Candidate exceeds child level max size "
                    f"({params:,} params > {next_level.max_parameters:,})"
                )

        if allowed:
            reasons.append(
                "All spawning requirements satisfied; proceed with specialist proposal"
            )

        return SpawnDecision(allowed=allowed, reasons=tuple(reasons), next_level=next_level)


def _parse_parameter_budget(raw_value: str) -> int:
    """Parse values like '200M_params' into an integer parameter count."""

    cleaned = raw_value.strip().lower().replace("_params", "").replace("params", "")
    if not cleaned:
        raise ChainingPolicyError("Empty parameter budget string")

    suffix_multiplier = {
        "k": 1_000,
        "m": 1_000_000,
        "b": 1_000_000_000,
        "t": 1_000_000_000_000,
    }

    unit = ""
    if cleaned[-1].isalpha():
        unit = cleaned[-1]
        cleaned = cleaned[:-1]

    try:
        value = float(cleaned)
    except ValueError as exc:
        raise ChainingPolicyError(
            f"Unable to parse parameter budget '{raw_value}'"
        ) from exc

    multiplier = suffix_multiplier.get(unit, 1)
    return int(value * multiplier)


__all__ = [
    "ChainingPolicyError",
    "ChainingLevel",
    "HierarchicalChainingPolicy",
    "SpawnDecision",
    "SpawnTrigger",
]
