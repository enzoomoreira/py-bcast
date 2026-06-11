"""Historical daily prices via ContentProxy (close history, OHLCV, first close)."""

from __future__ import annotations

from typing import Literal

import pandas as pd

from .._core.dates import default_end_date, to_date_str
from .._core.validation import DateParam, TickerList, validate_params
from .._legacy.columns import BHISTORY_SCHEMA, DAILY_OHLCV_SCHEMA
from .._legacy.endpoints import SPEC_BFIRST_CLOSE, SPEC_BHISTORY
from .._legacy.multi import vectorize
from .._legacy.output import empty_history_frame
from .._legacy._sync.executor import run_spec
from .._legacy._sync.ohlcv import ohlcv_core


@validate_params
def bhistory(
    tickers: TickerList,
    start_date: DateParam,
    end_date: DateParam | None = None,
    fields: Literal["close", "ohlcv"] = "close",
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch daily price history for one or more tickers.

    The unified historical entry point (Bloomberg-BDH-like):

    - ``fields="close"`` (default): adjusted close/settle series via
      HistoricoDiarioSimbolos — one request per ticker covering the whole
      window. Works for ALL instruments (B3 equities/FIIs, FX, indices,
      commodities, DI futures, AETAXAS). ``bclose`` is a shortcut.
    - ``fields="ohlcv"``: full OHLCV via HistoricoData — also one request
      per ticker (the endpoint serves the whole window; the end is cut
      client-side because its 1789 end tag is ignored).

    Args:
        tickers: Single ticker or list (e.g., "PETR4" or ["PETR4", "USDBRL"]).
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: End date (default: through today)
        fields: "close" (default) or "ohlcv".
        session_token: BCAA session token

    Returns:
        Flat (long) DataFrame with a DatetimeIndex and a ``ticker`` column
        holding the queried symbol (one block per ticker). "close" columns:
        close, settle, settle_rate, yield, net_asset (funds only). "ohlcv"
        columns: close, settle, settle_rate, low, high, open, trades, volume,
        turnover, open_interest, vwap, cum_trades. Empty DataFrame with the
        schema if no data.

    Example:
        >>> df = bhistory(["PETR4", "VALE3"], "20260101")
        >>> ohlcv = bhistory("PETR4", "20260501", "20260519", fields="ohlcv")
    """
    start_str = to_date_str(start_date)
    end_str = to_date_str(end_date) if end_date is not None else default_end_date()
    if start_str > end_str:
        return empty_history_frame(
            BHISTORY_SCHEMA if fields == "close" else DAILY_OHLCV_SCHEMA
        )
    if fields == "close":
        return run_spec(
            SPEC_BHISTORY,
            session_token=session_token,
            ticker=tickers,
            start_date=start_str,
            end_date=end_str,
        )
    return vectorize(
        tickers, lambda t: ohlcv_core(t, start_str, end_str, session_token)
    )


@validate_params
def bclose(
    tickers: TickerList,
    start_date: DateParam,
    end_date: DateParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch adjusted daily closing prices — shortcut for ``bhistory(fields="close")``.

    Args:
        tickers: Single ticker or list (e.g., "PETR4" or ["PETR4", "USDBRL"]).
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: End date (default: through today)
        session_token: BCAA session token

    Returns:
        Flat (long) DataFrame with a DatetimeIndex and a ``ticker`` column
        (one block per ticker). Columns: close, settle, settle_rate, yield,
        net_asset.

    Example:
        >>> df = bclose(["PETR4", "VALE3"], "20260101")
        >>> df[df["ticker"] == "PETR4"]["close"].plot()
    """
    return bhistory(tickers, start_date, end_date, "close", session_token)


@validate_params
def bfirst_close(
    ticker: TickerList,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch the first historical closing price for one or more tickers.

    Uses the FechamentoPrimeiro endpoint. Takes only the bare B3 ticker
    ("PETR4" — suffixed forms do not resolve); the close is adjusted for
    corporate events, so old values can be far below the prices of the time.

    Args:
        ticker: Single bare ticker or list (e.g., "PETR4" or ["PETR4", "VALE3"]).
        session_token: BCAA session token

    Returns:
        Flat DataFrame (RangeIndex), one row per ticker: ticker, date
        (YYYYMMDD int) and close. Unknown tickers are omitted; empty
        DataFrame with that schema if none resolves.

    Example:
        >>> df = bfirst_close("PETR4")
        >>> df[["ticker", "date", "close"]]
    """
    return run_spec(SPEC_BFIRST_CLOSE, session_token=session_token, ticker=ticker)
