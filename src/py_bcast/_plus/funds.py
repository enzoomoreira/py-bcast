"""Investment funds via Broadcast+ REST: search and detail.

A Broadcast+ capability with no legacy equivalent. ``bfunds`` searches funds by
name; ``bfund`` fetches one fund's full detail by its numeric id.
"""

from __future__ import annotations

import pandas as pd

from .._core.validation import validate_params
from ._sync.funds import fund_core, funds_core


@validate_params
def bfunds(query: str) -> pd.DataFrame:
    """Search investment funds by name via Broadcast+.

    Requires Broadcast+ backend — configure(terminal='plus'),
    configure(terminal='auto') with Broadcast+.exe running, or
    configure(plus_login=..., plus_password=...) for headless login.

    Args:
        query: Search string (the server requires at least 3 characters).

    Returns:
        Flat DataFrame, one row per matching fund, keyed by ``id`` (the lookup
        identifier for ``bfund``). Columns include symbol, cnpj, company,
        manager, administrator, status, quota, net_worth, fee fields, the
        ANBIMA classification, profitability windows (profit_daily through
        profit_5y, profit_annual), and the begin/end/last_quote_date datetimes.
        Empty DataFrame with the same schema if nothing matches.

    Example:
        >>> from py_bcast import bfunds, configure
        >>> configure(terminal="plus")
        >>> bfunds("Verde")[["id", "company", "quota", "profit_1y"]].head()
    """
    return funds_core(query)


@validate_params
def bfund(fund_id: int) -> pd.DataFrame:
    """Fetch one investment fund's detail by numeric id via Broadcast+.

    Requires Broadcast+ backend (see ``bfunds``).

    Args:
        fund_id: Numeric fund id (the ``id`` column from ``bfunds``).

    Returns:
        Single-row DataFrame with the same schema as ``bfunds``.

    Raises:
        NotFoundError: If the fund id does not exist.

    Example:
        >>> from py_bcast import bfund, configure
        >>> configure(terminal="plus")
        >>> bfund(779).iloc[0][["company", "manager", "net_worth"]]
    """
    return fund_core(fund_id)
