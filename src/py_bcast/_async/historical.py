"""Async historical data functions."""

from __future__ import annotations

import pandas as pd

from .._core.dates import (
    business_days,
    default_end_date,
    default_tick_end,
    to_date_str,
    to_datetime_str,
)
from .._core.normalize import ensure_list
from .._core.validation import DateParam, DateTimeParam, TickerList, validate_params
from .._legacy._async.bdh import bdh_core, bdh_ohlcv_one
from .._legacy._async.executor import run_spec as arun_spec
from .._legacy.endpoints import SPEC_BDI, SPEC_BDT
from .._legacy.multi import vectorize_async
from .._legacy.output import empty_bdh_frame


@validate_params
async def abdh(
    tickers: TickerList,
    start_date: DateParam,
    end_date: DateParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bdh``. Fetch historical closing prices.

    Returns a flat (long) DataFrame with a DatetimeIndex and a ``ticker``
    column (one block of rows per symbol). Empty DataFrame with that schema
    if there is no data.
    """
    tickers = ensure_list(tickers)
    start_str = to_date_str(start_date)
    end_str = to_date_str(end_date) if end_date is not None else default_end_date()

    dates = business_days(start_str, end_str)
    if not dates:
        return empty_bdh_frame()
    return await bdh_core(tickers, dates, session_token)


@validate_params
async def abdh_ohlcv(
    ticker: TickerList,
    date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bdh_ohlcv``.

    Flat DataFrame with a DatetimeIndex and a ``ticker`` column (one row per
    ticker). Empty DataFrame with schema if there is no data for the date;
    NotFoundError for an unknown ticker.
    """
    return await vectorize_async(
        ticker, lambda t: bdh_ohlcv_one(t, date, session_token)
    )


@validate_params
async def abdt(
    ticker: TickerList,
    start: DateTimeParam,
    end: DateTimeParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bdt``. Fetch tick-by-tick data.

    Flat DataFrame with a DatetimeIndex (from dat+hor) and a ``ticker`` column
    (one block per symbol).
    """
    start_str = to_datetime_str(start)
    end_str = default_tick_end(start_str) if end is None else to_datetime_str(end)
    return await arun_spec(
        SPEC_BDT,
        session_token=session_token,
        ticker=ticker,
        start=start_str,
        end=end_str,
    )


@validate_params
async def abdi(
    ticker: TickerList,
    start_date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bdi``. Fetch intraday bars.

    Flat DataFrame with a DatetimeIndex (from dat+hor) and a ``ticker`` column
    (one block per symbol).
    """
    return await arun_spec(
        SPEC_BDI,
        session_token=session_token,
        ticker=ticker,
        bar_start=f"{to_date_str(start_date)}0000",
    )
