"""
MetaQore Adversarial Testing Package

This package contains the adversarial test harness for validating MetaQore's
SecureGateway and PSMP conflict detection resilience.
"""

from .client import AdversarialMockLLMClient
from .harness import AdversarialTestHarness
from .scenarios import ScenarioRegistry

__all__ = ["AdversarialMockLLMClient", "AdversarialTestHarness", "ScenarioRegistry"]
