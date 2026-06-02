"""Unit tests for the numeric-coercion helper (pure pandas, no live session)."""

import pandas as pd
from pandas.api.types import is_numeric_dtype

from py_bcast._legacy.output import coerce_numeric_columns


class TestCoerceNumericColumns:
    def test_zero_padded_identifier_stays_string(self):
        # CNPJ-like 14-digit ids must not coerce: a leading zero would vanish
        # and the column would become an imprecise float.
        df = pd.DataFrame({"cnpj": ["08773135000100", "01547749000116"]})
        out = coerce_numeric_columns(df)
        assert not is_numeric_dtype(out["cnpj"])
        assert out["cnpj"].iloc[0] == "08773135000100"

    def test_all_zero_placeholder_stays_string(self):
        # "00000000000000" is a placeholder, not the number zero.
        df = pd.DataFrame({"cnpj": ["00000000000000", "08773135000100"]})
        out = coerce_numeric_columns(df)
        assert not is_numeric_dtype(out["cnpj"])
        assert out["cnpj"].iloc[0] == "00000000000000"

    def test_plain_integers_coerce(self):
        # No leading zero -> genuine quantities, must coerce.
        df = pd.DataFrame({"n": ["0", "1", "2", "10"]})
        out = coerce_numeric_columns(df)
        assert is_numeric_dtype(out["n"])

    def test_decimals_below_one_coerce(self):
        # "0.5" starts with 0 but the next char is "." (not a digit), so it is
        # a real number and must coerce.
        df = pd.DataFrame({"x": ["0.5", "0.7", "1.2"]})
        out = coerce_numeric_columns(df)
        assert is_numeric_dtype(out["x"])

    def test_dates_still_coerce_to_int(self):
        # Documents a known, non-corrupting limitation: YYYYMMDD has no leading
        # zero, so it still coerces to int (round-trips losslessly).
        df = pd.DataFrame({"d": ["19770720", "20180514"]})
        out = coerce_numeric_columns(df)
        assert is_numeric_dtype(out["d"])

    def test_sentinels_become_nan_column_stays_numeric(self):
        # Pre-existing behavior must be preserved: the n/d sentinel -> NaN and
        # the column still coerces.
        df = pd.DataFrame({"v": ["1.5", "n/d", "2.5"]})
        out = coerce_numeric_columns(df)
        assert is_numeric_dtype(out["v"])
        assert out["v"].isna().sum() == 1

    def test_genuine_text_stays_text(self):
        df = pd.DataFrame({"name": ["PETR4", "VALE3"]})
        out = coerce_numeric_columns(df)
        assert not is_numeric_dtype(out["name"])
