"""Vectorization helper for single-entity tabular functions.

Public data functions accept either one input (a ticker, or a ticker-or-cvm
identifier) or a list of them. The single-entity core (``_funcname_one``) keeps
producing one flat ``pd.DataFrame`` per input; this helper loops over a
normalized list of inputs, guarantees every block carries a ``ticker`` column
identifying its source entity, and concatenates the blocks into one flat frame.

Contract:
    - fail-fast: a single item's ``NotFoundError`` propagates (a bad input is
      never silently dropped).
    - ticker column, insert-if-absent: if a per-item frame already carries a
      ``ticker`` column (bquote/bconsensus/bdh_ohlcv emit one), it is left
      untouched; otherwise the item's identifier is inserted at position 0.
    - index type is preserved (DatetimeIndex for time-series cores, RangeIndex
      for reference cores) — ``pd.concat`` keeps each item's index.
    - the all-empty multi case yields one empty frame whose columns come from
      the cores' own schema-preserving empties.
"""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

import pandas as pd


def vectorize(
    identifiers: list[str],
    one: Callable[[str], pd.DataFrame],
) -> pd.DataFrame:
    """Run a single-entity core over each identifier and concatenate.

    Args:
        identifiers: Normalized, non-empty list of per-item identifiers. Each
            is passed to ``one`` and, unless the resulting frame already has a
            ``ticker`` column, inserted as that frame's ``ticker`` value.
        one: Single-entity core returning a flat DataFrame for one identifier.
            Must raise ``NotFoundError`` for a bad input (not caught here).

    Returns:
        One flat DataFrame combining every item's rows, each block tagged with
        a ``ticker`` column. The index type of each item's frame is preserved.
    """
    frames: list[pd.DataFrame] = []
    for identifier in identifiers:
        df = one(identifier)
        if "ticker" not in df.columns:
            df.insert(0, "ticker", str(identifier))
        frames.append(df)
    if len(frames) == 1:
        return frames[0]
    return pd.concat(frames)


async def vectorize_async(
    identifiers: list[str],
    one: Callable[[str], Awaitable[pd.DataFrame]],
) -> pd.DataFrame:
    """Async twin of ``vectorize``: run an async single-entity core per input.

    Same contract as ``vectorize`` (insert-if-absent ticker column, concat
    preserving each item's index, fail-fast on NotFoundError, single-input
    returns the lone frame). The cores run concurrently via ``asyncio.gather``;
    its default ``return_exceptions=False`` both propagates the first error
    (fail-fast) and preserves input order in the result list.

    Args:
        identifiers: Normalized, non-empty list of per-item identifiers. Each
            is passed to ``one`` and, unless the resulting frame already has a
            ``ticker`` column, inserted as that frame's ``ticker`` value.
        one: Async single-entity core returning a flat DataFrame for one
            identifier. Must raise ``NotFoundError`` for a bad input.

    Returns:
        One flat DataFrame combining every item's rows, each block tagged with
        a ``ticker`` column. The index type of each item's frame is preserved.
    """
    results = await asyncio.gather(*(one(identifier) for identifier in identifiers))
    frames: list[pd.DataFrame] = []
    for identifier, df in zip(identifiers, results):
        if "ticker" not in df.columns:
            df.insert(0, "ticker", str(identifier))
        frames.append(df)
    if len(frames) == 1:
        return frames[0]
    return pd.concat(frames)
