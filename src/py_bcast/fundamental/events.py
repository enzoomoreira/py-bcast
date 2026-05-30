"""Corporate events, dividends, and broker portfolios via aetp/output API."""

from __future__ import annotations

import pandas as pd

from .._core.aetp import aetp_request, rows_to_dicts
from .._core.columns import (
    CALENDAR_FIELDS,
    DIVIDEND_FIELDS,
    DY_FIELDS,
    PORTFOLIO_FIELDS,
    PORTFOLIO_LIST_FIELDS,
)
from .._core.dates import DateLike, to_date_str
from .._core.normalize import ensure_str
from .._core.output import to_dataframe, to_reference_dataframe
from .._core.resolve import resolve_cvm
from .._core.validation import CvmCode, DateParam, validate_params


@validate_params
def bcalendar(
    start_date: DateParam,
    end_date: DateParam,
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
    return to_reference_dataframe(rows_to_dicts(parsed), rename=CALENDAR_FIELDS)


def bdividends(
    ticker: str,
    cvm_code: str | int | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch dividend/JCP history for a company.

    Uses aetp/output/fundamental/EmpresaEventosJcpDividendos.

    Args:
        ticker: Ticker symbol (e.g., "PETR4"). Used directly and also
            to resolve cvm_code if not provided.
        cvm_code: CVM numeric code (e.g., 9512). If None, resolved
            automatically from the ticker.
        session_token: BCAA session token

    Returns:
        DataFrame with dividend events (date, type, value per share, etc.).

    Example:
        >>> df = bdividends("PETR4")
        >>> df.tail()
    """
    ticker = ticker.strip().upper()
    if cvm_code is None:
        cvm_code = resolve_cvm(ticker, session_token)
    parsed = aetp_request(
        "fundamental/empresa/eventos/jcp-dividendos",
        {"13004": ensure_str(cvm_code), "10068": ticker},
        session_token,
    )
    return to_reference_dataframe(rows_to_dicts(parsed), rename=DIVIDEND_FIELDS)


def bdy(
    ticker: str,
    start_date: DateLike,
    end_date: DateLike,
    cvm_code: str | int | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch dividend yield historical series for a company.

    Uses aetp/output/fundamental/EmpresaEventosDy.

    Args:
        ticker: Ticker symbol (e.g., "PETR4"). Used directly and also
            to resolve cvm_code if not provided.
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: End date (str YYYYMMDD, date, datetime, or Timestamp)
        cvm_code: CVM numeric code (e.g., 9512). If None, resolved
            automatically from the ticker.
        session_token: BCAA session token

    Returns:
        DataFrame with DatetimeIndex and DY values over time.

    Example:
        >>> df = bdy("PETR4", "20250101", "20260519")
        >>> df.tail()
    """
    ticker = ticker.strip().upper()
    if cvm_code is None:
        cvm_code = resolve_cvm(ticker, session_token)
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
    return to_dataframe(rows, rename=DY_FIELDS)


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
    return to_reference_dataframe(rows_to_dicts(parsed), rename=PORTFOLIO_LIST_FIELDS)


@validate_params
def bportfolio(
    broker_id: CvmCode,
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
        empty_ok=False,
    )
    return to_reference_dataframe(rows_to_dicts(parsed), rename=PORTFOLIO_FIELDS)
