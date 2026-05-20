"""Integration tests for bconsensus() — analyst consensus data."""

import pytest
from py_bcast import bconsensus


class TestBconsensus:
    """Test aefundamental/consenso endpoint via bconsensus()."""

    def test_petr4(self):
        """PETR4 returns consensus data."""
        data = bconsensus("PETR4")
        assert data
        assert "buy" in data
        assert "target_mean" in data

    def test_all_fields_present(self):
        """Response includes all expected fields."""
        data = bconsensus("PETR4")
        expected = {"buy", "hold", "sell", "total_analysts",
                    "target_low", "target_high", "target_mean",
                    "target_median", "upside_pct"}
        assert expected == set(data.keys())

    def test_numeric_values(self):
        """All values are parseable as numbers."""
        data = bconsensus("PETR4")
        for key, val in data.items():
            float(val)  # Should not raise

    def test_analysts_add_up(self):
        """buy + hold + sell == total_analysts."""
        data = bconsensus("PETR4")
        total = int(data["buy"]) + int(data["hold"]) + int(data["sell"])
        assert total == int(data["total_analysts"])

    def test_vale3(self):
        """VALE3 returns consensus."""
        data = bconsensus("VALE3")
        assert data
        assert float(data["target_mean"]) > 0

    def test_itub4(self):
        """ITUB4 (bank stock) returns consensus."""
        data = bconsensus("ITUB4")
        assert data
        assert int(data["total_analysts"]) > 0

    def test_nonexistent_ticker(self):
        """Unknown ticker returns empty dict (no crash)."""
        data = bconsensus("XXXXX99")
        assert data == {}

    def test_target_range_valid(self):
        """target_low <= target_mean <= target_high."""
        data = bconsensus("PETR4")
        low = float(data["target_low"])
        mean = float(data["target_mean"])
        high = float(data["target_high"])
        assert low <= mean <= high
