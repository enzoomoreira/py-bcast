"""Reference data via aetp/output HTTP API (binary protocol)."""

from __future__ import annotations

import pandas as pd

from .._legacy.aetp import aetp_request, rows_to_dicts
from .._legacy.columns import (
    COMPANY_DETAIL_FIELDS,
    COMPANY_LIST_FIELDS,
    COMPANY_LIST_SCHEMA,
    INDEX_FIELDS,
    INDEX_SCHEMA,
    INDICATOR_META_FIELDS,
    INDICATOR_META_SCHEMA,
    QUOTE_FIELDS,
    QUOTE_SCHEMA,
    SECTOR_FIELDS,
    SECTOR_SCHEMA,
    SHARES_FIELDS,
    SHARES_SCHEMA,
    TICKER_FIELDS,
)
from .._core.dates import DateLike
from .._core.logging import get_logger
from .._legacy.multi import vectorize
from .._core.normalize import ensure_id_list, ensure_list, ensure_str
from .._legacy.output import to_record_dataframe, to_reference_dataframe
from .._legacy.resolve import resolve_cvm
from .._legacy.executor import run_spec
from .._legacy.endpoints import SPEC_BINDICATORS

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
        Flat DataFrame of company data. List mode carries cvm_code,
        corporate_name, trade_name, cnpj (string, leading zeros preserved),
        tickers (";"-joined share classes), logo_url and B3 classification ids.
        Detail mode adds the sector/subsector/segment names, ipo_date,
        last_update, website and description.

    Example:
        >>> companies = bcompany()  # all companies
        >>> petr = bcompany(9512)   # Petrobras detail
    """
    if cvm_code is None:
        parsed = aetp_request("fundamental/empresa/metadado", {}, session_token)
        return to_reference_dataframe(
            rows_to_dicts(parsed),
            rename=COMPANY_LIST_FIELDS,
            schema=COMPANY_LIST_SCHEMA,
        )
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
    return to_reference_dataframe(
        rows_to_dicts(parsed), rename=INDEX_FIELDS, schema=INDEX_SCHEMA
    )


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
    return to_reference_dataframe(
        rows_to_dicts(parsed), rename=SECTOR_FIELDS, schema=SECTOR_SCHEMA
    )


def _quote_one(
    ticker: str,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Fetch the quote for a single symbol (one row, or empty with schema).

    Scalar core shared by the vectorized ``bquote`` and ``resolve_cvm``;
    ``resolve_cvm`` requires exactly one row, so it must never depend on the
    list-returning public ``bquote``.
    """
    parsed = aetp_request("fundamental/ativo/cotacao", {"10068": ticker}, session_token)
    rows = rows_to_dicts(parsed)
    record = rows[0] if rows else {}
    return to_record_dataframe(record, rename=QUOTE_FIELDS, schema=QUOTE_SCHEMA)


def bquote(
    ticker: str | list[str],
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch current quote (price, volume) for one or more symbols via aetp.

    Uses aetp/output/fundamental/AtivoCotacao. This is also the ticker → CVM
    resolution primitive (via the scalar ``_quote_one`` core), so it stays
    "soft": an unknown ticker yields an empty block (resolve_cvm turns that
    into NotFoundError) rather than raising here.

    Args:
        ticker: Single symbol or list (e.g., "PETR4" or ["PETR4", "VALE3"]).
        session_token: BCAA session token

    Returns:
        Flat DataFrame with quote fields (one row per symbol), each block
        tagged with a ``ticker`` column. Empty DataFrame with that schema if
        no symbol has a quote.

    Example:
        >>> q = bquote("PETR4")
        >>> print(q["close"].iloc[0])
    """
    tickers = ensure_list(ticker)
    return vectorize(tickers, lambda t: _quote_one(t, session_token))


def _btickers_one(
    ticker_or_cvm: str | int,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Fetch all tickers for one company (by CVM code or ticker)."""
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


def btickers(
    ticker_or_cvm: str | int | list[str | int],
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch all tickers (stocks/units) for one or more companies.

    Accepts either a CVM code (int) or a ticker string (auto-resolves CVM),
    or a list mixing both. Uses aetp/output/fundamental/AtivoSimbolo.

    Args:
        ticker_or_cvm: CVM code (int, e.g. 9512), ticker (str, e.g. "PETR4"),
            or a list mixing both.
        session_token: BCAA session token

    Returns:
        Flat DataFrame with ticker information. The endpoint emits its own
        ``ticker`` column (the company's symbols, e.g. PETR3/PETR4 for a
        Petrobras lookup), so that column is NOT the lookup identifier.

    Example:
        >>> df = btickers("PETR4")  # resolves CVM, returns PETR3+PETR4
        >>> df = btickers(9512)     # direct CVM code
        >>> df = btickers(["PETR4", 4170])  # mixed list
    """
    items = ensure_id_list(ticker_or_cvm)
    return vectorize(items, lambda x: _btickers_one(x, session_token))


def _bshares_one(
    ticker: str,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Fetch shares outstanding for a single ticker (raises if unknown)."""
    parsed = aetp_request(
        "fundamental/ativo/quantidade",
        {"10068": ticker},
        session_token,
        empty_ok=False,
    )

    rows = rows_to_dicts(parsed)
    record = rows[0] if rows else {}
    return to_record_dataframe(record, rename=SHARES_FIELDS, schema=SHARES_SCHEMA)


def bshares(
    ticker: str | list[str],
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch shares outstanding for one or more tickers.

    Uses aetp/output/fundamental/AtivoQuantidade.

    Args:
        ticker: Single symbol or list (e.g., "PETR4" or ["PETR4", "VALE3"]).
        session_token: BCAA session token

    Returns:
        Flat DataFrame with shares data (one row per ticker; ticker, total/
        float/treasury shares, etc.). Raises NotFoundError if any ticker is
        unknown (fail-fast).

    Example:
        >>> df = bshares("PETR4")
        >>> print(df["total_shares"].iloc[0])
    """
    tickers = ensure_list(ticker)
    return vectorize(tickers, lambda t: _bshares_one(t, session_token))


def bindicators(
    ticker_or_cvm: str | int | list[str | int],
    indicator: str | int,
    start_date: DateLike,
    end_date: DateLike,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch daily indicator history for one or more companies.

    Uses aetp/output/fundamental/IndicadorHistoricoDiario. This serves the
    *daily* indicator series — price-derived metrics such as market value and
    daily risk. Quarterly balance-sheet items (e.g. EBITDA) have no daily
    series and return an empty frame.

    Accepts ticker strings (auto-resolves CVM) or CVM codes directly, or a
    list mixing both. Accepts indicator names (e.g. "Valor de Mercado") or
    numeric IDs (see bindicator_meta()).

    Args:
        ticker_or_cvm: Ticker (str, e.g. "PETR4"), CVM code (int, e.g. 9512),
            or a list mixing both.
        indicator: Indicator name (str, e.g. "Valor de Mercado") or ID
            (int, e.g. 32).
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: End date (str YYYYMMDD, date, datetime, or Timestamp)
        session_token: BCAA session token

    Returns:
        Flat DataFrame (RangeIndex) with one row per (date, share class): a
        string ``date`` column, the indicator ``value``, its day-over-day
        ``value_change_pct``, and a ``ticker`` column holding the per-row share
        class. A "PETR4" query returns both PETR3 and PETR4 (like btickers), so
        ``ticker`` is NOT the input identifier.

    Example:
        >>> df = bindicators("PETR4", "Valor de Mercado", "20250101", "20251231")
        >>> df = bindicators(9512, 32, "20250101", "20251231")
        >>> df = bindicators(["PETR4", "VALE3"], 32, "20250101", "20251231")
    """
    return run_spec(
        SPEC_BINDICATORS,
        session_token=session_token,
        ticker_or_cvm=ticker_or_cvm,
        indicator=indicator,
        start_date=start_date,
        end_date=end_date,
    )


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
    return to_reference_dataframe(
        rows_to_dicts(parsed),
        rename=INDICATOR_META_FIELDS,
        schema=INDICATOR_META_SCHEMA,
    )
