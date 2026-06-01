"""Unit tests for the async vectorize helper (no backend, mock async cores).

Uses plain ``def test_*`` driving ``asyncio.run`` rather than ``async def``
tests, so the suite runs identically whether or not pytest-asyncio is
installed (an unconfigured ``async def`` test is silently skipped).
"""

from __future__ import annotations

import asyncio

import pandas as pd
import pytest

from py_bcast._core.exceptions import NotFoundError
from py_bcast._legacy.multi import vectorize_async


def test_multi_input_concat_and_ticker_column():
    """Multiple inputs concat into one frame; ticker is inserted per block."""

    async def one(identifier: str) -> pd.DataFrame:
        return pd.DataFrame({"value": [int(identifier)]})

    df = asyncio.run(vectorize_async(["1", "2", "3"], one))

    assert list(df.columns) == ["ticker", "value"]
    assert df["ticker"].tolist() == ["1", "2", "3"]
    assert df["value"].tolist() == [1, 2, 3]


def test_input_order_preserved():
    """Concurrent gather still yields blocks in input order."""

    async def one(identifier: str) -> pd.DataFrame:
        # Stagger completion so a naive impl would reorder.
        await asyncio.sleep(0.01 if identifier == "A" else 0.0)
        return pd.DataFrame({"value": [identifier]})

    df = asyncio.run(vectorize_async(["A", "B"], one))

    assert df["ticker"].tolist() == ["A", "B"]


def test_ticker_column_left_untouched_when_present():
    """A core that emits its own ticker column is not overwritten."""

    async def one(identifier: str) -> pd.DataFrame:
        return pd.DataFrame({"ticker": ["X" + identifier], "value": [1]})

    df = asyncio.run(vectorize_async(["1", "2"], one))

    assert df["ticker"].tolist() == ["X1", "X2"]


def test_fail_fast_propagates_not_found():
    """A NotFoundError from any item propagates (bad input never dropped)."""

    async def one(identifier: str) -> pd.DataFrame:
        if identifier == "BAD":
            raise NotFoundError("BAD", kind="ticker")
        return pd.DataFrame({"value": [1]})

    with pytest.raises(NotFoundError):
        asyncio.run(vectorize_async(["OK", "BAD", "OK2"], one))


def test_single_input_passthrough_with_ticker():
    """Single input returns the lone frame, still getting insert-if-absent."""

    async def one(identifier: str) -> pd.DataFrame:
        return pd.DataFrame({"value": [42]})

    df = asyncio.run(vectorize_async(["SOLO"], one))

    assert list(df.columns) == ["ticker", "value"]
    assert df["ticker"].tolist() == ["SOLO"]
    assert df["value"].tolist() == [42]


def test_single_input_index_preserved():
    """Single-input passthrough preserves the core's index type."""

    async def one(identifier: str) -> pd.DataFrame:
        idx = pd.DatetimeIndex(["2026-01-01"])
        return pd.DataFrame({"close": [10.0]}, index=idx)

    df = asyncio.run(vectorize_async(["SOLO"], one))

    assert isinstance(df.index, pd.DatetimeIndex)
    assert df["ticker"].tolist() == ["SOLO"]
