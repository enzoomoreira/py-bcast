"""Integration tests for reference data functions."""

from py_bcast import (
    bcompany, bindices, bsectors, bquote, btickers, bshares,
    bindicators, bindicator_meta,
)


class TestBcompany:
    def test_all_companies(self):
        companies = bcompany()
        assert len(companies) >= 100  # expect ~1020

    def test_single_company(self):
        # PETR = CVM 9512
        data = bcompany(9512)
        assert len(data) >= 1


class TestBindices:
    def test_returns_indices(self):
        indices = bindices()
        assert len(indices) >= 10  # expect ~37


class TestBsectors:
    def test_returns_sectors(self):
        sectors = bsectors()
        assert len(sectors) >= 10  # expect ~38


class TestBquote:
    def test_petr4(self):
        q = bquote("PETR4")
        assert q  # non-empty dict
        assert len(q) >= 1

    def test_unknown_returns_empty(self):
        q = bquote("ZZZZZ99")
        assert q == {}


class TestBtickers:
    def test_petrobras(self):
        # CVM 9512 = Petrobras (PETR3, PETR4)
        tickers = btickers(9512)
        assert len(tickers) >= 1


class TestBshares:
    def test_petr4(self):
        data = bshares("PETR4")
        assert data  # non-empty


class TestBindicators:
    def test_market_cap(self):
        # indicator 32 = Market Cap
        rows = bindicators(9512, 32, "20260501", "20260519")
        assert len(rows) >= 1

    def test_beta(self):
        # indicator 52 = Beta
        rows = bindicators(9512, 52, "20260501", "20260519")
        assert len(rows) >= 1


class TestBindicatorMeta:
    def test_returns_metadata(self):
        meta = bindicator_meta()
        assert len(meta) >= 10  # expect ~80
