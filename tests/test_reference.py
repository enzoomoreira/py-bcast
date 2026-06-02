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

    def test_cnpj_preserves_leading_zeros(self):
        # CNPJ is a 14-digit zero-padded identifier. The list column is
        # all-numeric, so blanket coercion turned it into a float that dropped
        # the leading zero ("08773135000100" -> 8773135000100.0) and made the
        # placeholder 0.0. It must stay string with leading zeros intact.
        df = bcompany()
        cnpjs = df["cnpj"].tolist()
        assert all(isinstance(v, str) for v in cnpjs)  # not coerced to float
        assert any(c.startswith("0") and len(c) == 14 for c in cnpjs)

    def test_tickers_column_not_listing_segment(self):
        # 10113 holds the company's tradable tickers (";"-joined share classes,
        # e.g. "RPAD3;RPAD5;RPAD6"); it was mislabeled listing_segment.
        df = bcompany()
        assert "tickers" in df.columns
        assert "listing_segment" not in df.columns
        nonblank = [str(v) for v in df["tickers"] if str(v).strip()]
        assert nonblank
        # values look like tickers (XXXX9 or ;-joined), not segment names
        assert any(v[:4].isalpha() and v[-1].isdigit() for v in nonblank[:50])


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
        # indicator 32 = Valor de Mercado (a daily, price-derived series).
        # 10068 holds the per-row share class (PETR3/PETR4), NOT the input CVM:
        # a regression mislabeled it change_pct, leaving `ticker` an echo of the
        # CVM "9512". It now behaves like btickers (every share class echoed),
        # and 13788 is the value's day-over-day pct (value_change_pct).
        df = bindicators(9512, 32, "20260501", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        assert {"ticker", "value", "value_change_pct"} <= set(df.columns)
        assert "change_pct" not in df.columns
        symbols = set(df["ticker"].unique())
        assert "9512" not in symbols  # not the CVM echo (the regression)
        # populated tickers are Petrobras share classes; market cap also emits
        # company-level rows with a blank ticker, which are tolerated.
        nonblank = {s for s in symbols if str(s).strip()}
        assert nonblank and all(s.startswith("PETR") for s in nonblank)

    def test_beta(self):
        # indicator 52 = Beta
        df = bindicators(9512, 52, "20260501", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1

    def test_multiple(self):
        # bindicators emits its OWN ticker column (the per-row share class), so
        # the lookup identifier is NOT echoed; the companies' symbols appear
        # instead (like btickers). PETR -> PETR3/PETR4, VALE -> VALE3/VALE5.
        df = bindicators(["PETR4", "VALE3"], 32, "20260501", "20260519")
        symbols = set(df["ticker"].unique())
        assert any(s.startswith("PETR") for s in symbols)
        assert any(s.startswith("VALE") for s in symbols)


class TestBindicatorMeta:
    def test_returns_metadata(self):
        df = bindicator_meta()
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 10  # expect ~80

    def test_text_fields_not_mislabeled(self):
        # The text-field tags were scrambled: the unit ("R$ Milhar") sat under
        # unit_type, the prose description under calculation_notes, and the
        # calc formula under long_description. Pin the corrected labels.
        df = bindicator_meta()
        assert {"unit", "note", "formula", "description"} <= set(df.columns)
        assert not (
            {"unit_type", "calculation_notes", "long_description"} & set(df.columns)
        )
        assert "R$ Milhar" in set(df["unit"].dropna())
        assert df["formula"].astype(str).str.strip().ne("").any()
        # description is prose, not a short code or a date
        assert df["description"].astype(str).str.len().max() > 20
