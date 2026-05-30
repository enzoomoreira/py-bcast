"""AE binary SOH protocol parser.

Protocol structure (SOH=0x01 separated records, NULL=0x00 separated fields):
    Record 0: Header [version, ?, ?, ?]
    Record 1: Metadata/status [count, key-value pairs...] ("0" = no metadata)
    Record 2: Field definitions [count, tag1, tag2, ...]
    Record 3+: Data rows [value1, value2, ...]
    Last record: ETX [0x03]
"""

from __future__ import annotations

from .exceptions import ProtocolError
from .logging import get_logger

logger = get_logger(__name__)


def parse_binary_response(data: bytes) -> dict:
    """
    Parse an AE binary protocol response into fields and rows.

    Returns:
        dict with keys 'fields' (list[str]) and 'rows' (list[list[str]]).

    Raises:
        RuntimeError: If the response contains an error or is malformed.
    """
    records = data.split(b"\x01")

    if len(records) < 3:
        logger.error("Malformed binary response: only %d records", len(records))
        raise ProtocolError(
            f"aefundamental error: malformed response ({len(records)} records)",
            record_count=len(records),
        )

    # Record 1 = metadata/status info
    error_fields = records[1].split(b"\x00")
    first_field = error_fields[0].decode("latin-1") if error_fields else ""

    # Check for error: if 10037 tag exists anywhere, it's an error response
    if b"10037" in data:
        all_fields = data.split(b"\x00")
        msg = ""
        for i, f in enumerate(all_fields):
            decoded = f.decode("latin-1", errors="replace")
            if decoded == "10037" and i + 1 < len(all_fields):
                msg = all_fields[i + 1].decode("utf-8", errors="replace")
                break
        logger.error("Binary protocol error: %s", msg or first_field)
        raise ProtocolError(
            f"aefundamental error: {msg or first_field}",
            error_tag=msg or first_field,
        )

    # Record 2 = field definitions
    field_record = records[2].split(b"\x00")
    # First element is field count, rest are tag numbers, last may be empty
    field_tags = [f.decode("latin-1") for f in field_record[1:] if f]
    n_fields = len(field_tags)

    # Record 3+ = data rows (before the ETX terminator record)
    rows = []
    for rec in records[3:]:
        if rec == b"\x03" or rec == b"":
            break
        parts = rec.split(b"\x00")
        values = [v.decode("latin-1", errors="replace") for v in parts]
        # Align positionally to the declared field count. Each data record
        # ends with a NULL terminator (trailing empty) which we drop; short
        # rows are padded. Interior empty fields are KEPT — filtering them
        # would shift every subsequent value left and corrupt the mapping on
        # sparse rows (e.g. a dividend with no ex-date / record-date).
        values = (values + [""] * n_fields)[:n_fields]
        if any(values):
            rows.append(values)

    return {"fields": field_tags, "rows": rows}
