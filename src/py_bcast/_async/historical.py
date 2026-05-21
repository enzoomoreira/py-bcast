"""Async historical data functions."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pandas as pd

from .._core.config import get_settings
from .._core.constants import BASE_URL
from .._core.dates import DateLike, business_days, default_end_date, to_date_str, to_datetime_str
from .._core.exceptions import ContentProxyError
from .._core.http import base_params, get_async_http_client, get_session_token
from .._core.logging import get_logger
from .._core.normalize import ensure_list
from .._core.output import to_dataframe, to_series
from .._core.ratelimit import rate_limit_async
from .._core.validation import DateParam, DateTimeParam, Ticker, TickerList, validate_params
from ._helpers import async_content_proxy_get
from .._core.xml_helpers import parse_ticks

logger = get_logger(__name__)


@validate_params
async def abdh(
    tickers: TickerList,
    start_date: DateParam,
    end_date: DateParam | None = None,
    session_token: str | None = None,
) -> dict[str, pd.DataFrame]:
    """Async version of ``bdh``. Fetch historical closing prices."""
    token = get_session_token(session_token)
    tickers = ensure_list(tickers)
    start_str = to_date_str(start_date)
    end_str = to_date_str(end_date) if end_date is not None else default_end_date()

    dates = business_days(start_str, end_str)
    if not dates:
        return {}

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
            timeout=get_settings().timeout,
        )

        root = ET.fromstring(r.text)
        if root.findtext("STATUS") != "success":
            msg = root.findtext("MESSAGE") or "Unknown error"
            raise ContentProxyError(
                f"ContentProxy error on HistoricoFechamentos: {msg}",
                endpoint="BaseHistoricaNumerica/HistoricoFechamentos",
                server_message=msg,
            )

        for tick in root.findall(".//TICK"):
            sym = tick.findtext("SYMBOL") or ""
            row = {child.tag.lower(): (child.text or "") for child in tick}
            results.setdefault(sym, []).append(row)

    for sym in results:
        results[sym].sort(key=lambda r: r["dat"])

    return {sym: to_dataframe(rows) for sym, rows in results.items()}


@validate_params
async def abdh_ohlcv(
    ticker: Ticker,
    date: DateParam,
    session_token: str | None = None,
) -> pd.Series:
    """Async version of ``bdh_ohlcv``."""
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

    root = ET.fromstring(r.text)
    if root.findtext("STATUS") != "success":
        return pd.Series(dtype="object")

    tick = root.find(".//TICK")
    if tick is None:
        return pd.Series(dtype="object")

    record = {child.tag.lower(): (child.text or "") for child in tick}
    return to_series(record)


@validate_params
async def abdt(
    ticker: Ticker,
    start: DateTimeParam,
    end: DateTimeParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bdt``. Fetch tick-by-tick data."""
    import datetime

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
    ticks.reverse()
    return to_dataframe(ticks, date_col="dat", time_col="hor")


@validate_params
async def abdi(
    ticker: Ticker,
    start_date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bdi``. Fetch intraday bars."""
    date_str = to_date_str(start_date)
    tag_10074 = f"{date_str}0000"

    root = await async_content_proxy_get(
        "BaseHistoricaNumerica/HistoricoIntraday",
        {"305": ticker, "10074": tag_10074, "10029": "4"},
        session_token=session_token,
        timeout=60,
    )

    bars = parse_ticks(root)
    bars.reverse()
    return to_dataframe(bars, date_col="dat", time_col="hor")
