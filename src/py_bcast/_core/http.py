"""Shared HTTP session factory for ContentProxy API."""

from __future__ import annotations

import httpx

from .constants import HTTP_PLATFORM, HTTP_USER_AGENT
from .session import get_session_token  # noqa: F401 — re-exported


def create_http_session() -> httpx.Client:
    """Create a pre-configured httpx.Client for ContentProxy."""
    return httpx.Client(
        headers={"User-Agent": HTTP_USER_AGENT},
        verify=False,
        trust_env=False,
    )


def base_params(session_token: str) -> dict[str, str]:
    """Common query params for all ContentProxy requests."""
    return {
        "10023": HTTP_PLATFORM,
        "10039": session_token,
        "TipoResposta": "xml",
    }
