"""AE binary SOH protocol parser.

Protocol structure (SOH=0x01 separated records, NULL=0x00 separated fields):
    Record 0: Header [version, ?, ?, ?]
    Record 1: Metadata/status [count, key-value pairs...] ("0" = no metadata)
    Record 2: Field definitions [count, tag1, tag2, ...]
    Record 3+: Data rows [value1, value2, ...]
    Last record: ETX [0x03]
"""

from __future__ import annotations

from .._core.exceptions import ProtocolError
from .._core.logging import get_logger

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

    # Record 2 = field definitions: first element is the field count, the rest
    # are tag numbers (last may be empty).
    field_record = records[2].split(b"\x00")
    field_tags = [f.decode("utf-8", errors="replace") for f in field_record[1:] if f]
    n_fields = len(field_tags)

    # An error response packs its (tag, value) pairs inline into this record
    # (e.g. ['2', '10036', 'af_88000', '10037', '<message>', '']), so the
    # message tag 10037 is followed by the message text among these tokens.
    # Detecting the error by an exact token here rather than by a substring
    # scan of the whole payload avoids a false positive when a large data
    # response happens to contain the bytes "10037" inside a value (e.g. a fund
    # id or CNPJ in the 10.7 MB fund autocomplete dump).
    if "10037" in field_tags:
        idx = field_tags.index("10037")
        msg = field_tags[idx + 1] if idx + 1 < len(field_tags) else ""
        logger.error("Binary protocol error: %s", msg)
        raise ProtocolError(f"aefundamental error: {msg}", error_tag=msg)

    # Record 3+ = data rows (before the ETX terminator record)
    rows = []
    for rec in records[3:]:
        if rec == b"\x03" or rec == b"":
            break
        parts = rec.split(b"\x00")
        values = [v.decode("utf-8", errors="replace") for v in parts]
        # Align positionally to the declared field count. Each data record
        # ends with a NULL terminator (trailing empty) which we drop; short
        # rows are padded. Interior empty fields are KEPT — filtering them
        # would shift every subsequent value left and corrupt the mapping on
        # sparse rows (e.g. a dividend with no ex-date / record-date).
        values = (values + [""] * n_fields)[:n_fields]
        if any(values):
            rows.append(values)

    return {"fields": field_tags, "rows": rows}
