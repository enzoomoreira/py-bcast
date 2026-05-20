"""Corporate events, dividends, and broker portfolios via aetp/output API."""

from __future__ import annotations

from ._constants import BASE_URL
from ._http import create_http_session, get_session_token
from .fundamental import _parse_binary_response
from .reference import _aetp_request, _rows_to_dicts


def bcalendar(
    start_date: str,
    end_date: str,
    session_token: str | None = None,
) -> list[dict[str, str]]:
    """
    Fetch corporate events calendar.

    Uses aetp/output/fundamental/CalendarioEventosCorporativos.
    Returns all scheduled events (dividends, JCP, splits, AGMs, etc.)
    in the given date range.

    Args:
        start_date: Start date as YYYYMMDD
        end_date: End date as YYYYMMDD
        session_token: BCAA session token

    Returns:
        List of dicts with event data (date, type, company, description).

    Example:
        >>> events = bcalendar("20260101", "20260519")
        >>> print(f"{len(events)} events found")
    """
    parsed = _aetp_request(
        "fundamental/calendario-eventos-corporativos",
        {"10057": start_date, "10058": end_date},
        session_token,
    )
    return _rows_to_dicts(parsed)


def bdividends(
    cvm_code: str | int,
    ticker: str,
    session_token: str | None = None,
) -> list[dict[str, str]]:
    """
    Fetch dividend/JCP history for a company.

    Uses aetp/output/fundamental/EmpresaEventosJcpDividendos.

    Args:
        cvm_code: CVM numeric code (e.g., 9512 for Petrobras)
        ticker: Ticker symbol (e.g., "PETR4")
        session_token: BCAA session token

    Returns:
        List of dicts with dividend events (date, type, value per share, etc.).

    Example:
        >>> divs = bdividends(9512, "PETR4")
        >>> for d in divs[-3:]:
        ...     print(d)
    """
    parsed = _aetp_request(
        "fundamental/empresa/eventos/jcp-dividendos",
        {"13004": str(cvm_code), "10068": ticker},
        session_token,
    )
    return _rows_to_dicts(parsed)


def bdy(
    cvm_code: str | int,
    ticker: str,
    start_date: str,
    end_date: str,
    session_token: str | None = None,
) -> list[dict[str, str]]:
    """
    Fetch dividend yield historical series for a company.

    Uses aetp/output/fundamental/EmpresaEventosDy.

    Args:
        cvm_code: CVM numeric code (e.g., 9512 for Petrobras)
        ticker: Ticker symbol (e.g., "PETR4")
        start_date: Start date as YYYYMMDD
        end_date: End date as YYYYMMDD
        session_token: BCAA session token

    Returns:
        List of dicts with DY values over time.

    Example:
        >>> dy = bdy(9512, "PETR4", "20250101", "20260519")
        >>> for row in dy[-3:]:
        ...     print(row)
    """
    parsed = _aetp_request(
        "fundamental/empresa/eventos/dividend-yield",
        {
            "13004": str(cvm_code),
            "10068": ticker,
            "10057": start_date,
            "10058": end_date,
            "10029": "1",
        },
        session_token,
    )
    return _rows_to_dicts(parsed)


def bportfolios(
    session_token: str | None = None,
) -> list[dict[str, str]]:
    """
    Fetch list of broker recommended portfolios.

    Uses aetp/output/fundamental/CarteiraRecomendadaCorretoras.
    Returns all brokers that publish model portfolios.

    Args:
        session_token: BCAA session token

    Returns:
        List of dicts with broker data (ID, name).

    Example:
        >>> brokers = bportfolios()
        >>> for b in brokers[:5]:
        ...     print(b)
    """
    parsed = _aetp_request(
        "fundamental/empresa/carteira-recomendada/corretoras", {}, session_token
    )
    return _rows_to_dicts(parsed)


def bportfolio(
    broker_id: str | int,
    session_token: str | None = None,
) -> list[dict[str, str]]:
    """
    Fetch the latest recommended portfolio from a broker.

    Uses aetp/output/fundamental/CarteiraRecomendadaUltima.

    Args:
        broker_id: Broker ID (from bportfolios())
        session_token: BCAA session token

    Returns:
        List of dicts with portfolio composition (ticker, weight, etc.).

    Example:
        >>> holdings = bportfolio(42)
        >>> for h in holdings:
        ...     print(h)
    """
    parsed = _aetp_request(
        "fundamental/empresa/carteira-recomendada/ultima",
        {"10087": str(broker_id)},
        session_token,
    )
    return _rows_to_dicts(parsed)
