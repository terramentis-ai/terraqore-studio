"""Tests for compliance auditing helpers."""

from __future__ import annotations

from metaqore.core.audit import (
    ComplianceAuditor,
    format_compliance_report,
    generate_compliance_report,
)
from metaqore.core.models import ConflictSeverity, VetoReason


def test_generate_compliance_report_counts_events(tmp_path) -> None:
    auditor = ComplianceAuditor(organization="acme", log_dir=tmp_path, flush_interval=1)
    auditor.log_routing_decision(
        {
            "agent_name": "PlannerAgent",
            "task_type": "planning",
            "sensitivity": "internal",
            "provider": "ollama",
            "policy": "default_local_first",
            "reason": "allowed",
        }
    )
    auditor.log_veto_event(
        VetoReason(
            reason="Provider unavailable",
            policy_violated="default_local_first",
            severity=ConflictSeverity.CRITICAL,
            details={"provider": "openrouter"},
        ),
        {"provider": "openrouter"},
    )
    auditor.close()

    report = generate_compliance_report("acme", tmp_path)
    assert report["organization"] == "acme"
    assert report["total_events"] == 2
    assert report["by_event"]["routing_decision"] == 1
    assert report["by_event"]["veto"] == 1
    assert report["by_provider"]["ollama"] == 1
    assert report["policy_violations"]["default_local_first"] == 1


def test_format_compliance_report_outputs_sorted_sections(tmp_path) -> None:
    report = {
        "organization": "acme",
        "total_events": 3,
        "by_event": {"veto": 2, "routing_decision": 1},
        "by_provider": {"openrouter": 2, "ollama": 1},
        "policy_violations": {"default_local_first": 2},
    }

    formatted = format_compliance_report(report)

    assert "Compliance Report :: acme" in formatted
    assert "Total Events: 3" in formatted
    assert "- veto: 2" in formatted
    assert "- routing_decision: 1" in formatted
    assert "- openrouter: 2" in formatted
    assert formatted.endswith("- default_local_first: 2")
