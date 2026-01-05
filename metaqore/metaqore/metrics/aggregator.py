"""Metrics aggregation and collection for observability."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from metaqore.streaming.events import Event, EventType


@dataclass
class MetricCounter:
    """Counter metric with timestamps."""

    name: str
    value: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = field(default_factory=dict)

    def increment(self, amount: int = 1) -> None:
        """Increment counter."""
        self.value += amount
        self.last_updated = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "last_updated": self.last_updated.isoformat(),
            "tags": self.tags,
        }


@dataclass
class MetricGauge:
    """Gauge metric (current value)."""

    name: str
    value: float = 0.0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = field(default_factory=dict)

    def set(self, value: float) -> None:
        """Set gauge value."""
        self.value = value
        self.last_updated = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "last_updated": self.last_updated.isoformat(),
            "tags": self.tags,
        }


@dataclass
class MetricHistogram:
    """Histogram metric for latency tracking."""

    name: str
    values: list[float] = field(default_factory=list)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = field(default_factory=dict)

    def record(self, value: float) -> None:
        """Record a value."""
        self.values.append(value)
        self.last_updated = datetime.now(timezone.utc)

    def percentile(self, p: float) -> Optional[float]:
        """Calculate percentile (0-100)."""
        if not self.values:
            return None
        sorted_values = sorted(self.values)
        index = int(len(sorted_values) * (p / 100))
        return sorted_values[min(index, len(sorted_values) - 1)]

    def to_dict(self) -> Dict[str, Any]:
        p50 = self.percentile(50)
        p99 = self.percentile(99)
        p999 = self.percentile(99.9)
        return {
            "name": self.name,
            "count": len(self.values),
            "min": min(self.values) if self.values else None,
            "max": max(self.values) if self.values else None,
            "p50": p50,
            "p99": p99,
            "p999": p999,
            "last_updated": self.last_updated.isoformat(),
            "tags": self.tags,
        }


class MetricsAggregator:
    """Aggregates metrics from events and LLM calls."""

    def __init__(self) -> None:
        self._counters: Dict[str, MetricCounter] = {}
        self._gauges: Dict[str, MetricGauge] = {}
        self._histograms: Dict[str, MetricHistogram] = {}

    def record_event(self, event: Event) -> None:
        """Record metrics from an event."""
        # Count by event type
        counter_key = f"events_{event.event_type.value}"
        if counter_key not in self._counters:
            self._counters[counter_key] = MetricCounter(
                name=counter_key,
                tags={"event_type": event.event_type.value},
            )
        self._counters[counter_key].increment()

        # Count by severity
        severity_key = f"events_severity_{event.severity}"
        if severity_key not in self._counters:
            self._counters[severity_key] = MetricCounter(
                name=severity_key,
                tags={"severity": event.severity},
            )
        self._counters[severity_key].increment()

        # Extract mock LLM metadata if present
        if "llm_metadata" in event.metadata:
            llm_meta = event.metadata["llm_metadata"]
            if "latency_ms" in llm_meta:
                latency_key = f"llm_latency_{llm_meta.get('provider', 'unknown')}"
                if latency_key not in self._histograms:
                    self._histograms[latency_key] = MetricHistogram(
                        name=latency_key,
                        tags={"provider": llm_meta.get("provider", "unknown")},
                    )
                self._histograms[latency_key].record(float(llm_meta["latency_ms"]))

            if "scenario_tag" in llm_meta:
                scenario_key = f"mock_llm_scenarios_{llm_meta['scenario_tag']}"
                if scenario_key not in self._counters:
                    self._counters[scenario_key] = MetricCounter(
                        name=scenario_key,
                        tags={"scenario": llm_meta["scenario_tag"]},
                    )
                self._counters[scenario_key].increment()

    def record_api_latency(self, endpoint: str, latency_ms: float) -> None:
        """Record API endpoint latency."""
        key = f"api_latency_{endpoint}"
        if key not in self._histograms:
            self._histograms[key] = MetricHistogram(
                name=key,
                tags={"endpoint": endpoint},
            )
        self._histograms[key].record(latency_ms)

    def record_conflict_detection(self, project_id: str, conflict_count: int) -> None:
        """Record conflict detection metrics."""
        key = f"conflicts_detected_{project_id}"
        if key not in self._counters:
            self._counters[key] = MetricCounter(
                name=key,
                tags={"project_id": project_id},
            )
        self._counters[key].increment(conflict_count)

    def set_active_connections(self, count: int) -> None:
        """Set gauge for active WebSocket connections."""
        key = "websocket_connections_active"
        if key not in self._gauges:
            self._gauges[key] = MetricGauge(name=key)
        self._gauges[key].set(float(count))

    def get_counters(self) -> Dict[str, Dict[str, Any]]:
        """Return all counters as dict."""
        return {key: counter.to_dict() for key, counter in self._counters.items()}

    def get_gauges(self) -> Dict[str, Dict[str, Any]]:
        """Return all gauges as dict."""
        return {key: gauge.to_dict() for key, gauge in self._gauges.items()}

    def get_histograms(self) -> Dict[str, Dict[str, Any]]:
        """Return all histograms as dict."""
        return {key: histogram.to_dict() for key, histogram in self._histograms.items()}

    def get_all_metrics(self) -> Dict[str, Any]:
        """Return all metrics in a structured format."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "counters": self.get_counters(),
            "gauges": self.get_gauges(),
            "histograms": self.get_histograms(),
        }

    def reset(self) -> None:
        """Clear all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()


# Global aggregator instance
_aggregator: Optional[MetricsAggregator] = None


def get_metrics_aggregator() -> MetricsAggregator:
    """Get the global metrics aggregator."""
    global _aggregator
    if _aggregator is None:
        _aggregator = MetricsAggregator()
    return _aggregator


__all__ = ["MetricsAggregator", "MetricCounter", "MetricGauge", "MetricHistogram", "get_metrics_aggregator"]
