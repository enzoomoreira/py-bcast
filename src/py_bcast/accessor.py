"""Pandas DataFrame accessor for reshaping py_bcast's flat/long frames.

Every tabular py_bcast function returns a *flat/long* DataFrame with a ``ticker``
column (easy to ``groupby``/``concat``/persist). Users coming from xbbg or
yfinance often want the *wide* layout — a column MultiIndex keyed by ticker, so
``df["PETR4"]`` selects one instrument. This accessor offers an opt-in bridge
without changing the default:

    >>> bhistory(["PETR4", "VALE3"], "20260501", "20260520").bcast.wide()["PETR4"]
    >>> wide_df.bcast.long()   # inverse

``wide()`` requires each (index, ticker) pair to be unique, so it suits the
time-series frames (``bhistory``, ``bmacro``, ``breturn``, ...). The default
flat layout stays the canonical one.
"""

from __future__ import annotations

import pandas as pd


@pd.api.extensions.register_dataframe_accessor("bcast")
class BcastAccessor:
    """``df.bcast`` — reshape helpers between flat/long and wide layouts."""

    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df

    def wide(self) -> pd.DataFrame:
        """Pivot the ``ticker`` column into the outer column level.

        Returns a frame with a ``(ticker, field)`` column MultiIndex and the
        original index, so ``out["PETR4"]`` selects one instrument's fields.

        Raises:
            ValueError: if there is no ``ticker`` column, or if (index, ticker)
                pairs are not unique (e.g. a RangeIndex reference frame).
        """
        df = self._df
        if "ticker" not in df.columns:
            raise ValueError("DataFrame.bcast.wide() requires a 'ticker' column.")
        try:
            pivoted = df.set_index("ticker", append=True).unstack("ticker")
        except ValueError as exc:
            raise ValueError(
                "bcast.wide() needs unique (index, ticker) pairs; this frame has "
                "duplicates (use a time-series frame such as bhistory/bmacro)."
            ) from exc
        # unstack yields (field, ticker); present it ticker-first.
        return pivoted.swaplevel(axis="columns").sort_index(axis="columns")

    def ohlc(self) -> pd.DataFrame:
        """Reshape an OHLCV frame for mplfinance/charting libraries.

        Returns the open/high/low/close[/volume] columns renamed to the
        capitalized ``Open``/``High``/``Low``/``Close``/``Volume`` that
        ``mplfinance.plot`` expects, in canonical O-H-L-C-V order, keeping the
        DatetimeIndex. The lib's default lowercase columns already suit
        pandas-ta/backtrader, so this is an opt-in bridge.

        Raises:
            ValueError: if the OHLC columns are absent, or the frame holds more
                than one instrument (filter by ``ticker`` first — charting
                libraries plot a single instrument).
        """
        df = self._df
        if "ticker" in df.columns and df["ticker"].nunique() > 1:
            raise ValueError(
                "bcast.ohlc() needs a single instrument; filter by ticker first "
                "(e.g. df[df['ticker'] == 'PETR4'])."
            )
        rename = {"open": "Open", "high": "High", "low": "Low", "close": "Close"}
        if not all(col in df.columns for col in rename):
            raise ValueError(
                "bcast.ohlc() needs open/high/low/close columns (an OHLCV frame "
                "such as bhistory(fields='ohlcv') or bdi)."
            )
        if "volume" in df.columns:
            rename["volume"] = "Volume"
        out = df[list(rename)].rename(columns=rename)
        order = [c for c in ("Open", "High", "Low", "Close", "Volume") if c in out]
        return out[order]

    def long(self) -> pd.DataFrame:
        """Inverse of :meth:`wide` — collapse the ticker column level back.

        A frame that is already flat (no column MultiIndex) is returned as a
        copy unchanged.
        """
        df = self._df
        if not isinstance(df.columns, pd.MultiIndex):
            return df.copy()
        stacked = df.stack(level=0)
        stacked.index = stacked.index.set_names("ticker", level=-1)
        return stacked.reset_index(level="ticker")
