"""Configuration utilities for MetaQore."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GovernanceMode(str, Enum):
    """Supported governance modes for MetaQore deployments."""

    STRICT = "strict"
    ADAPTIVE = "adaptive"
    PLAYGROUND = "playground"


class MetaQoreConfig(BaseSettings):
    """Global service configuration loaded from env vars or optional YAML file."""

    model_config = SettingsConfigDict(env_prefix="METAQORE_", case_sensitive=False)

    governance_mode: GovernanceMode = GovernanceMode.STRICT
    organization: str = Field(
        default="default",
        description="Organization or tenant identifier used for compliance logging.",
    )
    max_graph_depth: int = Field(default=3, ge=1, le=10)
    max_parallel_branches: int = Field(default=5, ge=1, le=20)
    max_conversation_turns: int = Field(default=10, ge=1, le=100)
    max_conversation_participants: int = Field(default=6, ge=1, le=32)
    storage_backend: str = Field(default="sqlite", description="sqlite | postgres | redis")
    storage_dsn: str = Field(default="sqlite:///metaqore.db")

    @field_validator("max_parallel_branches")
    @classmethod
    def _validate_parallel_branches(cls, value: int, info: ValidationInfo) -> int:  # noqa: D401
        governance_mode = (info.data or {}).get("governance_mode")
        if governance_mode == GovernanceMode.STRICT and value > 1:
            raise ValueError("STRICT mode allows max_parallel_branches <= 1")
        return value

    @classmethod
    def from_yaml(cls, path: str | Path, *, overrides: Optional[Dict[str, Any]] = None) -> "MetaQoreConfig":
        """Load configuration from a YAML file with optional overrides."""

        with Path(path).expanduser().open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        if overrides:
            data.update(overrides)
        return cls(**data)

    def as_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation of the config."""

        return self.model_dump()
