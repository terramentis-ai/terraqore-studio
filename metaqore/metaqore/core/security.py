"""Security-aware routing policies for MetaQore."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Type

from metaqore.core.models import ConflictSeverity, VetoReason
from metaqore.core.audit import ComplianceAuditor


class TaskSensitivity(str, Enum):
    """Sensitivity scale that guides routing and enforcement decisions."""

    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"
    CRITICAL = "critical"


@dataclass
class ProviderStatus:
    """Represents health/availability metadata for a provider."""

    available: bool = True
    latency_ms: Optional[float] = None
    capacity_score: Optional[float] = None


class RoutingPolicy(ABC):
    """Abstract routing policy that maps sensitivities to allowed providers."""

    name: str = "base"
    default_priority: List[str] = ("ollama", "openrouter")

    @abstractmethod
    def get_allowed_providers(self, sensitivity: TaskSensitivity) -> List[str]:
        """Return providers allowed for the supplied sensitivity level."""

    def get_recommended_provider(
        self,
        sensitivity: TaskSensitivity,
        provider_status: Dict[str, ProviderStatus],
    ) -> Optional[str]:
        """Pick the highest-priority provider that is presently available."""

        for provider in self.get_allowed_providers(sensitivity):
            status = provider_status.get(provider)
            if status is None or status.available:
                return provider
        return None


LOCAL_PROVIDERS: tuple[str, ...] = ("hmcp_gateway", "ollama")
LOCAL_AND_CLOUD_PROVIDERS: tuple[str, ...] = LOCAL_PROVIDERS + ("openrouter",)


class DefaultRoutingPolicy(RoutingPolicy):
    """Local-first routing with cloud fallback for non-sensitive work."""

    name = "default_local_first"
    default_priority = LOCAL_AND_CLOUD_PROVIDERS

    def get_allowed_providers(self, sensitivity: TaskSensitivity) -> List[str]:
        if sensitivity in (TaskSensitivity.CRITICAL, TaskSensitivity.SENSITIVE):
            return list(LOCAL_PROVIDERS)
        return list(LOCAL_AND_CLOUD_PROVIDERS)


class EnterpriseRoutingPolicy(RoutingPolicy):
    """Enterprise data-residency policy that locks all internal work to local providers."""

    name = "enterprise_residency"
    default_priority = LOCAL_AND_CLOUD_PROVIDERS

    def get_allowed_providers(self, sensitivity: TaskSensitivity) -> List[str]:
        if sensitivity == TaskSensitivity.PUBLIC:
            return list(LOCAL_AND_CLOUD_PROVIDERS)
        return list(LOCAL_PROVIDERS)


class CompliancePolicy(RoutingPolicy):
    """Strict compliance policy that forces all work through local providers."""

    name = "compliance_local_only"
    default_priority = LOCAL_PROVIDERS

    def get_allowed_providers(self, sensitivity: TaskSensitivity) -> List[str]:
        _ = sensitivity  # sensitivity does not impact selection for this policy
        return list(LOCAL_PROVIDERS)


class SecureGateway:
    """Security-first gateway that classifies tasks and enforces routing policies."""

    def __init__(
        self,
        *,
        policy: Optional[RoutingPolicy] = None,
        provider_status: Optional[Dict[str, ProviderStatus]] = None,
        auditor: Optional[ComplianceAuditor] = None,
        organization: str = "default",
    ) -> None:
        self.policy = policy or DefaultRoutingPolicy()
        priority = list(dict.fromkeys(self.policy.default_priority))
        self.provider_status: Dict[str, ProviderStatus] = provider_status or {
            provider: ProviderStatus() for provider in priority
        }
        self._last_veto: Optional[VetoReason] = None
        self.auditor = auditor or ComplianceAuditor(organization=organization)

    # ------------------------------------------------------------------
    # Classification & routing helpers
    # ------------------------------------------------------------------
    def classify_task(
        self,
        *,
        agent_name: str,
        task_type: str,
        has_private_data: bool = False,
        has_sensitive_data: bool = False,
        is_security_task: bool = False,
    ) -> TaskSensitivity:
        """Classify task sensitivity using task metadata heuristics."""

        task_type_lower = task_type.lower()
        agent_lower = agent_name.lower()

        if is_security_task:
            return TaskSensitivity.CRITICAL if has_sensitive_data else TaskSensitivity.SENSITIVE
        if has_sensitive_data or has_private_data:
            return TaskSensitivity.SENSITIVE
        if any(keyword in task_type_lower for keyword in ("plan", "state", "governance")):
            return TaskSensitivity.INTERNAL
        if agent_lower.endswith("validator") or "validator" in agent_lower:
            return TaskSensitivity.INTERNAL
        return TaskSensitivity.PUBLIC

    def get_allowed_providers(self, sensitivity: TaskSensitivity) -> List[str]:
        """Return policy-compliant providers for the supplied sensitivity level."""

        return self.policy.get_allowed_providers(sensitivity)

    def get_recommended_provider(self, sensitivity: TaskSensitivity) -> Optional[str]:
        """Return the best currently-available provider for the sensitivity level."""

        provider = self.policy.get_recommended_provider(sensitivity, self.provider_status)
        self._log_routing_decision(
            agent_name="auto",
            task_type="recommendation",
            sensitivity=sensitivity,
            provider=provider,
            reason="auto_recommendation",
        )
        return provider

    def register_provider_status(
        self,
        provider: str,
        *,
        available: bool,
        latency_ms: Optional[float] = None,
        capacity_score: Optional[float] = None,
    ) -> None:
        """Update (or register) health metadata for a provider."""

        self.provider_status[provider] = ProviderStatus(
            available=available,
            latency_ms=latency_ms,
            capacity_score=capacity_score,
        )

    def enforce_policy(
        self,
        *,
        agent_name: str,
        task_type: str,
        provider: str,
        has_private_data: bool = False,
        has_sensitive_data: bool = False,
        is_security_task: bool = False,
    ) -> bool:
        """Ensure the selected provider complies with routing policy."""

        sensitivity = self.classify_task(
            agent_name=agent_name,
            task_type=task_type,
            has_private_data=has_private_data,
            has_sensitive_data=has_sensitive_data,
            is_security_task=is_security_task,
        )
        allowed = self.get_allowed_providers(sensitivity)
        status = self.provider_status.get(provider, ProviderStatus())

        if provider not in allowed:
            self._last_veto = self._build_veto(
                reason=f"Provider '{provider}' disallowed for {sensitivity.value} tasks",
                policy=self.policy.name,
            )
            self._log_veto(agent_name, task_type, provider, sensitivity)
            return False
        if not status.available:
            self._last_veto = self._build_veto(
                reason=f"Provider '{provider}' unavailable",
                policy=self.policy.name,
            )
            self._log_veto(agent_name, task_type, provider, sensitivity)
            return False

        self._last_veto = None
        self._log_routing_decision(
            agent_name=agent_name,
            task_type=task_type,
            sensitivity=sensitivity,
            provider=provider,
            reason="allowed",
        )
        return True

    # ------------------------------------------------------------------
    # Veto helpers (stubs for downstream integrations)
    # ------------------------------------------------------------------
    def veto_graph_node(self, description: str) -> Optional[VetoReason]:
        """Return the last veto, optionally annotating it with extra context."""

        if self._last_veto is None:
            return None
        return VetoReason(
            reason=f"{self._last_veto.reason} :: {description}",
            policy_violated=self._last_veto.policy_violated,
            severity=self._last_veto.severity,
            details=self._last_veto.details,
        )

    def veto_conversation_message(self, message_summary: str) -> Optional[VetoReason]:
        """Expose veto information for conversation-level enforcement."""

        if self._last_veto is None:
            return None
        details = dict(self._last_veto.details)
        details["message"] = message_summary
        return VetoReason(
            reason=self._last_veto.reason,
            policy_violated=self._last_veto.policy_violated,
            severity=self._last_veto.severity,
            details=details,
        )

    def veto_state_transition(self, transition: str) -> Optional[VetoReason]:
        """Expose veto information for workflow state transitions."""

        if self._last_veto is None:
            return None
        details = dict(self._last_veto.details)
        details["transition"] = transition
        return VetoReason(
            reason=self._last_veto.reason,
            policy_violated=self._last_veto.policy_violated,
            severity=self._last_veto.severity,
            details=details,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @staticmethod
    def _build_veto(*, reason: str, policy: str) -> VetoReason:
        return VetoReason(
            reason=reason,
            policy_violated=policy,
            severity=ConflictSeverity.CRITICAL,
            details={"policy": policy},
        )

    def _log_routing_decision(
        self,
        *,
        agent_name: str,
        task_type: str,
        sensitivity: TaskSensitivity,
        provider: Optional[str],
        reason: str,
    ) -> None:
        if provider is None:
            return
        payload = {
            "agent_name": agent_name,
            "task_type": task_type,
            "sensitivity": sensitivity.value,
            "provider": provider,
            "policy": self.policy.name,
            "reason": reason,
        }
        self.auditor.log_routing_decision(payload)

    def _log_veto(
        self,
        agent_name: str,
        task_type: str,
        provider: str,
        sensitivity: TaskSensitivity,
    ) -> None:
        if self._last_veto is None:
            return
        context = {
            "agent_name": agent_name,
            "task_type": task_type,
            "sensitivity": sensitivity.value,
            "provider": provider,
        }
        self.auditor.log_veto_event(self._last_veto, context)


POLICY_REGISTRY = {
    DefaultRoutingPolicy.name: DefaultRoutingPolicy,
    EnterpriseRoutingPolicy.name: EnterpriseRoutingPolicy,
    CompliancePolicy.name: CompliancePolicy,
}

POLICY_ALIASES = {
    "default": DefaultRoutingPolicy.name,
    "local_first": DefaultRoutingPolicy.name,
    "default_local_first": DefaultRoutingPolicy.name,
    "enterprise": EnterpriseRoutingPolicy.name,
    "residency": EnterpriseRoutingPolicy.name,
    "enterprise_residency": EnterpriseRoutingPolicy.name,
    "compliance": CompliancePolicy.name,
    "local_only": CompliancePolicy.name,
    "compliance_local_only": CompliancePolicy.name,
}


def _normalize_policy_key(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def resolve_routing_policy(policy: Optional[str | RoutingPolicy]) -> RoutingPolicy:
    """Return a RoutingPolicy instance given a canonical name or alias."""

    if isinstance(policy, RoutingPolicy):
        return policy
    if policy is None:
        return DefaultRoutingPolicy()

    normalized = _normalize_policy_key(policy)
    canonical = POLICY_ALIASES.get(normalized, normalized)
    policy_cls = POLICY_REGISTRY.get(canonical)
    if policy_cls is None:
        known = ", ".join(sorted(POLICY_REGISTRY.keys()))
        raise ValueError(f"Unknown secure gateway policy '{policy}'. Known policies: {known}")
    return policy_cls()


__all__ = [
    "TaskSensitivity",
    "ProviderStatus",
    "RoutingPolicy",
    "DefaultRoutingPolicy",
    "EnterpriseRoutingPolicy",
    "CompliancePolicy",
    "SecureGateway",
    "resolve_routing_policy",
    "POLICY_REGISTRY",
]
