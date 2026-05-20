"""Analyst consensus data via aefundamental HTTP API."""

from __future__ import annotations

import datetime

import pandas as pd

from .._core.constants import BASE_URL
from .._core.http import create_http_session, get_session_token
from .._core.binary import parse_binary_response
from .._core.output import to_series


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
) -> pd.Series:
    """
    Get analyst consensus data for a stock.

    Uses aefundamental/consenso endpoint. Provides buy/hold/sell
    recommendation counts and target price statistics.

    Args:
        ticker: Stock ticker (e.g., "PETR4", "VALE3", "ITUB4")
        session_token: BCAA session token

    Returns:
        Series with numeric values: buy, hold, sell, total_analysts,
        target_low, target_high, target_mean, target_median, upside_pct.
        Empty Series if no consensus data available.

    Example:
        >>> s = bconsensus("PETR4")
        >>> print(f"Buy: {s['buy']}, Target: {s['target_mean']}")
    """
    token = get_session_token(session_token)
    s = create_http_session()

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
    )

    try:
        parsed = parse_binary_response(r.content)
    except RuntimeError:
        return pd.Series(dtype="object")

    if not parsed["rows"]:
        return pd.Series(dtype="object")

    # Map field tags to friendly names
    result = {}
    row = parsed["rows"][0]
    for i, tag in enumerate(parsed["fields"]):
        if i < len(row):
            name = _CONSENSO_FIELDS.get(tag, tag)
            result[name] = row[i]

    return to_series(result)
