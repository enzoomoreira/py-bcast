"""Shared helpers for aetp/output binary protocol endpoints."""

from __future__ import annotations

from .._core.cache import cache_get, cache_set
from .._core.config import get_settings
from .._core.constants import BASE_URL
from .._core.exceptions import NotFoundError, ProtocolError, is_no_records
from .http import get_http_client, get_session_token
from .binary import parse_binary_response
from .._core.logging import get_logger
from .._core.ratelimit import rate_limit
from .._core.retry import http_retry

logger = get_logger(__name__)

# AETP request param tags that identify the looked-up entity, in the order
# preferred for a NotFoundError message (most user-facing first).
_ENTITY_TAGS: tuple[tuple[str, str], ...] = (
    ("10068", "ticker"),
    ("13004", "cvm_code"),
    ("10087", "broker"),
)


def _aetp_identifier(params: dict[str, str]) -> tuple[object, str]:
    """Extract (value, kind) of the looked-up entity for a NotFoundError."""
    for tag, kind in _ENTITY_TAGS:
        if params.get(tag):
            return params[tag], kind
    return None, "entity"


def aetp_request(
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
    s = get_http_client()

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
    rate_limit()
    r = _aetp_fetch(s, path, params)

    try:
        result = parse_binary_response(r.content)
    except ProtocolError as exc:
        if not is_no_records(exc.error_tag):
            raise
        if not empty_ok:
            identifier, kind = _aetp_identifier(params)
            raise NotFoundError(identifier, kind=kind) from exc
        result = {"fields": [], "rows": []}

    # Store in cache
    cache_set(cache_key_endpoint, params, result, get_settings().cache_ttl)

    return result


@http_retry
def _aetp_fetch(s, path: str, params: dict):
    """Isolated HTTP call for retry decoration."""
    return s.get(
        f"{BASE_URL}/aetp/output/{path}",
        params=params,
        timeout=30,
    )


def rows_to_dicts(parsed: dict) -> list[dict[str, str]]:
    """Convert parsed binary response to list of dicts.

    Handles the \\x02 compaction character meaning "same as previous row".
    """
    fields = parsed["fields"]
    results = []
    prev_values: list[str] = [""] * len(fields)

    for row in parsed["rows"]:
        record = {}
        for i, tag in enumerate(fields):
            val = row[i] if i < len(row) else ""
            # \x02 means "same as previous row"
            if val == "\x02":
                val = prev_values[i]
            record[tag] = val
            prev_values[i] = val
        results.append(record)

    return results
