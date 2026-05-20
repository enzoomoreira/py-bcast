"""Integration tests for bdi() — intraday OHLCV bars."""

import pytest
from py_bcast import bdi


class TestBdi:
    """Test HistoricoIntraday endpoint via bdi()."""

    def test_petr4_today(self):
        """PETR4 intraday returns bars for today."""
        import datetime
        today = datetime.date.today().strftime("%Y%m%d")
        bars = bdi("PETR4", today)
        assert len(bars) > 0
        assert bars[0]["dat"] == today

    def test_bar_fields(self):
        """Each bar has expected OHLCV fields."""
        import datetime
        today = datetime.date.today().strftime("%Y%m%d")
        bars = bdi("PETR4", today)
        assert len(bars) > 0
        bar = bars[0]
        expected_keys = {"dat", "hor", "open", "high", "low", "last", "qtt", "neg"}
        assert expected_keys.issubset(bar.keys())

    def test_chronological_order(self):
        """Bars are sorted oldest-first."""
        import datetime
        today = datetime.date.today().strftime("%Y%m%d")
        bars = bdi("PETR4", today)
        if len(bars) >= 2:
            assert bars[0]["hor"] <= bars[-1]["hor"]

    def test_historical_range(self):
        """Can fetch multiple days of intraday data."""
        import datetime
        week_ago = (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y%m%d")
        bars = bdi("PETR4", week_ago)
        # Should have more bars than a single day (~200/day)
        assert len(bars) > 200
        # Should span multiple dates
        dates = set(b["dat"] for b in bars)
        assert len(dates) >= 2

    def test_international_usdbrl(self):
        """USDBRL intraday works."""
        import datetime
        today = datetime.date.today().strftime("%Y%m%d")
        bars = bdi("USDBRL", today)
        assert len(bars) > 0
        # FX has 4 decimal precision
        last = bars[-1]["last"]
        assert "." in last

    def test_international_gold(self):
        """GOLD intraday works."""
        import datetime
        today = datetime.date.today().strftime("%Y%m%d")
        bars = bdi("GOLD", today)
        assert len(bars) > 0

    def test_tipo_intervalo(self):
        """Bars include tipo_intervalo field."""
        import datetime
        today = datetime.date.today().strftime("%Y%m%d")
        bars = bdi("PETR4", today)
        assert len(bars) > 0
        tipos = set(b["tipo_intervalo"] for b in bars)
        # Regular session type should be present
        assert "1" in tipos

    def test_numeric_values(self):
        """OHLCV values are parseable as floats."""
        import datetime
        today = datetime.date.today().strftime("%Y%m%d")
        bars = bdi("PETR4", today)
        assert len(bars) > 0
        bar = bars[0]
        for field in ["open", "high", "low", "last"]:
            float(bar[field])  # Should not raise

    def test_vale3(self):
        """VALE3 (B3 stock) works for intraday."""
        import datetime
        today = datetime.date.today().strftime("%Y%m%d")
        bars = bdi("VALE3", today)
        assert len(bars) > 0
