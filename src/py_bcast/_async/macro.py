"""Async macroeconomic indicator functions."""

from __future__ import annotations

import pandas as pd

from .._core.validation import DateParam, Ticker, TickerList, validate_params
from .._legacy.endpoints import (
    SPEC_BDI_CDI,
    SPEC_BFX,
    SPEC_BINFLATION,
    SPEC_BINFLATION_HISTORY,
    SPEC_BMACRO,
    SPEC_BRETURN,
    SPEC_BSNAPSHOT,
    SPEC_BSTATS,
    SPEC_BVOLUME,
)
from .._legacy.multi import vectorize_async
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
    symbol). The special symbol "CDI" routes to DiCetipAcumulado.
    """

    async def one(symbol: str) -> pd.DataFrame:
        if symbol == "CDI":
            df = await arun_spec(
                SPEC_BDI_CDI,
                session_token=session_token,
                start_date=start_date,
                end_date=end_date,
            )
            df.insert(0, "ticker", "CDI")
            return df
        return await arun_spec(
            SPEC_BMACRO,
            session_token=session_token,
            ticker=symbol,
            start_date=start_date,
            end_date=end_date,
        )

    return await vectorize_async(ticker, one)


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


@validate_params
async def abfx(
    from_currency: Ticker,
    to_currency: Ticker,
    amount: float = 1.0,
    session_token: str | None = None,
) -> float:
    """Async version of ``bfx``.

    Spot currency conversion; returns the converted amount as a float.
    Raises NotFoundError for an unknown currency pair.
    """
    df = await arun_spec(
        SPEC_BFX,
        session_token=session_token,
        from_currency=from_currency,
        to_currency=to_currency,
        amount=amount,
    )
    return float(df["close"].iloc[0])


@validate_params
async def abstats(
    tickers: TickerList,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bstats``.

    Flat DataFrame (RangeIndex), one row per symbol with the market-stats
    snapshot (bid/ask at the close, dividend yield, 52-week range, average
    turnover). Unknown symbols are omitted.
    """
    return await arun_spec(SPEC_BSTATS, session_token=session_token, tickers=tickers)


@validate_params
async def absnapshot(
    tickers: TickerList,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bsnapshot``.

    Flat DataFrame (RangeIndex), one row per symbol with the latest intraday
    session snapshot (OHLC, volume, trades). Unknown symbols are omitted.
    """
    return await arun_spec(SPEC_BSNAPSHOT, session_token=session_token, tickers=tickers)


async def abinflation(
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``binflation``."""
    return await arun_spec(SPEC_BINFLATION, session_token=session_token)


@validate_params
async def abinflation_history(
    symbol: TickerList,
    start_date: DateParam,
    end_date: DateParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``binflation_history``.

    Flat DataFrame with a DatetimeIndex and a ``ticker`` column (one block per
    inflation symbol) and an ``accumulated`` column (% since start_date).
    """
    return await arun_spec(
        SPEC_BINFLATION_HISTORY,
        session_token=session_token,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )
