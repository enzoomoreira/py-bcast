"""Macroeconomic indicators and fixed-income data via ContentProxy HTTP API."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from ._constants import BASE_URL
from ._http import base_params, create_http_session, get_session_token


def bmacro(
    ticker: str,
    start_date: str,
    end_date: str,
    session_token: str | None = None,
) -> list[dict[str, str]]:
    """
    Fetch macroeconomic/index historical series.

    Uses MacroEconomicos endpoint. Supports FX, indices, commodities, rates,
    and synthetic AETAXAS indicators.

    Supported symbols include:
        FX: USDBRL, EURUSD, GBPUSD, JPYBRL, etc.
        Indices: IBOV, SPX, DAX, FTSE, NASDAQ, DJI, etc.
        Commodities: GOLD, SILVER, WTI, BRENT, etc.
        Rates/DI: DI1F26, DI1F27, DI1F28, etc.
        AETAXAS: AEIPCA, AEIGPM, AECTIP, AEB052, AEB200, AEFS10, etc.

    Args:
        ticker: Symbol (e.g., "USDBRL", "IBOV", "AEIPCA")
        start_date: Start date as YYYYMMDD
        end_date: End date as YYYYMMDD
        session_token: BCAA session token

    Returns:
        List of dicts sorted chronologically. Keys depend on symbol
        but typically include: dat, last, open, high, low, settle, var, neg, qtt.

    Example:
        >>> rows = bmacro("USDBRL", "20260101", "20260519")
        >>> for r in rows[-3:]:
        ...     print(r["dat"], r["last"])
    """
    token = get_session_token(session_token)
    s = create_http_session()

    params = base_params(token)
    params["305"] = ticker
    params["DataInicio"] = start_date
    params["DataFim"] = end_date

    r = s.get(
        f"{BASE_URL}/BaseHistoricaNumerica/MacroEconomicos",
        params=params,
        timeout=30,
        verify=False,
    )

    root = ET.fromstring(r.text)
    if root.findtext("STATUS") != "success":
        msg = root.findtext("MESSAGE") or "Unknown error"
        raise RuntimeError(f"MacroEconomicos error: {msg}")

    rows = []
    for tick in root.findall(".//TICK"):
        rows.append({child.tag.lower(): (child.text or "") for child in tick})

    rows.sort(key=lambda r: r.get("dat", ""))
    return rows


def bdi_cdi(
    start_date: str,
    end_date: str,
    session_token: str | None = None,
) -> list[dict[str, str]]:
    """
    Fetch accumulated CDI (DI-CETIP) series.

    Uses DiCetipAcumulado endpoint. Returns daily CDI data since 1986.

    Args:
        start_date: Start date as YYYYMMDD
        end_date: End date as YYYYMMDD
        session_token: BCAA session token

    Returns:
        List of dicts with keys: dat, last (accumulated %), var (daily rate).

    Example:
        >>> rows = bdi_cdi("20260101", "20260519")
        >>> print(rows[-1]["dat"], rows[-1]["last"])
    """
    token = get_session_token(session_token)
    s = create_http_session()

    params = base_params(token)
    params["DataInicio"] = start_date
    params["DataFim"] = end_date

    r = s.get(
        f"{BASE_URL}/BaseHistoricaNumerica/DiCetipAcumulado",
        params=params,
        timeout=30,
        verify=False,
    )

    root = ET.fromstring(r.text)
    if root.findtext("STATUS") != "success":
        msg = root.findtext("MESSAGE") or "Unknown error"
        raise RuntimeError(f"DiCetipAcumulado error: {msg}")

    rows = []
    for tick in root.findall(".//TICK"):
        rows.append({child.tag.lower(): (child.text or "") for child in tick})

    rows.sort(key=lambda r: r.get("dat", ""))
    return rows


def breturn(
    ticker: str,
    start_date: str,
    end_date: str,
    session_token: str | None = None,
) -> list[dict[str, str]]:
    """
    Fetch adjusted daily returns for a symbol.

    Uses RetornoDiario endpoint.

    Args:
        ticker: Symbol (e.g., "PETR4", "VALE3", "IBOV")
        start_date: Start date as YYYYMMDD
        end_date: End date as YYYYMMDD
        session_token: BCAA session token

    Returns:
        List of dicts with keys: dat, last (return value).

    Example:
        >>> rows = breturn("PETR4", "20260101", "20260519")
        >>> for r in rows[-3:]:
        ...     print(r["dat"], r["last"])
    """
    token = get_session_token(session_token)
    s = create_http_session()

    params = base_params(token)
    params["305"] = ticker
    params["DataInicio"] = start_date
    params["DataFim"] = end_date

    r = s.get(
        f"{BASE_URL}/BaseHistoricaNumerica/RetornoDiario",
        params=params,
        timeout=30,
        verify=False,
    )

    root = ET.fromstring(r.text)
    if root.findtext("STATUS") != "success":
        msg = root.findtext("MESSAGE") or "Unknown error"
        raise RuntimeError(f"RetornoDiario error: {msg}")

    rows = []
    for tick in root.findall(".//TICK"):
        rows.append({child.tag.lower(): (child.text or "") for child in tick})

    rows.sort(key=lambda r: r.get("dat", ""))
    return rows


def bvolume(
    tickers: str | list[str],
    session_token: str | None = None,
) -> dict[str, dict[str, str]]:
    """
    Fetch average volume statistics for one or more symbols.

    Uses VolumesMedios endpoint. Returns 1m/2m/3m/6m average volumes.

    Args:
        tickers: Single ticker or list (e.g., "PETR4" or ["PETR4", "VALE3"])
        session_token: BCAA session token

    Returns:
        Dict mapping symbol -> volume stats dict.

    Example:
        >>> data = bvolume(["PETR4", "VALE3"])
        >>> print(data["PETR4.BVMF"])
    """
    token = get_session_token(session_token)
    s = create_http_session()

    if isinstance(tickers, str):
        tickers = [tickers]

    params = base_params(token)
    params["10113"] = ";".join(tickers)

    r = s.get(
        f"{BASE_URL}/BaseHistoricaNumerica/VolumesMedios",
        params=params,
        timeout=15,
        verify=False,
    )

    root = ET.fromstring(r.text)
    if root.findtext("STATUS") != "success":
        msg = root.findtext("MESSAGE") or "Unknown error"
        raise RuntimeError(f"VolumesMedios error: {msg}")

    results: dict[str, dict[str, str]] = {}
    for tick in root.findall(".//TICK"):
        sym = tick.findtext("SYMBOL") or ""
        data = {child.tag.lower(): (child.text or "") for child in tick}
        results[sym] = data

    return results


def binflation(
    session_token: str | None = None,
) -> list[dict[str, str]]:
    """
    Fetch current inflation indices summary.

    Uses Inflacao endpoint. Returns up to 17 inflation indices with
    monthly, 3m, 6m, 12m, and YTD accumulated values.

    Args:
        session_token: BCAA session token

    Returns:
        List of dicts, one per index. Keys include: symbol, dat, last, var,
        accumulated periods (acum_3m, acum_6m, acum_12m, acum_ano).

    Example:
        >>> indices = binflation()
        >>> for idx in indices:
        ...     print(idx.get("symbol"), idx.get("last"))
    """
    token = get_session_token(session_token)
    s = create_http_session()

    params = base_params(token)

    r = s.get(
        f"{BASE_URL}/BaseHistoricaNumerica/Inflacao",
        params=params,
        timeout=15,
        verify=False,
    )

    root = ET.fromstring(r.text)
    if root.findtext("STATUS") != "success":
        msg = root.findtext("MESSAGE") or "Unknown error"
        raise RuntimeError(f"Inflacao error: {msg}")

    rows = []
    for tick in root.findall(".//TICK"):
        rows.append({child.tag.lower(): (child.text or "") for child in tick})

    return rows
