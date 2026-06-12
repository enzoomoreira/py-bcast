"""Integration tests for historical data functions."""

import pandas as pd
import pytest

from py_bcast import bclose, bdt, bhistory

pytestmark = pytest.mark.legacy_session


class TestBhistoryClose:
    def test_single_ticker(self):
        df = bhistory("PETR4", "20260512", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        # output ticker is bare (the queried symbol, not the server's echo)
        assert "PETR4" in df["ticker"].values
        assert "close" in df.columns
        assert pd.notna(df["close"].iloc[0])

    def test_multiple_tickers(self):
        df = bhistory(["PETR4", "VALE3"], "20260515", "20260519")
        tickers = set(df["ticker"].unique())
        assert "PETR4" in tickers
        assert "VALE3" in tickers

    def test_fx(self):
        df = bhistory("USDBRL", "20260512", "20260519")
        assert "USDBRL" in df["ticker"].values

    def test_sorted_chronologically(self):
        df = bhistory("PETR4", "20260501", "20260519")
        petr = df[df["ticker"] == "PETR4"]
        if not petr.empty:
            assert petr.index.is_monotonic_increasing

    def test_empty_range(self):
        df = bhistory("PETR4", "20260518", "20260510")  # end < start
        assert isinstance(df, pd.DataFrame)
        assert df.empty
        assert "ticker" in df.columns  # schema preserved

    def test_close_is_float(self):
        df = bhistory("PETR4", "20260501", "20260519")
        assert pd.api.types.is_float_dtype(df["close"])

    def test_bclose_shortcut_matches(self):
        a = bhistory("PETR4", "20260512", "20260519")
        b = bclose("PETR4", "20260512", "20260519")
        pd.testing.assert_frame_equal(a, b)


class TestBhistoryOhlcv:
    def test_single_date(self):
        df = bhistory("PETR4", "20260519", "20260519", fields="ohlcv")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df["ticker"].iloc[0] == "PETR4"
        for col in ("close", "high", "low", "open"):
            assert col in df.columns

    def test_multi_day_multi_ticker(self):
        df = bhistory(["PETR4", "VALE3"], "20260518", "20260519", fields="ohlcv")
        assert isinstance(df, pd.DataFrame)
        assert {"PETR4", "VALE3"} <= set(df["ticker"].unique())
        petr = df[df["ticker"] == "PETR4"]
        assert len(petr) == 2
        assert petr.index.is_monotonic_increasing

    def test_no_data_returns_empty(self):
        # In-range window with no trading days (a weekend) -> valid query, no
        # rows. (A pre-history date is a server DB-gap error, not an empty, and
        # raises for both legs — same as bhistory(fields="close").)
        df = bhistory("PETR4", "20260606", "20260607", fields="ohlcv")
        assert isinstance(df, pd.DataFrame)
        assert df.empty
        assert "close" in df.columns  # schema preserved


class TestBdt:
    def test_usdbrl_ticks(self):
        df = bdt("USDBRL", "20260519100000", "20260519101000")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        assert "price" in df.columns
        assert "ticker" in df.columns
        assert df["ticker"].iloc[0] == "USDBRL"
        # window and index are Brasilia time (tz-aware)
        assert str(df.index.tz) == "America/Sao_Paulo"

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
