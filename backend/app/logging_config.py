"""Structured logging. Pipeline logs carry counts and durations, never manuscript text."""

from __future__ import annotations

import json
import logging
import sys
import time

logger = logging.getLogger("manuscript")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        payload.update(getattr(record, "extra_fields", {}))
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO", fmt: str = "json") -> None:
    handler = logging.StreamHandler(sys.stdout)
    if fmt == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())


def log_stage(
    event: str,
    document_id: str,
    stage: str = "",
    duration_ms: float | None = None,
    **counts: object,
) -> None:
    """Emit one structured line for a pipeline event. No document text, ever."""
    fields: dict[str, object] = {"event": event, "document_id": document_id}
    if stage:
        fields["stage"] = stage
    if duration_ms is not None:
        fields["duration_ms"] = round(duration_ms, 1)
    fields.update(counts)
    logger.info(event, extra={"extra_fields": fields})
