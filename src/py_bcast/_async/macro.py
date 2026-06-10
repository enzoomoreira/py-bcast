"""Async macroeconomic indicator functions."""

from __future__ import annotations

import pandas as pd

from .._core.validation import DateParam, TickerList, validate_params
from .._legacy.endpoints import (
    SPEC_BDI_CDI,
    SPEC_BINFLATION,
    SPEC_BMACRO,
    SPEC_BRETURN,
    SPEC_BVOLUME,
)
from .._legacy._async.executor import run_spec as arun_spec


@validate_params
async def abmacro(
    ticker: TickerList,
    start_date: DateParam,
    end_date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bmacro``.

    Flat DataFrame with a DatetimeIndex and a ``ticker`` column (one block per
    symbol).
    """
    return await arun_spec(
        SPEC_BMACRO,
        session_token=session_token,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
    )


@validate_params
async def abdi_cdi(
    start_date: DateParam,
    end_date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bdi_cdi`` (single series, no ticker arg)."""
    return await arun_spec(
        SPEC_BDI_CDI,
        session_token=session_token,
        start_date=start_date,
        end_date=end_date,
    )


@validate_params
async def abreturn(
    ticker: TickerList,
    start_date: DateParam,
    end_date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``breturn``.

    Flat DataFrame with a DatetimeIndex and a ``ticker`` column (one block per
    symbol).
    """
    return await arun_spec(
        SPEC_BRETURN,
        session_token=session_token,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
    )


@validate_params
async def abvolume(
    tickers: TickerList,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bvolume``.

    Flat DataFrame (RangeIndex), one row per (ticker, averaging window).
    ``ticker`` stays a column because it repeats per window.
    """
    return await arun_spec(SPEC_BVOLUME, session_token=session_token, tickers=tickers)


async def abinflation(
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``binflation``."""
    return await arun_spec(SPEC_BINFLATION, session_token=session_token)
