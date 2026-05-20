"""Shared HTTP session factory for ContentProxy API."""

from __future__ import annotations

import os

import requests
import urllib3

from ._constants import BASE_URL, HTTP_PLATFORM, HTTP_USER_AGENT

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_session_token(session_token: str | None = None) -> str:
    """Resolve session token from argument or BROADCAST_SESSION env var."""
    if session_token:
        return session_token
    token = os.environ.get("BROADCAST_SESSION", "")
    if not token:
        raise ValueError(
            "session_token required. Either pass it explicitly or set "
            "the BROADCAST_SESSION environment variable."
        )
    return token


def create_http_session() -> requests.Session:
    """Create a pre-configured requests.Session for ContentProxy."""
    s = requests.Session()
    s.headers["User-Agent"] = HTTP_USER_AGENT
    s.trust_env = False
    return s


def base_params(session_token: str) -> dict[str, str]:
    """Common query params for all ContentProxy requests."""
    return {
        "10023": HTTP_PLATFORM,
        "10039": session_token,
        "TipoResposta": "xml",
    }
