"""Async fundamental data functions."""

from __future__ import annotations

import pandas as pd

from .._core.dates import DateLike
from .._core.normalize import ensure_list
from .._core.validation import TickerList, validate_params
from .._legacy.aetp import rows_to_dicts
from .._legacy.columns import QUOTE_FIELDS, QUOTE_SCHEMA
from .._legacy.endpoints import (
    SPEC_BCOMPANY_DETAIL,
    SPEC_BCOMPANY_LIST,
    SPEC_BCONSENSUS,
    SPEC_BINDICATOR_META,
    SPEC_BINDICATORS,
    SPEC_BINDICES,
    SPEC_BSECTORS,
    SPEC_BSHARES,
    SPEC_BTICKERS,
)
from .._legacy.multi import vectorize_async
from .._legacy.output import Index, finalize_frame
from ._helpers import async_aetp_request
from .executor import arun_spec


async def abcompany(
    cvm_code: str | int | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bcompany``.

    Without ``cvm_code``: the full company list. With ``cvm_code``: detail for
    one company (NotFoundError if unknown).
    """
    if cvm_code is None:
        return await arun_spec(SPEC_BCOMPANY_LIST, session_token=session_token)
    return await arun_spec(
        SPEC_BCOMPANY_DETAIL, session_token=session_token, cvm_code=cvm_code
    )


@validate_params
async def abconsensus(
    ticker: TickerList,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bconsensus``.

    Flat DataFrame (one row per covered ticker) with a ``ticker`` column. A
    ticker with no analyst coverage contributes an empty block.
    """
    return await arun_spec(SPEC_BCONSENSUS, session_token=session_token, ticker=ticker)


async def _abquote_one(
    ticker: str,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Fetch the quote for a single symbol (one row, or empty with schema).

    Soft (empty_ok default): an unknown ticker yields an empty block rather
    than raising — symmetry with sync ``_quote_one``.
    """
    parsed = await async_aetp_request(
        "fundamental/ativo/cotacao", {"10068": ticker}, session_token
    )
    rows = rows_to_dicts(parsed)
    record = rows[0] if rows else {}
    return finalize_frame(
        record, index=Index.RECORD, rename=QUOTE_FIELDS, schema=QUOTE_SCHEMA
    )


async def abquote(
    ticker: str | list[str],
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bquote``.

    Flat DataFrame with quote fields (one row per symbol), each block tagged
    with a ``ticker`` column. Empty DataFrame with schema if no symbol has a
    quote.
    """
    return await vectorize_async(
        ensure_list(ticker), lambda t: _abquote_one(t, session_token)
    )


async def abtickers(
    ticker_or_cvm: str | int | list[str | int],
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``btickers``. Accepts ticker or CVM code (or a list).

    The endpoint emits its own ``ticker`` column (the company's symbols), so
    that column is NOT the lookup identifier.
    """
    return await arun_spec(
        SPEC_BTICKERS, session_token=session_token, ticker_or_cvm=ticker_or_cvm
    )


async def abshares(
    ticker: str | list[str],
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bshares``.

    Flat DataFrame with shares data (one row per ticker). Raises NotFoundError
    if any ticker is unknown (fail-fast).
    """
    return await arun_spec(SPEC_BSHARES, session_token=session_token, ticker=ticker)


async def abindices(session_token: str | None = None) -> pd.DataFrame:
    """Async version of ``bindices``. List of B3 market indices."""
    return await arun_spec(SPEC_BINDICES, session_token=session_token)


async def absectors(session_token: str | None = None) -> pd.DataFrame:
    """Async version of ``bsectors``. B3 sector/subsector/segment classification."""
    return await arun_spec(SPEC_BSECTORS, session_token=session_token)


async def abindicator_meta(session_token: str | None = None) -> pd.DataFrame:
    """Async version of ``bindicator_meta``. Metadata for all indicators."""
    return await arun_spec(SPEC_BINDICATOR_META, session_token=session_token)


async def abindicators(
    ticker_or_cvm: str | int | list[str | int],
    indicator: str | int,
    start_date: DateLike,
    end_date: DateLike,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bindicators``.

    Flat DataFrame (RangeIndex), one row per (date, share class): a string
    ``date`` column, the indicator ``value``, its day-over-day
    ``value_change_pct``, and a ``ticker`` column holding the per-row share
    class (a "PETR4" query returns both PETR3 and PETR4), not the input.
    """
    return await arun_spec(
        SPEC_BINDICATORS,
        session_token=session_token,
        ticker_or_cvm=ticker_or_cvm,
        indicator=indicator,
        start_date=start_date,
        end_date=end_date,
    )
