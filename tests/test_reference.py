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
from py_bcast import NotFoundError

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
        assert isinstance(q, pd.DataFrame)
        assert len(q) == 1
        assert q["ticker"].iloc[0] == "PETR4"

    def test_multiple(self):
        df = bquote(["PETR4", "VALE3"])
        assert isinstance(df, pd.DataFrame)
        assert {"PETR4", "VALE3"} <= set(df["ticker"].unique())

    def test_multiple_with_bogus_is_soft(self):
        # bquote is soft: a bogus entry yields an empty block (no row), not a
        # raise. The valid ticker still comes through.
        df = bquote(["PETR4", "ZZZZ99"])
        assert isinstance(df, pd.DataFrame)
        assert "PETR4" in set(df["ticker"].unique())

    def test_unknown_returns_empty(self):
        # bquote is the soft resolution primitive: unknown -> empty (with
        # schema), which resolve_cvm turns into NotFoundError.
        q = bquote("ZZZZZ99")
        assert isinstance(q, pd.DataFrame)
        assert q.empty
        assert "cvm_code" in q.columns


class TestBtickers:
    def test_petrobras(self):
        # CVM 9512 = Petrobras (PETR3, PETR4)
        df = btickers(9512)
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1

    def test_multiple(self):
        # The endpoint emits its OWN ticker column (the company's symbols), so
        # the lookup identifier is NOT in df["ticker"]. Assert the companies'
        # known symbols appear instead. CVM 9512 = Petrobras, 4170 = Vale.
        df = btickers([9512, 4170])
        symbols = set(df["ticker"].unique())
        assert any(s.startswith("PETR") for s in symbols)
        assert any(s.startswith("VALE") for s in symbols)

    def test_unknown_raises(self):
        # btickers uses empty_ok=False -> a non-existent CVM raises NotFound.
        with pytest.raises(NotFoundError):
            btickers([9512, 99999999])


class TestBshares:
    def test_petr4(self):
        data = bshares("PETR4")
        assert isinstance(data, pd.DataFrame)
        assert len(data) == 1
        assert data["ticker"].iloc[0] == "PETR4"

    def test_multiple(self):
        df = bshares(["PETR4", "VALE3"])
        assert isinstance(df, pd.DataFrame)
        assert {"PETR4", "VALE3"} <= set(df["ticker"].unique())

    def test_bogus_raises(self):
        # bshares uses empty_ok=False -> fail-fast NotFound for a bad ticker.
        with pytest.raises(NotFoundError):
            bshares(["PETR4", "ZZZZ99"])


class TestBindicators:
    def test_market_cap(self):
        # indicator 32 = Market Cap
        df = bindicators(9512, 32, "20260501", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        assert "_unused" not in df.columns  # B2: trailing filler tag dropped
        assert "ticker" in df.columns

    def test_beta(self):
        # indicator 52 = Beta
        df = bindicators(9512, 52, "20260501", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1

    def test_multiple(self):
        # bindicators does NOT emit a server ticker column, so the wrapper
        # inserts each input identifier (here ticker strings).
        df = bindicators(["PETR4", "VALE3"], 32, "20260501", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert {"PETR4", "VALE3"} <= set(df["ticker"].unique())


class TestBindicatorMeta:
    def test_returns_metadata(self):
        df = bindicator_meta()
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 10  # expect ~80
