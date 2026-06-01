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

    def test_exchange_id_columns(self):
        # B8: the bid/ask exchangeId is retained as a string venue code
        # (an identifier, not a quantity, so it is not coerced to numeric).
        df = btrades("PETR4", default_end_date())
        if df.empty:
            pytest.skip("no trades available for the date")
        assert "ask_exchange_id" in df.columns
        assert "bid_exchange_id" in df.columns
        # Kept as a string identifier, never coerced to a numeric quantity.
        assert not pd.api.types.is_numeric_dtype(df["ask_exchange_id"])
