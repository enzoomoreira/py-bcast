"""Corporate events, dividends, and broker portfolios via aetp/output API."""

from __future__ import annotations

import pandas as pd

from .._core.dates import DateLike
from .._core.normalize import ensure_list
from .._core.validation import CvmCode, DateParam, validate_params
from .._core.validation import Ticker
from .._legacy.endpoints import (
    SPEC_BCALENDAR,
    SPEC_BDIVIDENDS,
    SPEC_BDIVIDENDS_BYCVM,
    SPEC_BDY,
    SPEC_BDY_BYCVM,
    SPEC_BPORTFOLIO,
    SPEC_BPORTFOLIOS,
    SPEC_BPORTFOLIOS_WITH,
)
from .._legacy._sync.executor import run_spec


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
    return run_spec(
        SPEC_BCALENDAR,
        session_token=session_token,
        start_date=start_date,
        end_date=end_date,
    )


def bdividends(
    ticker: str | list[str],
    cvm_code: str | int | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch dividend/JCP history for one or more companies.

    Uses aetp/output/fundamental/EmpresaEventosJcpDividendos.

    Args:
        ticker: Ticker symbol or list (e.g., "PETR4" or ["PETR4", "VALE3"]).
            Used directly and also to resolve cvm_code per ticker.
        cvm_code: CVM numeric code (e.g., 9512). Only honored for a single
            ticker; for a list, each ticker resolves its own CVM (a scalar
            code cannot apply across multiple companies). If None, resolved
            automatically.
        session_token: BCAA session token

    Returns:
        Flat DataFrame with dividend events (date, type, value per share,
        etc.) and a ``ticker`` column (one block per company).

    Example:
        >>> df = bdividends("PETR4")
        >>> df.tail()
        >>> df = bdividends(["PETR4", "VALE3"])
    """
    tickers = [t.strip().upper() for t in ensure_list(ticker)]
    if cvm_code is not None and len(tickers) == 1:
        return run_spec(
            SPEC_BDIVIDENDS_BYCVM,
            session_token=session_token,
            ticker=tickers,
            cvm_code=cvm_code,
        )
    return run_spec(SPEC_BDIVIDENDS, session_token=session_token, ticker=tickers)


def bdy(
    ticker: str | list[str],
    start_date: DateLike,
    end_date: DateLike,
    cvm_code: str | int | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch dividend yield historical series for one or more companies.

    Uses aetp/output/fundamental/EmpresaEventosDy.

    Args:
        ticker: Ticker symbol or list (e.g., "PETR4" or ["PETR4", "VALE3"]).
            Used directly and also to resolve cvm_code per ticker.
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: End date (str YYYYMMDD, date, datetime, or Timestamp)
        cvm_code: CVM numeric code (e.g., 9512). Only honored for a single
            ticker; for a list, each ticker resolves its own CVM. If None,
            resolved automatically.
        session_token: BCAA session token

    Returns:
        Flat DataFrame with DatetimeIndex, DY values over time, and a
        ``ticker`` column (one block per company).

    Example:
        >>> df = bdy("PETR4", "20250101", "20260519")
        >>> df.tail()
        >>> df = bdy(["PETR4", "VALE3"], "20250101", "20260519")
    """
    tickers = [t.strip().upper() for t in ensure_list(ticker)]
    if cvm_code is not None and len(tickers) == 1:
        return run_spec(
            SPEC_BDY_BYCVM,
            session_token=session_token,
            ticker=tickers,
            cvm_code=cvm_code,
            start_date=start_date,
            end_date=end_date,
        )
    return run_spec(
        SPEC_BDY,
        session_token=session_token,
        ticker=tickers,
        start_date=start_date,
        end_date=end_date,
    )


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
    return run_spec(SPEC_BPORTFOLIOS, session_token=session_token)


@validate_params
def bportfolio(
    broker_id: CvmCode,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch a broker's recommended portfolios.

    Uses aetp/output/fundamental/CarteiraRecomendadaUltima. One broker returns
    several portfolios in a single response: the default PADRAO holdings plus
    themed lists (e.g. "Carteira Top 10", "Arrojada", "Dividendos", "Small
    Caps"), distinguished by the ``portfolio_name`` column.

    Args:
        broker_id: Broker ID (from bportfolios()).
        session_token: BCAA session token.

    Returns:
        Flat DataFrame, one row per held stock, with columns: broker_id, date,
        ticker, portfolio_name, recommendation, target_price, dy_pct, company,
        sector/subsector/segment (+ ids), and per-stock fundamentals.
        ``recommendation`` (COMPRA/NEUTRA/...), ``target_price`` (broker price
        target) and ``dy_pct`` (12-month dividend yield) are populated only on
        the themed-portfolio rows; they are empty for the PADRAO holdings.

    Example:
        >>> df = bportfolio(27)
        >>> df[df["portfolio_name"] == "Carteira Dividendos"][["ticker", "recommendation"]]
    """
    return run_spec(SPEC_BPORTFOLIO, session_token=session_token, broker_id=broker_id)


@validate_params
def bportfolios_with(
    ticker: Ticker,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch the recommended portfolios that contain a ticker.

    Uses aetp/output/fundamental/CarteiraRecomendadaTicker. Returns the FULL
    composition of every portfolio (all brokers) whose recommendation list
    includes the queried ticker — not just the matching rows. Filter by
    ``broker_id``/``portfolio_name`` or by ``ticker == <query>`` as needed.

    Args:
        ticker: Single ticker (e.g. "PETR4"). One ticker per call: the rows'
            ``ticker`` column is each portfolio's per-row stock, so a
            multi-ticker query would be indistinguishable.
        session_token: BCAA session token.

    Returns:
        Flat DataFrame with the same columns as ``bportfolio`` (broker_id,
        date, ticker, portfolio_name, company, sector data, fundamentals).
        Empty DataFrame with that schema if no portfolio holds the ticker.

    Example:
        >>> df = bportfolios_with("PETR4")
        >>> df[df["ticker"] == "PETR4"][["broker_id", "portfolio_name", "date"]]
    """
    return run_spec(SPEC_BPORTFOLIOS_WITH, session_token=session_token, ticker=ticker)
