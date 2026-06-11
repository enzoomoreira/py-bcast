"""Async corporate events, dividends, and broker portfolios (aetp/output)."""

from __future__ import annotations

import pandas as pd

from .._core.dates import DateLike
from .._core.normalize import ensure_list
from .._core.validation import CvmCode, DateParam, Ticker, validate_params
from .._legacy.endpoints import (
    SPEC_BCALENDAR,
    SPEC_BDIVIDENDS,
    SPEC_BDIVIDENDS_BYCVM,
    SPEC_BDY,
    SPEC_BDY_BYCVM,
    SPEC_BPORTFOLIO,
    SPEC_BPORTFOLIOS,
    SPEC_BPORTFOLIOS_WITH,
)
from .._legacy._async.executor import run_spec as arun_spec


@validate_params
async def abcalendar(
    start_date: DateParam,
    end_date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bcalendar``. Corporate events calendar."""
    return await arun_spec(
        SPEC_BCALENDAR,
        session_token=session_token,
        start_date=start_date,
        end_date=end_date,
    )


async def abdividends(
    ticker: str | list[str],
    cvm_code: str | int | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bdividends``.

    Flat DataFrame with dividend events and a ``ticker`` column (one block per
    company). A scalar ``cvm_code`` is honored only for a single ticker.
    """
    tickers = [t.strip().upper() for t in ensure_list(ticker)]
    if cvm_code is not None and len(tickers) == 1:
        return await arun_spec(
            SPEC_BDIVIDENDS_BYCVM,
            session_token=session_token,
            ticker=tickers,
            cvm_code=cvm_code,
        )
    return await arun_spec(SPEC_BDIVIDENDS, session_token=session_token, ticker=tickers)


async def abdy(
    ticker: str | list[str],
    start_date: DateLike,
    end_date: DateLike,
    cvm_code: str | int | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bdy``.

    Flat DataFrame with a DatetimeIndex, DY values over time, and a ``ticker``
    column (one block per company).
    """
    tickers = [t.strip().upper() for t in ensure_list(ticker)]
    if cvm_code is not None and len(tickers) == 1:
        return await arun_spec(
            SPEC_BDY_BYCVM,
            session_token=session_token,
            ticker=tickers,
            cvm_code=cvm_code,
            start_date=start_date,
            end_date=end_date,
        )
    return await arun_spec(
        SPEC_BDY,
        session_token=session_token,
        ticker=tickers,
        start_date=start_date,
        end_date=end_date,
    )


async def abportfolios(session_token: str | None = None) -> pd.DataFrame:
    """Async version of ``bportfolios``. List of broker recommended portfolios."""
    return await arun_spec(SPEC_BPORTFOLIOS, session_token=session_token)


@validate_params
async def abportfolio(
    broker_id: CvmCode,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bportfolio``. Latest recommended portfolio from a broker."""
    return await arun_spec(
        SPEC_BPORTFOLIO, session_token=session_token, broker_id=broker_id
    )


@validate_params
async def abportfolios_with(
    ticker: Ticker,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bportfolios_with``.

    Full composition of every recommended portfolio containing the ticker
    (same columns as ``bportfolio``); empty frame with schema if none does.
    """
    return await arun_spec(
        SPEC_BPORTFOLIOS_WITH, session_token=session_token, ticker=ticker
    )
