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
    "date_ref": "ref_date",
}


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
INDICATOR_HISTORY_FIELDS: dict[str, str] = {
    "13760": "indicator_id",
    "13762": "indicator_name",
    "13763": "label",
    "13784": "date",
    "13016": "value",
    "13764": "frequency",
    "10068": "change_pct",
    "13788": "period_change_pct",
    "13789": "_unused",
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
}

# bcalendar(start, end)
CALENDAR_FIELDS: dict[str, str] = {
    "12024": "event_date",
    "13004": "cvm_code",
    "12063": "company",
    "13824": "sector",
    "13702": "subsector",
    "13703": "segment",
    "13704": "event_type",
    "13763": "description",
    "13007": "announcement_date",
    "10066": "time",
    "13813": "details",
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
DY_FIELDS: dict[str, str] = {
    "10078": "date",
    "13893": "price",
    "13155": "ref_date",
    "13894": "dps",
    "13895": "dy_pct",
    "13896": "dps_12m",
    "13897": "dy_12m_pct",
    "13898": "_unused",
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
}
