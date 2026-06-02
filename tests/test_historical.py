"""Integration tests for historical data functions."""

import pandas as pd
import pytest

from py_bcast import bdh, bdh_ohlcv, bdt

pytestmark = pytest.mark.legacy_session


class TestBdh:
    def test_single_ticker(self):
        df = bdh("PETR4", "20260512", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        assert "PETR4.BVMF" in df["ticker"].values
        assert "close" in df.columns
        assert pd.notna(df["close"].iloc[0])

    def test_multiple_tickers(self):
        df = bdh(["PETR4", "VALE3"], "20260515", "20260519")
        tickers = set(df["ticker"].unique())
        assert "PETR4.BVMF" in tickers
        assert "VALE3.BVMF" in tickers

    def test_fx(self):
        df = bdh("USDBRL", "20260512", "20260519")
        assert any("USDBRL" in t for t in df["ticker"].unique())

    def test_sorted_chronologically(self):
        df = bdh("PETR4", "20260501", "20260519")
        petr = df[df["ticker"] == "PETR4.BVMF"]
        if not petr.empty:
            assert petr.index.is_monotonic_increasing

    def test_empty_range(self):
        df = bdh("PETR4", "20260518", "20260510")  # end < start
        assert isinstance(df, pd.DataFrame)
        assert df.empty
        assert "ticker" in df.columns  # schema preserved

    def test_close_is_float(self):
        # A no-trade tolerance row carries an "n/d" sentinel; it must not
        # poison numeric coercion and leave close as str/object.
        df = bdh("PETR4", "20260501", "20260519")
        assert pd.api.types.is_float_dtype(df["close"])


class TestBdhOhlcv:
    def test_single_date(self):
        df = bdh_ohlcv("PETR4", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df["ticker"].iloc[0] == "PETR4"
        for col in ("close", "high", "low", "open"):
            assert col in df.columns

    def test_multiple(self):
        df = bdh_ohlcv(["PETR4", "VALE3"], "20260519")
        assert isinstance(df, pd.DataFrame)
        assert {"PETR4", "VALE3"} <= set(df["ticker"].unique())

    def test_no_data_returns_empty(self):
        # Very old date (before history start) -> valid query, no rows
        df = bdh_ohlcv("PETR4", "19000101")
        assert isinstance(df, pd.DataFrame)
        assert df.empty
        assert "close" in df.columns  # schema preserved


class TestBdt:
    def test_usdbrl_ticks(self):
        df = bdt("USDBRL", "20260519100000", "20260519101000")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        assert "close" in df.columns
        assert "ticker" in df.columns
        assert df["ticker"].iloc[0] == "USDBRL"

    def test_multiple(self):
        df = bdt(["USDBRL", "EURUSD"], "20260519100000", "20260519101000")
        assert isinstance(df, pd.DataFrame)
        assert {"USDBRL", "EURUSD"} <= set(df["ticker"].unique())

    def test_chronological_order(self):
        df = bdt("USDBRL", "20260519100000", "20260519110000")
        if len(df) >= 2:
            valid = df[df.index.notna()]
            assert valid.index.is_monotonic_increasing

    def test_bvmf_returns_empty(self):
        # B3 ticks blocked by query registration
        df = bdt("PETR4", "20260519100000", "20260519101000")
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_default_end_time(self):
        # Should default to start + 1 hour
        df = bdt("USDBRL", "20260519100000")
        assert isinstance(df, pd.DataFrame)
