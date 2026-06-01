"""Integration tests for bconsensus() — analyst consensus data."""

import pandas as pd
import pytest

from py_bcast import bconsensus

pytestmark = pytest.mark.legacy_session


class TestBconsensus:
    """Test aefundamental/consenso endpoint via bconsensus()."""

    _NUMERIC = {
        "buy",
        "hold",
        "sell",
        "total_analysts",
        "target_low",
        "target_high",
        "target_mean",
        "target_median",
        "upside_pct",
    }

    def test_petr4(self):
        """PETR4 returns consensus data."""
        df = bconsensus("PETR4")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "buy" in df.columns
        assert "target_mean" in df.columns
        assert df["ticker"].iloc[0] == "PETR4"

    def test_multiple(self):
        """A list returns one flat frame covering every covered ticker."""
        df = bconsensus(["PETR4", "VALE3"])
        assert isinstance(df, pd.DataFrame)
        assert {"PETR4", "VALE3"} <= set(df["ticker"].unique())

    def test_multiple_with_bogus_is_soft(self):
        """bconsensus is soft: a bogus entry yields an empty block, not a raise."""
        df = bconsensus(["PETR4", "XXXXX99"])
        assert isinstance(df, pd.DataFrame)
        assert "PETR4" in set(df["ticker"].unique())

    def test_all_fields_present(self):
        """Response includes all expected fields plus the ticker column."""
        df = bconsensus("PETR4")
        assert self._NUMERIC <= set(df.columns)
        assert "ticker" in df.columns

    def test_numeric_values(self):
        """All consensus values are numeric."""
        df = bconsensus("PETR4")
        for col in self._NUMERIC:
            float(df[col].iloc[0])  # Should not raise

    def test_analysts_add_up(self):
        """buy + hold + sell == total_analysts."""
        df = bconsensus("PETR4")
        total = (
            int(df["buy"].iloc[0]) + int(df["hold"].iloc[0]) + int(df["sell"].iloc[0])
        )
        assert total == int(df["total_analysts"].iloc[0])

    def test_vale3(self):
        """VALE3 returns consensus."""
        df = bconsensus("VALE3")
        assert not df.empty
        assert float(df["target_mean"].iloc[0]) > 0

    def test_itub4(self):
        """ITUB4 (bank stock) returns consensus."""
        df = bconsensus("ITUB4")
        assert not df.empty
        assert int(df["total_analysts"].iloc[0]) > 0

    def test_nonexistent_ticker(self):
        """Unknown ticker returns an empty DataFrame with schema (no crash)."""
        df = bconsensus("XXXXX99")
        assert isinstance(df, pd.DataFrame)
        assert df.empty
        assert "target_mean" in df.columns  # schema preserved

    def test_target_range_valid(self):
        """target_low <= target_mean <= target_high."""
        df = bconsensus("PETR4")
        low = float(df["target_low"].iloc[0])
        mean = float(df["target_mean"].iloc[0])
        high = float(df["target_high"].iloc[0])
        assert low <= mean <= high
