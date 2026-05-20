"""Reference data via aetp/output HTTP API (binary protocol)."""

from __future__ import annotations

import pandas as pd

from .._core.aetp import aetp_request, rows_to_dicts
from .._core.dates import DateLike, to_date_str
from .._core.normalize import ensure_str
from .._core.output import to_dataframe, to_reference_dataframe, to_series


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
        parsed = aetp_request(
            "fundamental/empresa/metadado", {}, session_token
        )
    else:
        parsed = aetp_request(
            "fundamental/empresa",
            {"13004": ensure_str(cvm_code)},
            session_token,
        )

    return to_reference_dataframe(rows_to_dicts(parsed))


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
    return to_reference_dataframe(rows_to_dicts(parsed))


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
    parsed = aetp_request(
        "fundamental/setor", {}, session_token
    )
    return to_reference_dataframe(rows_to_dicts(parsed))


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
        >>> print(q["last"])
    """
    try:
        parsed = aetp_request(
            "fundamental/ativo/cotacao",
            {"10068": ticker},
            session_token,
        )
    except RuntimeError:
        return pd.Series(dtype="object")

    rows = rows_to_dicts(parsed)
    return to_series(rows[0]) if rows else pd.Series(dtype="object")


def btickers(
    cvm_code: str | int,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch all tickers (stocks/units) for a company by CVM code.

    Uses aetp/output/fundamental/AtivoSimbolo.

    Args:
        cvm_code: CVM numeric code (e.g., 9512 for Petrobras)
        session_token: BCAA session token

    Returns:
        DataFrame with ticker information.

    Example:
        >>> df = btickers(9512)  # PETR3, PETR4
    """
    parsed = aetp_request(
        "fundamental/ativo/simbolo",
        {"13004": ensure_str(cvm_code)},
        session_token,
    )
    return to_reference_dataframe(rows_to_dicts(parsed))


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
    )

    rows = rows_to_dicts(parsed)
    return to_series(rows[0]) if rows else pd.Series(dtype="object")


def bindicators(
    cvm_code: str | int,
    indicator_id: str | int,
    start_date: DateLike,
    end_date: DateLike,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch daily indicator history for a company.

    Uses aetp/output/fundamental/IndicadorHistoricoDiario.
    Known indicator IDs: 32 = Market Cap, 52 = Beta.

    Args:
        cvm_code: CVM numeric code (e.g., 9512 for Petrobras)
        indicator_id: Indicator ID (e.g., 32 for Market Cap, 52 for Beta)
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: End date (str YYYYMMDD, date, datetime, or Timestamp)
        session_token: BCAA session token

    Returns:
        DataFrame with DatetimeIndex and daily indicator values.

    Example:
        >>> df = bindicators(9512, 32, "20260101", "20260519")
        >>> df.tail()
    """
    parsed = aetp_request(
        "fundamental/indicador/historico-diario",
        {
            "13004": ensure_str(cvm_code),
            "13760": ensure_str(indicator_id),
            "10057": to_date_str(start_date),
            "10058": to_date_str(end_date),
        },
        session_token,
    )
    rows = rows_to_dicts(parsed)
    return to_dataframe(rows)


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
    return to_reference_dataframe(rows_to_dicts(parsed))
