"""Logging utilities for MetaQore.

Provides a single entry point to obtain structured loggers that include
correlation and governance context in every message.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

_DEFAULT_LOG_LEVEL = os.environ.get("METAQORE_LOG_LEVEL", "INFO").upper()
_LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | "
    "project=%(project_id)s | agent=%(agent)s | message=%(message)s"
)


class _ContextFilter(logging.Filter):
    """Injects default values for contextual fields if missing."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401 (short method)
        if not hasattr(record, "project_id"):
            record.project_id = "-"
        if not hasattr(record, "agent"):
            record.agent = "-"
        return True


def configure_logging(level: str | None = None) -> None:
    """Configure root logging handlers once.

    Parameters
    ----------
    level:
        Optional log level override (e.g., "DEBUG"). Defaults to the value from
        ``METAQORE_LOG_LEVEL`` or ``INFO`` if not provided.
    """

    logging.basicConfig(level=getattr(logging, (level or _DEFAULT_LOG_LEVEL), logging.INFO), format=_LOG_FORMAT)
    logging.getLogger().addFilter(_ContextFilter())


def get_logger(name: str) -> logging.Logger:
    """Return a module-specific logger with context filter attached."""

    logger = logging.getLogger(name)
    if not any(isinstance(f, _ContextFilter) for f in logger.filters):
        logger.addFilter(_ContextFilter())
    return logger


def log_with_context(logger: logging.Logger, level: int, message: str, **context: Dict[str, Any]) -> None:
    """Helper to emit a structured log message with additional context fields."""

    extra = {"project_id": context.get("project_id", "-"), "agent": context.get("agent", "-")}
    logger.log(level, message, extra=extra)
