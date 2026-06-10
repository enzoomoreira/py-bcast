"""Async Broadcast+ data functions."""

from __future__ import annotations

import pandas as pd

from .._core.dates import to_date_str
from .._core.normalize import ensure_id_list
from .._core.validation import DateParam, Ticker, TickerList, validate_params
from .._plus._async.corporate import corpevents_core
from .._plus._async.funds import fund_core, funds_core
from .._plus._async.news import content_core, headlines_core, sections_core
from .._plus._async.reference import (
    holiday_tables_core,
    index_list_core,
    index_members_core,
    info_core,
    logo_core,
)
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


@validate_params
async def abinfo(symbols: TickerList) -> pd.DataFrame:
    """Async version of ``binfo``. Instrument metadata via Broadcast+.

    Flat DataFrame, one row per resolved symbol. Unknown symbols are omitted;
    an all-unknown request returns an empty DataFrame with the same schema.
    """
    return await info_core(symbols)


@validate_params
async def abindex_members(index: Ticker) -> pd.DataFrame:
    """Async version of ``bindex_members``. Index composition via Broadcast+.

    DataFrame with columns index, symbol, relevance (one row per member).
    Raises NotFoundError if the index code does not exist.
    """
    return await index_members_core(index)


@validate_params
async def ablogo(symbol: Ticker) -> bytes:
    """Async version of ``blogo``. Instrument PNG logo bytes via Broadcast+.

    Raises NotFoundError if the symbol has no logo.
    """
    return await logo_core(symbol)


@validate_params
async def abfunds(query: str) -> pd.DataFrame:
    """Async version of ``bfunds``. Fund search via Broadcast+.

    Flat DataFrame, one row per matching fund, keyed by ``id``. Empty DataFrame
    with the same schema if nothing matches.
    """
    return await funds_core(query)


@validate_params
async def abfund(fund_id: int) -> pd.DataFrame:
    """Async version of ``bfund``. Fund detail by numeric id via Broadcast+.

    Single-row DataFrame. Raises NotFoundError if the id does not exist.
    """
    return await fund_core(fund_id)


async def absections() -> pd.DataFrame:
    """Async version of ``bsections``. News section catalog via Broadcast+."""
    return await sections_core()


@validate_params
async def abheadlines(sections: int | list[int], count: int = 50) -> pd.DataFrame:
    """Async version of ``bheadlines``. Paginated headlines via Broadcast+.

    Flat DataFrame, newest first; empty with schema if the sections have none.
    """
    return await headlines_core([int(s) for s in ensure_id_list(sections)], count)


@validate_params
async def abnews_content(content_id: int | str) -> dict:
    """Async version of ``bnews_content``. Article body + tagging via Broadcast+.

    Raises NotFoundError if the id does not exist or is not accessible.
    """
    return await content_core(content_id)


@validate_params
async def abcorpevents(symbol: Ticker) -> pd.DataFrame:
    """Async version of ``bcorpevents``. Corporate events with adjustment factors.

    Raises NotFoundError if the symbol does not exist; empty-with-schema if it
    has no events.
    """
    return await corpevents_core(symbol)


async def abindexes() -> pd.DataFrame:
    """Async version of ``bindexes``. Available index codes via Broadcast+."""
    return await index_list_core()


async def abholidays() -> pd.DataFrame:
    """Async version of ``bholidays``. Holiday-table catalog via Broadcast+."""
    return await holiday_tables_core()
