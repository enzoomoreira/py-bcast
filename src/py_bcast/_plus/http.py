"""HTTP client and request helper for the Broadcast+ REST API.

Provides:
- ``get_plus_http_client()`` — singleton httpx.Client for svc.aebroadcast.com.br
- ``plus_auth_headers()`` — builds Authorization + x-version headers
- ``plus_request()`` — authenticated request with automatic 401 token refresh
"""

from __future__ import annotations

import httpx

from .._core.constants import PLUS_BASE_URL, plus_base_headers
from .._core.exceptions import BroadcastPlusAuthError
from .._core.logging import get_logger
from .._core.retry import http_retry
from .session import get_plus_token, refresh_plus_token

logger = get_logger(__name__)

_plus_client: httpx.Client | None = None


def get_plus_http_client() -> httpx.Client:
    """Return the singleton httpx.Client for the Broadcast+ API.

    Separate from the legacy ContentProxy client — different base URL,
    different TLS behavior, different connection pool.
    """
    global _plus_client
    if _plus_client is None or _plus_client.is_closed:
        _plus_client = httpx.Client(
            base_url=PLUS_BASE_URL,
            verify=False,
            trust_env=False,
            timeout=30,
        )
    return _plus_client


def close_plus_client() -> None:
    """Close the singleton Plus HTTP client. Used for cleanup/testing."""
    global _plus_client
    if _plus_client and not _plus_client.is_closed:
        _plus_client.close()
    _plus_client = None


def plus_auth_headers() -> dict[str, str]:
    """Build Authorization + versioning headers for an authenticated Plus call."""
    token = get_plus_token()
    return {**plus_base_headers(), "Authorization": f"Bearer {token}"}


def plus_request(method: str, path: str, **kwargs) -> httpx.Response:
    """Make an authenticated request to the Broadcast+ API.

    Handles JWT injection, automatic token refresh on 401, and HTTP retry
    on transient 5xx / network errors (via ``@http_retry``).

    Args:
        method: ``"get"`` or ``"post"``.
        path: API path relative to PLUS_BASE_URL (e.g. ``"/stock/v1/quote/symbol"``).
        **kwargs: Forwarded to :meth:`httpx.Client.request` (``json``, ``params``, etc.).
                  Do NOT pass ``headers`` — auth headers are injected automatically.

    Returns:
        :class:`httpx.Response` with a non-401 status code.

    Raises:
        BroadcastPlusAuthError: If 401 persists after a token refresh attempt.
        httpx.HTTPStatusError: On 4xx (other than 401) or 5xx after retries.
        httpx.NetworkError / httpx.TimeoutException: On network failures.
    """
    s = get_plus_http_client()
    r = _raw_request(s, method, path, plus_auth_headers(), **kwargs)

    if r.status_code == 401:
        logger.info("Broadcast+ 401 received — refreshing JWT and retrying.")
        try:
            refresh_plus_token()
        except BroadcastPlusAuthError:
            raise
        r = _raw_request(s, method, path, plus_auth_headers(), **kwargs)

    if r.status_code == 401:
        raise BroadcastPlusAuthError(
            "Broadcast+ returned 401 after token refresh.",
            endpoint=path,
            status_code=401,
        )

    return r


@http_retry
def _raw_request(
    s: httpx.Client,
    method: str,
    path: str,
    headers: dict[str, str],
    **kwargs,
) -> httpx.Response:
    """Isolated HTTP call so ``@http_retry`` can replay on transient failures."""
    return s.request(method.upper(), path, headers=headers, **kwargs)
