"""Async fundamental data functions."""

from __future__ import annotations

import pandas as pd

from .._core.aetp import rows_to_dicts
from .._core.dates import DateLike, to_date_str
from .._core.exceptions import ProtocolError
from .._core.logging import get_logger
from .._core.normalize import ensure_str
from .._core.output import to_reference_dataframe, to_series
from .._core.resolve import resolve_cvm
from .._core.validation import CvmCode, Ticker, validate_params
from ._helpers import async_aetp_request

logger = get_logger(__name__)


async def abcompany(
    cvm_code: str | int | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bcompany``."""
    if cvm_code is None:
        parsed = await async_aetp_request(
            "fundamental/empresa/metadado", {}, session_token
        )
    else:
        parsed = await async_aetp_request(
            "fundamental/empresa",
            {"13004": ensure_str(cvm_code)},
            session_token,
        )
    return to_reference_dataframe(rows_to_dicts(parsed))


@validate_params
async def abconsensus(
    ticker: Ticker,
    session_token: str | None = None,
) -> pd.Series:
    """Async version of ``bconsensus``."""
    import datetime
    from .._core.constants import BASE_URL
    from .._core.http import get_async_http_client, get_session_token, base_params
    from .._core.binary import parse_binary_response
    from .._core.ratelimit import rate_limit_async

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
    except ProtocolError:
        return pd.Series(dtype="object")

    if not parsed["rows"]:
        return pd.Series(dtype="object")

    from .._core.output import to_series
    _CONSENSO_FIELDS = {
        "13019": "buy", "13020": "hold", "13021": "sell",
        "13022": "total_analysts", "13023": "target_low", "13024": "target_high",
        "13025": "target_mean", "13026": "target_median", "13027": "upside_pct",
    }
    result = {}
    row = parsed["rows"][0]
    for i, tag in enumerate(parsed["fields"]):
        if i < len(row):
            name = _CONSENSO_FIELDS.get(tag, tag)
            result[name] = row[i]
    return to_series(result, rename=None)


@validate_params
async def abquote(
    ticker: Ticker,
    session_token: str | None = None,
) -> pd.Series:
    """Async version of ``bquote``."""
    try:
        parsed = await async_aetp_request(
            "fundamental/ativo/cotacao",
            {"10068": ticker},
            session_token,
        )
    except ProtocolError:
        return pd.Series(dtype="object")
    rows = rows_to_dicts(parsed)
    return to_series(rows[0]) if rows else pd.Series(dtype="object")


async def abtickers(
    ticker_or_cvm: str | int,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``btickers``. Accepts ticker or CVM code."""
    if isinstance(ticker_or_cvm, int) or str(ticker_or_cvm).isdigit():
        cvm_code = int(ticker_or_cvm)
    else:
        cvm_code = resolve_cvm(str(ticker_or_cvm), session_token)
    parsed = await async_aetp_request(
        "fundamental/ativo/simbolo",
        {"13004": str(cvm_code)},
        session_token,
    )
    return to_reference_dataframe(rows_to_dicts(parsed))


@validate_params
async def abshares(
    ticker: Ticker,
    session_token: str | None = None,
) -> pd.Series:
    """Async version of ``bshares``."""
    parsed = await async_aetp_request(
        "fundamental/ativo/quantidade",
        {"10068": ticker},
        session_token,
    )
    rows = rows_to_dicts(parsed)
    return to_series(rows[0]) if rows else pd.Series(dtype="object")
