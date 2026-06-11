"""Async fixed-income functions (treasuries, accrual, savings)."""

from __future__ import annotations

import pandas as pd

from .._core.validation import DateParam, TickerList, validate_params
from .._legacy._async.executor import run_spec as arun_spec
from .._legacy.endpoints import (
    SPEC_BACCRUAL,
    SPEC_BSAVINGS,
    SPEC_BTREASURY,
    SPEC_BTREASURY_HISTORY,
    SPEC_BUNIT_PRICE,
)


@validate_params
async def abtreasury(
    symbols: TickerList,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``btreasury``.

    Flat DataFrame (RangeIndex), one row per bond: ticker (bare), date, rate
    (trading yield % p.a.) and unit_price. Unknown symbols are omitted.
    """
    return await arun_spec(SPEC_BTREASURY, session_token=session_token, symbols=symbols)


@validate_params
async def abtreasury_history(
    symbol: TickerList,
    start_date: DateParam,
    end_date: DateParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``btreasury_history``.

    Flat DataFrame with a DatetimeIndex and a ``ticker`` column (one block
    per ".TRDM" symbol); values are trading yields in % p.a.
    """
    return await arun_spec(
        SPEC_BTREASURY_HISTORY,
        session_token=session_token,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )


@validate_params
async def abaccrual(
    rate: float,
    start_date: DateParam,
    end_date: DateParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``baccrual``.

    DatetimeIndex frame with an ``accumulated`` column: ``rate`` (% p.a.)
    compounded over the window's working days on the 252 convention.
    """
    return await arun_spec(
        SPEC_BACCRUAL,
        session_token=session_token,
        rate=rate,
        start_date=start_date,
        end_date=end_date,
    )


@validate_params
async def absavings(
    start_date: DateParam,
    end_date: DateParam,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bsavings``.

    DatetimeIndex frame with an ``accumulated`` column (% accumulated
    poupanca return since start_date).
    """
    return await arun_spec(
        SPEC_BSAVINGS,
        session_token=session_token,
        start_date=start_date,
        end_date=end_date,
    )


@validate_params
async def abunit_price(
    symbol: TickerList,
    start_date: DateParam,
    end_date: DateParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bunit_price``.

    Flat DataFrame with a DatetimeIndex and a ``ticker`` column (one block per
    symbol): accumulated_return, unit_price (PU) and change_pct.
    """
    return await arun_spec(
        SPEC_BUNIT_PRICE,
        session_token=session_token,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )
