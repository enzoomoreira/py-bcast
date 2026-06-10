"""Fixed-income data via ContentProxy HTTP API: treasuries, accrual, savings."""

from __future__ import annotations

import pandas as pd

from ._core.validation import DateParam, TickerList, validate_params
from ._legacy._sync.executor import run_spec
from ._legacy.endpoints import (
    SPEC_BACCRUAL,
    SPEC_BSAVINGS,
    SPEC_BTREASURY,
    SPEC_BTREASURY_HISTORY,
)


@validate_params
def btreasury(
    symbols: TickerList,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch the latest reference price for one or more Treasury bonds.

    Uses the TitulosPublicosUltimos endpoint with ANBIMA daily reference ids:
    the symbol format is ``<paper><maturity YYMMDD>.ANBIMA`` (e.g.
    "LTN260701.ANBIMA", "NTNB270515.ANBIMA"). A bare symbol such as "LTN"
    resolves to the wrong instrument (LTN.NYSE) and returns nothing.

    Args:
        symbols: Single ANBIMA id or list (e.g. "LTN260701.ANBIMA").
        session_token: BCAA session token

    Returns:
        Flat DataFrame (RangeIndex), one row per bond: ticker (echoed bare,
        e.g. "LTN260701"), date, rate (trading yield % p.a.) and unit_price
        (PU). Unknown symbols are omitted; empty DataFrame with that schema
        if none resolves.

    Example:
        >>> df = btreasury(["LTN260701.ANBIMA", "NTNB270515.ANBIMA"])
        >>> df[["ticker", "rate", "unit_price"]]
    """
    return run_spec(SPEC_BTREASURY, session_token=session_token, symbols=symbols)


@validate_params
def btreasury_history(
    symbol: TickerList,
    start_date: DateParam,
    end_date: DateParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch OTC trading-yield history for one or more Treasury bonds.

    Uses the TitulosPublicos endpoint with Trademate (balcao) symbols:
    ``<paper><month code><YY>.TRDM`` (e.g. "NTNBK27.TRDM", "LTNF28.TRDM" —
    find them via ``bsearch(..., exchange="TRDM")``). Values are trading
    yields in % p.a., not prices. OTC trading is sparse: papers with no
    trades in the window return no rows.

    Args:
        symbol: Single Trademate symbol or list (e.g. "NTNBK27.TRDM").
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: Optional end date (default: through today).
        session_token: BCAA session token

    Returns:
        Flat DataFrame with a DatetimeIndex and a ``ticker`` column (one
        block per symbol). Columns: close/high/open/low (yields % p.a.),
        calendar_days, working_days, expiration_date (text), unit_price,
        stddev (sparse).

    Example:
        >>> df = btreasury_history("NTNBK27.TRDM", "20260101")
        >>> df[["ticker", "close", "working_days"]]
    """
    return run_spec(
        SPEC_BTREASURY_HISTORY,
        session_token=session_token,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )


@validate_params
def baccrual(
    rate: float,
    start_date: DateParam,
    end_date: DateParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Accrue a fixed annual rate over business days (server-side calculator).

    Uses the CalculoTaxaPre endpoint: compounds ``rate`` (% p.a.) over the
    window's working days on the 252 convention. Verified live: rate=100
    over 15 working days returns 2**(15/252)-1 = 4.21%.

    Args:
        rate: Annual rate in percent (e.g. 14.65 for 14.65% p.a.).
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp);
            the accumulated value is 0.0 on this date.
        end_date: Optional end date (default: through today).
        session_token: BCAA session token

    Returns:
        DataFrame with a DatetimeIndex (one row per calendar day in the
        window) and an ``accumulated`` column (% accrued since start_date).

    Example:
        >>> df = baccrual(14.65, "20260101", "20260601")
        >>> df["accumulated"].iloc[-1]
    """
    return run_spec(
        SPEC_BACCRUAL,
        session_token=session_token,
        rate=rate,
        start_date=start_date,
        end_date=end_date,
    )


@validate_params
def bsavings(
    start_date: DateParam,
    end_date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Fetch the accumulated poupanca (savings account) return over a window.

    Uses the CalculoPoupanca endpoint. The accumulation follows the savings
    anniversary rule, so the first days of the window may read 0.0 until the
    first monthly credit lands.

    Args:
        start_date: Start date (str YYYYMMDD, date, datetime, or Timestamp)
        end_date: End date (str YYYYMMDD, date, datetime, or Timestamp)
        session_token: BCAA session token

    Returns:
        DataFrame with a DatetimeIndex and an ``accumulated`` column
        (% accumulated since start_date).

    Example:
        >>> df = bsavings("20260101", "20260601")
        >>> df["accumulated"].iloc[-1]
    """
    return run_spec(
        SPEC_BSAVINGS,
        session_token=session_token,
        start_date=start_date,
        end_date=end_date,
    )


__all__ = ["btreasury", "btreasury_history", "baccrual", "bsavings"]
