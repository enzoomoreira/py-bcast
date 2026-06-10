"""Macroeconomic indicators and fixed-income data via ContentProxy HTTP API."""

from __future__ import annotations

import pandas as pd

from .._core.validation import DateParam, TickerList, validate_params
from .._legacy.endpoints import (
    SPEC_BDI_CDI,
    SPEC_BINFLATION,
    SPEC_BMACRO,
    SPEC_BRETURN,
    SPEC_BVOLUME,
)
from .._legacy._sync.executor import run_spec


@validate_params
def bmacro(
    ticker: TickerList,
    start_date: DateParam,
    end_date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch macroeconomic/index historical series for one or more symbols.

    Uses MacroEconomicos endpoint. Supports FX, indices, commodities, rates,
    and synthetic AETAXAS indicators.

    Supported symbols include:
        FX: USDBRL, EURUSD, GBPUSD, JPYBRL, etc.
        Indices: IBOV, SPX, DAX, FTSE, NASDAQ, DJI, etc.
        Commodities: GOLD, SILVER, WTI, BRENT, etc.
        Rates/DI: DI1F26, DI1F27, DI1F28, etc.
        AETAXAS: AEIPCA, AEIGPM, AECTIP, AEB052, AEB200, AEFS10, etc.

    Args:
        ticker: Single symbol or list (e.g., "USDBRL" or ["USDBRL", "IBOV"]).
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: End date (str YYYYMMDD, date, datetime, or Timestamp)
        session_token: BCAA session token

    Returns:
        Flat DataFrame with a DatetimeIndex and a ``ticker`` column (one block
        per symbol). Columns depend on symbol but typically include close,
        open, high, low, settle, change_pct, trades, volume.

    Example:
        >>> df = bmacro("USDBRL", "20260101", "20260519")
        >>> df["close"].plot()
    """
    return run_spec(
        SPEC_BMACRO,
        session_token=session_token,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
    )


@validate_params
def bdi_cdi(
    start_date: DateParam,
    end_date: DateParam,
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
        >>> df["close"].iloc[-1]
    """
    return run_spec(
        SPEC_BDI_CDI,
        session_token=session_token,
        start_date=start_date,
        end_date=end_date,
    )


@validate_params
def breturn(
    ticker: TickerList,
    start_date: DateParam,
    end_date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch adjusted daily returns for one or more symbols.

    Uses RetornoDiario endpoint.

    Args:
        ticker: Single symbol or list (e.g., "PETR4" or ["PETR4", "VALE3"]).
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: End date (str YYYYMMDD, date, datetime, or Timestamp)
        session_token: BCAA session token

    Returns:
        Flat DataFrame with a DatetimeIndex and a ``ticker`` column (one block
        per symbol). Columns: change_pct, close.

    Example:
        >>> df = breturn("PETR4", "20260101", "20260519")
        >>> df["close"].cumsum().plot()
    """
    return run_spec(
        SPEC_BRETURN,
        session_token=session_token,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
    )


@validate_params
def bvolume(
    tickers: TickerList,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch average volume statistics for one or more symbols.

    Uses VolumesMedios endpoint. Returns 1m/2m/3m/6m average volumes.

    Args:
        tickers: Single ticker or list (e.g., "PETR4" or ["PETR4", "VALE3"])
        session_token: BCAA session token

    Returns:
        Flat DataFrame (RangeIndex), one row per (ticker, averaging window).
        Columns: ticker, avg_volume, avg_turnover, avg_trades, months, dat.

    Example:
        >>> df = bvolume(["PETR4", "VALE3"])
        >>> df[df["ticker"] == "PETR4.BVMF"]
    """
    return run_spec(SPEC_BVOLUME, session_token=session_token, tickers=tickers)


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
        >>> df[["symbol", "close"]]
    """
    return run_spec(SPEC_BINFLATION, session_token=session_token)
