"""Integration tests for historical data functions."""

import pandas as pd

from py_bcast import bdh, bdh_ohlcv, bdt


class TestBdh:
    def test_single_ticker(self):
        data = bdh("PETR4", "20260512", "20260519")
        assert "PETR4.BVMF" in data
        df = data["PETR4.BVMF"]
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        assert "last" in df.columns
        assert pd.notna(df["last"].iloc[0])

    def test_multiple_tickers(self):
        data = bdh(["PETR4", "VALE3"], "20260515", "20260519")
        assert "PETR4.BVMF" in data
        assert "VALE3.BVMF" in data

    def test_fx(self):
        data = bdh("USDBRL", "20260512", "20260519")
        assert any("USDBRL" in k for k in data.keys())

    def test_sorted_chronologically(self):
        data = bdh("PETR4", "20260501", "20260519")
        df = data.get("PETR4.BVMF", pd.DataFrame())
        if not df.empty:
            # Drop NaT (tolerance rows with no actual date) before checking order
            valid = df[df.index.notna()]
            assert valid.index.is_monotonic_increasing

    def test_empty_range(self):
        data = bdh("PETR4", "20260518", "20260510")  # end < start
        assert data == {}


class TestBdhOhlcv:
    def test_single_date(self):
        data = bdh_ohlcv("PETR4", "20260519")
        assert isinstance(data, pd.Series)
        assert not data.empty
        assert "last" in data.index
        assert "high" in data.index
        assert "low" in data.index
        assert "open" in data.index

    def test_no_data_returns_empty(self):
        # Weekend date
        data = bdh_ohlcv("PETR4", "20260517")
        assert isinstance(data, pd.Series)
        assert data.empty or data.get("last") == ""


class TestBdt:
    def test_usdbrl_ticks(self):
        df = bdt("USDBRL", "20260519100000", "20260519101000")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        assert "last" in df.columns

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
