"""HTTP retry decorator powered by tenacity.

Provides ``http_retry`` — a pre-configured decorator for transient
network failures (timeouts, connection errors, HTTP 5xx).
"""

from __future__ import annotations

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from py_bcast._core.logging import get_logger

logger = get_logger(__name__)

_MAX_ATTEMPTS = 3
_WAIT_MIN = 1  # seconds
_WAIT_MAX = 4  # seconds


def _is_retryable(exc: BaseException) -> bool:
    """Return True if the exception warrants a retry."""
    if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500:
        return True
    return False


http_retry = retry(
    retry=retry_if_exception(_is_retryable),
    stop=stop_after_attempt(_MAX_ATTEMPTS),
    wait=wait_exponential(multiplier=1, min=_WAIT_MIN, max=_WAIT_MAX),
    before_sleep=before_sleep_log(logger, log_level=20),  # INFO
    reraise=True,
)
"""Decorator: retries on httpx timeout/network errors and HTTP 5xx.

Usage::

    from py_bcast._core.retry import http_retry

    @http_retry
    def my_http_call(...):
        ...
"""
