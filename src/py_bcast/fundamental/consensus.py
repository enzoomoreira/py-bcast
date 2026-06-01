"""Analyst consensus data via aefundamental HTTP API."""

from __future__ import annotations

import datetime

import pandas as pd

from .._core.aetp import rows_to_dicts
from .._core.binary import parse_binary_response
from .._core.columns import CONSENSUS_FIELDS, CONSENSUS_SCHEMA
from .._core.constants import BASE_URL
from .._core.exceptions import ProtocolError, is_no_records
from .._core.http import get_http_client, get_session_token
from .._core.logging import get_logger
from .._core.output import to_record_dataframe
from .._core.retry import http_retry
from .._core.validation import Ticker, validate_params

logger = get_logger(__name__)


@validate_params
def bconsensus(
    ticker: Ticker,
    session_token: str | None = None,
) -> pd.DataFrame:
    """
    Get analyst consensus data for a stock.

    Uses aefundamental/consenso endpoint. Provides buy/hold/sell
    recommendation counts and target price statistics.

    Args:
        ticker: Stock ticker (e.g., "PETR4", "VALE3", "ITUB4")
        session_token: BCAA session token

    Returns:
        One-row DataFrame with columns: ticker, buy, hold, sell,
        total_analysts, target_low, target_high, target_mean,
        target_median, upside_pct. Empty DataFrame with that schema when no
        consensus exists (e.g. a small cap with no analyst coverage).

    Example:
        >>> df = bconsensus("PETR4")
        >>> print(f"Buy: {df['buy'].iloc[0]}, Target: {df['target_mean'].iloc[0]}")
    """
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


@http_retry
def _consensus_fetch(s, ticker: str, token: str, today: str):
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
