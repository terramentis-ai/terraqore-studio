"""Tests for MetaQore configuration helpers."""

from __future__ import annotations

from metaqore.config import MetaQoreConfig


def test_secure_gateway_policy_normalizes_aliases() -> None:
    config = MetaQoreConfig(secure_gateway_policy="Compliance", max_parallel_branches=1)

    assert config.secure_gateway_policy == "compliance_local_only"
