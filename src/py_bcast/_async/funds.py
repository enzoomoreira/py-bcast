"""Async legacy investment-fund functions (quota history, returns)."""

from __future__ import annotations

import pandas as pd

from .._core.validation import DateParam, TickerList, validate_params
from .._legacy._async.executor import run_spec as arun_spec
from .._legacy.endpoints import SPEC_BFUND_HISTORY, SPEC_BFUND_RETURNS


@validate_params
async def abfund_history(
    fund: TickerList,
    start_date: DateParam,
    end_date: DateParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bfund_history``.

    Flat DataFrame with a DatetimeIndex and a ``ticker`` column (one block
    per fund). Fund-accounting fields only populate for ".ANBIMA" ids.
    """
    return await arun_spec(
        SPEC_BFUND_HISTORY,
        session_token=session_token,
        fund=fund,
        start_date=start_date,
        end_date=end_date,
    )


@validate_params
async def abfund_returns(
    fund: TickerList,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bfund_returns``.

    Flat DataFrame (RangeIndex), one row per fund with the per-window
    accumulated returns (%); incomplete windows are NaN.
    """
    return await arun_spec(SPEC_BFUND_RETURNS, session_token=session_token, fund=fund)
