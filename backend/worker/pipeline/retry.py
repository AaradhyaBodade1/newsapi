"""Small retry-with-backoff helper used for every outbound network call
(RSS fetch, Groq/Gemini, Unsplash, image upload) so transient failures don't
fail a whole cycle or a whole article."""
from __future__ import annotations

import logging
import time
from typing import Callable, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


def call_with_retry(
    fn: Callable[[], T],
    *,
    max_attempts: int = 3,
    backoff_base_seconds: float = 1.5,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    context: str = "",
) -> T:
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except retryable_exceptions as exc:  # noqa: PERF203 - retry loop is intentional
            last_exc = exc
            logger.warning(
                "Attempt %s/%s failed for %s: %s",
                attempt,
                max_attempts,
                context or fn.__name__,
                exc,
            )
            if attempt < max_attempts:
                time.sleep(backoff_base_seconds * (2 ** (attempt - 1)))
    assert last_exc is not None
    raise last_exc
