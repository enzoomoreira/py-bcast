"""Historical daily closing prices and OHLCV via ContentProxy."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pandas as pd

from .._core.columns import DAILY_OHLCV_SCHEMA
from .._core.constants import BASE_URL
from .._core.dates import business_days, default_end_date, to_date_str
from .._core.exceptions import ContentProxyError
from .._core.http import base_params, get_http_client, get_session_token
from .._core.logging import get_logger
from .._core.multi import vectorize
from .._core.normalize import ensure_list
from .._core.output import empty_bdh_frame, to_dataframe
from .._core.retry import http_retry
from .._core.validation import DateParam, TickerList, validate_params
from .._core.xml_helpers import raise_for_content_proxy_status

logger = get_logger(__name__)


@validate_params
def bdh(
    tickers: TickerList,
    start_date: DateParam,
    end_date: DateParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch historical closing prices for one or more tickers.

    Uses HistoricoFechamentos endpoint (works for ALL instruments).

    Args:
        tickers: Single ticker or list (e.g., "PETR4" or ["PETR4", "VALE3"])
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: End date (default: today)
        session_token: BCAA session token (or set BROADCAST_SESSION env var)

    Returns:
        Flat (long) DataFrame with a DatetimeIndex and a ``ticker`` column
        (one block of rows per symbol). Columns: ticker, close, settle,
        settle_rate, yield. Empty DataFrame with that schema if no data.

    Example:
        >>> df = bdh(["PETR4", "VALE3"], "20260501", "20260519")
        >>> df[df["ticker"] == "PETR4.BVMF"]["close"].plot()
    """
    token = get_session_token(session_token)
    tickers = ensure_list(tickers)
    start_str = to_date_str(start_date)
    end_str = to_date_str(end_date) if end_date is not None else default_end_date()

    dates = business_days(start_str, end_str)
    if not dates:
        return empty_bdh_frame()

    s = get_http_client()
    results: dict[str, list[dict[str, str]]] = {}

    # Fetch in chunks of 250 dates (URL length limit)
    CHUNK = 250
    for i in range(0, len(dates), CHUNK):
        chunk_dates = dates[i : i + CHUNK]
        params = base_params(token)
        params["10113"] = ";".join(tickers)
        params["DatasTolerancia"] = ";".join(chunk_dates)

        logger.debug("bdh: fetching %d dates for %s", len(chunk_dates), tickers)
        r = _bdh_fetch(s, params)

        try:
            root = ET.fromstring(r.text)
        except ET.ParseError as exc:
            logger.error("bdh: XML parse error: %s", exc)
            raise ContentProxyError(
                f"bdh: malformed XML response: {exc}",
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


@http_retry
def _bdh_fetch(s, params: dict):
    """Isolated HTTP call for retry."""
    return s.get(
        f"{BASE_URL}/BaseHistoricaNumerica/HistoricoFechamentos",
        params=params,
        timeout=30,
    )


def _bdh_ohlcv_one(
    ticker: str,
    date: str,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Get full OHLCV data for a single ticker on a single date."""
    token = get_session_token(session_token)
    s = get_http_client()
    date_str = to_date_str(date)

    params = base_params(token)
    params["305"] = ticker
    params["10077"] = date_str
    params["Precisao"] = "2"

    logger.debug("bdh_ohlcv: %s on %s", ticker, date_str)
    r = _bdh_ohlcv_fetch(s, params)

    try:
        root = ET.fromstring(r.text)
    except ET.ParseError as exc:
        logger.error("bdh_ohlcv: XML parse error: %s", exc)
        raise ContentProxyError(
            f"bdh_ohlcv: malformed XML response: {exc}",
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
def bdh_ohlcv(
    ticker: TickerList,
    date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Get full OHLCV data for one or more tickers on a single date.

    Uses HistoricoData endpoint.

    Args:
        ticker: Single ticker or list (e.g., "PETR4" or ["PETR4", "VALE3"]).
        date: Date (str YYYYMMDD, date, datetime, or Timestamp)
        session_token: BCAA session token

    Returns:
        Flat DataFrame with a DatetimeIndex and a ``ticker`` column (one row
        per ticker). Columns: ticker, close, settle, settle_rate, low, high,
        open, trades, volume, turnover, open_interest, vwap, cum_trades.
        Empty DataFrame with that schema if there is no data for the date;
        NotFoundError for an unknown ticker.

    Example:
        >>> df = bdh_ohlcv("PETR4", "20260519")
        >>> print(df["close"].iloc[0], df["high"].iloc[0])
    """
    return vectorize(ticker, lambda t: _bdh_ohlcv_one(t, date, session_token))


@http_retry
def _bdh_ohlcv_fetch(s, params: dict):
    """Isolated HTTP call for retry."""
    return s.get(
        f"{BASE_URL}/BaseHistoricaNumerica/HistoricoData",
        params=params,
        timeout=15,
    )
