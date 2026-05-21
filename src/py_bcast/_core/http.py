"""Shared HTTP client pool for ContentProxy API.

Provides singleton httpx clients (sync + async) with connection pooling.
"""

from __future__ import annotations

import warnings

import httpx

from .config import get_settings
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
    """Close the singleton HTTP clients. Used for cleanup/testing."""
    global _sync_client, _async_client
    if _sync_client and not _sync_client.is_closed:
        _sync_client.close()
    _sync_client = None
    _async_client = None


def create_http_session() -> httpx.Client:
    """Create a pre-configured httpx.Client for ContentProxy.

    .. deprecated::
        Use ``get_http_client()`` instead. This function now returns the
        shared singleton client rather than creating a new one each call.
    """
    warnings.warn(
        "create_http_session() is deprecated, use get_http_client()",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_http_client()


def base_params(session_token: str) -> dict[str, str]:
    """Common query params for all ContentProxy requests."""
    settings = get_settings()
    return {
        "10023": settings.platform,
        "10039": session_token,
        "TipoResposta": "xml",
    }
