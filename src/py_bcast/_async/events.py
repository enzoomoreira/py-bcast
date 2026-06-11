"""Async corporate events, dividends, and broker portfolios (aetp/output)."""

from __future__ import annotations

import pandas as pd

from .._core.exceptions import ValidationError
from .._core.validation import (
    CvmCode,
    DateParam,
    Ticker,
    TickerList,
    validate_params,
)
from .._legacy.endpoints import (
    SPEC_BCALENDAR,
    SPEC_BDIVIDENDS,
    SPEC_BDIVIDENDS_BYCVM,
    SPEC_BDY,
    SPEC_BDY_BYCVM,
    SPEC_BPORTFOLIO,
    SPEC_BPORTFOLIO_AT,
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


@validate_params
async def abdividends(
    ticker: TickerList,
    cvm_code: CvmCode | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bdividends``.

    Flat DataFrame with dividend events and a ``ticker`` column (one block per
    company). A scalar ``cvm_code`` is honored only for a single ticker.
    """
    tickers = ticker  # TickerList: already a normalized, uppercased list
    if cvm_code is not None and len(tickers) == 1:
        return await arun_spec(
            SPEC_BDIVIDENDS_BYCVM,
            session_token=session_token,
            ticker=tickers,
            cvm_code=cvm_code,
        )
    return await arun_spec(SPEC_BDIVIDENDS, session_token=session_token, ticker=tickers)


@validate_params
async def abdy(
    ticker: TickerList,
    start_date: DateParam,
    end_date: DateParam,
    cvm_code: CvmCode | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bdy``.

    Flat DataFrame (RangeIndex) with a string ``date`` column, the DY values,
    and a ``ticker`` column (one block per company).
    """
    tickers = ticker  # TickerList: already a normalized, uppercased list
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


@validate_params
async def abportfolio(
    broker_id: CvmCode | None = None,
    date: DateParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bportfolio``.

    Without ``broker_id``: the list of brokers that publish portfolios.
    With ``broker_id``: the broker's current portfolios. Adding ``date``:
    the composition in force on that date (empty frame before the first).
    """
    if broker_id is None:
        if date is not None:
            raise ValidationError("bportfolio: date requires broker_id")
        return await arun_spec(SPEC_BPORTFOLIOS, session_token=session_token)
    if date is None:
        return await arun_spec(
            SPEC_BPORTFOLIO, session_token=session_token, broker_id=broker_id
        )
    return await arun_spec(
        SPEC_BPORTFOLIO_AT,
        session_token=session_token,
        broker_id=broker_id,
        date=date,
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
