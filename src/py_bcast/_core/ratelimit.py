"""Token bucket rate limiter for py_bcast HTTP requests.

Prevents server overload by throttling outgoing requests to a
configurable rate (default: 10 requests/second).
"""

from __future__ import annotations

import asyncio
import threading
import time

from .config import get_settings
from .logging import get_logger

logger = get_logger(__name__)


class _TokenBucket:
    """Thread-safe token bucket rate limiter."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tokens: float = 0
        self._last_refill: float = 0
        self._initialized = False

    def _refill(self, max_tokens: int, period: float) -> None:
        now = time.time()
        if not self._initialized:
            self._tokens = max_tokens
            self._last_refill = now
            self._initialized = True
            return
        elapsed = now - self._last_refill
        new_tokens = elapsed * (max_tokens / period)
        self._tokens = min(max_tokens, self._tokens + new_tokens)
        self._last_refill = now

    def acquire(self) -> None:
        """Block until a token is available (sync)."""
        settings = get_settings()
        max_tokens = settings.rate_limit_calls
        period = settings.rate_limit_period

        while True:
            with self._lock:
                self._refill(max_tokens, period)
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                # Calculate wait time for next token
                wait = period / max_tokens
            time.sleep(wait)

    async def acquire_async(self) -> None:
        """Non-blocking wait until a token is available (async)."""
        settings = get_settings()
        max_tokens = settings.rate_limit_calls
        period = settings.rate_limit_period

        while True:
            with self._lock:
                self._refill(max_tokens, period)
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                wait = period / max_tokens
            await asyncio.sleep(wait)


# Module-level singleton
_limiter = _TokenBucket()


def rate_limit() -> None:
    """Acquire a rate limit token (blocking). Call before each HTTP request."""
    _limiter.acquire()


async def rate_limit_async() -> None:
    """Acquire a rate limit token (async). Call before each async HTTP request."""
    await _limiter.acquire_async()
