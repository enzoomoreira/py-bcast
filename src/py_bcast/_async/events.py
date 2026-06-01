"""Async corporate events, dividends, and broker portfolios (aetp/output)."""

from __future__ import annotations

import pandas as pd

from .._legacy.columns import (
    CALENDAR_FIELDS,
    CALENDAR_SCHEMA,
    DIVIDEND_FIELDS,
    DIVIDEND_SCHEMA,
    DY_FIELDS,
    DY_SCHEMA,
    PORTFOLIO_FIELDS,
    PORTFOLIO_LIST_FIELDS,
    PORTFOLIO_LIST_SCHEMA,
)
from .._legacy.aetp import rows_to_dicts
from .._core.dates import DateLike, to_date_str
from .._legacy.multi import vectorize_async
from .._core.normalize import ensure_list, ensure_str
from .._legacy.output import to_reference_dataframe
from .._legacy.resolve import aresolve_cvm
from .._core.validation import CvmCode, DateParam, validate_params
from ._helpers import async_aetp_request


@validate_params
async def abcalendar(
    start_date: DateParam,
    end_date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bcalendar``. Corporate events calendar."""
    parsed = await async_aetp_request(
        "fundamental/calendario-eventos-corporativos",
        {"10057": to_date_str(start_date), "10058": to_date_str(end_date)},
        session_token,
    )
    return to_reference_dataframe(
        rows_to_dicts(parsed), rename=CALENDAR_FIELDS, schema=CALENDAR_SCHEMA
    )


async def _abdividends_one(
    ticker: str,
    cvm_code: str | int | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Fetch dividend/JCP history for a single company."""
    ticker = ticker.strip().upper()
    if cvm_code is None:
        cvm_code = await aresolve_cvm(ticker, session_token)
    parsed = await async_aetp_request(
        "fundamental/empresa/eventos/jcp-dividendos",
        {"13004": ensure_str(cvm_code), "10068": ticker},
        session_token,
    )
    return to_reference_dataframe(
        rows_to_dicts(parsed), rename=DIVIDEND_FIELDS, schema=DIVIDEND_SCHEMA
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
    cvm = cvm_code if len(tickers) == 1 else None
    return await vectorize_async(
        tickers, lambda t: _abdividends_one(t, cvm, session_token)
    )


async def _abdy_one(
    ticker: str,
    start_date: DateLike,
    end_date: DateLike,
    cvm_code: str | int | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Fetch the dividend yield series for a single company."""
    ticker = ticker.strip().upper()
    if cvm_code is None:
        cvm_code = await aresolve_cvm(ticker, session_token)
    parsed = await async_aetp_request(
        "fundamental/empresa/eventos/dividend-yield",
        {
            "13004": ensure_str(cvm_code),
            "10068": ticker,
            "10057": to_date_str(start_date),
            "10058": to_date_str(end_date),
            "10029": "1",
        },
        session_token,
    )
    rows = rows_to_dicts(parsed)
    return to_reference_dataframe(rows, rename=DY_FIELDS, schema=DY_SCHEMA)


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
    cvm = cvm_code if len(tickers) == 1 else None
    return await vectorize_async(
        tickers,
        lambda t: _abdy_one(t, start_date, end_date, cvm, session_token),
    )


async def abportfolios(session_token: str | None = None) -> pd.DataFrame:
    """Async version of ``bportfolios``. List of broker recommended portfolios."""
    parsed = await async_aetp_request(
        "fundamental/empresa/carteira-recomendada/corretoras", {}, session_token
    )
    return to_reference_dataframe(
        rows_to_dicts(parsed),
        rename=PORTFOLIO_LIST_FIELDS,
        schema=PORTFOLIO_LIST_SCHEMA,
    )


@validate_params
async def abportfolio(
    broker_id: CvmCode,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bportfolio``. Latest recommended portfolio from a broker."""
    parsed = await async_aetp_request(
        "fundamental/empresa/carteira-recomendada/ultima",
        {"10087": ensure_str(broker_id)},
        session_token,
        empty_ok=False,
    )
    return to_reference_dataframe(rows_to_dicts(parsed), rename=PORTFOLIO_FIELDS)
