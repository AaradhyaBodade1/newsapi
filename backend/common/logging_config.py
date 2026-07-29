"""Structured JSON logging shared by the backend and worker.

Platform log aggregators (Render/Railway/GitHub Actions) capture stdout, so
a JSON-per-line format keeps logs greppable/queryable without extra infra.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        extra = getattr(record, "extra_fields", None)
        if extra:
            payload.update(extra)
        return json.dumps(payload, default=str)


def configure_logging(service_name: str) -> logging.Logger:
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    return logging.getLogger(service_name)


def log_extra(**fields) -> dict:
    """Usage: logger.info("message", extra=log_extra(article_id=..., source="rss"))"""
    return {"extra_fields": fields}
