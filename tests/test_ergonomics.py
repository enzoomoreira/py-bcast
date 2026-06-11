"""Unit tests for the ergonomic layer: Ticker facade + .bcast accessor.

All offline — Ticker delegation is checked via monkeypatch, and the accessor is
pure pandas reshaping.
"""

import pandas as pd
import pytest

import py_bcast  # noqa: F401 — registers the .bcast accessor
from py_bcast import Ticker
from py_bcast import ticker as ticker_mod


class TestTickerFacade:
    def test_normalizes_symbol(self):
        assert Ticker("petr4").ticker == "PETR4"
        assert Ticker("  vale3 ").ticker == "VALE3"

    def test_repr(self):
        assert repr(Ticker("PETR4")) == "Ticker('PETR4')"

    @pytest.mark.parametrize(
        "method, target, args",
        [
            ("history", "bhistory", ("20260501", "20260520")),
            ("ohlcv", "bhistory", ("20260519",)),
            ("intraday", "bdi", ("20260519",)),
            ("ticks", "bdt", ("20260519",)),
            ("dy", "bdy", ("20260101", "20260519")),
            ("indicators", "bindicators", ("EBITDA", "20260101", "20260519")),
        ],
    )
    def test_method_delegates(self, monkeypatch, method, target, args):
        calls = {}

        def spy(*a, **kw):
            calls["args"] = a
            calls["kwargs"] = kw
            return "SENTINEL"

        monkeypatch.setattr(ticker_mod, target, spy)
        result = getattr(Ticker("PETR4", session_token="TOK"), method)(*args)
        assert result == "SENTINEL"
        # ticker is always first positional arg; token is forwarded
        assert calls["args"][0] == "PETR4"
        assert calls["kwargs"]["session_token"] == "TOK"

    @pytest.mark.parametrize(
        "prop, target",
        [
            ("quote", "bquote"),
            ("shares", "bshares"),
            ("consensus", "bconsensus"),
            ("dividends", "bdividends"),
            ("symbols", "btickers"),
        ],
    )
    def test_property_delegates(self, monkeypatch, prop, target):
        calls = {}

        def spy(*a, **kw):
            calls["args"] = a
            calls["kwargs"] = kw
            return "SENTINEL"

        monkeypatch.setattr(ticker_mod, target, spy)
        result = getattr(Ticker("PETR4"), prop)
        assert result == "SENTINEL"
        assert calls["args"][0] == "PETR4"


def _flat_frame():
    idx = pd.to_datetime(
        ["20260501", "20260502", "20260501", "20260502"], format="%Y%m%d"
    )
    return pd.DataFrame(
        {
            "ticker": ["PETR4", "PETR4", "VALE3", "VALE3"],
            "close": [40.0, 41.0, 60.0, 61.0],
            "settle": [40.1, 41.1, 60.1, 61.1],
        },
        index=idx,
    )


class TestBcastAccessor:
    def test_wide_builds_ticker_field_multiindex(self):
        wide = _flat_frame().bcast.wide()
        assert isinstance(wide.columns, pd.MultiIndex)
        assert ("PETR4", "close") in wide.columns
        assert list(wide["PETR4"].columns) == ["close", "settle"]
        assert wide[("PETR4", "close")].tolist() == [40.0, 41.0]

    def test_long_round_trips(self):
        flat = _flat_frame()
        back = flat.bcast.wide().bcast.long()
        # compare value-by-value, order-independent
        a = back.sort_values(["ticker", "close"]).reset_index(drop=True)
        b = flat.sort_values(["ticker", "close"]).reset_index(drop=True)
        assert a["ticker"].tolist() == b["ticker"].tolist()
        assert a["close"].tolist() == b["close"].tolist()
        assert a["settle"].tolist() == b["settle"].tolist()

    def test_wide_requires_ticker_column(self):
        df = pd.DataFrame({"close": [1.0, 2.0]})
        with pytest.raises(ValueError, match="ticker"):
            df.bcast.wide()

    def test_wide_rejects_duplicate_pairs(self):
        # Genuine duplicate (index, ticker) pairs: same date + ticker twice.
        idx = pd.to_datetime(["20260501", "20260501"], format="%Y%m%d")
        df = pd.DataFrame(
            {"ticker": ["PETR4", "PETR4"], "close": [1.0, 2.0]}, index=idx
        )
        with pytest.raises(ValueError, match="unique"):
            df.bcast.wide()

    def test_long_passthrough_when_already_flat(self):
        flat = _flat_frame()
        out = flat.bcast.long()
        assert "ticker" in out.columns
        assert not isinstance(out.columns, pd.MultiIndex)
