"""Intraday tick data via Broadcast+ timesAndTrades endpoint."""

from __future__ import annotations

import pandas as pd

from .._core.dates import to_date_str
from .._core.logging import get_logger
from .._core.validation import DateParam, Ticker, validate_params
from .http import plus_request

logger = get_logger(__name__)

_ENDPOINT = "/stock/v1/timesAndTrades"

# Flat schema (column order) for the times & trades frame. ``ticker`` leads so
# results from several symbols stack cleanly; exchange ids and ``is_trade`` are
# non-numeric.
_TRADE_COLUMNS = [
    "ticker",
    "last",
    "size",
    "tendency",
    "sequence",
    "is_trade",
    "ask_price",
    "ask_size",
    "ask_exchange_id",
    "bid_price",
    "bid_size",
    "bid_exchange_id",
]


def _empty_btrades(ticker: str) -> pd.DataFrame:
    """Empty trades frame carrying the full schema and a tz-aware index."""
    idx = pd.DatetimeIndex([], tz="America/Sao_Paulo", name=None)
    return pd.DataFrame(
        {col: pd.Series(dtype="object") for col in _TRADE_COLUMNS}, index=idx
    )


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
            ticker      — instrument code (the queried symbol)
            last        — trade price
            size        — trade quantity
            tendency    — price tendency (0 = unchanged, 1 = up, -1 = down)
            sequence    — server sequence number
            is_trade    — True for actual trades (vs quotes)
            ask_price       — best ask at trade time
            ask_size        — ask quantity
            ask_exchange_id — venue code for the ask (string identifier)
            bid_price       — best bid at trade time
            bid_size        — bid quantity
            bid_exchange_id — venue code for the bid (string identifier)
        Empty DataFrame (same columns + tz-aware index) if no trades found.

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
        return _empty_btrades(ticker)

    rows = data["data"]
    if not rows:
        return _empty_btrades(ticker)

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
                "ask_exchange_id": ask.get("exchangeId"),
                "bid_price": bid.get("price"),
                "bid_size": bid.get("size"),
                "bid_exchange_id": bid.get("exchangeId"),
            }
        )

    df = pd.DataFrame(records)

    # Build DatetimeIndex from Unix milliseconds, localized to Sao Paulo
    df.index = pd.to_datetime(
        df.pop("unix_time_ms"), unit="ms", utc=True
    ).dt.tz_convert("America/Sao_Paulo")
    df.index.name = None

    # Coerce numeric columns. is_trade is bool; exchange IDs are venue codes
    # (identifiers, not quantities), so they stay strings.
    _non_numeric = {"is_trade", "ask_exchange_id", "bid_exchange_id"}
    for col in df.columns:
        if col not in _non_numeric:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Tag with the queried symbol (after numeric coercion so it stays a string).
    df.insert(0, "ticker", ticker)

    # API returns newest-first; sort ascending (oldest first, chronological)
    return df.sort_index()
