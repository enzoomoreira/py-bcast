"""Async fundamental data functions."""

from __future__ import annotations

import datetime

import pandas as pd

from .._core.aetp import rows_to_dicts
from .._core.binary import parse_binary_response
from .._core.columns import (
    COMPANY_DETAIL_FIELDS,
    COMPANY_LIST_FIELDS,
    COMPANY_LIST_SCHEMA,
    CONSENSUS_FIELDS,
    CONSENSUS_SCHEMA,
    QUOTE_FIELDS,
    QUOTE_SCHEMA,
    SHARES_FIELDS,
    SHARES_SCHEMA,
    TICKER_FIELDS,
)
from .._core.constants import BASE_URL
from .._core.exceptions import ProtocolError, is_no_records
from .._core.http import get_async_http_client, get_session_token
from .._core.logging import get_logger
from .._core.multi import vectorize_async
from .._core.normalize import ensure_id_list, ensure_list, ensure_str
from .._core.output import to_record_dataframe, to_reference_dataframe
from .._core.ratelimit import rate_limit_async
from .._core.resolve import resolve_cvm
from .._core.validation import TickerList, validate_params
from ._helpers import async_aetp_request

logger = get_logger(__name__)


async def abcompany(
    cvm_code: str | int | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bcompany``.

    Without ``cvm_code``: the full company list. With ``cvm_code``: detail for
    one company (NotFoundError if unknown).
    """
    if cvm_code is None:
        parsed = await async_aetp_request(
            "fundamental/empresa/metadado", {}, session_token
        )
        return to_reference_dataframe(
            rows_to_dicts(parsed),
            rename=COMPANY_LIST_FIELDS,
            schema=COMPANY_LIST_SCHEMA,
        )
    parsed = await async_aetp_request(
        "fundamental/empresa",
        {"13004": ensure_str(cvm_code)},
        session_token,
        empty_ok=False,
    )
    return to_reference_dataframe(rows_to_dicts(parsed), rename=COMPANY_DETAIL_FIELDS)


async def _abconsensus_one(
    ticker: str,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Get analyst consensus for a single ticker (soft: no coverage -> empty)."""
    token = get_session_token(session_token)
    s = get_async_http_client()
    today = datetime.date.today().strftime("%Y%m%d")

    await rate_limit_async()
    r = await s.get(
        f"{BASE_URL}/aefundamental/{ticker}/consenso",
        params={"10023": "4", "10039": token, "10068": ticker, "13004": today},
        timeout=15,
    )

    try:
        parsed = parse_binary_response(r.content)
    except ProtocolError as exc:
        # No coverage for this (valid) ticker reads as an empty result, not a
        # missing entity — small caps simply have no analyst consensus.
        if is_no_records(exc.error_tag):
            logger.debug("abconsensus: no consensus for %s", ticker)
            return to_record_dataframe({}, schema=CONSENSUS_SCHEMA)
        raise

    rows = rows_to_dicts(parsed)
    record = rows[0] if rows else {}
    return to_record_dataframe(
        record, rename=CONSENSUS_FIELDS, schema=CONSENSUS_SCHEMA, ticker=ticker
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
    return await vectorize_async(ticker, lambda t: _abconsensus_one(t, session_token))


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
    return to_record_dataframe(record, rename=QUOTE_FIELDS, schema=QUOTE_SCHEMA)


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


async def _abtickers_one(
    ticker_or_cvm: str | int,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Fetch all tickers for one company (by CVM code or ticker)."""
    if isinstance(ticker_or_cvm, int) or str(ticker_or_cvm).isdigit():
        cvm_code = int(ticker_or_cvm)
    else:
        cvm_code = resolve_cvm(str(ticker_or_cvm), session_token)
    parsed = await async_aetp_request(
        "fundamental/ativo/simbolo",
        {"13004": str(cvm_code)},
        session_token,
        empty_ok=False,
    )
    return to_reference_dataframe(rows_to_dicts(parsed), rename=TICKER_FIELDS)


async def abtickers(
    ticker_or_cvm: str | int | list[str | int],
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``btickers``. Accepts ticker or CVM code (or a list).

    The endpoint emits its own ``ticker`` column (the company's symbols), so
    that column is NOT the lookup identifier.
    """
    return await vectorize_async(
        ensure_id_list(ticker_or_cvm), lambda x: _abtickers_one(x, session_token)
    )


async def _abshares_one(
    ticker: str,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Fetch shares outstanding for a single ticker (raises if unknown)."""
    parsed = await async_aetp_request(
        "fundamental/ativo/quantidade",
        {"10068": ticker},
        session_token,
        empty_ok=False,
    )
    rows = rows_to_dicts(parsed)
    record = rows[0] if rows else {}
    return to_record_dataframe(record, rename=SHARES_FIELDS, schema=SHARES_SCHEMA)


async def abshares(
    ticker: str | list[str],
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bshares``.

    Flat DataFrame with shares data (one row per ticker). Raises NotFoundError
    if any ticker is unknown (fail-fast).
    """
    return await vectorize_async(
        ensure_list(ticker), lambda t: _abshares_one(t, session_token)
    )
