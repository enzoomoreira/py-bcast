"""Legacy HTTP transports: AETP binary and ContentProxy XML requests."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import httpx

from ..._core.cache import cache_get, cache_set
from ..._core.config import get_settings
from ..._core.constants import BASE_URL
from ..._core.exceptions import NotFoundError, ProtocolError, is_no_records
from ..._core.logging import get_logger
from ..._core.ratelimit import rate_limit_async
from ..._core.retry import http_retry
from ..aetp import _aetp_identifier
from ..binary import parse_binary_response
from ..http import base_params, get_async_http_client, get_session_token
from ..xml_helpers import raise_for_content_proxy_status

logger = get_logger(__name__)


@http_retry
async def _aetp_fetch(s: httpx.AsyncClient, path: str, params: dict) -> httpx.Response:
    """Isolated HTTP call for retry decoration (aetp/output)."""
    return await s.get(f"{BASE_URL}/aetp/output/{path}", params=params, timeout=30)


@http_retry
async def _content_proxy_fetch(
    s: httpx.AsyncClient, endpoint: str, params: dict, timeout: int
) -> httpx.Response:
    """Isolated HTTP call for retry decoration (ContentProxy)."""
    return await s.get(f"{BASE_URL}/{endpoint}", params=params, timeout=timeout)


async def aetp_request(
    path: str,
    params: dict[str, str],
    session_token: str | None = None,
    *,
    empty_ok: bool = True,
) -> dict:
    """Make a request to aetp/output/* and decode the binary response.

    Args:
        path: Endpoint path after ``aetp/output/``.
        params: Request tags (entity codes, dates, etc.).
        session_token: Optional explicit BCAA session token.
        empty_ok: How to treat the server's "no records" response. The AETP
            server returns the same message for an unknown entity and an
            empty-but-valid range, so the caller disambiguates:
                - ``True``  (lists / ranges): return ``{"fields": [], "rows": []}``
                  so the caller yields an empty DataFrame with schema.
                - ``False`` (entity lookups): raise ``NotFoundError``.

    Returns:
        dict with keys ``fields`` (list[str]) and ``rows`` (list[list[str]]).
    """
    token = get_session_token(session_token)
    s = get_async_http_client()

    params.setdefault("10023", "4")
    params["10039"] = token

    # Check cache (key excludes token)
    cache_key_endpoint = f"aetp/{path}"
    cached = cache_get(cache_key_endpoint, params)
    if cached is not None:
        return cached

    logger.debug(
        "AETP request: %s params=%s",
        path,
        {k: v for k, v in params.items() if k != "10039"},
    )
    await rate_limit_async()
    r = await _aetp_fetch(s, path, params)

    try:
        result = parse_binary_response(r.content)
    except ProtocolError as exc:
        if not is_no_records(exc.error_tag):
            raise
        if not empty_ok:
            identifier, kind = _aetp_identifier(params)
            raise NotFoundError(identifier, kind=kind) from exc
        result = {"fields": [], "rows": []}

    cache_set(cache_key_endpoint, params, result, get_settings().cache_ttl)
    return result


async def content_proxy_get(
    endpoint: str,
    params: dict[str, str],
    session_token: str | None = None,
    timeout: int = 30,
) -> ET.Element:
    """Execute a ContentProxy GET request and return the parsed XML root.

    ``raise_for_content_proxy_status`` maps the server STATUS to NotFoundError
    (unknown symbol), a benign no-op (valid query, zero rows), or
    ContentProxyError (anything else).

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
    s = get_async_http_client()

    merged = base_params(token)
    merged.update(params)

    # Check cache
    cached = cache_get(endpoint, merged)
    if cached is not None:
        return cached

    logger.debug("ContentProxy GET %s params=%s", endpoint, params)
    await rate_limit_async()
    r = await _content_proxy_fetch(s, endpoint, merged, timeout)

    root = ET.fromstring(r.text)
    raise_for_content_proxy_status(root, endpoint, params)

    cache_set(endpoint, merged, root, get_settings().cache_ttl)
    return root
