"""Historical market data via ContentProxy HTTP API."""

from __future__ import annotations

import datetime
import xml.etree.ElementTree as ET

from ._constants import BASE_URL
from ._http import base_params, create_http_session, get_session_token


def bdh(
    tickers: str | list[str],
    start_date: str,
    end_date: str | None = None,
    session_token: str | None = None,
) -> dict[str, list[dict[str, str]]]:
    """
    Fetch historical closing prices for one or more tickers.

    Uses HistoricoFechamentos endpoint (works for ALL instruments).

    Args:
        tickers: Single ticker or list (e.g., "PETR4" or ["PETR4", "VALE3"])
        start_date: Start date as YYYYMMDD
        end_date: End date as YYYYMMDD (default: today)
        session_token: BCAA session token (or set BROADCAST_SESSION env var)

    Returns:
        Dict mapping "SYMBOL.EXCHANGE" -> list of daily records.
        Each record: {date, last, settle, settle_rate, yield, dattol}

    Example:
        >>> data = bdh("PETR4", "20260501", "20260519")
        >>> for row in data["PETR4.BVMF"]:
        ...     print(row["date"], row["last"])
    """
    token = get_session_token(session_token)

    if isinstance(tickers, str):
        tickers = [tickers]

    if end_date is None:
        end_date = datetime.date.today().strftime("%Y%m%d")

    # Generate business days in range
    dates = []
    d = datetime.datetime.strptime(start_date, "%Y%m%d").date()
    end = datetime.datetime.strptime(end_date, "%Y%m%d").date()
    while d <= end:
        if d.weekday() < 5:
            dates.append(d.strftime("%Y%m%d"))
        d += datetime.timedelta(days=1)

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
            verify=False,
        )

        root = ET.fromstring(r.text)
        if root.findtext("STATUS") != "success":
            msg = root.findtext("MESSAGE") or "Unknown error"
            raise RuntimeError(f"ContentProxy error: {msg}")

        for tick in root.findall(".//TICK"):
            sym = tick.findtext("SYMBOL") or ""
            row = {
                "date": tick.findtext("DAT") or "",
                "last": tick.findtext("LAST") or "",
                "settle": tick.findtext("SETTLE") or "",
                "settle_rate": tick.findtext("SETTLE_RATE") or "",
                "yield": tick.findtext("YIELD") or "",
                "dattol": tick.findtext("DATTOL") or "",
            }
            results.setdefault(sym, []).append(row)

    for sym in results:
        results[sym].sort(key=lambda r: r["date"])

    return results


def bdh_ohlcv(
    ticker: str,
    date: str,
    session_token: str | None = None,
) -> dict[str, str]:
    """
    Get full OHLCV data for a single ticker on a single date.

    Uses HistoricoData endpoint.

    Args:
        ticker: Single ticker (e.g., "PETR4")
        date: Date as YYYYMMDD
        session_token: BCAA session token

    Returns:
        Dict with keys: dat, last, settle, low, high, open, neg, qtt,
        total_value, open_interest, vwap, total_neg. Empty dict if no data.

    Example:
        >>> bdh_ohlcv("PETR4", "20260519")
        {'dat': '20260519', 'last': '46.09', 'high': '46.3', ...}
    """
    token = get_session_token(session_token)
    s = create_http_session()

    params = base_params(token)
    params["305"] = ticker
    params["10077"] = date
    params["Precisao"] = "2"

    r = s.get(
        f"{BASE_URL}/BaseHistoricaNumerica/HistoricoData",
        params=params,
        timeout=15,
        verify=False,
    )

    root = ET.fromstring(r.text)
    if root.findtext("STATUS") != "success":
        return {}

    tick = root.find(".//TICK")
    if tick is None:
        return {}

    return {child.tag.lower(): (child.text or "") for child in tick}


def bdt(
    ticker: str,
    start: str,
    end: str | None = None,
    session_token: str | None = None,
) -> list[dict[str, str]]:
    """
    Get tick-by-tick (trade) data for a symbol.

    Uses HistoricoTick endpoint. Works for international instruments:
    FX pairs (USDBRL, EURUSD, GBPUSD, etc.), precious metals (GOLD, SILVER),
    energy (WTI), indices (DAX, FTSE, VIX, DXY), treasuries (US10Y, US2Y).

    Note: B3/BVMF instruments return empty due to server-side query
    registration requirement.

    Args:
        ticker: Symbol (e.g., "USDBRL", "GOLD", "EURUSD", "DAX")
        start: Start datetime as YYYYMMDDHHMMSS
        end: End datetime as YYYYMMDDHHMMSS (default: start + 1 hour)
        session_token: BCAA session token

    Returns:
        List of tick dicts sorted chronologically (oldest first).
        Keys: dat, hor, last, size, neg, open_interest, calendar_days, working_days.

    Example:
        >>> ticks = bdt("USDBRL", "20260519100000", "20260519103000")
        >>> for t in ticks:
        ...     print(f"{t['hor']} {t['last']}")
    """
    token = get_session_token(session_token)

    if end is None:
        dt = datetime.datetime.strptime(start, "%Y%m%d%H%M%S")
        end = (dt + datetime.timedelta(hours=1)).strftime("%Y%m%d%H%M%S")

    s = create_http_session()

    params = base_params(token)
    params["305"] = ticker
    params["10071"] = start
    params["10072"] = end

    r = s.get(
        f"{BASE_URL}/BaseHistoricaNumerica/HistoricoTick",
        params=params,
        timeout=60,
        verify=False,
    )

    root = ET.fromstring(r.text)
    if root.findtext("STATUS") != "success":
        msg = root.findtext("MESSAGE") or "Unknown error"
        raise RuntimeError(f"ContentProxy error: {msg}")

    ticks = []
    for tick in root.findall(".//TICK"):
        ticks.append({child.tag.lower(): (child.text or "") for child in tick})

    # API returns newest first — reverse to chronological order
    ticks.reverse()
    return ticks


def bdi(
    ticker: str,
    start_date: str,
    session_token: str | None = None,
) -> list[dict[str, str]]:
    """
    Get intraday OHLCV bars (2-minute candles) for a symbol.

    Uses HistoricoIntraday endpoint. Works for ALL instruments (B3 + international).
    Returns bars from start_date up to the current time.

    Args:
        ticker: Symbol (e.g., "PETR4", "VALE3", "USDBRL", "GOLD")
        start_date: Start date as YYYYMMDD (data from this date onwards)
        session_token: BCAA session token

    Returns:
        List of bar dicts sorted chronologically (oldest first).
        Keys: dat, hor, open, high, low, last (close), qtt, neg,
        total_value, open_interest, total_neg, tipo_intervalo.

        tipo_intervalo values:
            1 = Regular session
            5 = After-hours session
            9 = Closing auction

    Example:
        >>> bars = bdi("PETR4", "20260519")
        >>> for bar in bars[-5:]:
        ...     print(f"{bar['dat']} {bar['hor']} O={bar['open']} H={bar['high']} L={bar['low']} C={bar['last']}")
    """
    token = get_session_token(session_token)
    s = create_http_session()

    # Format: YYYYMMDDHHMM (12 digits). Server uses only the date portion;
    # the last 4 digits (HHMM) are required but ignored.
    tag_10074 = f"{start_date}0000"

    params = base_params(token)
    params["305"] = ticker
    params["10074"] = tag_10074
    params["10029"] = "4"  # Precisao (decimal places)

    r = s.get(
        f"{BASE_URL}/BaseHistoricaNumerica/HistoricoIntraday",
        params=params,
        timeout=60,
        verify=False,
    )

    root = ET.fromstring(r.text)
    if root.findtext("STATUS") != "success":
        msg = root.findtext("MESSAGE") or "Unknown error"
        raise RuntimeError(f"ContentProxy error: {msg}")

    bars = []
    for tick in root.findall(".//TICK"):
        bars.append({child.tag.lower(): (child.text or "") for child in tick})

    # API returns newest first — reverse to chronological order
    bars.reverse()
    return bars
