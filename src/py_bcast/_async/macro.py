"""Async macroeconomic indicator functions."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pandas as pd

from .._core.columns import (
    CDI_SCHEMA,
    CONTENT_PROXY_RENAME,
    INFLATION_SCHEMA,
    MACRO_SCHEMA,
    RETURN_SCHEMA,
    VOLUME_SCHEMA,
)
from .._core.constants import BASE_URL
from .._core.dates import to_date_str
from .._core.exceptions import ContentProxyError
from .._core.http import base_params, get_async_http_client, get_session_token
from .._core.logging import get_logger
from .._core.multi import vectorize_async
from .._core.normalize import ensure_list
from .._core.output import to_dataframe, to_reference_dataframe
from .._core.ratelimit import rate_limit_async
from .._core.validation import DateParam, TickerList, validate_params
from .._core.xml_helpers import parse_ticks
from ._helpers import async_content_proxy_get

logger = get_logger(__name__)


async def _abmacro_one(
    ticker: str,
    start_date: str,
    end_date: str,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Fetch the macro series for a single symbol."""
    root = await async_content_proxy_get(
        "BaseHistoricaNumerica/MacroEconomicos",
        {
            "305": ticker,
            "DataInicio": to_date_str(start_date),
            "DataFim": to_date_str(end_date),
        },
        session_token=session_token,
    )
    rows = parse_ticks(root, sort_by="dat")
    return to_dataframe(rows, schema=MACRO_SCHEMA)


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
    return await vectorize_async(
        ticker,
        lambda t: _abmacro_one(t, start_date, end_date, session_token),
    )


@validate_params
async def abdi_cdi(
    start_date: DateParam,
    end_date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bdi_cdi`` (single series, no ticker arg)."""
    root = await async_content_proxy_get(
        "BaseHistoricaNumerica/DiCetipAcumulado",
        {"DataInicio": to_date_str(start_date), "DataFim": to_date_str(end_date)},
        session_token=session_token,
    )
    rows = parse_ticks(root, sort_by="dat")
    return to_dataframe(rows, schema=CDI_SCHEMA)


async def _abreturn_one(
    ticker: str,
    start_date: str,
    end_date: str,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Fetch adjusted daily returns for a single symbol."""
    root = await async_content_proxy_get(
        "BaseHistoricaNumerica/RetornoDiario",
        {
            "305": ticker,
            "DataInicio": to_date_str(start_date),
            "DataFim": to_date_str(end_date),
        },
        session_token=session_token,
    )
    rows = parse_ticks(root, sort_by="dat")
    return to_dataframe(rows, schema=RETURN_SCHEMA)


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
    return await vectorize_async(
        ticker,
        lambda t: _abreturn_one(t, start_date, end_date, session_token),
    )


@validate_params
async def abvolume(
    tickers: TickerList,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bvolume``.

    Flat DataFrame (RangeIndex), one row per (symbol, averaging window).
    ``symbol`` stays a column because it repeats per window.
    """
    token = get_session_token(session_token)
    s = get_async_http_client()
    tickers = ensure_list(tickers)

    params = base_params(token)
    params["10113"] = ";".join(tickers)

    await rate_limit_async()
    r = await s.get(
        f"{BASE_URL}/BaseHistoricaNumerica/VolumesMedios",
        params=params,
        timeout=15,
    )

    root = ET.fromstring(r.text)
    if root.findtext("STATUS") != "success":
        msg = root.findtext("MESSAGE") or "Unknown error"
        logger.error("abvolume ContentProxy error: %s", msg)
        raise ContentProxyError(
            f"ContentProxy error on VolumesMedios: {msg}",
            endpoint="BaseHistoricaNumerica/VolumesMedios",
            server_message=msg,
        )

    rows = [
        {child.tag.lower(): (child.text or "") for child in tick}
        for tick in root.findall(".//TICK")
    ]
    return to_reference_dataframe(
        rows, rename=CONTENT_PROXY_RENAME, schema=VOLUME_SCHEMA
    )


async def abinflation(
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``binflation``."""
    root = await async_content_proxy_get(
        "BaseHistoricaNumerica/Inflacao",
        {},
        session_token=session_token,
        timeout=15,
    )
    rows = parse_ticks(root)
    return to_reference_dataframe(
        rows, rename=CONTENT_PROXY_RENAME, schema=INFLATION_SCHEMA
    )
