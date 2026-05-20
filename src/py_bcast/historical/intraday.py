"""Intraday bars and tick-by-tick data via ContentProxy."""

from __future__ import annotations

import datetime

import pandas as pd

from .._core.dates import DateLike, to_date_str, to_datetime_str
from .._core.output import to_dataframe
from .._core.xml_helpers import content_proxy_get, parse_ticks


def bdt(
    ticker: str,
    start: DateLike,
    end: DateLike | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Get tick-by-tick (trade) data for a symbol.

    Uses HistoricoTick endpoint. Works for international instruments:
    FX pairs (USDBRL, EURUSD, GBPUSD, etc.), precious metals (GOLD, SILVER),
    energy (WTI), indices (DAX, FTSE, VIX, DXY), treasuries (US10Y, US2Y).

    Note: B3/BVMF instruments return empty due to server-side query
    registration requirement.

    Args:
        ticker: Symbol (e.g., "USDBRL", "GOLD", "EURUSD", "DAX")
        start: Start datetime (str YYYYMMDDHHMMSS, datetime, or Timestamp)
        end: End datetime (default: start + 1 hour)
        session_token: BCAA session token

    Returns:
        DataFrame with DatetimeIndex (from dat+hor) and numeric columns:
        last, size, neg, open_interest, calendar_days, working_days.

    Example:
        >>> df = bdt("USDBRL", "20260519100000", "20260519103000")
        >>> df["last"].plot()
    """
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
    return to_dataframe(ticks, date_col="dat", time_col="hor")


def bdi(
    ticker: str,
    start_date: DateLike,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Get intraday OHLCV bars (2-minute candles) for a symbol.

    Uses HistoricoIntraday endpoint. Works for ALL instruments (B3 + international).
    Returns bars from start_date up to the current time.

    Args:
        ticker: Symbol (e.g., "PETR4", "VALE3", "USDBRL", "GOLD")
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        session_token: BCAA session token

    Returns:
        DataFrame with DatetimeIndex (from dat+hor) and numeric columns:
        open, high, low, last (close), qtt, neg, total_value,
        open_interest, total_neg, tipo_intervalo.

        tipo_intervalo values:
            1 = Regular session
            5 = After-hours session
            9 = Closing auction

    Example:
        >>> df = bdi("PETR4", "20260519")
        >>> df[["open", "high", "low", "last"]].tail()
    """
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
    return to_dataframe(bars, date_col="dat", time_col="hor")
