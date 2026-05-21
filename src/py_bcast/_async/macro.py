"""Async macroeconomic indicator functions."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pandas as pd

from .._core.config import get_settings
from .._core.constants import BASE_URL
from .._core.dates import DateLike, to_date_str
from .._core.exceptions import ContentProxyError
from .._core.http import base_params, get_async_http_client, get_session_token
from .._core.logging import get_logger
from .._core.normalize import ensure_list
from .._core.output import to_dataframe, to_reference_dataframe
from .._core.ratelimit import rate_limit_async
from .._core.validation import DateParam, Ticker, TickerList, validate_params
from ._helpers import async_content_proxy_get
from .._core.xml_helpers import parse_ticks

logger = get_logger(__name__)


@validate_params
async def abmacro(
    ticker: Ticker,
    start_date: DateParam,
    end_date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bmacro``."""
    root = await async_content_proxy_get(
        "BaseHistoricaNumerica/MacroEconomicos",
        {"305": ticker, "DataInicio": to_date_str(start_date), "DataFim": to_date_str(end_date)},
        session_token=session_token,
    )
    rows = parse_ticks(root, sort_by="dat")
    return to_dataframe(rows)


@validate_params
async def abdi_cdi(
    start_date: DateParam,
    end_date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bdi_cdi``."""
    root = await async_content_proxy_get(
        "BaseHistoricaNumerica/DiCetipAcumulado",
        {"DataInicio": to_date_str(start_date), "DataFim": to_date_str(end_date)},
        session_token=session_token,
    )
    rows = parse_ticks(root, sort_by="dat")
    return to_dataframe(rows)


@validate_params
async def abreturn(
    ticker: Ticker,
    start_date: DateParam,
    end_date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``breturn``."""
    root = await async_content_proxy_get(
        "BaseHistoricaNumerica/RetornoDiario",
        {"305": ticker, "DataInicio": to_date_str(start_date), "DataFim": to_date_str(end_date)},
        session_token=session_token,
    )
    rows = parse_ticks(root, sort_by="dat")
    return to_dataframe(rows)


@validate_params
async def abvolume(
    tickers: TickerList,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bvolume``."""
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
        raise ContentProxyError(
            f"ContentProxy error on VolumesMedios: {msg}",
            endpoint="BaseHistoricaNumerica/VolumesMedios",
            server_message=msg,
        )

    rows = []
    for tick in root.findall(".//TICK"):
        data = {child.tag.lower(): (child.text or "") for child in tick}
        rows.append(data)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    if "symbol" in df.columns:
        df = df.set_index("symbol")
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(df[col])
    return df


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
    return to_reference_dataframe(rows)
