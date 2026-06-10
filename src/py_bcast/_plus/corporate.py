"""Corporate events via Broadcast+ REST.

A Broadcast+ capability distinct from the legacy ``bdividends``: it carries the
price/volume adjustment factors (add_factor, calculated_factor) the legacy feed
does not provide.
"""

from __future__ import annotations

import pandas as pd

from .._core.validation import Ticker, validate_params
from ._sync.corporate import corpevents_core


@validate_params
def bcorpevents(symbol: Ticker) -> pd.DataFrame:
    """Fetch corporate events with adjustment factors for a symbol via Broadcast+.

    Returns dividends, JCP, income and splits together with the price/volume
    adjustment factors used to back-adjust historical series — data the legacy
    ``bdividends`` does not expose.

    Requires Broadcast+ backend — configure(terminal='plus'),
    configure(terminal='auto') with Broadcast+.exe running, or
    configure(plus_login=..., plus_password=...) for headless login.

    Args:
        symbol: Instrument code (e.g. "PETR4").

    Returns:
        Flat DataFrame with columns: ticker, type, legal_type, effective_date,
        execution_date, meeting_date (all Sao Paulo tz-aware), previous_symbol,
        should_adjust_price, should_adjust_volume, add_factor, calculated_factor,
        multiplicative_factor. Empty DataFrame with the same schema if the symbol
        has no events.

    Raises:
        NotFoundError: If the symbol does not exist.

    Example:
        >>> from py_bcast import bcorpevents, configure
        >>> configure(terminal="plus")
        >>> bcorpevents("PETR4")[["type", "effective_date", "calculated_factor"]]
    """
    return corpevents_core(symbol)
