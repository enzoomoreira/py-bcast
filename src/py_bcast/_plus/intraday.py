"""Intraday tick data via Broadcast+ timesAndTrades endpoint."""

from __future__ import annotations

import pandas as pd

from .._core.dates import to_date_str
from .._core.logging import get_logger
from .._core.validation import DateParam, Ticker, validate_params
from .http import plus_request

logger = get_logger(__name__)

_ENDPOINT = "/stock/v1/timesAndTrades"


@validate_params
def btrades(
    ticker: Ticker,
    date: DateParam,
) -> pd.DataFrame:
    """Fetch intraday tick data (times & trades) via Broadcast+.

    Returns the most recent trades for a given ticker on a given date.
    The endpoint caps at 500 records per call (newest first, returned
    sorted oldest-first in the DataFrame).

    Requires Broadcast+ backend — either configure(terminal='plus'),
    configure(terminal='auto') with Broadcast+.exe running, or
    configure(plus_login=..., plus_password=...) for headless login.

    Args:
        ticker: Instrument code (e.g. "PETR4").
        date:   Trade date (YYYYMMDD, date, datetime, or Timestamp).

    Returns:
        DataFrame with DatetimeIndex (America/Sao_Paulo timezone) and columns:
            last        — trade price
            size        — trade quantity
            tendency    — price tendency (0 = unchanged, 1 = up, -1 = down)
            sequence    — server sequence number
            is_trade    — True for actual trades (vs quotes)
            ask_price   — best ask at trade time
            ask_size    — ask quantity
            bid_price   — best bid at trade time
            bid_size    — bid quantity
        Empty DataFrame if no trades found.

    Raises:
        BroadcastPlusAuthError: If authentication with Broadcast+ fails.
        BroadcastPlusError: If the API returns an unexpected error.

    Example:
        >>> from py_bcast import btrades, configure
        >>> configure(terminal="plus")
        >>> df = btrades("PETR4", "20260525")
        >>> print(df[["last", "size"]].head())
    """
    date_str = to_date_str(date)
    logger.debug("btrades: %s on %s", ticker, date_str)

    r = plus_request("post", _ENDPOINT, json={"symbol": ticker, "date": date_str})

    data = r.json()
    if not isinstance(data, dict) or not data.get("data"):
        return pd.DataFrame()

    rows = data["data"]
    if not rows:
        return pd.DataFrame()

    records = []
    for row in rows:
        ask = row.get("ask") or {}
        bid = row.get("bid") or {}
        records.append(
            {
                "unix_time_ms": row.get("unixTime"),
                "last": row.get("last"),
                "size": row.get("size"),
                "tendency": row.get("tendency"),
                "sequence": row.get("sequence"),
                "is_trade": row.get("isTrade", True),
                "ask_price": ask.get("price"),
                "ask_size": ask.get("size"),
                "bid_price": bid.get("price"),
                "bid_size": bid.get("size"),
            }
        )

    df = pd.DataFrame(records)

    # Build DatetimeIndex from Unix milliseconds, localized to Sao Paulo
    df.index = pd.to_datetime(
        df.pop("unix_time_ms"), unit="ms", utc=True
    ).dt.tz_convert("America/Sao_Paulo")
    df.index.name = None

    # Coerce numeric columns
    for col in df.columns:
        if col != "is_trade":
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # API returns newest-first; sort ascending (oldest first, chronological)
    return df.sort_index()
