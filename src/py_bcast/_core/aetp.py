"""Shared helpers for aetp/output binary protocol endpoints."""

from __future__ import annotations

from .constants import BASE_URL
from .http import create_http_session, get_session_token
from .binary import parse_binary_response


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

    r = s.get(
        f"{BASE_URL}/aetp/output/{path}",
        params=params,
        timeout=30,
    )

    return parse_binary_response(r.content)


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
