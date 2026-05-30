"""Integration tests for macroeconomic data functions."""

import pandas as pd
import pytest

from py_bcast import bmacro, bdi_cdi, breturn, bvolume, binflation

pytestmark = pytest.mark.legacy_session


class TestBmacro:
    def test_usdbrl(self):
        df = bmacro("USDBRL", "20260512", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        assert "close" in df.columns

    def test_ibov(self):
        df = bmacro("IBOV", "20260512", "20260519")
        assert len(df) >= 1

    def test_spx(self):
        df = bmacro("SPX", "20260512", "20260516")
        assert len(df) >= 1

    def test_aetaxas_ipca(self):
        df = bmacro("AEIPCA", "20250101", "20260519")
        assert len(df) >= 1

    def test_sorted_chronologically(self):
        df = bmacro("USDBRL", "20260501", "20260519")
        assert df.index.is_monotonic_increasing

    def test_empty_range(self):
        # Valid symbol, no rows in the (inverted) range: the server replies
        # "não foram encontrados registros", which the unified error policy
        # maps to an empty DataFrame rather than an exception.
        df = bmacro("USDBRL", "20260518", "20260510")
        assert isinstance(df, pd.DataFrame)
        assert df.empty


class TestBdiCdi:
    def test_recent(self):
        df = bdi_cdi("20260501", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        assert "close" in df.columns

    def test_historical_since_1986(self):
        df = bdi_cdi("19860601", "19860630")
        assert len(df) >= 1

    def test_sorted(self):
        df = bdi_cdi("20260501", "20260519")
        assert df.index.is_monotonic_increasing


class TestBreturn:
    def test_petr4(self):
        df = breturn("PETR4", "20260501", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        assert "close" in df.columns

    def test_sorted(self):
        df = breturn("PETR4", "20260501", "20260519")
        assert df.index.is_monotonic_increasing


class TestBvolume:
    def test_single(self):
        df = bvolume("PETR4")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        assert any("PETR4" in idx for idx in df.index)

    def test_multiple(self):
        df = bvolume(["PETR4", "VALE3"])
        assert len(df) >= 2


class TestBinflation:
    def test_returns_indices(self):
        df = binflation()
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 5
