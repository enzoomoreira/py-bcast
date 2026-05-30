"""Reference data via aetp/output HTTP API (binary protocol)."""

from __future__ import annotations

import pandas as pd

from .._core.aetp import aetp_request, rows_to_dicts
from .._core.columns import (
    COMPANY_DETAIL_FIELDS,
    COMPANY_LIST_FIELDS,
    INDEX_FIELDS,
    INDICATOR_HISTORY_FIELDS,
    INDICATOR_META_FIELDS,
    QUOTE_FIELDS,
    SECTOR_FIELDS,
    SHARES_FIELDS,
    TICKER_FIELDS,
)
from .._core.dates import DateLike, to_date_str
from .._core.exceptions import ProtocolError
from .._core.logging import get_logger
from .._core.normalize import ensure_str
from .._core.output import to_dataframe, to_reference_dataframe, to_series
from .._core.resolve import resolve_cvm, resolve_indicator

logger = get_logger(__name__)


def bcompany(
    cvm_code: str | int | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch company metadata from the fundamental database.

    Without cvm_code: returns all ~1020 companies (EmpresaMetadado).
    With cvm_code: returns detailed data for one company (EmpresaDados).

    Args:
        cvm_code: CVM numeric code (e.g., 9512 for PETR, 4170 for VALE).
                  If None, returns the full list.
        session_token: BCAA session token

    Returns:
        DataFrame with company data.
        Full list fields: 13004 (CVM), 13003 (name), 13786 (ticker), etc.
        Detail fields: CNPJ, sector, foundation date, etc.

    Example:
        >>> companies = bcompany()  # all companies
        >>> petr = bcompany(9512)   # Petrobras detail
    """
    if cvm_code is None:
        parsed = aetp_request("fundamental/empresa/metadado", {}, session_token)
        return to_reference_dataframe(rows_to_dicts(parsed), rename=COMPANY_LIST_FIELDS)
    else:
        parsed = aetp_request(
            "fundamental/empresa",
            {"13004": ensure_str(cvm_code)},
            session_token,
            empty_ok=False,
        )
        return to_reference_dataframe(
            rows_to_dicts(parsed), rename=COMPANY_DETAIL_FIELDS
        )


def bindices(
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch list of B3 market indices.

    Uses aetp/output/fundamental/Indices. Returns ~37 indices
    (IBOV, IBRX, SMLL, IDIV, etc.).

    Args:
        session_token: BCAA session token

    Returns:
        DataFrame with index information.

    Example:
        >>> df = bindices()
        >>> df.head()
    """
    parsed = aetp_request("ativos/indice", {}, session_token)
    return to_reference_dataframe(rows_to_dicts(parsed), rename=INDEX_FIELDS)


def bsectors(
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch B3 sector/subsector/segment classification.

    Uses aetp/output/fundamental/SetorSubsetorSegmento. Returns ~38 sectors.

    Args:
        session_token: BCAA session token

    Returns:
        DataFrame with sector classification hierarchy.

    Example:
        >>> df = bsectors()
        >>> df.head()
    """
    parsed = aetp_request("fundamental/setor", {}, session_token)
    return to_reference_dataframe(rows_to_dicts(parsed), rename=SECTOR_FIELDS)


def bquote(
    ticker: str,
    session_token: str | None = None,
) -> pd.Series:
    """
    Fetch current quote (price, volume) for a symbol via aetp.

    Uses aetp/output/fundamental/AtivoCotacao.

    Args:
        ticker: Symbol (e.g., "PETR4", "VALE3")
        session_token: BCAA session token

    Returns:
        Series with quote fields (price, volume, quantity, etc.).
        Empty Series if not found.

    Example:
        >>> q = bquote("PETR4")
        >>> print(q["close"])
    """
    try:
        parsed = aetp_request(
            "fundamental/ativo/cotacao",
            {"10068": ticker},
            session_token,
        )
    except ProtocolError:
        logger.warning("bquote: no data for %s", ticker)
        return pd.Series(dtype="object")

    rows = rows_to_dicts(parsed)
    return (
        to_series(rows[0], rename=QUOTE_FIELDS) if rows else pd.Series(dtype="object")
    )


def btickers(
    ticker_or_cvm: str | int,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch all tickers (stocks/units) for a company.

    Accepts either a CVM code (int) or a ticker string (auto-resolves CVM).
    Uses aetp/output/fundamental/AtivoSimbolo.

    Args:
        ticker_or_cvm: CVM numeric code (int, e.g. 9512) or ticker (str, e.g. "PETR4").
        session_token: BCAA session token

    Returns:
        DataFrame with ticker information.

    Example:
        >>> df = btickers("PETR4")  # resolves CVM, returns PETR3+PETR4
        >>> df = btickers(9512)     # direct CVM code
    """
    if isinstance(ticker_or_cvm, int) or str(ticker_or_cvm).isdigit():
        cvm_code = int(ticker_or_cvm)
    else:
        cvm_code = resolve_cvm(str(ticker_or_cvm), session_token)
    parsed = aetp_request(
        "fundamental/ativo/simbolo",
        {"13004": str(cvm_code)},
        session_token,
        empty_ok=False,
    )
    return to_reference_dataframe(rows_to_dicts(parsed), rename=TICKER_FIELDS)


def bshares(
    ticker: str,
    session_token: str | None = None,
) -> pd.Series:
    """
    Fetch shares outstanding for a ticker.

    Uses aetp/output/fundamental/AtivoQuantidade.

    Args:
        ticker: Symbol (e.g., "PETR4")
        session_token: BCAA session token

    Returns:
        Series with shares data. Empty Series if not found.

    Example:
        >>> s = bshares("PETR4")
        >>> print(s)
    """
    parsed = aetp_request(
        "fundamental/ativo/quantidade",
        {"10068": ticker},
        session_token,
        empty_ok=False,
    )

    rows = rows_to_dicts(parsed)
    return (
        to_series(rows[0], rename=SHARES_FIELDS) if rows else pd.Series(dtype="object")
    )


def bindicators(
    ticker_or_cvm: str | int,
    indicator: str | int,
    start_date: DateLike,
    end_date: DateLike,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch daily indicator history for a company.

    Uses aetp/output/fundamental/IndicadorHistoricoDiario.

    Accepts ticker strings (auto-resolves CVM) or CVM codes directly.
    Accepts indicator names (e.g. "EBITDA", "ROE") or numeric IDs.

    Args:
        ticker_or_cvm: Ticker (str, e.g. "PETR4") or CVM code (int, e.g. 9512).
        indicator: Indicator name (str, e.g. "EBITDA") or ID (int, e.g. 11).
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: End date (str YYYYMMDD, date, datetime, or Timestamp)
        session_token: BCAA session token

    Returns:
        DataFrame with DatetimeIndex and daily indicator values.

    Example:
        >>> df = bindicators("PETR4", "EBITDA", "20260101", "20260519")
        >>> df = bindicators(9512, 32, "20260101", "20260519")
    """
    # Resolve ticker → CVM
    if isinstance(ticker_or_cvm, int) or str(ticker_or_cvm).isdigit():
        cvm_code = int(ticker_or_cvm)
    else:
        cvm_code = resolve_cvm(str(ticker_or_cvm), session_token)

    # Resolve indicator name → ID
    indicator_id = resolve_indicator(indicator, session_token)

    parsed = aetp_request(
        "fundamental/indicador/historico-diario",
        {
            "13004": str(cvm_code),
            "13760": str(indicator_id),
            "10057": to_date_str(start_date),
            "10058": to_date_str(end_date),
        },
        session_token,
    )
    rows = rows_to_dicts(parsed)
    return to_dataframe(rows, rename=INDICATOR_HISTORY_FIELDS)


def bindicator_meta(
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch metadata for all available fundamental indicators.

    Uses aetp/output/fundamental/IndicadorMetadado. Returns ~80 indicators
    with their IDs, names, and categories.

    Args:
        session_token: BCAA session token

    Returns:
        DataFrame with indicator metadata.

    Example:
        >>> df = bindicator_meta()
        >>> df.head()
    """
    parsed = aetp_request("fundamental/indicador/metadado", {}, session_token)
    return to_reference_dataframe(rows_to_dicts(parsed), rename=INDICATOR_META_FIELDS)
