"""Analyst consensus data via aefundamental HTTP API."""

from __future__ import annotations

import datetime

import httpx
import pandas as pd

from .._legacy.aetp import rows_to_dicts
from .._legacy.binary import parse_binary_response
from .._legacy.columns import CONSENSUS_FIELDS, CONSENSUS_SCHEMA
from .._core.constants import BASE_URL
from .._core.exceptions import ProtocolError, is_no_records
from .._legacy.http import get_http_client, get_session_token
from .._core.logging import get_logger
from .._legacy.multi import vectorize
from .._legacy.output import to_record_dataframe
from .._core.retry import http_retry
from .._core.validation import TickerList, validate_params

logger = get_logger(__name__)


def _bconsensus_one(
    ticker: str,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Get analyst consensus for a single ticker (soft: no coverage -> empty)."""
    token = get_session_token(session_token)
    s = get_http_client()

    today = datetime.date.today().strftime("%Y%m%d")

    logger.debug("bconsensus: fetching consensus for %s", ticker)
    r = _consensus_fetch(s, ticker, token, today)

    try:
        parsed = parse_binary_response(r.content)
    except ProtocolError as exc:
        # No coverage for this (valid) ticker reads as an empty result, not a
        # missing entity — small caps simply have no analyst consensus.
        if is_no_records(exc.error_tag):
            logger.debug("bconsensus: no consensus for %s", ticker)
            return to_record_dataframe({}, schema=CONSENSUS_SCHEMA)
        raise

    rows = rows_to_dicts(parsed)
    record = rows[0] if rows else {}
    return to_record_dataframe(
        record, rename=CONSENSUS_FIELDS, schema=CONSENSUS_SCHEMA, ticker=ticker
    )


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
    return vectorize(ticker, lambda t: _bconsensus_one(t, session_token))


@http_retry
def _consensus_fetch(
    s: httpx.Client, ticker: str, token: str, today: str
) -> httpx.Response:
    """Isolated HTTP call for retry."""
    return s.get(
        f"{BASE_URL}/aefundamental/{ticker}/consenso",
        params={
            "10023": "4",
            "10039": token,
            "10068": ticker,
            "13004": today,
        },
        timeout=15,
    )
