"""Integration tests for events, dividends, and portfolios."""

import pandas as pd

from py_bcast import bcalendar, bdividends, bdy, bportfolios, bportfolio


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
        # CVM 9512 = Petrobras
        df = bdividends(9512, "PETR4")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1


class TestBdy:
    def test_petrobras_dy(self):
        df = bdy(9512, "PETR4", "20250101", "20260519")
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1


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
