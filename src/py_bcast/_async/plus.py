"""Async Broadcast+ data functions."""

from __future__ import annotations

import pandas as pd

from .._core.dates import to_date_str
from .._core.validation import DateParam, Ticker, validate_params
from .._plus._async.trades import trades_core


@validate_params
async def abtrades(
    ticker: Ticker,
    date: DateParam,
) -> pd.DataFrame:
    """Async version of ``btrades``. Intraday times & trades via Broadcast+.

    DataFrame with a Sao Paulo tz-aware DatetimeIndex and a ``ticker`` column
    (most recent 500 trades, sorted oldest-first). Empty DataFrame with the
    same schema if no trades are found.
    """
    return await trades_core(ticker, to_date_str(date))
