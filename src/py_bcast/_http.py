"""Shared HTTP session factory for ContentProxy API."""

from __future__ import annotations

import requests
import urllib3

from ._constants import HTTP_PLATFORM, HTTP_USER_AGENT
from ._session import get_session_token  # noqa: F401 — re-exported

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
