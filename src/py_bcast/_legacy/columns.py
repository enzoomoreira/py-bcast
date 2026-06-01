"""Centralized column name mappings for API response standardization.

Defines rename maps that convert raw server field names (ContentProxy XML)
and numeric tag IDs (AETP binary) into consistent, finance-standard English
column names used across the library's public DataFrame/Series outputs.

Naming conventions:
    - close: last/closing price (server calls it "last")
    - trades: number of trades/negotiations (server: "neg")
    - volume: quantity of shares/contracts (server: "qtt")
    - turnover: financial volume in BRL (server: "total_value")
    - change_pct: percentage change/return (server: "var")
    - Standard OHLCV: open, high, low, close, volume
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────
# Group A: ContentProxy XML endpoints — universal column rename
# Applied by output.py functions. Keys map to None = drop column.
# ─────────────────────────────────────────────────────────────────────

CONTENT_PROXY_RENAME: dict[str, str | None] = {
    "last": "close",
    "neg": "trades",
    "qtt": "volume",
    "total_value": "turnover",
    "total_neg": "cum_trades",
    "tipo_intervalo": "session_type",
    "var": "change_pct",
    "dattol": None,  # drop: request artifact with no data value
    "hor": None,  # drop: empty on daily series (consumed as time index intraday)
    "settle_rate": "settle_rate",  # keep (fixed-income only)
    "open_interest": "open_interest",  # keep (derivatives)
    "vwap": "vwap",  # keep (standard finance term)
    # bvolume
    "average_volume": "avg_volume",
    "average_value": "avg_turnover",
    "average_count": "avg_trades",
    "meses": "months",
    # binflation
    "ret_3meses": "return_3m",
    "ret_6meses": "return_6m",
    "ret_12meses": "return_12m",
    "ret_ano": "return_ytd",
    # bdi_cdi
    "acum": "accumulated",
    # bmacro
    "date_ref": None,  # drop: empty / duplicates the DatetimeIndex
}


# bvolume: the shared rename plus symbol -> ticker (the queried key). binflation
# deliberately keeps `symbol` (a list of distinct indices, not a per-entity
# lookup key), so the rename is scoped to bvolume rather than shared.
VOLUME_RENAME: dict[str, str | None] = {**CONTENT_PROXY_RENAME, "symbol": "ticker"}


# ─────────────────────────────────────────────────────────────────────
# Group B: AETP binary endpoints — per-endpoint tag-to-name maps
# ─────────────────────────────────────────────────────────────────────

# bconsensus (already existed, canonicalized here)
CONSENSUS_FIELDS: dict[str, str] = {
    "13019": "buy",
    "13020": "hold",
    "13021": "sell",
    "13022": "total_analysts",
    "13023": "target_low",
    "13024": "target_high",
    "13025": "target_mean",
    "13026": "target_median",
    "13027": "upside_pct",
}

# bcompany() — all companies list
COMPANY_LIST_FIELDS: dict[str, str] = {
    "13004": "cvm_code",
    "13112": "corporate_name",
    "12088": "trade_name",
    "12066": "cnpj",
    "10113": "listing_segment",
    "13824": "logo_url",
    "13798": "sector_id",
    "13799": "subsector_id",
    "13800": "segment_id",
    "13906": "classification",
}

# bcompany(cvm_code) — single company detail
COMPANY_DETAIL_FIELDS: dict[str, str] = {
    "10096": "internal_id",
    "13004": "cvm_code",
    "12066": "cnpj",
    "12063": "name",
    "12088": "corporate_name",
    "12067": "ipo_date",
    "12068": "last_update",
    "13798": "sector_id",
    "13702": "sector",
    "13799": "subsector_id",
    "13703": "subsector",
    "13800": "segment_id",
    "13704": "segment",
    "12087": "cvm_sector",
    "12064": "description",
    "12065": "website",
    "13824": "logo_url",
    "13158": "ticker_prefix",
    "10094": "keywords",
    "13906": "classification",
}

# bindices()
INDEX_FIELDS: dict[str, str] = {
    "14085": "code",
}

# bsectors()
SECTOR_FIELDS: dict[str, str] = {
    "13798": "sector_id",
    "13702": "sector",
    "13799": "subsector_id",
    "13703": "subsector",
    "13800": "segment_id",
    "13704": "segment",
}

# bquote(ticker)
QUOTE_FIELDS: dict[str, str] = {
    "13004": "cvm_code",
    "10068": "ticker",
    "13908": "share_type",
    "13784": "date",
    "13909": "close",
    "13910": "adj_close",
    "13038": "turnover",
    "12075": "total_shares",
    "12073": "float_shares",
    "12074": "treasury_shares",
}

# btickers(cvm_code)
TICKER_FIELDS: dict[str, str] = {
    "13004": "cvm_code",
    "10068": "ticker",
    "13908": "share_type",
}

# bshares(ticker)
SHARES_FIELDS: dict[str, str] = {
    "13004": "cvm_code",
    "10068": "ticker",
    "13908": "share_type",
    "13784": "date",
    "12075": "total_shares",
    "12073": "float_shares",
    "12074": "treasury_shares",
}

# bindicators(cvm, indicator_id, start, end)
INDICATOR_HISTORY_FIELDS: dict[str, str | None] = {
    "13760": "indicator_id",
    "13762": "indicator_name",
    "13763": "label",
    "13784": "date",
    "13016": "value",
    "13764": "frequency",
    "10068": "change_pct",
    "13788": "period_change_pct",
    "13789": None,  # drop: trailing positional filler with no data value
}

# bindicator_meta()
INDICATOR_META_FIELDS: dict[str, str] = {
    "13760": "indicator_id",
    "13761": "active",
    "13762": "name",
    "13763": "category",
    "13764": "frequency",
    "13765": "has_quarterly",
    "13766": "has_annual",
    "13767": "has_ttm",
    "13770": "available_since",
    "13771": "unit",
    "13774": "description",
    # Additional metadata flags
    "13791": "is_percentage",
    "13792": "is_per_share",
    "13785": "normalization",
    "13769": "has_chart",
    "13822": "has_ranking",
    "13823": "has_comparison",
    "13772": "long_description",
    "13773": "calculation_notes",
    "13870": "unit_type",
}

# bcalendar(start, end)
CALENDAR_FIELDS: dict[str, str] = {
    "12024": "event_date",
    "13004": "cvm_code",
    "12063": "company",
    "13824": "logo_url",
    "13702": "sector",
    "13703": "subsector",
    "13704": "segment",
    "13763": "description",
    "13007": "reference_period",
    "10066": "time",
    "13813": "announcement_date",
}

# bdividends(cvm, ticker)
DIVIDEND_FIELDS: dict[str, str] = {
    "12025": "ex_date",
    "10078": "payment_date",
    "12024": "record_date",
    "10081": "type",
    "12053": "value_per_share",
}

# bdy(cvm, ticker, start, end)
DY_FIELDS: dict[str, str | None] = {
    "10078": "date",
    "13893": "price",
    "13155": "ref_date",
    "13894": "dps",
    "13895": "dy_pct",
    "13896": "dps_12m",
    "13897": "dy_12m_pct",
    "13898": None,  # drop: trailing positional filler with no data value
}

# bportfolios()
PORTFOLIO_LIST_FIELDS: dict[str, str] = {
    "10087": "broker_id",
    "13784": "last_updated",
    "10044": "portfolio_name",
}

# bportfolio(broker_id)
PORTFOLIO_FIELDS: dict[str, str] = {
    "10087": "broker_id",
    "13784": "date",
    "13902": "ticker",
    "10068": "portfolio_name",
    "10044": "active",
    "13022": "company",
    "13918": "weight",
    "13025": "sector",
    "13991": "subsector",
    "13982": "segment",
    # Stock classification (B3 sector of the held ticker)
    "13965": "stock_sector_id",
    "13956": "stock_subsector_id",
    "13895": "stock_segment_id",
    "13732": "stock_classification",
    # Recommended stock fields
    "12063": "rec_company",
    "13798": "rec_sector_id",
    "13702": "rec_sector",
    "13799": "rec_subsector_id",
    "13703": "rec_subsector",
    "13800": "rec_segment_id",
    "13704": "rec_segment",
}


# ─────────────────────────────────────────────────────────────────────
# Group C: empty-result schemas (column -> dtype)
#
# Used ONLY to build a schema-preserving empty DataFrame when a valid query
# returns zero rows. The populated frame keeps its coercion-inferred dtypes
# untouched — server dtypes are data-dependent (an all-blank text column
# coerces to float64; an integer column flips int64<->float64 with blanks),
# so forcing a dtype on real data would corrupt it. Two families:
#   - numeric / time-series: float64 columns (concat with populated frames
#     stays numeric instead of upcasting to object)
#   - reference / mixed: object columns named after the field map (the column
#     set is the deliverable; dtypes here are not stable enough to declare)
# ─────────────────────────────────────────────────────────────────────


def _object_schema(fields: dict[str, str | None]) -> dict[str, str]:
    """Empty-frame schema with every named field-map column as object dtype.

    Fields mapped to None are dropped from the populated frame, so they are
    excluded from the schema too.
    """
    return {name: "object" for name in fields.values() if name is not None}


# Numeric time-series (paired with an empty DatetimeIndex)
MACRO_SCHEMA: dict[str, str] = {"close": "float64"}
CDI_SCHEMA: dict[str, str] = {
    "accumulated": "float64",
    "close": "float64",
    "change_pct": "float64",
}
RETURN_SCHEMA: dict[str, str] = {"change_pct": "float64", "close": "float64"}
INTRADAY_BAR_SCHEMA: dict[str, str] = {  # bdi
    "open": "float64",
    "high": "float64",
    "low": "float64",
    "close": "float64",
    "volume": "float64",
    "trades": "float64",
    "turnover": "float64",
    "open_interest": "float64",
    "cum_trades": "float64",
    "session_type": "float64",
}
TICK_SCHEMA: dict[str, str] = {  # bdt
    "close": "float64",
    "size": "float64",
    "trades": "float64",
    "open_interest": "float64",
    "calendar_days": "float64",
    "working_days": "float64",
}

# Numeric reference (RangeIndex)
INFLATION_SCHEMA: dict[str, str] = {
    "symbol": "object",
    **{f"mes{i}": "float64" for i in range(12)},
    "return_3m": "float64",
    "return_6m": "float64",
    "return_12m": "float64",
    "return_ytd": "float64",
}
VOLUME_SCHEMA: dict[str, str] = {
    "ticker": "object",
    "avg_volume": "float64",
    "avg_turnover": "float64",
    "avg_trades": "float64",
    "months": "float64",
    "dat": "float64",
}

# Reference / mixed (RangeIndex, object) — only endpoints that can return empty
COMPANY_LIST_SCHEMA = _object_schema(COMPANY_LIST_FIELDS)
INDEX_SCHEMA = _object_schema(INDEX_FIELDS)
SECTOR_SCHEMA = _object_schema(SECTOR_FIELDS)
INDICATOR_META_SCHEMA = _object_schema(INDICATOR_META_FIELDS)
INDICATOR_HISTORY_SCHEMA = _object_schema(INDICATOR_HISTORY_FIELDS)
CALENDAR_SCHEMA = _object_schema(CALENDAR_FIELDS)
DIVIDEND_SCHEMA = _object_schema(DIVIDEND_FIELDS)
DY_SCHEMA = _object_schema(DY_FIELDS)
PORTFOLIO_LIST_SCHEMA = _object_schema(PORTFOLIO_LIST_FIELDS)

# Single-entity snapshots returned as a one-row DataFrame (RangeIndex)
QUOTE_SCHEMA = _object_schema(QUOTE_FIELDS)
SHARES_SCHEMA = _object_schema(SHARES_FIELDS)
CONSENSUS_SCHEMA: dict[str, str] = {
    "ticker": "object",
    **{name: "float64" for name in CONSENSUS_FIELDS.values()},
}

# bdh_ohlcv — one trading day of OHLCV (DatetimeIndex; ticker added by caller)
DAILY_OHLCV_SCHEMA: dict[str, str] = {
    "close": "float64",
    "settle": "float64",
    "settle_rate": "float64",
    "low": "float64",
    "high": "float64",
    "open": "float64",
    "trades": "float64",
    "volume": "float64",
    "turnover": "float64",
    "open_interest": "float64",
    "vwap": "float64",
    "cum_trades": "float64",
}

# bdh — daily close history, flat/long (DatetimeIndex; ticker added by caller)
BDH_DATA_SCHEMA: dict[str, str] = {
    "close": "float64",
    "settle": "float64",
    "settle_rate": "float64",
    "yield": "float64",
}
