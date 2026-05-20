"""Macroeconomic indicators and fixed-income data via ContentProxy HTTP API."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pandas as pd

from .._core.constants import BASE_URL
from .._core.dates import DateLike, to_date_str
from .._core.http import base_params, create_http_session, get_session_token
from .._core.normalize import ensure_list
from .._core.output import to_dataframe, to_reference_dataframe
from .._core.xml_helpers import content_proxy_get, parse_ticks


def bmacro(
    ticker: str,
    start_date: DateLike,
    end_date: DateLike,
    session_token: str | None = None,
) -> pd.DataFrame:
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
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: End date (str YYYYMMDD, date, datetime, or Timestamp)
        session_token: BCAA session token

    Returns:
        DataFrame with DatetimeIndex. Columns depend on symbol but typically
        include: last, open, high, low, settle, var, neg, qtt.

    Example:
        >>> df = bmacro("USDBRL", "20260101", "20260519")
        >>> df["last"].plot()
    """
    root = content_proxy_get(
        "BaseHistoricaNumerica/MacroEconomicos",
        {"305": ticker, "DataInicio": to_date_str(start_date), "DataFim": to_date_str(end_date)},
        session_token=session_token,
    )
    rows = parse_ticks(root, sort_by="dat")
    return to_dataframe(rows)


def bdi_cdi(
    start_date: DateLike,
    end_date: DateLike,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch accumulated CDI (DI-CETIP) series.

    Uses DiCetipAcumulado endpoint. Returns daily CDI data since 1986.

    Args:
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: End date (str YYYYMMDD, date, datetime, or Timestamp)
        session_token: BCAA session token

    Returns:
        DataFrame with DatetimeIndex. Columns: last (accumulated %), var (daily rate).

    Example:
        >>> df = bdi_cdi("20260101", "20260519")
        >>> df["last"].iloc[-1]
    """
    root = content_proxy_get(
        "BaseHistoricaNumerica/DiCetipAcumulado",
        {"DataInicio": to_date_str(start_date), "DataFim": to_date_str(end_date)},
        session_token=session_token,
    )
    rows = parse_ticks(root, sort_by="dat")
    return to_dataframe(rows)


def breturn(
    ticker: str,
    start_date: DateLike,
    end_date: DateLike,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch adjusted daily returns for a symbol.

    Uses RetornoDiario endpoint.

    Args:
        ticker: Symbol (e.g., "PETR4", "VALE3", "IBOV")
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: End date (str YYYYMMDD, date, datetime, or Timestamp)
        session_token: BCAA session token

    Returns:
        DataFrame with DatetimeIndex. Columns: last (return value).

    Example:
        >>> df = breturn("PETR4", "20260101", "20260519")
        >>> df["last"].cumsum().plot()
    """
    root = content_proxy_get(
        "BaseHistoricaNumerica/RetornoDiario",
        {"305": ticker, "DataInicio": to_date_str(start_date), "DataFim": to_date_str(end_date)},
        session_token=session_token,
    )
    rows = parse_ticks(root, sort_by="dat")
    return to_dataframe(rows)


def bvolume(
    tickers: str | list[str],
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch average volume statistics for one or more symbols.

    Uses VolumesMedios endpoint. Returns 1m/2m/3m/6m average volumes.

    Args:
        tickers: Single ticker or list (e.g., "PETR4" or ["PETR4", "VALE3"])
        session_token: BCAA session token

    Returns:
        DataFrame with symbol as index and volume stats as columns.

    Example:
        >>> df = bvolume(["PETR4", "VALE3"])
        >>> df.loc["PETR4.BVMF"]
    """
    token = get_session_token(session_token)
    s = create_http_session()
    tickers = ensure_list(tickers)

    params = base_params(token)
    params["10113"] = ";".join(tickers)

    r = s.get(
        f"{BASE_URL}/BaseHistoricaNumerica/VolumesMedios",
        params=params,
        timeout=15,
    )

    root = ET.fromstring(r.text)
    if root.findtext("STATUS") != "success":
        msg = root.findtext("MESSAGE") or "Unknown error"
        raise RuntimeError(f"ContentProxy error: {msg}")

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


def binflation(
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch current inflation indices summary.

    Uses Inflacao endpoint. Returns up to 17 inflation indices with
    monthly, 3m, 6m, 12m, and YTD accumulated values.

    Args:
        session_token: BCAA session token

    Returns:
        DataFrame with inflation indices. Columns include: symbol, dat, last,
        var, acum_3m, acum_6m, acum_12m, acum_ano.

    Example:
        >>> df = binflation()
        >>> df[["symbol", "last"]]
    """
    root = content_proxy_get(
        "BaseHistoricaNumerica/Inflacao",
        {},
        session_token=session_token,
        timeout=15,
    )
    rows = parse_ticks(root)
    return to_reference_dataframe(rows)
