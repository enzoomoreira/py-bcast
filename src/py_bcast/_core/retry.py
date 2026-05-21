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

from py_bcast._core.config import get_settings
from py_bcast._core.logging import get_logger

logger = get_logger(__name__)


def _is_retryable(exc: BaseException) -> bool:
    """Return True if the exception warrants a retry."""
    if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500:
        return True
    return False


def _make_retry():
    """Build the retry decorator reading current settings."""
    settings = get_settings()
    return retry(
        retry=retry_if_exception(_is_retryable),
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(
            multiplier=1,
            min=settings.retry_wait_min,
            max=settings.retry_wait_max,
        ),
        before_sleep=before_sleep_log(logger, log_level=20),  # INFO
        reraise=True,
    )


# Default instance — reads settings at import time.
# Functions decorated with this get the settings active at decoration time.
http_retry = _make_retry()
"""Decorator: retries on httpx timeout/network errors and HTTP 5xx.

Usage::

    from py_bcast._core.retry import http_retry

    @http_retry
    def my_http_call(...):
        ...
"""
