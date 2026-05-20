"""Integration tests for historical data functions."""

from py_bcast import bdh, bdh_ohlcv, bdt


class TestBdh:
    def test_single_ticker(self):
        data = bdh("PETR4", "20260512", "20260519")
        assert "PETR4.BVMF" in data
        rows = data["PETR4.BVMF"]
        assert len(rows) >= 1
        assert "date" in rows[0]
        assert "last" in rows[0]
        assert rows[0]["last"]  # non-empty price

    def test_multiple_tickers(self):
        data = bdh(["PETR4", "VALE3"], "20260515", "20260519")
        assert "PETR4.BVMF" in data
        assert "VALE3.BVMF" in data

    def test_fx(self):
        data = bdh("USDBRL", "20260512", "20260519")
        assert any("USDBRL" in k for k in data.keys())

    def test_sorted_chronologically(self):
        data = bdh("PETR4", "20260501", "20260519")
        rows = data.get("PETR4.BVMF", [])
        dates = [r["date"] for r in rows]
        assert dates == sorted(dates)

    def test_empty_range(self):
        data = bdh("PETR4", "20260518", "20260510")  # end < start
        assert data == {}


class TestBdhOhlcv:
    def test_single_date(self):
        data = bdh_ohlcv("PETR4", "20260519")
        assert data
        assert "last" in data
        assert "high" in data
        assert "low" in data
        assert "open" in data

    def test_no_data_returns_empty(self):
        # Weekend date
        data = bdh_ohlcv("PETR4", "20260517")
        assert data == {} or data.get("last") == ""


class TestBdt:
    def test_usdbrl_ticks(self):
        ticks = bdt("USDBRL", "20260519100000", "20260519101000")
        assert len(ticks) >= 1
        assert "hor" in ticks[0]
        assert "last" in ticks[0]

    def test_chronological_order(self):
        ticks = bdt("USDBRL", "20260519100000", "20260519110000")
        if len(ticks) >= 2:
            assert ticks[0]["hor"] <= ticks[-1]["hor"]

    def test_bvmf_returns_empty(self):
        # B3 ticks blocked by query registration
        ticks = bdt("PETR4", "20260519100000", "20260519101000")
        assert ticks == []

    def test_default_end_time(self):
        # Should default to start + 1 hour
        ticks = bdt("USDBRL", "20260519100000")
        assert isinstance(ticks, list)
