"""Integration tests for reference data functions."""

import pandas as pd
import pytest

from py_bcast import (
    bcompany,
    bindices,
    bsectors,
    bquote,
    btickers,
    bshares,
    bindicators,
    bindicator_meta,
)

pytestmark = pytest.mark.legacy_session


class TestBcompany:
    def test_all_companies(self):
        df = bcompany()
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 100  # expect ~1020

    def test_single_company(self):
        # PETR = CVM 9512
        df = bcompany(9512)
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1


class TestBindices:
    def test_returns_indices(self):
        df = bindices()
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 10  # expect ~37


class TestBsectors:
    def test_returns_sectors(self):
        df = bsectors()
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 10  # expect ~38


class TestBquote:
    def test_petr4(self):
        q = bquote("PETR4")
        assert isinstance(q, pd.Series)
        assert not q.empty

    def test_unknown_returns_empty(self):
        q = bquote("ZZZZZ99")
        assert isinstance(q, pd.Series)
        assert q.empty


class TestBtickers:
    def test_petrobras(self):
        # CVM 9512 = Petrobras (PETR3, PETR4)
        df = btickers(9512)
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1


class TestBshares:
    def test_petr4(self):
        data = bshares("PETR4")
        assert isinstance(data, pd.Series)
        assert not data.empty


class TestBindicators:
    def test_market_cap(self):
        # indicator 32 = Market Cap
        df = bindicators(9512, 32, "20260501", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1

    def test_beta(self):
        # indicator 52 = Beta
        df = bindicators(9512, 52, "20260501", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1


class TestBindicatorMeta:
    def test_returns_metadata(self):
        df = bindicator_meta()
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 10  # expect ~80
