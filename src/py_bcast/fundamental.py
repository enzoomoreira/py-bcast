"""Fundamental data via aefundamental HTTP API."""

from __future__ import annotations

from ._http import create_http_session, get_session_token
from ._constants import BASE_URL


def _parse_binary_response(data: bytes) -> dict:
    """
    Parse the AE binary protocol response.

    Protocol structure (SOH=0x01 separated records, NULL=0x00 separated fields):
        Record 0: Header [version, ?, ?, ?]
        Record 1: Error code ["0" = success]
        Record 2: Field definitions [count, tag1, tag2, ...]
        Record 3+: Data rows [value1, value2, ...]
        Last record: ETX [0x03]
    """
    records = data.split(b"\x01")

    # Record 1 = error info
    error_fields = records[1].split(b"\x00")
    error_code = error_fields[0].decode("latin-1") if error_fields else ""

    if error_code != "0":
        # Error response — extract message from tag 10037
        all_fields = data.split(b"\x00")
        msg = ""
        for i, f in enumerate(all_fields):
            decoded = f.decode("latin-1", errors="replace")
            if decoded == "10037" and i + 1 < len(all_fields):
                msg = all_fields[i + 1].decode("utf-8", errors="replace")
                break
        raise RuntimeError(f"aefundamental error: {msg or error_code}")

    # Record 2 = field definitions
    field_record = records[2].split(b"\x00")
    # First element is field count, rest are tag numbers, last may be empty
    field_tags = [f.decode("latin-1") for f in field_record[1:] if f]

    # Record 3+ = data rows (before the ETX terminator record)
    rows = []
    for rec in records[3:]:
        if rec == b"\x03" or rec == b"":
            break
        values = [v.decode("latin-1", errors="replace") for v in rec.split(b"\x00") if v]
        if values:
            rows.append(values)

    return {"fields": field_tags, "rows": rows}


# Consenso field tag mapping
_CONSENSO_FIELDS = {
    "13019": "buy",
    "13020": "hold",
    "13021": "sell",
    "13022": "total_analysts",
    "13023": "target_low",
    "13024": "target_high",
    "13025": "target_mean",
    "13026": "target_median",
    "13027": "upside_pct",
}


def bconsensus(
    ticker: str,
    session_token: str | None = None,
) -> dict[str, str]:
    """
    Get analyst consensus data for a stock.

    Uses aefundamental/consenso endpoint. Provides buy/hold/sell
    recommendation counts and target price statistics.

    Args:
        ticker: Stock ticker (e.g., "PETR4", "VALE3", "ITUB4")
        session_token: BCAA session token

    Returns:
        Dict with keys: buy, hold, sell, total_analysts, target_low,
        target_high, target_mean, target_median, upside_pct.
        Empty dict if no consensus data available.

    Example:
        >>> data = bconsensus("PETR4")
        >>> print(f"Buy: {data['buy']}, Target: {data['target_mean']}")
    """
    token = get_session_token(session_token)
    s = create_http_session()

    import datetime

    today = datetime.date.today().strftime("%Y%m%d")

    r = s.get(
        f"{BASE_URL}/aefundamental/{ticker}/consenso",
        params={
            "10023": "4",
            "10039": token,
            "10068": ticker,
            "13004": today,
        },
        timeout=15,
        verify=False,
    )

    try:
        parsed = _parse_binary_response(r.content)
    except RuntimeError:
        return {}

    if not parsed["rows"]:
        return {}

    # Map field tags to friendly names
    result = {}
    row = parsed["rows"][0]
    for i, tag in enumerate(parsed["fields"]):
        if i < len(row):
            name = _CONSENSO_FIELDS.get(tag, tag)
            result[name] = row[i]

    return result
