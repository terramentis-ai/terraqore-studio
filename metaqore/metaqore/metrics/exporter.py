"""Prometheus metrics exporter."""

from __future__ import annotations

from typing import Any, Dict

from metaqore.metrics.aggregator import get_metrics_aggregator


def generate_prometheus_metrics() -> str:
    """Generate Prometheus-formatted metrics."""
    aggregator = get_metrics_aggregator()
    lines = []

    # HELP and TYPE declarations
    lines.append("# HELP metaqore_events_total Total events by type")
    lines.append("# TYPE metaqore_events_total counter")

    # Counters
    for key, counter in aggregator.get_counters().items():
        tags = _format_prometheus_tags(counter.get("tags", {}))
        value = counter.get("value", 0)
        lines.append(f"metaqore_{key}{tags} {value}")

    lines.append("# HELP metaqore_connections_active Active WebSocket connections")
    lines.append("# TYPE metaqore_connections_active gauge")

    # Gauges
    for key, gauge in aggregator.get_gauges().items():
        tags = _format_prometheus_tags(gauge.get("tags", {}))
        value = gauge.get("value", 0)
        lines.append(f"metaqore_{key}{tags} {value}")

    lines.append("# HELP metaqore_latency_ms Latency histogram in milliseconds")
    lines.append("# TYPE metaqore_latency_ms histogram")

    # Histograms
    for key, histogram in aggregator.get_histograms().items():
        tags = _format_prometheus_tags(histogram.get("tags", {}))
        count = histogram.get("count", 0)
        total = sum([float(v) for v in histogram.get("values", [])])
        lines.append(f"metaqore_{key}_sum{tags} {total}")
        lines.append(f"metaqore_{key}_count{tags} {count}")

        for percentile in [50, 99, 99.9]:
            p_key = f"p{int(percentile * 10)}" if percentile != int(percentile) else f"p{int(percentile)}"
            p_value = histogram.get(f"p{int(percentile) if percentile == int(percentile) else percentile}", 0)
            if p_value is not None:
                lines.append(f"metaqore_{key}_{p_key}{tags} {p_value}")

    return "\n".join(lines) + "\n"


def _format_prometheus_tags(tags: Dict[str, Any]) -> str:
    """Format tags for Prometheus output."""
    if not tags:
        return ""
    tag_pairs = [f'{key}="{value}"' for key, value in tags.items()]
    return "{" + ",".join(tag_pairs) + "}"


__all__ = ["generate_prometheus_metrics"]
