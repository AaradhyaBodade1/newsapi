"""Dev/debug entrypoint: runs a single ingest -> generate -> publish cycle
and exits, without starting the full FastAPI server. Useful for forcing a
cycle immediately during local development instead of waiting for the
in-process scheduler's next interval (see app/main.py, which is what runs
this automatically and continuously in production).
"""
from __future__ import annotations

import sys

from common.logging_config import configure_logging
from worker.pipeline.orchestrator import run_cycle


def main() -> int:
    logger = configure_logging("worker")
    try:
        result = run_cycle()
    except Exception:
        logger.exception("Worker cycle crashed unexpectedly")
        return 1
    return 0 if result["errors_count"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
