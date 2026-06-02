"""Intraday bars and tick-by-tick data via ContentProxy."""

from __future__ import annotations

import datetime

import pandas as pd

from .._core.dates import to_date_str, to_datetime_str
from .._legacy.columns import INTRADAY_BAR_SCHEMA, TICK_SCHEMA
from .._legacy.multi import vectorize
from .._legacy.output import to_dataframe
from .._core.validation import DateParam, DateTimeParam, TickerList, validate_params
from .._legacy.xml_helpers import content_proxy_get, parse_ticks


def _bdt_one(
    ticker: str,
    start: str,
    end: str | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Get tick-by-tick data for a single symbol."""
    start_str = to_datetime_str(start)

    if end is None:
        dt = datetime.datetime.strptime(start_str, "%Y%m%d%H%M%S")
        end_str = (dt + datetime.timedelta(hours=1)).strftime("%Y%m%d%H%M%S")
    else:
        end_str = to_datetime_str(end)

    root = content_proxy_get(
        "BaseHistoricaNumerica/HistoricoTick",
        {"305": ticker, "10071": start_str, "10072": end_str},
        session_token=session_token,
        timeout=60,
    )

    ticks = parse_ticks(root)
    # API returns newest first — reverse to chronological order
    ticks.reverse()
    return to_dataframe(ticks, date_col="dat", time_col="hor", schema=TICK_SCHEMA)


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
    return vectorize(ticker, lambda t: _bdt_one(t, start, end, session_token))


def _bdi_one(
    ticker: str,
    start_date: str,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Get intraday OHLCV bars for a single symbol."""
    date_str = to_date_str(start_date)
    # Format: YYYYMMDDHHMM (12 digits). Server uses only the date portion;
    # the last 4 digits (HHMM) are required but ignored.
    tag_10074 = f"{date_str}0000"

    root = content_proxy_get(
        "BaseHistoricaNumerica/HistoricoIntraday",
        {"305": ticker, "10074": tag_10074, "10029": "4"},
        session_token=session_token,
        timeout=60,
    )

    bars = parse_ticks(root)
    # API returns newest first — reverse to chronological order
    bars.reverse()
    return to_dataframe(
        bars, date_col="dat", time_col="hor", schema=INTRADAY_BAR_SCHEMA
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
    return vectorize(ticker, lambda t: _bdi_one(t, start_date, session_token))
