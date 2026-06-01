"""Integration tests for bdi() — intraday OHLCV bars."""

import datetime

import pandas as pd
import pytest

from py_bcast import bdi

pytestmark = pytest.mark.legacy_session


class TestBdi:
    """Test HistoricoIntraday endpoint via bdi()."""

    def test_petr4_today(self):
        """PETR4 intraday returns bars for today."""
        today = datetime.date.today().strftime("%Y%m%d")
        df = bdi("PETR4", today)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_bar_fields(self):
        """Each bar has expected OHLCV fields."""
        today = datetime.date.today().strftime("%Y%m%d")
        df = bdi("PETR4", today)
        assert len(df) > 0
        expected_cols = {"open", "high", "low", "close", "volume", "trades"}
        assert expected_cols.issubset(df.columns)

    def test_chronological_order(self):
        """Bars are sorted oldest-first."""
        today = datetime.date.today().strftime("%Y%m%d")
        df = bdi("PETR4", today)
        if len(df) >= 2:
            valid = df[df.index.notna()]
            assert valid.index.is_monotonic_increasing

    def test_historical_range(self):
        """Can fetch multiple days of intraday data."""
        week_ago = (datetime.date.today() - datetime.timedelta(days=7)).strftime(
            "%Y%m%d"
        )
        df = bdi("PETR4", week_ago)
        # Should have more bars than a single day (~200/day)
        assert len(df) > 200

    def test_international_usdbrl(self):
        """USDBRL intraday works."""
        today = datetime.date.today().strftime("%Y%m%d")
        df = bdi("USDBRL", today)
        assert len(df) > 0
        # FX has decimal precision
        assert "close" in df.columns

    def test_international_gold(self):
        """GOLD intraday works."""
        today = datetime.date.today().strftime("%Y%m%d")
        df = bdi("GOLD", today)
        assert len(df) > 0

    def test_session_type(self):
        """Bars include session_type field."""
        today = datetime.date.today().strftime("%Y%m%d")
        df = bdi("PETR4", today)
        assert len(df) > 0
        assert "session_type" in df.columns
        # Regular session type should be present
        assert 1 in df["session_type"].values or "1" in df["session_type"].values

    def test_numeric_values(self):
        """OHLCV values are numeric."""
        today = datetime.date.today().strftime("%Y%m%d")
        df = bdi("PETR4", today)
        assert len(df) > 0
        for field in ["open", "high", "low", "close"]:
            assert pd.api.types.is_numeric_dtype(df[field])

    def test_vale3(self):
        """VALE3 (B3 stock) works for intraday."""
        today = datetime.date.today().strftime("%Y%m%d")
        df = bdi("VALE3", today)
        assert len(df) > 0

    def test_single_has_ticker_column(self):
        """Single-symbol call now carries a ticker column."""
        today = datetime.date.today().strftime("%Y%m%d")
        df = bdi("PETR4", today)
        assert "ticker" in df.columns
        assert df["ticker"].iloc[0] == "PETR4"

    def test_multiple(self):
        """A list returns one flat frame covering every symbol."""
        today = datetime.date.today().strftime("%Y%m%d")
        df = bdi(["PETR4", "VALE3"], today)
        assert isinstance(df, pd.DataFrame)
        assert {"PETR4", "VALE3"} <= set(df["ticker"].unique())
