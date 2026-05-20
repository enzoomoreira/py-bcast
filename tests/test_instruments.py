"""Integration tests for instrument database."""

from py_bcast import bsearch, InstrumentDB


class TestInstrumentDB:
    def test_singleton(self):
        db1 = InstrumentDB.get()
        db2 = InstrumentDB.get()
        assert db1 is db2

    def test_has_instruments(self):
        db = InstrumentDB.get()
        assert len(db) > 600_000

    def test_exchanges(self):
        db = InstrumentDB.get()
        exc = db.exchanges
        assert "BVMF" in exc
        assert exc["BVMF"] > 100_000

    def test_lookup_petr4(self):
        db = InstrumentDB.get()
        inst = db.lookup("PETR4")
        assert inst is not None
        assert inst["full_symbol"] == "PETR4.BVMF"
        assert "PETROBRAS" in inst["name"].upper()
        assert inst["isin"].startswith("BR")

    def test_lookup_not_found(self):
        db = InstrumentDB.get()
        assert db.lookup("XYZXYZXYZ999") is None


class TestBsearch:
    def test_exact_match_first(self):
        results = bsearch("PETR4", exchange="BVMF")
        assert results[0]["ticker"] == "PETR4"

    def test_starts_with(self):
        results = bsearch("PETR", exchange="BVMF", max_results=10)
        tickers = [r["ticker"] for r in results]
        assert "PETR3" in tickers or "PETR4" in tickers

    def test_exchange_filter(self):
        results = bsearch("VIX", exchange="CBOEI")
        assert all(r["exchange"] == "CBOEI" for r in results)
        assert results[0]["ticker"] == "VIX"

    def test_max_results(self):
        results = bsearch("A", max_results=5)
        assert len(results) <= 5

    def test_fx_search(self):
        results = bsearch("USDBRL")
        assert any("USDBRL" in r["ticker"] for r in results)

    def test_isin_search(self):
        results = bsearch("BRPETRACNPR6")
        assert any(r["ticker"] == "PETR4" for r in results)
