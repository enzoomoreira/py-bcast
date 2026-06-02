"""Shared helpers for ContentProxy XML endpoints (BaseHistoricaNumerica)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import httpx

from .._core.cache import cache_get, cache_set
from .._core.config import get_settings
from .._core.constants import BASE_URL
from .._core.exceptions import (
    ContentProxyError,
    NotFoundError,
    is_no_records,
    is_not_found,
)
from .http import base_params, get_http_client, get_session_token
from .._core.logging import get_logger
from .._core.ratelimit import rate_limit
from .._core.retry import http_retry

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
    raise_for_content_proxy_status(root, endpoint, params)

    # Store in cache
    cache_set(endpoint, merged, root, get_settings().cache_ttl)

    return root


def raise_for_content_proxy_status(
    root: ET.Element,
    endpoint: str,
    params: dict[str, str],
) -> None:
    """Classify a ContentProxy STATUS != success response.

    Maps the server MESSAGE to the unified error policy:
        - unknown symbol ("não existe")          -> NotFoundError
        - valid query, no rows ("não foram ...")  -> return (benign; caller
          gets a zero-TICK root and yields an empty DataFrame with schema)
        - anything else                           -> ContentProxyError

    A ``success`` status is a no-op.
    """
    if root.findtext("STATUS") == "success":
        return
    msg = root.findtext("MESSAGE") or "Unknown error"
    if is_not_found(msg):
        raise NotFoundError(params.get("305") or params.get("10113"), kind="symbol")
    if not is_no_records(msg):
        logger.error("ContentProxy error on %s: %s", endpoint, msg)
        raise ContentProxyError(
            f"ContentProxy error on {endpoint}: {msg}",
            endpoint=endpoint,
            server_message=msg,
        )
    logger.debug("ContentProxy no records on %s: %s", endpoint, msg)


@http_retry
def _content_proxy_fetch(
    s: httpx.Client, endpoint: str, params: dict, timeout: int
) -> httpx.Response:
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
