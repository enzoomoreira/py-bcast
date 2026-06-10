"""Shared HTTP client pool for ContentProxy API.

Provides singleton httpx clients (sync + async) with connection pooling.
"""

from __future__ import annotations

import asyncio

import httpx

from .._core.config import get_settings
from .session import get_session_token  # noqa: F401 — re-exported

_sync_client: httpx.Client | None = None
_async_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.Client:
    """Return the singleton sync httpx.Client with keep-alive pooling.

    The client is created lazily on first call and reused for all
    subsequent requests within the process.
    """
    global _sync_client
    if _sync_client is None or _sync_client.is_closed:
        settings = get_settings()
        _sync_client = httpx.Client(
            headers={"User-Agent": settings.user_agent},
            verify=False,
            trust_env=False,
            timeout=settings.timeout,
        )
    return _sync_client


def get_async_http_client() -> httpx.AsyncClient:
    """Return the singleton async httpx.AsyncClient with keep-alive pooling.

    The client is created lazily on first call and reused for all
    subsequent async requests within the process.
    """
    global _async_client
    if _async_client is None or _async_client.is_closed:
        settings = get_settings()
        _async_client = httpx.AsyncClient(
            headers={"User-Agent": settings.user_agent},
            verify=False,
            trust_env=False,
            timeout=settings.timeout,
        )
    return _async_client


def close_clients() -> None:
    """Close the singleton HTTP clients. Used for cleanup/testing.

    The async client is closed via ``asyncio.run``, so this must not be called
    from inside a running event loop — use :func:`aclose_clients` there.
    """
    global _sync_client, _async_client
    if _sync_client and not _sync_client.is_closed:
        _sync_client.close()
    _sync_client = None
    if _async_client and not _async_client.is_closed:
        asyncio.run(_async_client.aclose())
    _async_client = None


async def aclose_clients() -> None:
    """Async twin of :func:`close_clients`, for use inside an event loop."""
    global _sync_client, _async_client
    if _sync_client and not _sync_client.is_closed:
        _sync_client.close()
    _sync_client = None
    if _async_client and not _async_client.is_closed:
        await _async_client.aclose()
    _async_client = None


def base_params(session_token: str) -> dict[str, str]:
    """Common query params for all ContentProxy requests."""
    settings = get_settings()
    return {
        "10023": settings.platform,
        "10039": session_token,
        "TipoResposta": "xml",
    }
