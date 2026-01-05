"""Unit tests for SecureGateway routing and classification."""

from __future__ import annotations

from metaqore.core.security import (
    ProviderStatus,
    SecureGateway,
    TaskSensitivity,
    CompliancePolicy,
    resolve_routing_policy,
)


class _StubAuditor:
    def __init__(self) -> None:
        self.routing_events = []
        self.veto_events = []

    def log_routing_decision(self, payload):
        self.routing_events.append(payload)

    def log_veto_event(self, veto, context=None):
        self.veto_events.append((veto, context))


def test_classify_task_uses_priority_hints() -> None:
    gateway = SecureGateway(auditor=_StubAuditor())

    sensitive_security = gateway.classify_task(
        agent_name="SecurityAgent",
        task_type="penetration testing",
        is_security_task=True,
    )
    assert sensitive_security == TaskSensitivity.SENSITIVE

    critical_security = gateway.classify_task(
        agent_name="SecurityAgent",
        task_type="penetration testing",
        is_security_task=True,
        has_sensitive_data=True,
    )
    assert critical_security == TaskSensitivity.CRITICAL

    validator = gateway.classify_task(agent_name="CodeValidator", task_type="review", has_sensitive_data=False)
    assert validator == TaskSensitivity.INTERNAL

    planner = gateway.classify_task(agent_name="PlannerAgent", task_type="governance plan")
    assert planner == TaskSensitivity.INTERNAL

    public = gateway.classify_task(agent_name="CoderAgent", task_type="implement feature")
    assert public == TaskSensitivity.PUBLIC


def test_enforce_policy_disallows_wrong_provider_and_logs_veto() -> None:
    auditor = _StubAuditor()
    gateway = SecureGateway(auditor=auditor)

    allowed = gateway.enforce_policy(
        agent_name="PlannerAgent",
        task_type="plan",
        provider="openrouter",
        has_sensitive_data=True,
    )
    assert allowed is False
    assert len(auditor.veto_events) == 1

    veto, context = auditor.veto_events[0]
    assert "disallowed" in veto.reason
    assert context["provider"] == "openrouter"

    conv_veto = gateway.veto_conversation_message("summary")
    assert conv_veto is not None
    assert conv_veto.details["message"] == "summary"


def test_enforce_policy_allows_available_provider_and_logs_routing() -> None:
    auditor = _StubAuditor()
    gateway = SecureGateway(auditor=auditor)
    gateway.register_provider_status("ollama", available=True, latency_ms=5.0)

    allowed = gateway.enforce_policy(
        agent_name="CoderAgent",
        task_type="implement feature",
        provider="ollama",
    )
    assert allowed is True
    assert len(auditor.routing_events) >= 1

    last_event = auditor.routing_events[-1]
    assert last_event["provider"] == "ollama"
    assert last_event["reason"] == "allowed"


def test_get_recommended_provider_falls_back_to_available_option() -> None:
    auditor = _StubAuditor()
    gateway = SecureGateway(auditor=auditor)
    gateway.provider_status["ollama"] = ProviderStatus(available=False)
    gateway.provider_status["openrouter"] = ProviderStatus(available=True)

    recommended = gateway.get_recommended_provider(TaskSensitivity.PUBLIC)
    assert recommended == "hmcp_gateway"
    assert auditor.routing_events[-1]["reason"] == "auto_recommendation"


def test_resolve_routing_policy_accepts_aliases() -> None:
    policy = resolve_routing_policy("compliance")
    assert isinstance(policy, CompliancePolicy)

    default_policy = resolve_routing_policy(None)
    assert default_policy.name == "default_local_first"
