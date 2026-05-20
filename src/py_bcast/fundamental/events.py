"""Corporate events, dividends, and broker portfolios via aetp/output API."""

from __future__ import annotations

import pandas as pd

from .._core.aetp import aetp_request, rows_to_dicts
from .._core.dates import DateLike, to_date_str
from .._core.normalize import ensure_str
from .._core.output import to_dataframe, to_reference_dataframe


def bcalendar(
    start_date: DateLike,
    end_date: DateLike,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch corporate events calendar.

    Uses aetp/output/fundamental/CalendarioEventosCorporativos.
    Returns all scheduled events (dividends, JCP, splits, AGMs, etc.)
    in the given date range.

    Args:
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: End date (str YYYYMMDD, date, datetime, or Timestamp)
        session_token: BCAA session token

    Returns:
        DataFrame with event data (date, type, company, description).

    Example:
        >>> df = bcalendar("20260101", "20260519")
        >>> print(f"{len(df)} events found")
    """
    parsed = aetp_request(
        "fundamental/calendario-eventos-corporativos",
        {"10057": to_date_str(start_date), "10058": to_date_str(end_date)},
        session_token,
    )
    return to_reference_dataframe(rows_to_dicts(parsed))


def bdividends(
    cvm_code: str | int,
    ticker: str,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch dividend/JCP history for a company.

    Uses aetp/output/fundamental/EmpresaEventosJcpDividendos.

    Args:
        cvm_code: CVM numeric code (e.g., 9512 for Petrobras)
        ticker: Ticker symbol (e.g., "PETR4")
        session_token: BCAA session token

    Returns:
        DataFrame with dividend events (date, type, value per share, etc.).

    Example:
        >>> df = bdividends(9512, "PETR4")
        >>> df.tail()
    """
    parsed = aetp_request(
        "fundamental/empresa/eventos/jcp-dividendos",
        {"13004": ensure_str(cvm_code), "10068": ticker},
        session_token,
    )
    return to_reference_dataframe(rows_to_dicts(parsed))


def bdy(
    cvm_code: str | int,
    ticker: str,
    start_date: DateLike,
    end_date: DateLike,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch dividend yield historical series for a company.

    Uses aetp/output/fundamental/EmpresaEventosDy.

    Args:
        cvm_code: CVM numeric code (e.g., 9512 for Petrobras)
        ticker: Ticker symbol (e.g., "PETR4")
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: End date (str YYYYMMDD, date, datetime, or Timestamp)
        session_token: BCAA session token

    Returns:
        DataFrame with DatetimeIndex and DY values over time.

    Example:
        >>> df = bdy(9512, "PETR4", "20250101", "20260519")
        >>> df.tail()
    """
    parsed = aetp_request(
        "fundamental/empresa/eventos/dividend-yield",
        {
            "13004": ensure_str(cvm_code),
            "10068": ticker,
            "10057": to_date_str(start_date),
            "10058": to_date_str(end_date),
            "10029": "1",
        },
        session_token,
    )
    rows = rows_to_dicts(parsed)
    return to_dataframe(rows)


def bportfolios(
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch list of broker recommended portfolios.

    Uses aetp/output/fundamental/CarteiraRecomendadaCorretoras.
    Returns all brokers that publish model portfolios.

    Args:
        session_token: BCAA session token

    Returns:
        DataFrame with broker data (ID, name).

    Example:
        >>> df = bportfolios()
        >>> df.head()
    """
    parsed = aetp_request(
        "fundamental/empresa/carteira-recomendada/corretoras", {}, session_token
    )
    return to_reference_dataframe(rows_to_dicts(parsed))


def bportfolio(
    broker_id: str | int,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch the latest recommended portfolio from a broker.

    Uses aetp/output/fundamental/CarteiraRecomendadaUltima.

    Args:
        broker_id: Broker ID (from bportfolios())
        session_token: BCAA session token

    Returns:
        DataFrame with portfolio composition (ticker, weight, etc.).

    Example:
        >>> df = bportfolio(42)
        >>> df.head()
    """
    parsed = aetp_request(
        "fundamental/empresa/carteira-recomendada/ultima",
        {"10087": ensure_str(broker_id)},
        session_token,
    )
    return to_reference_dataframe(rows_to_dicts(parsed))
