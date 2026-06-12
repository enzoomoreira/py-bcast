"""Integration tests for Broadcast+ intraday tick data (btrades).

Requires the Plus backend (Broadcast+.exe running or BROADCAST_PLUS_TOKEN set);
skipped otherwise by the conftest resource gate.
"""

import pandas as pd
import pytest

from py_bcast import btrades
from py_bcast._core.dates import default_end_date

pytestmark = pytest.mark.plus


class TestBtrades:
    def test_returns_dataframe(self):
        df = btrades("PETR4", default_end_date())
        assert isinstance(df, pd.DataFrame)

    def test_broker_id_columns(self):
        # The bid/ask exchangeId field is, in the B3 book, the broker on each
        # side; surfaced as ask_broker_id/bid_broker_id (nullable Int64 so the
        # frame joins with bbrokers() on broker id).
        df = btrades("PETR4", default_end_date())
        if df.empty:
            pytest.skip("no trades available for the date")
        assert "ask_broker_id" in df.columns
        assert "bid_broker_id" in df.columns
        assert df["ask_broker_id"].dtype == "Int64"
        assert df["bid_broker_id"].dtype == "Int64"
