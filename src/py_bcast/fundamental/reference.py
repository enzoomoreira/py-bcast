"""Reference data via aetp/output HTTP API (binary protocol)."""

from __future__ import annotations

import pandas as pd

from .._core.dates import DateLike
from .._core.normalize import ensure_list
from .._legacy._sync.executor import run_spec
from .._legacy._sync.quote import quote_one
from .._legacy.endpoints import (
    SPEC_BCOMPANY_DETAIL,
    SPEC_BCOMPANY_LIST,
    SPEC_BFREE_FLOAT,
    SPEC_BFUND_HOLDERS,
    SPEC_BINDICATOR_META,
    SPEC_BINDICATORS,
    SPEC_BINDICES,
    SPEC_BSECTORS,
    SPEC_BSHARES,
    SPEC_BTICKERS,
)
from .._legacy.multi import vectorize


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
        return run_spec(SPEC_BCOMPANY_LIST, session_token=session_token)
    return run_spec(
        SPEC_BCOMPANY_DETAIL, session_token=session_token, cvm_code=cvm_code
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
    return run_spec(SPEC_BINDICES, session_token=session_token)


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
    return run_spec(SPEC_BSECTORS, session_token=session_token)


def bquote(
    ticker: str | list[str],
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch current quote (price, volume) for one or more symbols via aetp.

    Uses aetp/output/fundamental/AtivoCotacao. This is also the ticker → CVM
    resolution primitive (via the scalar ``quote_one`` core), so it stays
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
    return vectorize(tickers, lambda t: quote_one(t, session_token))


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
    return run_spec(
        SPEC_BTICKERS, session_token=session_token, ticker_or_cvm=ticker_or_cvm
    )


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
    return run_spec(SPEC_BSHARES, session_token=session_token, ticker=ticker)


def bfree_float(
    ticker_or_cvm: str | int | list[str | int],
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch share classes with free float and units composition for companies.

    Uses aetp/output/fundamental/EmpresaAcoesUnits. One row per share class
    (ON/PN/UNIT): total, free-float and treasury share counts (thousands),
    the free-float percentage, and — on UNIT rows — how many ON/PN shares
    compose one unit (the share counts are blank there).

    Args:
        ticker_or_cvm: Ticker (str, e.g. "PETR4"), CVM code (int, e.g. 9512),
            or a list mixing both.
        session_token: BCAA session token

    Returns:
        Flat DataFrame (RangeIndex) with ticker, share_type, total_shares,
        float_shares, treasury_shares, float_pct, unit_on, unit_pn. The
        endpoint emits its own ``ticker`` column (the company's share
        classes), so it is NOT the lookup identifier. Raises NotFoundError if
        any identifier is unknown (fail-fast).

    Example:
        >>> df = bfree_float("PETR4")   # PETR3 + PETR4 rows
        >>> df = bfree_float("SANB11")  # SANB3 + SANB4 + SANB11 (UNIT) rows
    """
    return run_spec(
        SPEC_BFREE_FLOAT, session_token=session_token, ticker_or_cvm=ticker_or_cvm
    )


def bfund_holders(
    ticker_or_cvm: str | int | list[str | int],
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch the top investment funds holding one or more companies.

    Uses aetp/output/fundamental/CarteiraTopFundos. One row per fund position:
    the fund's id, names, CNPJ, administrator, manager and category, the
    position's value and quantity, the asset's share of the fund's equity
    (``pct_of_fund``), and the position's reference year/month.

    Args:
        ticker_or_cvm: Ticker (str, e.g. "PETR4"), CVM code (int, e.g. 9512),
            or a list mixing both.
        session_token: BCAA session token

    Returns:
        Flat DataFrame (RangeIndex), each block tagged with a ``ticker``
        column holding the queried identifier. A company no fund holds
        contributes an empty block; empty DataFrame with the schema if none
        has holders.

    Example:
        >>> df = bfund_holders("PETR4")
        >>> df[["fund_trade_name", "position_value", "pct_of_fund"]].head()
    """
    return run_spec(
        SPEC_BFUND_HOLDERS, session_token=session_token, ticker_or_cvm=ticker_or_cvm
    )


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
    return run_spec(SPEC_BINDICATOR_META, session_token=session_token)
