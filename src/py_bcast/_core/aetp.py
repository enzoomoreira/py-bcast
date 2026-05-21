"""Shared helpers for aetp/output binary protocol endpoints."""

from __future__ import annotations

from .constants import BASE_URL
from .http import create_http_session, get_session_token
from .binary import parse_binary_response
from .logging import get_logger
from .retry import http_retry

logger = get_logger(__name__)


def aetp_request(
    path: str,
    params: dict[str, str],
    session_token: str | None = None,
) -> dict:
    """Make a request to aetp/output/* and decode binary response."""
    token = get_session_token(session_token)
    s = create_http_session()

    params.setdefault("10023", "4")
    params["10039"] = token

    logger.debug("AETP request: %s params=%s", path, {k: v for k, v in params.items() if k != "10039"})
    r = _aetp_fetch(s, path, params)

    return parse_binary_response(r.content)


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
