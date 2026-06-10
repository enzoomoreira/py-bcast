"""HTTP client singletons and auth headers for the Broadcast+ REST API.

The request side (``plus_request``) lives in the twin trees ``_plus/_async/``
(source) and ``_plus/_sync/`` (generated); this module keeps the shared state
both import: the client singletons and the auth-header builder.
"""

from __future__ import annotations

import asyncio

import httpx

from .._core.constants import PLUS_BASE_URL, plus_base_headers
from .session import get_plus_token

_plus_client: httpx.Client | None = None
_plus_async_client: httpx.AsyncClient | None = None


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


def get_plus_async_http_client() -> httpx.AsyncClient:
    """Return the singleton httpx.AsyncClient for the Broadcast+ API."""
    global _plus_async_client
    if _plus_async_client is None or _plus_async_client.is_closed:
        _plus_async_client = httpx.AsyncClient(
            base_url=PLUS_BASE_URL,
            verify=False,
            trust_env=False,
            timeout=30,
        )
    return _plus_async_client


def close_plus_clients() -> None:
    """Close the singleton Plus HTTP clients. Used for cleanup/testing.

    The async client is closed via ``asyncio.run``, so this must not be called
    from inside a running event loop — use :func:`aclose_plus_clients` there.
    """
    global _plus_client, _plus_async_client
    if _plus_client and not _plus_client.is_closed:
        _plus_client.close()
    _plus_client = None
    if _plus_async_client and not _plus_async_client.is_closed:
        asyncio.run(_plus_async_client.aclose())
    _plus_async_client = None


async def aclose_plus_clients() -> None:
    """Async twin of :func:`close_plus_clients`, for use inside an event loop."""
    global _plus_client, _plus_async_client
    if _plus_client and not _plus_client.is_closed:
        _plus_client.close()
    _plus_client = None
    if _plus_async_client and not _plus_async_client.is_closed:
        await _plus_async_client.aclose()
    _plus_async_client = None


def plus_auth_headers() -> dict[str, str]:
    """Build Authorization + versioning headers for an authenticated Plus call."""
    token = get_plus_token()
    return {**plus_base_headers(), "Authorization": f"Bearer {token}"}
