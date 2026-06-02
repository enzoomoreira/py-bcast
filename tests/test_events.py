"""Integration tests for events, dividends, and portfolios."""

import pandas as pd
import pytest

from py_bcast import bcalendar, bdividends, bdy, bportfolios, bportfolio

pytestmark = pytest.mark.legacy_session


class TestBcalendar:
    def test_returns_events(self):
        df = bcalendar("20260101", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 10  # expect hundreds

    def test_narrow_range(self):
        df = bcalendar("20260515", "20260519")
        assert isinstance(df, pd.DataFrame)


class TestBdividends:
    def test_petrobras(self):
        # Ticker-only (auto-resolves CVM)
        df = bdividends("PETR4")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        assert "ticker" in df.columns
        assert df["ticker"].iloc[0] == "PETR4"

    def test_multiple(self):
        # List resolves each ticker's CVM independently.
        df = bdividends(["PETR4", "VALE3"])
        assert isinstance(df, pd.DataFrame)
        assert {"PETR4", "VALE3"} <= set(df["ticker"].unique())


class TestBdy:
    def test_petrobras_dy(self):
        df = bdy("PETR4", "20250101", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        assert "_unused" not in df.columns  # B1: trailing filler tag dropped
        assert "ticker" in df.columns
        assert df["ticker"].iloc[0] == "PETR4"

    def test_multiple(self):
        df = bdy(["PETR4", "VALE3"], "20250101", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert {"PETR4", "VALE3"} <= set(df["ticker"].unique())


class TestBportfolios:
    def test_returns_brokers(self):
        df = bportfolios()
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1


class TestBportfolio:
    def test_first_broker(self):
        brokers = bportfolios()
        if not brokers.empty:
            # Get the first broker's ID from whatever column contains it
            first = brokers.iloc[0]
            broker_id = None
            for v in first.values:
                try:
                    int(v)
                    broker_id = v
                    break
                except (ValueError, TypeError):
                    continue
            if broker_id:
                holdings = bportfolio(broker_id)
                assert isinstance(holdings, pd.DataFrame)

    def test_columns_not_scrambled(self):
        # Broker 27 has a populated portfolio. The held ticker lives in 10068
        # (the lib-wide ticker tag); a regression mapped it to 13902, leaving
        # `ticker` all-NaN and `portfolio_name` holding the ticker instead.
        df = bportfolio(27)
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        assert "ticker" in df.columns
        assert df["ticker"].notna().any()  # ticker column is populated, not all-NaN
        assert "portfolio_name" in df.columns
        assert df["portfolio_name"].notna().any()

    def test_recommendation_column(self):
        # Themed portfolios (e.g. "Carteira Top 10", "Dividendos") carry a
        # per-stock analyst recommendation in tag 13022; the PADRAO holdings
        # leave it empty. Earlier this tag was dropped as unidentified.
        df = bportfolio(27)
        assert "recommendation" in df.columns
        recs = {str(v).strip().upper() for v in df["recommendation"] if str(v).strip()}
        assert recs, "recommendation column has no populated values"
        assert recs & {"COMPRA", "NEUTRA", "VENDA"}, (
            f"unexpected recommendation tokens: {recs}"
        )

    def test_target_and_dy_columns(self):
        # Themed-portfolio rows also carry a broker target price (13025) and a
        # 12-month dividend yield (13895), confirmed empirically against the
        # stocks' consensus target and bdy. Populated only on themed rows.
        df = bportfolio(27)
        assert "target_price" in df.columns
        assert "dy_pct" in df.columns
        themed = df[df["recommendation"].astype(str).str.strip() != ""]
        assert pd.to_numeric(themed["target_price"], errors="coerce").gt(0).any()
        assert pd.to_numeric(themed["dy_pct"], errors="coerce").ge(0).any()
