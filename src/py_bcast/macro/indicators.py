"""Macroeconomic indicators and fixed-income data via ContentProxy HTTP API."""

from __future__ import annotations

import pandas as pd

from .._core.validation import DateParam, Ticker, TickerList, validate_params
from .._legacy.endpoints import (
    SPEC_BDI_CDI,
    SPEC_BFX,
    SPEC_BINFLATION,
    SPEC_BINFLATION_HISTORY,
    SPEC_BMACRO,
    SPEC_BRETURN,
    SPEC_BSNAPSHOT,
    SPEC_BSTATS,
    SPEC_BVOLUME,
)
from .._legacy.multi import vectorize
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

    Uses the MacroEconomicos endpoint. Supports FX, indices, commodities,
    rates, and synthetic AETAXAS indicators. The special symbol "CDI" routes
    to the DiCetipAcumulado endpoint (daily accumulated CDI since 1986),
    whose block additionally carries an ``accumulated`` column.

    Supported symbols include:
        FX: USDBRL, EURUSD, GBPUSD, JPYBRL, etc.
        Indices: IBOV, SPX, DAX, FTSE, NASDAQ, DJI, etc.
        Commodities: GOLD, SILVER, WTI, BRENT, etc.
        Rates/DI: CDI, DI1F26, DI1F27, DI1F28, etc.
        AETAXAS: AEIPCA, AEIGPM, AECTIP, AEB052, AEB200, AEFS10, etc.

    Args:
        ticker: Single symbol or list (e.g., "USDBRL" or ["USDBRL", "CDI"]).
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: End date (str YYYYMMDD, date, datetime, or Timestamp)
        session_token: BCAA session token

    Returns:
        Flat DataFrame with a DatetimeIndex and a ``ticker`` column (one block
        per symbol). Columns depend on symbol but typically include close,
        open, high, low, settle, change_pct, trades, volume; the "CDI" block
        adds accumulated.

    Example:
        >>> df = bmacro("USDBRL", "20260101", "20260519")
        >>> cdi = bmacro("CDI", "20260101", "20260519")
    """

    def one(symbol: str) -> pd.DataFrame:
        if symbol == "CDI":
            df = run_spec(
                SPEC_BDI_CDI,
                session_token=session_token,
                start_date=start_date,
                end_date=end_date,
            )
            df.insert(0, "ticker", "CDI")
            return df
        return run_spec(
            SPEC_BMACRO,
            session_token=session_token,
            ticker=symbol,
            start_date=start_date,
            end_date=end_date,
        )

    return vectorize(ticker, one)


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
        Columns: ticker, avg_volume, avg_turnover, avg_trades, months, date.

    Example:
        >>> df = bvolume(["PETR4", "VALE3"])
        >>> df[df["ticker"] == "PETR4"]
    """
    return run_spec(SPEC_BVOLUME, session_token=session_token, tickers=tickers)


@validate_params
def bfx(
    from_currency: Ticker,
    to_currency: Ticker,
    amount: float = 1.0,
    session_token: str | None = None,
) -> float:
    """
    Convert an amount between currencies at the current spot rate.

    Uses the ConversorMoedas endpoint — a server-side spot calculation
    (historical conversion is not supported; date parameters are inert).

    Args:
        from_currency: Source currency code (e.g. "USD").
        to_currency: Target currency code (e.g. "BRL").
        amount: Amount in the source currency (default 1.0, which makes the
            return value the spot rate itself).
        session_token: BCAA session token

    Returns:
        The converted amount as a float.

    Raises:
        NotFoundError: If the currency pair is unknown to the server.

    Example:
        >>> bfx("USD", "BRL")        # spot rate
        5.1716
        >>> bfx("USD", "BRL", 100)   # converted amount
        517.16
    """
    df = run_spec(
        SPEC_BFX,
        session_token=session_token,
        from_currency=from_currency,
        to_currency=to_currency,
        amount=amount,
    )
    return float(df["close"].iloc[0])


@validate_params
def bstats(
    tickers: TickerList,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch a market-statistics snapshot for one or more symbols.

    Uses the FIIAnbimaBovespa endpoint, which despite the name serves any B3
    symbol (stocks, FIIs, units): bid/ask at the last session's close, last
    dividend and dividend yield, 52-week range (adjusted), last and average
    financial volumes, and average daily trade count. FIIs additionally
    populate ``net_assets``.

    Args:
        tickers: Single ticker or list (e.g., "HGLG11" or ["PETR4", "HGLG11"]).
        session_token: BCAA session token

    Returns:
        Flat DataFrame (RangeIndex), one row per symbol. Columns: ticker, bid,
        bid_date, ask, ask_date, last_dividend, last_dividend_date,
        dividend_yield_pct, shares_outstanding, low_52w, low_52w_date,
        high_52w, high_52w_date, turnover_last, avg_turnover_30d,
        avg_turnover_100d, avg_turnover_180d, source, net_assets,
        avg_trades_180d. Unknown symbols are omitted; empty DataFrame with
        that schema if none resolves.

    Example:
        >>> df = bstats(["HGLG11", "PETR4"])
        >>> df[["ticker", "dividend_yield_pct"]]
    """
    return run_spec(SPEC_BSTATS, session_token=session_token, tickers=tickers)


@validate_params
def bsnapshot(
    tickers: TickerList,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch the latest intraday session snapshot for one or more symbols.

    Uses the UltimosIntraday endpoint: near-real-time OHLC, volume, trade
    count and turnover without needing the DDE channel. While the session
    is open the snapshot accumulates the running session; after the close
    the server was observed serving only the session's last interval.

    Args:
        tickers: Single ticker or list (e.g., "PETR4" or ["PETR4", "VALE3"]).
        session_token: BCAA session token

    Returns:
        Flat DataFrame (RangeIndex), one row per symbol: ticker, date, time
        (snapshot timestamp), close (last), low, high, open, volume, trades,
        turnover, open_interest. Unknown symbols are omitted; empty
        DataFrame with that schema if none resolves.

    Example:
        >>> df = bsnapshot(["PETR4", "VALE3"])
        >>> df[["ticker", "close", "volume"]]
    """
    return run_spec(SPEC_BSNAPSHOT, session_token=session_token, tickers=tickers)


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


@validate_params
def binflation_history(
    symbol: TickerList,
    start_date: DateParam,
    end_date: DateParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch the accumulated-inflation series for one or more inflation indices.

    Uses the CalculoInflacao endpoint with the synthetic AE inflation symbols
    (``AEIPCA``, ``AEIGPM``, ``AEINPC``, etc. — the same family ``bmacro``
    accepts). Returns the index compounded from the window start, mirroring the
    accumulated shape of ``baccrual`` / ``bsavings``. Unlike ``binflation``
    (the latest monthly snapshot), this is a daily time series.

    Args:
        symbol: Single inflation symbol or list (e.g. "AEIPCA").
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: Optional end date (default: through today).
        session_token: BCAA session token

    Returns:
        Flat DataFrame with a DatetimeIndex and a ``ticker`` column (one block
        per symbol) and an ``accumulated`` column (% since start_date).

    Example:
        >>> df = binflation_history("AEIPCA", "20250101")
        >>> df["accumulated"].iloc[-1]
    """
    return run_spec(
        SPEC_BINFLATION_HISTORY,
        session_token=session_token,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )
