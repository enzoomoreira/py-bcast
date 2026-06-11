"""Async fundamental data functions."""

from __future__ import annotations

import pandas as pd

from .._core.validation import (
    CvmCode,
    DateParam,
    TickerList,
    validate_params,
)
from .._legacy._async.executor import run_spec as arun_spec
from .._legacy._async.quote import quote_one
from .._legacy.endpoints import (
    SPEC_BCOMPANY_DETAIL,
    SPEC_BCOMPANY_LIST,
    SPEC_BCONSENSUS,
    SPEC_BFILINGS,
    SPEC_BFREE_FLOAT,
    SPEC_BFUND_HOLDERS,
    SPEC_BINDICATOR_META,
    SPEC_BINDICATORS,
    SPEC_BINDICES,
    SPEC_BSECTORS,
    SPEC_BSECTOR_MEMBERS,
    SPEC_BSHAREHOLDER_DATES,
    SPEC_BSHARES,
    SPEC_BSTATEMENT_DATES,
    SPEC_BTICKERS,
)
from .._legacy.multi import vectorize_async


@validate_params
async def abcompany(
    cvm_code: CvmCode | None = None,
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


@validate_params
async def abquote(
    ticker: TickerList,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bquote``.

    Flat DataFrame with quote fields (one row per symbol), each block tagged
    with a ``ticker`` column. Empty DataFrame with schema if no symbol has a
    quote.
    """
    return await vectorize_async(ticker, lambda t: quote_one(t, session_token))


@validate_params
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


@validate_params
async def abshares(
    ticker: TickerList,
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


@validate_params
async def abfree_float(
    ticker_or_cvm: str | int | list[str | int],
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bfree_float``.

    One row per share class (ON/PN/UNIT) with free float and units
    composition. The endpoint emits its own ``ticker`` column (the company's
    share classes). Raises NotFoundError if any identifier is unknown.
    """
    return await arun_spec(
        SPEC_BFREE_FLOAT, session_token=session_token, ticker_or_cvm=ticker_or_cvm
    )


@validate_params
async def abfund_holders(
    ticker_or_cvm: str | int | list[str | int],
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bfund_holders``.

    One row per fund position, each block tagged with a ``ticker`` column
    holding the queried identifier. A company no fund holds contributes an
    empty block.
    """
    return await arun_spec(
        SPEC_BFUND_HOLDERS, session_token=session_token, ticker_or_cvm=ticker_or_cvm
    )


@validate_params
async def abshareholder_dates(
    ticker_or_cvm: str | int | list[str | int],
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bshareholder_dates``.

    One row per published shareholder composition (reference_date,
    position_date), each block tagged with a ``ticker`` column holding the
    queried identifier.
    """
    return await arun_spec(
        SPEC_BSHAREHOLDER_DATES,
        session_token=session_token,
        ticker_or_cvm=ticker_or_cvm,
    )


@validate_params
async def abfilings(
    ticker_or_cvm: str | int | list[str | int],
    start_date: DateParam,
    end_date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bfilings``.

    One row per financial-statement PDF (date, url) in the window, each
    block tagged with a ``ticker`` column holding the queried identifier.
    """
    return await arun_spec(
        SPEC_BFILINGS,
        session_token=session_token,
        ticker_or_cvm=ticker_or_cvm,
        start_date=start_date,
        end_date=end_date,
    )


@validate_params
async def abindicators(
    ticker_or_cvm: str | int | list[str | int],
    indicator: str | int,
    start_date: DateParam,
    end_date: DateParam,
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


async def absector_members(
    sector_id: int,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bsector_members``.

    Every company under a B3 sector id (RangeIndex). Empty frame for an
    unpopulated (subsector/segment) id.
    """
    return await arun_spec(
        SPEC_BSECTOR_MEMBERS, session_token=session_token, sector_id=sector_id
    )


@validate_params
async def abstatement_dates(
    ticker_or_cvm: str | int | list[str | int],
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bstatement_dates``.

    The latest annual (DFP) and quarterly (ITR) statement dates per company,
    each row tagged with a ``ticker`` column. NotFoundError if unknown.
    """
    return await arun_spec(
        SPEC_BSTATEMENT_DATES,
        session_token=session_token,
        ticker_or_cvm=ticker_or_cvm,
    )
