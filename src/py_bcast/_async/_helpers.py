"""Async infrastructure helpers for py_bcast._async modules."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import httpx

from .._legacy.aetp import _aetp_identifier
from .._legacy.binary import parse_binary_response
from .._core.cache import cache_get, cache_set
from .._core.config import get_settings
from .._core.constants import BASE_URL
from .._core.exceptions import NotFoundError, ProtocolError, is_no_records
from .._legacy.http import base_params, get_async_http_client, get_session_token
from .._core.logging import get_logger
from .._core.ratelimit import rate_limit_async
from .._core.retry import http_retry
from .._legacy.xml_helpers import raise_for_content_proxy_status

logger = get_logger(__name__)


@http_retry
async def _async_content_proxy_fetch(
    s: httpx.AsyncClient, endpoint: str, params: dict, timeout: int
) -> httpx.Response:
    """Isolated async HTTP call for retry decoration (ContentProxy)."""
    return await s.get(f"{BASE_URL}/{endpoint}", params=params, timeout=timeout)


@http_retry
async def _async_aetp_fetch(
    s: httpx.AsyncClient, path: str, params: dict
) -> httpx.Response:
    """Isolated async HTTP call for retry decoration (aetp/output)."""
    return await s.get(f"{BASE_URL}/aetp/output/{path}", params=params, timeout=30)


async def async_content_proxy_get(
    endpoint: str,
    params: dict[str, str],
    session_token: str | None = None,
    timeout: int = 30,
) -> ET.Element:
    """Async version of ``content_proxy_get``.

    Mirrors the sync error policy: ``raise_for_content_proxy_status`` maps the
    server STATUS to NotFoundError (unknown symbol), a benign no-op (valid
    query, zero rows), or ContentProxyError (anything else). Caching behavior
    is preserved.
    """
    token = get_session_token(session_token)
    s = get_async_http_client()

    merged = base_params(token)
    merged.update(params)

    # Check cache
    cached = cache_get(endpoint, merged)
    if cached is not None:
        return cached

    logger.debug("Async ContentProxy GET %s params=%s", endpoint, params)
    await rate_limit_async()
    r = await _async_content_proxy_fetch(s, endpoint, merged, timeout)

    root = ET.fromstring(r.text)
    raise_for_content_proxy_status(root, endpoint, params)

    # Store in cache
    cache_set(endpoint, merged, root, get_settings().cache_ttl)
    return root


async def async_aetp_request(
    path: str,
    params: dict[str, str],
    session_token: str | None = None,
    *,
    empty_ok: bool = True,
) -> dict:
    """Async version of ``aetp_request``.

    Mirrors the sync ``empty_ok`` policy: a no_records ProtocolError yields an
    empty parsed result (``{"fields": [], "rows": []}``) when ``empty_ok`` is
    True, else raises NotFoundError with the looked-up identifier/kind.
    """
    token = get_session_token(session_token)
    s = get_async_http_client()

    params.setdefault("10023", "4")
    params["10039"] = token

    cache_key_endpoint = f"aetp/{path}"
    cached = cache_get(cache_key_endpoint, params)
    if cached is not None:
        return cached

    logger.debug(
        "Async AETP request: %s params=%s",
        path,
        {k: v for k, v in params.items() if k != "10039"},
    )
    await rate_limit_async()
    r = await _async_aetp_fetch(s, path, params)

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
