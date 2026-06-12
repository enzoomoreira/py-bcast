"""Reference data via Broadcast+ REST: instrument metadata, index composition, logos.

These are Broadcast+ capabilities with no legacy equivalent: ``binfo`` returns
instrument metadata (never price — price is WebSocket-only via
``BroadcastPlusClient``), ``bindex_members`` returns index composition with
relevance weights (the legacy terminal has no composition endpoint), and
``blogo`` returns the instrument's PNG logo bytes.
"""

from __future__ import annotations

import pandas as pd

from .._core.validation import Ticker, TickerList, validate_params
from ._sync.reference import (
    holiday_tables_core,
    index_list_core,
    index_members_core,
    info_core,
    logo_core,
)


@validate_params
def binfo(symbols: TickerList) -> pd.DataFrame:
    """Fetch instrument metadata for one or more symbols via Broadcast+.

    Returns descriptive metadata only — type, market, exchange, currency,
    CVM code, data-availability flags. Never returns price (price is exclusively
    via the ``BroadcastPlusClient`` WebSocket stream).

    Requires Broadcast+ backend — configure(terminal='plus'),
    configure(terminal='auto') with Broadcast+.exe running, or
    configure(plus_login=..., plus_password=...) for headless login.

    Args:
        symbols: One symbol or a list (e.g. "PETR4" or ["PETR4", "USDBRL"]).

    Returns:
        Flat DataFrame, one row per resolved symbol, with columns:
            ticker, name, type, market, exchange (legacy code), exchange_id,
            cvm_code, currency, decimal_places, flag, graphic_type, has_book,
            has_daily, has_intraday, is_realtime, is_delay, timezone.
        Unknown symbols are omitted; an all-unknown request returns an empty
        DataFrame with the same schema.

    Example:
        >>> from py_bcast import binfo, configure
        >>> configure(terminal="plus")
        >>> binfo(["PETR4", "USDBRL"])[["name", "type", "currency"]]
    """
    return info_core(symbols)


def bindexes() -> pd.DataFrame:
    """List the available market-index codes via Broadcast+.

    The codes feed ``bindex_members``. The legacy ``bindices`` returns a richer
    list (names + ids); this is the Plus discovery primitive (codes only).

    Requires Broadcast+ backend (see ``binfo``).

    Returns:
        Single-column DataFrame ``code`` with the available index codes (IBOV,
        IFIX, SMLL, etc.), matching the legacy ``bindices`` column name.

    Example:
        >>> from py_bcast import bindexes, configure
        >>> configure(terminal="plus")
        >>> bindexes()["code"].tolist()
    """
    return index_list_core()


def bholidays() -> pd.DataFrame:
    """List the holiday-table catalog (country/exchange calendars) via Broadcast+.

    Returns only the table catalog. The per-table holiday DATES endpoint exists
    but its filter parameter is undiscovered (the server ignores every probed
    body shape), so the dates themselves are not yet reachable.

    Requires Broadcast+ backend (see ``binfo``).

    Returns:
        Flat DataFrame with columns: id (table id), name (country/exchange).

    Example:
        >>> from py_bcast import bholidays, configure
        >>> configure(terminal="plus")
        >>> bholidays()[bholidays()["name"] == "Brasil"]
    """
    return holiday_tables_core()


@validate_params
def bindex_members(index: Ticker) -> pd.DataFrame:
    """Fetch the member composition of a market index with relevance weights.

    A Broadcast+ capability with no legacy equivalent. The ``relevance`` column
    holds each member's published participation weight in the index.

    Requires Broadcast+ backend (see ``binfo``).

    Args:
        index: Index code (e.g. "IBOV", "IFIX", "SMLL"). See the Broadcast+
            index list for valid codes.

    Returns:
        Flat DataFrame with columns: index (the queried code), ticker (the
        member symbol), relevance. One row per member.

    Raises:
        NotFoundError: If the index code does not exist.

    Example:
        >>> from py_bcast import bindex_members, configure
        >>> configure(terminal="plus")
        >>> df = bindex_members("IBOV")
        >>> df.sort_values("relevance", ascending=False).head()
    """
    return index_members_core(index)


@validate_params
def blogo(symbol: Ticker) -> bytes:
    """Fetch the PNG logo bytes for an instrument via Broadcast+.

    A Broadcast+ capability with no legacy equivalent.

    Requires Broadcast+ backend (see ``binfo``).

    Args:
        symbol: Instrument code (e.g. "PETR4").

    Returns:
        Raw PNG bytes (typically 2-4 KB). Write them to a ``.png`` file or load
        with an imaging library.

    Raises:
        NotFoundError: If the symbol has no logo.

    Example:
        >>> from py_bcast import blogo, configure
        >>> configure(terminal="plus")
        >>> open("petr4.png", "wb").write(blogo("PETR4"))
    """
    return logo_core(symbol)
