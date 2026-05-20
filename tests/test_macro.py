"""Integration tests for macroeconomic data functions."""

from py_bcast import bmacro, bdi_cdi, breturn, bvolume, binflation


class TestBmacro:
    def test_usdbrl(self):
        rows = bmacro("USDBRL", "20260512", "20260519")
        assert len(rows) >= 1
        assert "dat" in rows[0]
        assert "last" in rows[0]
        assert rows[0]["last"]  # non-empty

    def test_ibov(self):
        rows = bmacro("IBOV", "20260512", "20260519")
        assert len(rows) >= 1

    def test_spx(self):
        rows = bmacro("SPX", "20260512", "20260516")
        assert len(rows) >= 1

    def test_aetaxas_ipca(self):
        rows = bmacro("AEIPCA", "20250101", "20260519")
        assert len(rows) >= 1

    def test_sorted_chronologically(self):
        rows = bmacro("USDBRL", "20260501", "20260519")
        dates = [r["dat"] for r in rows]
        assert dates == sorted(dates)

    def test_empty_range(self):
        import pytest
        with pytest.raises(RuntimeError):
            bmacro("USDBRL", "20260518", "20260510")


class TestBdiCdi:
    def test_recent(self):
        rows = bdi_cdi("20260501", "20260519")
        assert len(rows) >= 1
        assert "dat" in rows[0]
        assert "last" in rows[0]

    def test_historical_since_1986(self):
        rows = bdi_cdi("19860601", "19860630")
        assert len(rows) >= 1

    def test_sorted(self):
        rows = bdi_cdi("20260501", "20260519")
        dates = [r["dat"] for r in rows]
        assert dates == sorted(dates)


class TestBreturn:
    def test_petr4(self):
        rows = breturn("PETR4", "20260501", "20260519")
        assert len(rows) >= 1
        assert "dat" in rows[0]
        assert "last" in rows[0]

    def test_sorted(self):
        rows = breturn("PETR4", "20260501", "20260519")
        dates = [r["dat"] for r in rows]
        assert dates == sorted(dates)


class TestBvolume:
    def test_single(self):
        data = bvolume("PETR4")
        assert len(data) >= 1
        key = next(iter(data))
        assert "PETR4" in key

    def test_multiple(self):
        data = bvolume(["PETR4", "VALE3"])
        assert len(data) >= 2


class TestBinflation:
    def test_returns_indices(self):
        rows = binflation()
        assert len(rows) >= 1
        # Should have multiple inflation indices
        assert len(rows) >= 5
