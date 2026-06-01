"""Object-oriented facade over the functional ``b*`` API.

``Ticker`` is a thin convenience wrapper for a single instrument: every method
delegates to the matching functional call (``bdh``, ``bquote``, ...). It holds
no state beyond the symbol and an optional session token, and adds no new logic
— it exists purely for discoverability (``Ticker("PETR4").dividends``) for users
who prefer an object-oriented style (as in yfinance's ``Ticker``).
"""

from __future__ import annotations

import pandas as pd

from ._core.dates import DateLike
from .fundamental import (
    bconsensus,
    bdividends,
    bdy,
    bindicators,
    bquote,
    bshares,
    btickers,
)
from .historical import bdh, bdh_ohlcv, bdi, bdt


class Ticker:
    """Convenience handle for one instrument that delegates to the ``b*`` API.

    Example:
        >>> from py_bcast import Ticker
        >>> petr = Ticker("PETR4")
        >>> petr.history("20260501", "20260520")   # -> bdh
        >>> petr.dividends                          # -> bdividends
        >>> petr.quote                              # -> bquote
    """

    def __init__(self, ticker: str, session_token: str | None = None) -> None:
        self.ticker = ticker.strip().upper()
        self._token = session_token

    def __repr__(self) -> str:
        return f"Ticker({self.ticker!r})"

    # ── Historical / intraday ────────────────────────────────────────────────
    def history(
        self, start_date: DateLike, end_date: DateLike | None = None
    ) -> pd.DataFrame:
        """Daily close history (delegates to ``bdh``)."""
        return bdh(self.ticker, start_date, end_date, session_token=self._token)

    def ohlcv(self, date: DateLike) -> pd.DataFrame:
        """Single-day OHLCV (delegates to ``bdh_ohlcv``)."""
        return bdh_ohlcv(self.ticker, date, session_token=self._token)

    def intraday(self, date: DateLike) -> pd.DataFrame:
        """Intraday bars for a date (delegates to ``bdi``)."""
        return bdi(self.ticker, date, session_token=self._token)

    def ticks(self, start: DateLike, end: DateLike | None = None) -> pd.DataFrame:
        """Tick-by-tick data (delegates to ``bdt``)."""
        return bdt(self.ticker, start, end, session_token=self._token)

    # ── Fundamental / events ─────────────────────────────────────────────────
    @property
    def quote(self) -> pd.DataFrame:
        """Current quote snapshot (delegates to ``bquote``)."""
        return bquote(self.ticker, session_token=self._token)

    @property
    def shares(self) -> pd.DataFrame:
        """Shares outstanding (delegates to ``bshares``)."""
        return bshares(self.ticker, session_token=self._token)

    @property
    def consensus(self) -> pd.DataFrame:
        """Analyst consensus (delegates to ``bconsensus``)."""
        return bconsensus(self.ticker, session_token=self._token)

    @property
    def dividends(self) -> pd.DataFrame:
        """Dividend/JCP history (delegates to ``bdividends``)."""
        return bdividends(self.ticker, session_token=self._token)

    @property
    def symbols(self) -> pd.DataFrame:
        """All tickers for this company (delegates to ``btickers``)."""
        return btickers(self.ticker, session_token=self._token)

    def dy(self, start_date: DateLike, end_date: DateLike) -> pd.DataFrame:
        """Dividend-yield series (delegates to ``bdy``)."""
        return bdy(self.ticker, start_date, end_date, session_token=self._token)

    def indicators(
        self, indicator: str | int, start_date: DateLike, end_date: DateLike
    ) -> pd.DataFrame:
        """Fundamental indicator history (delegates to ``bindicators``)."""
        return bindicators(
            self.ticker, indicator, start_date, end_date, session_token=self._token
        )
