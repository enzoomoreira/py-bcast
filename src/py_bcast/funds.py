"""Legacy investment-fund data via ContentProxy HTTP API (quota history, returns)."""

from __future__ import annotations

import pandas as pd

from ._core.validation import DateParam, TickerList, validate_params
from ._legacy._sync.executor import run_spec
from ._legacy.endpoints import SPEC_BFUND_HISTORY, SPEC_BFUND_RETURNS, SPEC_BFUND_LIST
from ._legacy.resolve_state import _strip_accents


@validate_params
def bfund_history(
    fund: TickerList,
    start_date: DateParam,
    end_date: DateParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch daily quota history for one or more investment funds.

    Uses the Fundos endpoint. Accepts exchange-traded tickers (ETFs/FIIs,
    e.g. "BBSD11") and ANBIMA fund ids in the ``<id>.ANBIMA`` format — the
    same ids the Broadcast+ ``bfunds``/``bfund`` adapters return. The
    fund-accounting fields (net_asset, inflows, outflows, quote_holders)
    only populate for ANBIMA ids; exchange tickers carry the quote alone.

    Args:
        fund: Single fund symbol or list (e.g. "214248.ANBIMA" or "BBSD11").
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: Optional end date (default: through today).
        session_token: BCAA session token

    Returns:
        Flat DataFrame with a DatetimeIndex and a ``ticker`` column (one
        block per fund). Columns: close (quota), net_asset, inflows,
        outflows, total_assets, quote_holders, open, high, low.

    Example:
        >>> df = bfund_history("214248.ANBIMA", "20260101")
        >>> df[["ticker", "close", "net_asset"]].tail()
    """
    return run_spec(
        SPEC_BFUND_HISTORY,
        session_token=session_token,
        fund=fund,
        start_date=start_date,
        end_date=end_date,
    )


@validate_params
def bfund_returns(
    fund: TickerList,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch per-window accumulated returns for one or more investment funds.

    Uses the FundosRentabilidade endpoint. Accepts the same symbols as
    ``bfund_history`` (exchange tickers or ``<id>.ANBIMA``). Windows the
    fund has not completed come back as NaN.

    Args:
        fund: Single fund symbol or list (e.g. "BBSD11").
        session_token: BCAA session token

    Returns:
        Flat DataFrame (RangeIndex), one row per fund: ticker, return_1d,
        return_1m, return_3m, return_6m, return_12m, return_18m, return_2y,
        return_3y, return_5y (all in %).

    Example:
        >>> df = bfund_returns(["BBSD11", "214248.ANBIMA"])
        >>> df[["ticker", "return_12m"]]
    """
    return run_spec(SPEC_BFUND_RETURNS, session_token=session_token, fund=fund)


def _filter_fund_list(df: pd.DataFrame, query: str | None) -> pd.DataFrame:
    """Filter the fund universe by a case/accent-insensitive name substring."""
    if not query:
        return df
    needle = _strip_accents(str(query)).upper()
    mask = df["name"].map(lambda v: needle in _strip_accents(str(v)).upper())
    return df[mask].reset_index(drop=True)


def bfund_list(
    query: str | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    List the legacy fund universe, optionally filtered by name.

    Uses the BuscarFundosAutoComplete endpoint, which serves the whole CVM fund
    catalog (~45k funds) in one cached call; ``query`` filters it client-side by
    a case/accent-insensitive name substring. The ``symbol`` column is the
    ``<id>.ANBIMA`` form that ``bfund_history`` / ``bfund_returns`` consume, so
    this is the discovery path for those functions on the legacy backend.

    Args:
        query: Optional name substring (e.g. "Petrobras", min. a few chars to
            be useful). None returns the full universe.
        session_token: BCAA session token

    Returns:
        Flat DataFrame (RangeIndex), one row per fund: name, legal_name,
        anbima_id, cnpj, symbol (``<id>.ANBIMA``) and anbima_class.

    Example:
        >>> funds = bfund_list("Tesouro Selic")
        >>> hist = bfund_history(funds["symbol"].iloc[0], "20260101")
    """
    df = run_spec(SPEC_BFUND_LIST, session_token=session_token)
    return _filter_fund_list(df, query)


__all__ = ["bfund_history", "bfund_returns", "bfund_list"]
