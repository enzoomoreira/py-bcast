"""Async historical data functions."""

from __future__ import annotations

import datetime
import xml.etree.ElementTree as ET

import pandas as pd

from .._core.columns import (
    DAILY_OHLCV_SCHEMA,
    INTRADAY_BAR_SCHEMA,
    TICK_SCHEMA,
)
from .._core.constants import BASE_URL
from .._core.dates import business_days, default_end_date, to_date_str, to_datetime_str
from .._core.exceptions import ContentProxyError
from .._core.http import base_params, get_async_http_client, get_session_token
from .._core.logging import get_logger
from .._core.multi import vectorize_async
from .._core.normalize import ensure_list
from .._core.output import empty_bdh_frame, to_dataframe
from .._core.ratelimit import rate_limit_async
from .._core.validation import DateParam, DateTimeParam, TickerList, validate_params
from .._core.xml_helpers import parse_ticks, raise_for_content_proxy_status
from ._helpers import async_content_proxy_get

logger = get_logger(__name__)


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
        r = await s.get(
            f"{BASE_URL}/BaseHistoricaNumerica/HistoricoFechamentos",
            params=params,
            timeout=30,
        )

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
        df = to_dataframe(results[sym])
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
    r = await s.get(
        f"{BASE_URL}/BaseHistoricaNumerica/HistoricoData",
        params=params,
        timeout=15,
    )

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
    df = to_dataframe(rows, date_col="dat", schema=DAILY_OHLCV_SCHEMA)
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


async def _abdt_one(
    ticker: str,
    start: str,
    end: str | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Get tick-by-tick data for a single symbol."""
    start_str = to_datetime_str(start)
    if end is None:
        dt = datetime.datetime.strptime(start_str, "%Y%m%d%H%M%S")
        end_str = (dt + datetime.timedelta(hours=1)).strftime("%Y%m%d%H%M%S")
    else:
        end_str = to_datetime_str(end)

    root = await async_content_proxy_get(
        "BaseHistoricaNumerica/HistoricoTick",
        {"305": ticker, "10071": start_str, "10072": end_str},
        session_token=session_token,
        timeout=60,
    )

    ticks = parse_ticks(root)
    # API returns newest first — reverse to chronological order
    ticks.reverse()
    return to_dataframe(ticks, date_col="dat", time_col="hor", schema=TICK_SCHEMA)


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
    return await vectorize_async(
        ticker, lambda t: _abdt_one(t, start, end, session_token)
    )


async def _abdi_one(
    ticker: str,
    start_date: str,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Get intraday OHLCV bars for a single symbol."""
    date_str = to_date_str(start_date)
    tag_10074 = f"{date_str}0000"

    root = await async_content_proxy_get(
        "BaseHistoricaNumerica/HistoricoIntraday",
        {"305": ticker, "10074": tag_10074, "10029": "4"},
        session_token=session_token,
        timeout=60,
    )

    bars = parse_ticks(root)
    # API returns newest first — reverse to chronological order
    bars.reverse()
    return to_dataframe(
        bars, date_col="dat", time_col="hor", schema=INTRADAY_BAR_SCHEMA
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
    return await vectorize_async(
        ticker, lambda t: _abdi_one(t, start_date, session_token)
    )
