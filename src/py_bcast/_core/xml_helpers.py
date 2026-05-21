"""Shared helpers for ContentProxy XML endpoints (BaseHistoricaNumerica)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from .cache import cache_get, cache_set
from .config import get_settings
from .constants import BASE_URL
from .exceptions import ContentProxyError
from .http import base_params, get_http_client, get_session_token
from .logging import get_logger
from .ratelimit import rate_limit
from .retry import http_retry

logger = get_logger(__name__)


def content_proxy_get(
    endpoint: str,
    params: dict[str, str],
    session_token: str | None = None,
    timeout: int = 30,
) -> ET.Element:
    """Execute a ContentProxy GET request and return the parsed XML root.

    Handles session token resolution, HTTP session creation, base params,
    and status/error checking.

    Args:
        endpoint: Path after BASE_URL (e.g. "BaseHistoricaNumerica/MacroEconomicos")
        params: Additional query parameters (merged with base_params)
        session_token: Optional explicit session token
        timeout: Request timeout in seconds

    Returns:
        Parsed XML root element.

    Raises:
        ContentProxyError: If the response STATUS is not 'success'.
    """
    token = get_session_token(session_token)
    s = get_http_client()

    merged = base_params(token)
    merged.update(params)

    # Check cache
    cached = cache_get(endpoint, merged)
    if cached is not None:
        return cached

    logger.debug("ContentProxy GET %s params=%s", endpoint, params)
    rate_limit()
    r = _content_proxy_fetch(s, endpoint, merged, timeout)

    root = ET.fromstring(r.text)
    if root.findtext("STATUS") != "success":
        msg = root.findtext("MESSAGE") or "Unknown error"
        logger.error("ContentProxy error on %s: %s", endpoint, msg)
        raise ContentProxyError(f"ContentProxy error: {msg}")

    # Store in cache
    cache_set(endpoint, merged, root, get_settings().cache_ttl)

    return root


@http_retry
def _content_proxy_fetch(s, endpoint: str, params: dict, timeout: int):
    """Isolated HTTP call for retry decoration."""
    return s.get(
        f"{BASE_URL}/{endpoint}",
        params=params,
        timeout=timeout,
    )


def parse_ticks(root: ET.Element, sort_by: str = "") -> list[dict[str, str]]:
    """Parse <TICK> elements from XML root into a list of dicts.

    Args:
        root: XML root element containing .//TICK elements
        sort_by: If non-empty, sort results by this key (e.g. "dat")

    Returns:
        List of dicts with lowercased tag names as keys.
    """
    rows = [
        {child.tag.lower(): (child.text or "") for child in tick}
        for tick in root.findall(".//TICK")
    ]
    if sort_by:
        rows.sort(key=lambda r: r.get(sort_by, ""))
    return rows
