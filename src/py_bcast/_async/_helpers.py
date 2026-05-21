"""Async infrastructure helpers for py_bcast._async modules."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from .._core.cache import cache_get, cache_set
from .._core.config import get_settings
from .._core.constants import BASE_URL
from .._core.exceptions import ContentProxyError
from .._core.http import base_params, get_async_http_client, get_session_token
from .._core.binary import parse_binary_response
from .._core.logging import get_logger
from .._core.ratelimit import rate_limit_async

logger = get_logger(__name__)


async def async_content_proxy_get(
    endpoint: str,
    params: dict[str, str],
    session_token: str | None = None,
    timeout: int = 30,
) -> ET.Element:
    """Async version of content_proxy_get."""
    token = get_session_token(session_token)
    s = get_async_http_client()

    merged = base_params(token)
    merged.update(params)

    # Check cache
    cached = cache_get(endpoint, merged)
    if cached is not None:
        return cached

    logger.debug("Async ContentProxy GET %s", endpoint)
    await rate_limit_async()

    r = await s.get(
        f"{BASE_URL}/{endpoint}",
        params=merged,
        timeout=timeout,
    )

    root = ET.fromstring(r.text)
    if root.findtext("STATUS") != "success":
        msg = root.findtext("MESSAGE") or "Unknown error"
        raise ContentProxyError(
            f"ContentProxy error on {endpoint}: {msg}",
            endpoint=endpoint,
            server_message=msg,
        )

    cache_set(endpoint, merged, root, get_settings().cache_ttl)
    return root


async def async_aetp_request(
    path: str,
    params: dict[str, str],
    session_token: str | None = None,
) -> dict:
    """Async version of aetp_request."""
    token = get_session_token(session_token)
    s = get_async_http_client()

    params.setdefault("10023", "4")
    params["10039"] = token

    cache_key_endpoint = f"aetp/{path}"
    cached = cache_get(cache_key_endpoint, params)
    if cached is not None:
        return cached

    logger.debug("Async AETP request: %s", path)
    await rate_limit_async()

    r = await s.get(
        f"{BASE_URL}/aetp/output/{path}",
        params=params,
        timeout=30,
    )

    result = parse_binary_response(r.content)
    cache_set(cache_key_endpoint, params, result, get_settings().cache_ttl)
    return result
