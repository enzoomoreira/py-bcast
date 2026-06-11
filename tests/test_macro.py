"""Integration tests for macroeconomic data functions."""

import pandas as pd
import pytest

from py_bcast import bmacro, breturn, bvolume, binflation

pytestmark = pytest.mark.legacy_session


class TestBmacro:
    def test_usdbrl(self):
        df = bmacro("USDBRL", "20260512", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        assert "close" in df.columns
        assert "ticker" in df.columns
        assert df["ticker"].iloc[0] == "USDBRL"
        # B5: redundant ref_date (dup of index) and empty hor are dropped
        assert "ref_date" not in df.columns
        assert "hor" not in df.columns

    def test_multiple(self):
        df = bmacro(["USDBRL", "IBOV"], "20260512", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert {"USDBRL", "IBOV"} <= set(df["ticker"].unique())

    def test_ibov(self):
        df = bmacro("IBOV", "20260512", "20260519")
        assert len(df) >= 1

    def test_spx(self):
        df = bmacro("SPX", "20260512", "20260516")
        assert len(df) >= 1

    def test_aetaxas_ipca(self):
        df = bmacro("AEIPCA", "20250101", "20260519")
        assert len(df) >= 1

    def test_sorted_chronologically(self):
        df = bmacro("USDBRL", "20260501", "20260519")
        assert df.index.is_monotonic_increasing

    def test_empty_range(self):
        # Valid symbol, no rows in the (inverted) range: the server replies
        # "não foram encontrados registros", which the unified error policy
        # maps to an empty DataFrame rather than an exception.
        df = bmacro("USDBRL", "20260518", "20260510")
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_multiple_all_empty(self):
        # Multi input where every item is empty: one empty frame with schema
        # (+ ticker column) and the DatetimeIndex preserved through concat.
        df = bmacro(["USDBRL", "IBOV"], "20260518", "20260510")
        assert isinstance(df, pd.DataFrame)
        assert df.empty
        assert "ticker" in df.columns
        assert "close" in df.columns
        assert isinstance(df.index, pd.DatetimeIndex)


class TestBmacroCdi:
    def test_recent(self):
        df = bmacro("CDI", "20260501", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        assert "close" in df.columns
        assert "accumulated" in df.columns
        assert (df["ticker"] == "CDI").all()

    def test_historical_since_1986(self):
        df = bmacro("CDI", "19860601", "19860630")
        assert len(df) >= 1

    def test_mixed_with_macro_symbol(self):
        df = bmacro(["CDI", "USDBRL"], "20260512", "20260519")
        assert {"CDI", "USDBRL"} <= set(df["ticker"].unique())

    def test_sorted(self):
        df = bmacro("CDI", "20260501", "20260519")
        assert df.index.is_monotonic_increasing


class TestBreturn:
    def test_petr4(self):
        df = breturn("PETR4", "20260501", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        assert "close" in df.columns
        assert "ticker" in df.columns
        assert df["ticker"].iloc[0] == "PETR4"

    def test_multiple(self):
        df = breturn(["PETR4", "VALE3"], "20260501", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert {"PETR4", "VALE3"} <= set(df["ticker"].unique())

    def test_sorted(self):
        df = breturn("PETR4", "20260501", "20260519")
        assert df.index.is_monotonic_increasing


class TestBvolume:
    def test_single(self):
        df = bvolume("PETR4")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        # ticker is a regular column (it repeats per averaging window, so it
        # cannot be a unique index) — unified with the rest of the library.
        assert "ticker" in df.columns
        assert any("PETR4" in s for s in df["ticker"])

    def test_multiple(self):
        df = bvolume(["PETR4", "VALE3"])
        assert df["ticker"].nunique() >= 2


class TestBinflation:
    def test_returns_indices(self):
        df = binflation()
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 5
