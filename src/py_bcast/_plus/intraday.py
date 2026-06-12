"""Intraday tick data via Broadcast+ timesAndTrades endpoint."""

from __future__ import annotations

import pandas as pd

from .._core.dates import to_date_str
from .._core.validation import DateParam, Ticker, validate_params
from ._sync.trades import trades_core


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
            price       — trade price
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
        >>> print(df[["price", "size"]].head())
    """
    return trades_core(ticker, to_date_str(date))
