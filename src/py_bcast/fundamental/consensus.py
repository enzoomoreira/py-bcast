"""Analyst consensus data via the aefundamental HTTP API."""

from __future__ import annotations

import pandas as pd

from .._core.validation import TickerList, validate_params
from .._legacy.endpoints import SPEC_BCONSENSUS
from .._legacy.executor import run_spec


@validate_params
def bconsensus(
    ticker: TickerList,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Get analyst consensus data for one or more stocks.

    Uses aefundamental/consenso endpoint. Provides buy/hold/sell
    recommendation counts and target price statistics.

    Args:
        ticker: Single ticker or list (e.g., "PETR4" or ["PETR4", "VALE3"]).
        session_token: BCAA session token

    Returns:
        Flat DataFrame with columns: ticker, buy, hold, sell, total_analysts,
        target_low, target_high, target_mean, target_median, upside_pct (one
        row per covered ticker). A ticker with no analyst coverage contributes
        an empty block (it is a valid stock with no consensus, not an error).

    Example:
        >>> df = bconsensus("PETR4")
        >>> print(f"Buy: {df['buy'].iloc[0]}, Target: {df['target_mean'].iloc[0]}")
    """
    return run_spec(SPEC_BCONSENSUS, session_token=session_token, ticker=ticker)
