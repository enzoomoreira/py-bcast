"""Historical daily closing prices and OHLCV via ContentProxy."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pandas as pd

from .._core.constants import BASE_URL
from .._core.dates import DateLike, business_days, default_end_date, to_date_str
from .._core.http import base_params, create_http_session, get_session_token
from .._core.normalize import ensure_list
from .._core.output import to_dataframe, to_series


def bdh(
    tickers: str | list[str],
    start_date: DateLike,
    end_date: DateLike | None = None,
    session_token: str | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Fetch historical closing prices for one or more tickers.

    Uses HistoricoFechamentos endpoint (works for ALL instruments).

    Args:
        tickers: Single ticker or list (e.g., "PETR4" or ["PETR4", "VALE3"])
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: End date (default: today)
        session_token: BCAA session token (or set BROADCAST_SESSION env var)

    Returns:
        Dict mapping "SYMBOL.EXCHANGE" -> DataFrame with DatetimeIndex.
        Columns: last, settle, settle_rate, yield, dattol (numeric where applicable).

    Example:
        >>> data = bdh("PETR4", "20260501", "20260519")
        >>> data["PETR4.BVMF"]["last"].plot()
    """
    token = get_session_token(session_token)
    tickers = ensure_list(tickers)
    start_str = to_date_str(start_date)
    end_str = to_date_str(end_date) if end_date is not None else default_end_date()

    dates = business_days(start_str, end_str)
    if not dates:
        return {}

    s = create_http_session()
    results: dict[str, list[dict[str, str]]] = {}

    # Fetch in chunks of 250 dates (URL length limit)
    CHUNK = 250
    for i in range(0, len(dates), CHUNK):
        chunk_dates = dates[i : i + CHUNK]
        params = base_params(token)
        params["10113"] = ";".join(tickers)
        params["DatasTolerancia"] = ";".join(chunk_dates)

        r = s.get(
            f"{BASE_URL}/BaseHistoricaNumerica/HistoricoFechamentos",
            params=params,
            timeout=30,
        )

        root = ET.fromstring(r.text)
        if root.findtext("STATUS") != "success":
            msg = root.findtext("MESSAGE") or "Unknown error"
            raise RuntimeError(f"ContentProxy error: {msg}")

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

    return {sym: to_dataframe(rows) for sym, rows in results.items()}


def bdh_ohlcv(
    ticker: str,
    date: DateLike,
    session_token: str | None = None,
) -> pd.Series:
    """
    Get full OHLCV data for a single ticker on a single date.

    Uses HistoricoData endpoint.

    Args:
        ticker: Single ticker (e.g., "PETR4")
        date: Date (str YYYYMMDD, date, datetime, or Timestamp)
        session_token: BCAA session token

    Returns:
        Series with numeric values: last, settle, low, high, open, neg, qtt,
        total_value, open_interest, vwap, total_neg. Empty Series if no data.

    Example:
        >>> s = bdh_ohlcv("PETR4", "20260519")
        >>> print(s["last"], s["high"])
    """
    token = get_session_token(session_token)
    s = create_http_session()
    date_str = to_date_str(date)

    params = base_params(token)
    params["305"] = ticker
    params["10077"] = date_str
    params["Precisao"] = "2"

    r = s.get(
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
