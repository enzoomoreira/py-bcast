"""Async historical data functions."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import httpx
import pandas as pd

from .._core.constants import BASE_URL
from .._core.dates import (
    business_days,
    default_end_date,
    default_tick_end,
    to_date_str,
    to_datetime_str,
)
from .._core.exceptions import ContentProxyError
from .._core.logging import get_logger
from .._core.normalize import ensure_list
from .._core.ratelimit import rate_limit_async
from .._core.retry import http_retry
from .._core.validation import DateParam, DateTimeParam, TickerList, validate_params
from .._legacy.columns import DAILY_OHLCV_SCHEMA, CONTENT_PROXY_RENAME
from .._legacy.endpoints import SPEC_BDI, SPEC_BDT
from .._legacy.http import base_params, get_async_http_client, get_session_token
from .._legacy.multi import vectorize_async
from .._legacy.output import Index, empty_bdh_frame, finalize_frame
from .._legacy.xml_helpers import raise_for_content_proxy_status
from .executor import arun_spec

logger = get_logger(__name__)


@http_retry
async def _abdh_fetch(s: httpx.AsyncClient, params: dict) -> httpx.Response:
    """Isolated async HTTP call for retry."""
    return await s.get(
        f"{BASE_URL}/BaseHistoricaNumerica/HistoricoFechamentos",
        params=params,
        timeout=30,
    )


@http_retry
async def _abdh_ohlcv_fetch(s: httpx.AsyncClient, params: dict) -> httpx.Response:
    """Isolated async HTTP call for retry."""
    return await s.get(
        f"{BASE_URL}/BaseHistoricaNumerica/HistoricoData",
        params=params,
        timeout=15,
    )


@validate_params
async def abdh(
    tickers: TickerList,
    start_date: DateParam,
    end_date: DateParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bdh``. Fetch historical closing prices.

    Returns a flat (long) DataFrame with a DatetimeIndex and a ``ticker``
    column (one block of rows per symbol). Empty DataFrame with that schema
    if there is no data.
    """
    token = get_session_token(session_token)
    tickers = ensure_list(tickers)
    start_str = to_date_str(start_date)
    end_str = to_date_str(end_date) if end_date is not None else default_end_date()

    dates = business_days(start_str, end_str)
    if not dates:
        return empty_bdh_frame()

    s = get_async_http_client()
    results: dict[str, list[dict[str, str]]] = {}

    CHUNK = 250
    for i in range(0, len(dates), CHUNK):
        chunk_dates = dates[i : i + CHUNK]
        params = base_params(token)
        params["10113"] = ";".join(tickers)
        params["DatasTolerancia"] = ";".join(chunk_dates)

        await rate_limit_async()
        r = await _abdh_fetch(s, params)

        try:
            root = ET.fromstring(r.text)
        except ET.ParseError as exc:
            logger.error("abdh: XML parse error: %s", exc)
            raise ContentProxyError(
                f"abdh: malformed XML response: {exc}",
                endpoint="BaseHistoricaNumerica/HistoricoFechamentos",
            ) from exc
        raise_for_content_proxy_status(
            root, "BaseHistoricaNumerica/HistoricoFechamentos", params
        )

        for tick in root.findall(".//TICK"):
            sym = tick.findtext("SYMBOL") or ""
            row = {
                "dat": tick.findtext("DAT") or "",
                "last": tick.findtext("LAST") or "",
                "settle": tick.findtext("SETTLE") or "",
                "settle_rate": tick.findtext("SETTLE_RATE") or "",
                "yield": tick.findtext("YIELD") or "",
                "dattol": tick.findtext("DATTOL") or "",
            }
            results.setdefault(sym, []).append(row)

    for sym in results:
        results[sym].sort(key=lambda r: r["dat"])

    frames = []
    for sym in sorted(results):
        df = finalize_frame(
            results[sym], index=Index.DATETIME, rename=CONTENT_PROXY_RENAME
        )
        # Drop tolerance rows with no actual trade data (NaT index)
        df = df[df.index.notna()]
        if df.empty:
            continue
        df.insert(0, "ticker", sym)
        frames.append(df)

    if not frames:
        return empty_bdh_frame()
    return pd.concat(frames)


async def _abdh_ohlcv_one(
    ticker: str,
    date: str,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Get full OHLCV data for a single ticker on a single date."""
    token = get_session_token(session_token)
    s = get_async_http_client()
    date_str = to_date_str(date)

    params = base_params(token)
    params["305"] = ticker
    params["10077"] = date_str
    params["Precisao"] = "2"

    await rate_limit_async()
    r = await _abdh_ohlcv_fetch(s, params)

    try:
        root = ET.fromstring(r.text)
    except ET.ParseError as exc:
        logger.error("abdh_ohlcv: XML parse error: %s", exc)
        raise ContentProxyError(
            f"abdh_ohlcv: malformed XML response: {exc}",
            endpoint="BaseHistoricaNumerica/HistoricoData",
        ) from exc
    raise_for_content_proxy_status(root, "BaseHistoricaNumerica/HistoricoData", params)

    tick = root.find(".//TICK")
    rows = (
        [{child.tag.lower(): (child.text or "") for child in tick}]
        if tick is not None
        else []
    )
    df = finalize_frame(
        rows,
        index=Index.DATETIME,
        rename=CONTENT_PROXY_RENAME,
        schema=DAILY_OHLCV_SCHEMA,
    )
    df.insert(0, "ticker", ticker)
    return df


@validate_params
async def abdh_ohlcv(
    ticker: TickerList,
    date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bdh_ohlcv``.

    Flat DataFrame with a DatetimeIndex and a ``ticker`` column (one row per
    ticker). Empty DataFrame with schema if there is no data for the date;
    NotFoundError for an unknown ticker.
    """
    return await vectorize_async(
        ticker, lambda t: _abdh_ohlcv_one(t, date, session_token)
    )


@validate_params
async def abdt(
    ticker: TickerList,
    start: DateTimeParam,
    end: DateTimeParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bdt``. Fetch tick-by-tick data.

    Flat DataFrame with a DatetimeIndex (from dat+hor) and a ``ticker`` column
    (one block per symbol).
    """
    start_str = to_datetime_str(start)
    end_str = default_tick_end(start_str) if end is None else to_datetime_str(end)
    return await arun_spec(
        SPEC_BDT,
        session_token=session_token,
        ticker=ticker,
        start=start_str,
        end=end_str,
    )


@validate_params
async def abdi(
    ticker: TickerList,
    start_date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bdi``. Fetch intraday bars.

    Flat DataFrame with a DatetimeIndex (from dat+hor) and a ``ticker`` column
    (one block per symbol).
    """
    return await arun_spec(
        SPEC_BDI,
        session_token=session_token,
        ticker=ticker,
        bar_start=f"{to_date_str(start_date)}0000",
    )
