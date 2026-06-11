"""Intraday bars and tick-by-tick data via ContentProxy."""

from __future__ import annotations

import pandas as pd

from .._core.dates import default_tick_end, to_date_str, to_datetime_str
from .._core.validation import DateParam, DateTimeParam, TickerList, validate_params
from .._legacy.endpoints import SPEC_BDI, SPEC_BDT
from .._legacy.multi import vectorize
from .._legacy._sync.executor import run_spec
from .._legacy._sync.ticks import bticks_core


@validate_params
def bdt(
    ticker: TickerList,
    start: DateTimeParam,
    end: DateTimeParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Get tick-by-tick (trade) data for one or more symbols.

    Uses HistoricoTick endpoint. Works for both B3/BVMF instruments (PETR4,
    VALE3, IBOV, ...) and international ones: FX pairs (USDBRL, EURUSD, ...),
    precious metals (GOLD, SILVER), energy (WTI), indices (DAX, FTSE, VIX,
    DXY), treasuries (US10Y, US2Y).

    The request window is interpreted in **UTC**, while B3's floor session
    runs 10:00-17:00 in Brasilia time. So the B3 regular session is
    13:00-20:00 UTC in ``start``/``end`` and in the returned timestamps. A
    Brasilia-clock window (e.g. start "...100000") lands in pre-market and
    returns no rows. International feeds trade ~24h, so any hour works.

    B3 tick history is short and irregular: recent dates return data, older
    dates can come back empty even when the floor traded (use ``bdi`` for
    intraday detail on those). International instruments retain tick history
    much longer.

    Args:
        ticker: Single symbol or list (e.g., "PETR4" or ["PETR4", "USDBRL"]).
        start: Start datetime, UTC (str YYYYMMDDHHMMSS, datetime, or Timestamp)
        end: End datetime, UTC (default: start + 1 hour)
        session_token: BCAA session token

    Returns:
        Flat DataFrame with a DatetimeIndex (from dat+hor) and a ``ticker``
        column (one block per symbol). Numeric columns: close, size, trades,
        open_interest, calendar_days, working_days.

    Example:
        >>> # B3 floor open: 13:00 UTC = 10:00 Brasilia
        >>> df = bdt("PETR4", "20260601130000", "20260601140000")
        >>> df["close"].plot()
    """
    start_str = to_datetime_str(start)
    end_str = default_tick_end(start_str) if end is None else to_datetime_str(end)
    return run_spec(
        SPEC_BDT,
        session_token=session_token,
        ticker=ticker,
        start=start_str,
        end=end_str,
    )


@validate_params
def bdi(
    ticker: TickerList,
    start_date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Get intraday OHLCV bars (2-minute candles) for one or more symbols.

    Uses HistoricoIntraday endpoint. Works for ALL instruments (B3 + international).
    Returns bars from start_date up to the current time.

    Args:
        ticker: Single symbol or list (e.g., "PETR4" or ["PETR4", "VALE3"]).
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        session_token: BCAA session token

    Returns:
        Flat DataFrame with a DatetimeIndex (from dat+hor) and a ``ticker``
        column (one block per symbol). Numeric columns: open, high, low,
        close, volume, trades, turnover, open_interest, cum_trades,
        session_type.

        session_type values:
            1 = Regular session
            5 = After-hours session
            9 = Closing auction

    Example:
        >>> df = bdi("PETR4", "20260519")
        >>> df[["open", "high", "low", "close"]].tail()
    """
    return run_spec(
        SPEC_BDI,
        session_token=session_token,
        ticker=ticker,
        bar_start=f"{to_date_str(start_date)}0000",
    )


@validate_params
def bticks(
    ticker: TickerList,
    start: DateTimeParam,
    end: DateTimeParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Get times-and-trades with top-of-book quotes for one or more B3 symbols.

    Uses the TimesTrades endpoint: every trade (type "TRD") and every
    top-of-book change (type "QTE") in the window. TRD rows carry price,
    size, seq_num and the buyer/seller broker ids in bid_participant/
    ask_participant; QTE rows carry bid/ask price and size and the
    participant ids of the standing orders.

    Like ``bdt``, the request window is interpreted in **UTC** (B3's regular
    session is 13:00-20:00 UTC). Retention is short — only the current
    session returned data in live tests; previous days come back empty.
    The data is dense (thousands of rows per 10 minutes on liquid names),
    so keep windows tight.

    Args:
        ticker: Single symbol or list (e.g., "PETR4" or ["PETR4", "VALE3"]).
        start: Start datetime, UTC (str YYYYMMDDHHMMSS, datetime, or Timestamp)
        end: End datetime, UTC (default: start + 1 hour)
        session_token: BCAA session token

    Returns:
        Flat DataFrame indexed by the exchange timestamp (tz-aware,
        America/Sao_Paulo), oldest first, with a ``ticker`` column (one
        block per symbol). Columns: type, price, size, bid_price, bid_size,
        ask_price, ask_size, bid_participant, ask_participant, seq_num.

    Example:
        >>> # 10:00-10:10 Brasilia = 13:00-13:10 UTC
        >>> df = bticks("PETR4", "20260610130000", "20260610131000")
        >>> trades = df[df["type"] == "TRD"]
    """
    start_str = to_datetime_str(start)
    end_str = default_tick_end(start_str) if end is None else to_datetime_str(end)
    return vectorize(
        ticker, lambda t: bticks_core(t, start_str, end_str, session_token)
    )
