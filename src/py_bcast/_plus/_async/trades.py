"""Times & trades core for the Broadcast+ timesAndTrades endpoint."""

from __future__ import annotations

import pandas as pd

from ..._core.logging import get_logger
from .transport import plus_request

logger = get_logger(__name__)

_ENDPOINT = "/stock/v1/timesAndTrades"

# Flat schema (column order) for the times & trades frame. ``ticker`` leads so
# results from several symbols stack cleanly. The bid/ask ``exchangeId`` field
# is, in the B3 book, the id of the BROKER on each side (verified against the
# broker registry — every value resolves there), so it is surfaced as
# ``ask_broker_id``/``bid_broker_id`` and joins with ``bbrokers()``.
_TRADE_COLUMNS = [
    "ticker",
    "price",
    "size",
    "tendency",
    "sequence",
    "is_trade",
    "ask_price",
    "ask_size",
    "ask_broker_id",
    "bid_price",
    "bid_size",
    "bid_broker_id",
]


def empty_btrades(ticker: str) -> pd.DataFrame:
    """Empty trades frame carrying the full schema and a tz-aware index."""
    idx = pd.DatetimeIndex([], tz="America/Sao_Paulo", name=None)
    return pd.DataFrame(
        {col: pd.Series(dtype="object") for col in _TRADE_COLUMNS}, index=idx
    )


async def trades_core(ticker: str, date_str: str) -> pd.DataFrame:
    """Fetch and assemble the times & trades frame for one symbol/date.

    The endpoint caps at 500 records per call (newest first); the frame is
    returned sorted oldest-first on a Sao Paulo tz-aware DatetimeIndex.
    """
    logger.debug("btrades: %s on %s", ticker, date_str)

    r = await plus_request("post", _ENDPOINT, json={"symbol": ticker, "date": date_str})

    data = r.json()
    if not isinstance(data, dict) or not data.get("data"):
        return empty_btrades(ticker)

    rows = data["data"]
    if not rows:
        return empty_btrades(ticker)

    records = []
    for row in rows:
        ask = row.get("ask") or {}
        bid = row.get("bid") or {}
        records.append(
            {
                "unix_time_ms": row.get("unixTime"),
                "price": row.get("last"),
                "size": row.get("size"),
                "tendency": row.get("tendency"),
                "sequence": row.get("sequence"),
                "is_trade": row.get("isTrade", True),
                "ask_price": ask.get("price"),
                "ask_size": ask.get("size"),
                "ask_broker_id": ask.get("exchangeId"),
                "bid_price": bid.get("price"),
                "bid_size": bid.get("size"),
                "bid_broker_id": bid.get("exchangeId"),
            }
        )

    df = pd.DataFrame(records)

    # Build DatetimeIndex from Unix milliseconds, localized to Sao Paulo
    df.index = pd.to_datetime(
        df.pop("unix_time_ms"), unit="ms", utc=True
    ).dt.tz_convert("America/Sao_Paulo")
    df.index.name = None

    # Coerce numeric columns. is_trade is bool; the broker ids are categorical
    # integer identifiers surfaced as nullable Int64 (so they join cleanly with
    # ``bbrokers()`` and never render as 114.0); the rest are float quantities.
    _broker_id = {"ask_broker_id", "bid_broker_id"}
    for col in df.columns:
        if col == "is_trade":
            continue
        coerced = pd.to_numeric(df[col], errors="coerce")
        df[col] = coerced.astype("Int64") if col in _broker_id else coerced

    # Tag with the queried symbol (after numeric coercion so it stays a string).
    df.insert(0, "ticker", ticker)

    # API returns newest-first; sort ascending (oldest first, chronological)
    return df.sort_index()
