"""Integration tests for instrument database and bsearch routing."""

import pandas as pd
import pytest

from py_bcast import bsearch, InstrumentDB
from py_bcast._core.config import configure
from py_bcast.instruments.db import INSTRUMENT_COLUMNS


@pytest.fixture
def force_legacy():
    """Pin the active backend to legacy for the duration of the test."""
    configure(terminal="legacy")
    yield
    configure(terminal="auto")


@pytest.fixture
def force_plus():
    """Pin the active backend to plus for the duration of the test."""
    configure(terminal="plus")
    yield
    configure(terminal="auto")


@pytest.mark.legacy_db
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
        assert inst["backend"] == "legacy"

    def test_lookup_not_found(self):
        db = InstrumentDB.get()
        assert db.lookup("XYZXYZXYZ999") is None


@pytest.mark.legacy_db
class TestBsearchLegacy:
    def test_returns_dataframe(self, force_legacy):
        results = bsearch("PETR4", exchange="BVMF")
        assert isinstance(results, pd.DataFrame)
        assert list(results.columns) == INSTRUMENT_COLUMNS

    def test_exact_match_first(self, force_legacy):
        results = bsearch("PETR4", exchange="BVMF")
        assert results.iloc[0]["ticker"] == "PETR4"

    def test_starts_with(self, force_legacy):
        results = bsearch("PETR", exchange="BVMF", max_results=10)
        tickers = results["ticker"].tolist()
        assert "PETR3" in tickers or "PETR4" in tickers

    def test_exchange_filter(self, force_legacy):
        results = bsearch("VIX", exchange="CBOEI")
        assert (results["exchange"] == "CBOEI").all()
        assert results.iloc[0]["ticker"] == "VIX"

    def test_max_results(self, force_legacy):
        results = bsearch("A", max_results=5)
        assert len(results) <= 5

    def test_fx_search(self, force_legacy):
        results = bsearch("USDBRL")
        assert results["ticker"].str.contains("USDBRL").any()

    def test_isin_search(self, force_legacy):
        results = bsearch("BRPETRACNPR6")
        assert (results["ticker"] == "PETR4").any()

    def test_backend_column_is_legacy(self, force_legacy):
        results = bsearch("PETR4", exchange="BVMF")
        assert (results["backend"] == "legacy").all()

    def test_plus_only_columns_are_na(self, force_legacy):
        results = bsearch("PETR4", exchange="BVMF")
        for col in ("cvm_code", "has_intraday", "has_daily", "is_realtime"):
            assert results[col].isna().all()


@pytest.mark.plus
class TestBsearchPlus:
    def test_returns_dataframe(self, force_plus):
        results = bsearch("PETR", max_results=5)
        assert isinstance(results, pd.DataFrame)
        assert list(results.columns) == INSTRUMENT_COLUMNS

    def test_backend_column_is_plus(self, force_plus):
        results = bsearch("PETR", max_results=5)
        assert (results["backend"] == "plus").all()

    def test_legacy_only_columns_are_na(self, force_plus):
        results = bsearch("PETR", max_results=5)
        for col in ("full_symbol", "isin"):
            assert results[col].isna().all()

    def test_exchange_normalized_when_known(self, force_plus):
        results = bsearch("PETR4", max_results=5)
        if (results["ticker"] == "PETR4").any():
            row = results[results["ticker"] == "PETR4"].iloc[0]
            assert row["exchange"] == "BVMF"
