"""Pure helpers for aetp/output binary protocol responses.

The I/O side (``aetp_request``) lives in the twin trees ``_legacy/_async/``
(source) and ``_legacy/_sync/`` (generated); this module keeps the shared
protocol knowledge both import.
"""

from __future__ import annotations

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
