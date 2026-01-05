"""Compliance audit logging utilities for MetaQore."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from metaqore.core.models import VetoReason
from metaqore.streaming.events import Event, EventType
from metaqore.streaming.hub import get_event_hub
from metaqore.logger import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class AuditEvent:
    """Represents a single compliance event stored in JSONL format."""

    timestamp: str
    event_type: str
    organization: str
    payload: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "organization": self.organization,
            "payload": self.payload,
        }


class ComplianceAuditor:
    """Persist routing/veto events and generate compliance reports."""

    def __init__(
        self,
        *,
        organization: str = "default",
        log_dir: Optional[Path] = None,
        flush_interval: int = 10,
    ) -> None:
        self.organization = organization
        self.flush_interval = max(1, flush_interval)
        base_dir = log_dir or (Path(__file__).resolve().parents[2] / "logs")
        base_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = base_dir / f"compliance_audit_{organization}.jsonl"
        self._buffer: List[AuditEvent] = []

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------
    def log_routing_decision(self, decision: Dict[str, Any]) -> None:
        """Record a routing decision emitted by SecureGateway."""

        event = self._build_event("routing_decision", decision)
        self._buffer_event(event)
        self._emit_streaming_event("compliance.routing_decision", decision)

    def log_veto_event(self, veto: VetoReason, context: Optional[Dict[str, Any]] = None) -> None:
        """Record a veto event (policy enforcement failure)."""

        payload: Dict[str, Any] = {"veto": veto.model_dump()}
        if context:
            payload.update(context)
        event = self._build_event("veto", payload)
        self._buffer_event(event)
        self._emit_streaming_event("compliance.veto", payload)

    def flush(self) -> None:
        """Write any buffered events to disk."""

        if not self._buffer:
            return
        try:
            with self.log_file.open("a", encoding="utf-8") as handle:
                for event in self._buffer:
                    handle.write(json.dumps(event.to_dict(), default=self._default_serializer) + "\n")
            logger.debug("Flushed %s audit events to %s", len(self._buffer), self.log_file)
        finally:
            self._buffer.clear()

    def close(self) -> None:
        """Flush outstanding events; safe to call multiple times."""

        self.flush()

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def get_audit_trail(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Return all audit events filtered by the supplied criteria."""

        self.flush()
        events = self._load_events()
        if not filters:
            return events

        def _matches(event: Dict[str, Any]) -> bool:
            return all(
                event.get(key) == value or event.get("payload", {}).get(key) == value
                for key, value in filters.items()
            )

        return [event for event in events if _matches(event)]

    def get_compliance_report(self, organization: Optional[str] = None) -> Dict[str, Any]:
        """Aggregate audit events into a simple compliance summary."""

        org = organization or self.organization
        events = self.get_audit_trail({"organization": org})
        total = len(events)
        by_event: Dict[str, int] = {}
        by_provider: Dict[str, int] = {}
        policy_violations: Dict[str, int] = {}

        for event in events:
            event_type = event.get("event_type", "unknown")
            by_event[event_type] = by_event.get(event_type, 0) + 1
            payload = event.get("payload", {})
            provider = payload.get("provider")
            if provider:
                by_provider[provider] = by_provider.get(provider, 0) + 1
            policy = payload.get("veto", {}).get("policy_violated")
            if policy:
                policy_violations[policy] = policy_violations.get(policy, 0) + 1

        return {
            "organization": org,
            "total_events": total,
            "by_event": by_event,
            "by_provider": by_provider,
            "policy_violations": policy_violations,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _buffer_event(self, event: AuditEvent) -> None:
        self._buffer.append(event)
        if len(self._buffer) >= self.flush_interval:
            self.flush()

    def _build_event(self, event_type: str, payload: Dict[str, Any]) -> AuditEvent:
        timestamp = datetime.now(timezone.utc).isoformat()
        return AuditEvent(
            timestamp=timestamp,
            event_type=event_type,
            organization=self.organization,
            payload=payload,
        )

    def _load_events(self) -> List[Dict[str, Any]]:
        if not self.log_file.exists():
            return []
        events: List[Dict[str, Any]] = []
        with self.log_file.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning("Skipping corrupted audit line")
        return events

    @staticmethod
    def _default_serializer(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def __enter__(self) -> "ComplianceAuditor":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _emit_streaming_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Mirror compliance events to the streaming layer."""

        try:
            # Map string event type to EventType enum if possible
            try:
                evt_type = EventType(event_type)
            except ValueError:
                # Fallback: create custom event type string
                evt_type = event_type  # type: ignore
            
            event = Event(
                event_type=evt_type,
                changes=payload,
                metadata={"organization": self.organization}
            )
            get_event_hub().emit(event)
        except Exception:  # pragma: no cover - streaming is best-effort
            logger.debug("Failed to emit streaming event", exc_info=True)


def generate_compliance_report(
    organization: str = "default",
    log_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Return the compliance report for an organization in one call."""

    resolved_dir = Path(log_dir).expanduser().resolve() if log_dir else None
    auditor = ComplianceAuditor(organization=organization, log_dir=resolved_dir)
    try:
        return auditor.get_compliance_report(organization)
    finally:
        auditor.close()


def format_compliance_report(report: Dict[str, Any]) -> str:
    """Format a compliance report dictionary into a readable string."""

    organization = report.get("organization", "unknown")
    header = f"Compliance Report :: {organization}"
    divider = "=" * len(header)
    lines = [header, divider, f"Total Events: {report.get('total_events', 0)}", ""]

    def _append_section(title: str, data: Dict[str, int]) -> None:
        lines.append(title)
        if not data:
            lines.append("  (none)")
        else:
            for key, value in sorted(data.items(), key=lambda item: (-item[1], item[0])):
                lines.append(f"  - {key}: {value}")
        lines.append("")

    _append_section("Events by Type", report.get("by_event", {}))
    _append_section("Events by Provider", report.get("by_provider", {}))
    _append_section("Policy Violations", report.get("policy_violations", {}))

    return "\n".join(lines).rstrip()


__all__ = [
    "ComplianceAuditor",
    "AuditEvent",
    "generate_compliance_report",
    "format_compliance_report",
]
