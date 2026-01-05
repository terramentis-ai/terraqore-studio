"""Utilities for loading the HMCP policy configuration."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

HMCP_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "hmcp.json"


class HMCPConfigError(RuntimeError):
    """Raised when the HMCP policy configuration cannot be loaded."""


@lru_cache(maxsize=1)
def load_hmcp_config(path: str | Path | None = None) -> Dict[str, Any]:
    """Load and cache the HMCP configuration dictionary."""

    target = Path(path).expanduser().resolve() if path else HMCP_CONFIG_PATH
    if not target.exists():
        raise HMCPConfigError(f"HMCP policy file not found at {target}")

    with target.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    policy = data.get("gated_chaining_protocol")
    if not policy:
        raise HMCPConfigError("Invalid HMCP policy file: missing 'gated_chaining_protocol' section")
    return policy


__all__ = ["load_hmcp_config", "HMCPConfigError", "HMCP_CONFIG_PATH"]
