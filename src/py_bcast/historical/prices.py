"""Historical daily closing prices and OHLCV via ContentProxy."""

from __future__ import annotations

import pandas as pd

from .._core.dates import business_days, default_end_date, to_date_str
from .._core.normalize import ensure_list
from .._core.validation import DateParam, TickerList, validate_params
from .._legacy._sync.bdh import bdh_core, bdh_ohlcv_one
from .._legacy.multi import vectorize
from .._legacy.output import empty_bdh_frame


@validate_params
def bdh(
    tickers: TickerList,
    start_date: DateParam,
    end_date: DateParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch historical closing prices for one or more tickers.

    Uses HistoricoFechamentos endpoint (works for ALL instruments).

    Args:
        tickers: Single ticker or list (e.g., "PETR4" or ["PETR4", "VALE3"])
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: End date (default: today)
        session_token: BCAA session token (or set BROADCAST_SESSION env var)

    Returns:
        Flat (long) DataFrame with a DatetimeIndex and a ``ticker`` column
        (one block of rows per symbol). Columns: ticker, close, settle,
        settle_rate, yield. Empty DataFrame with that schema if no data.

    Example:
        >>> df = bdh(["PETR4", "VALE3"], "20260501", "20260519")
        >>> df[df["ticker"] == "PETR4.BVMF"]["close"].plot()
    """
    tickers = ensure_list(tickers)
    start_str = to_date_str(start_date)
    end_str = to_date_str(end_date) if end_date is not None else default_end_date()

    dates = business_days(start_str, end_str)
    if not dates:
        return empty_bdh_frame()
    return bdh_core(tickers, dates, session_token)


@validate_params
def bdh_ohlcv(
    ticker: TickerList,
    date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Get full OHLCV data for one or more tickers on a single date.

    Uses HistoricoData endpoint.

    Args:
        ticker: Single ticker or list (e.g., "PETR4" or ["PETR4", "VALE3"]).
        date: Date (str YYYYMMDD, date, datetime, or Timestamp)
        session_token: BCAA session token

    Returns:
        Flat DataFrame with a DatetimeIndex and a ``ticker`` column (one row
        per ticker). Columns: ticker, close, settle, settle_rate, low, high,
        open, trades, volume, turnover, open_interest, vwap, cum_trades.
        Empty DataFrame with that schema if there is no data for the date;
        NotFoundError for an unknown ticker.

    Example:
        >>> df = bdh_ohlcv("PETR4", "20260519")
        >>> print(df["close"].iloc[0], df["high"].iloc[0])
    """
    return vectorize(ticker, lambda t: bdh_ohlcv_one(t, date, session_token))
