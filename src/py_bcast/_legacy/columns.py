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

from .output import is_date_column


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
    "dat": "date",  # session date where it survives as a column (RANGE frames)
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


# bvolume / binflation: the shared rename plus symbol -> ticker (the per-row
# index/symbol becomes the lib-wide entity column). Scoped here rather than in
# CONTENT_PROXY_RENAME because the time-series endpoints have no symbol column.
VOLUME_RENAME: dict[str, str | None] = {**CONTENT_PROXY_RENAME, "symbol": "ticker"}
INFLATION_RENAME: dict[str, str | None] = {**CONTENT_PROXY_RENAME, "symbol": "ticker"}


# bfund_history: Fundos quota history. Accepts exchange tickers (ETFs/FIIs)
# and ANBIMA fund ids (e.g. "214248.ANBIMA", the id bfunds returns); the
# fund-accounting fields (net_asset, inflows/outflows, quote_holders) only
# populate for ANBIMA ids.
FUND_HISTORY_RENAME: dict[str, str | None] = {
    **CONTENT_PROXY_RENAME,
    "raising_day": "inflows",
    "redemption_day": "outflows",
    "total_quote_holder": "quote_holders",
}

# btreasury: TitulosPublicosUltimos last prices. `last` is the trading yield
# (% p.a.), unit_price the PU; the echoed symbol comes back bare (no suffix).
TREASURY_LAST_RENAME: dict[str, str | None] = {
    "symbol": "ticker",
    "dat": "date",
    "last": "rate",
}

# bsnapshot: UltimosIntraday per-symbol session snapshot. hor is the snapshot
# time (overriding the shared drop) and dat the session date.
SNAPSHOT_RENAME: dict[str, str | None] = {
    **CONTENT_PROXY_RENAME,
    "symbol": "ticker",
    "hor": "time",
}

# bfirst_close: FechamentoPrimeiro — the symbol's first historical close
# (adjusted). The shared map drops the empty hor and renames last -> close.
FIRST_CLOSE_RENAME: dict[str, str | None] = {
    **CONTENT_PROXY_RENAME,
    "symbol": "ticker",
}

# bfund_returns: FundosRentabilidade per-window returns. ret_anual is the
# 12-month return (verified against bdh BBSD11 closes, not calendar-year).
FUND_RETURNS_RENAME: dict[str, str | None] = {
    "symbol": "ticker",
    "ret_diario": "return_1d",
    "ret_mensal": "return_1m",
    "ret_3meses": "return_3m",
    "ret_6meses": "return_6m",
    "ret_anual": "return_12m",
    "ret_18meses": "return_18m",
    "ret_2anos": "return_2y",
    "ret_3anos": "return_3y",
    "ret_5anos": "return_5y",
}

# bstats: FIIAnbimaBovespa per-asset market-stats snapshot. Field meanings
# derived from live values cross-checked against sibling endpoints: ulcp/ulvd
# straddle the session close (HGLG11 151.8 <= bdh close 151.83 <= 152.0) and
# mirror the DDE OCP/OVD bid/ask pair; qtct matches EmpresaAcoesUnits
# total_shares for PETR4; pliq/qtct reproduces the FII's net asset value per
# quota (HGLG11 ~224). davl is a sparse FII-only date of unconfirmed meaning.
STATS_RENAME: dict[str, str | None] = {
    "cod_broad": "ticker",
    "ulcp": "bid",
    "dulcp": "bid_date",
    "ulvd": "ask",
    "dulvd": "ask_date",
    "uldv": "last_dividend",
    "duldv": "last_dividend_date",
    "dvyld": "dividend_yield_pct",
    "qtct": "shares_outstanding",
    "min1ano": "low_52w",
    "dmin1ano": "low_52w_date",
    "max1ano": "high_52w",
    "dmax1ano": "high_52w_date",
    "vfult": "turnover_last",
    "vm30d": "avg_turnover_30d",
    "vm100d": "avg_turnover_100d",
    "vm180d": "avg_turnover_180d",
    "qnm180d": "avg_trades_180d",
    "pliq": "net_assets",
    "fnt": "source",
    "davl": None,  # drop: sparse FII-only date, meaning unconfirmed
}

# bunit_price: CalculoPreco daily series for a fixed-income reference symbol
# (".ANBIMA"/".TRDM"). dat is the DatetimeIndex; last is the unit price (PU),
# acum the accumulated return since the window start, var the day's change.
UNIT_PRICE_RENAME: dict[str, str | None] = {
    "last": "unit_price",
    "acum": "accumulated_return",
    "var": "change_pct",
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
# 10113 holds the company's tradable tickers (a ";"-joined list of share
# classes, e.g. "RPAD3;RPAD5;RPAD6"), confirmed from live values — it was
# mislabeled listing_segment. 12066 (cnpj) is a 14-digit zero-padded id kept as
# string by the coerce_numeric_columns leading-zero guard.
COMPANY_LIST_FIELDS: dict[str, str] = {
    "13004": "cvm_code",
    "13112": "corporate_name",
    "12088": "trade_name",
    "12066": "cnpj",
    "10113": "tickers",
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
# Tail re-derived from live PETR4 indicator-50 rows (90 rows, 2 share classes):
#   10068 holds the share class (PETR3/PETR4) — the lib-wide ticker tag, it was
#     mislabeled change_pct. A query echoes both classes of the company, so this
#     column is the per-row symbol (like btickers), not the input identifier.
#   13788 is the day-over-day % change of `value` (13016), verified 88/88 against
#     groupby(ticker).value.pct_change() — it is NOT a price return.
#   13789 tracks neither the value change (29/88) nor the price return (0/46), so
#     its meaning is unconfirmed and it stays dropped (not guessed).
INDICATOR_HISTORY_FIELDS: dict[str, str | None] = {
    "13760": "indicator_id",
    "13762": "indicator_name",
    "13763": "label",
    "13784": "date",
    "13016": "value",
    "13764": "frequency",
    "10068": "ticker",
    "13788": "value_change_pct",
    "13789": None,  # drop: tracks neither value nor price change; unconfirmed
}

# bindicator_meta()
# Text-field tags re-derived from live values (80 rows):
#   13870 = unit ("R$ Milhar", 80/80) — was mislabeled unit_type.
#   13771 = note (availability/calc caveats, 38/80) — was mislabeled unit.
#   13772 = formula (calc expression, e.g. "<ticker>.MCAPT*1000", 11/80) — was
#           mislabeled long_description.
#   13773 = description (prose explaining the indicator, 80/80) — was mislabeled
#           calculation_notes.
#   13774 is a date (2/80) of unconfirmed meaning — dropped, was mislabeled
#           description.
INDICATOR_META_FIELDS: dict[str, str | None] = {
    "13760": "indicator_id",
    "13761": "active",
    "13762": "name",
    "13763": "category",
    "13764": "frequency",
    "13765": "has_quarterly",
    "13766": "has_annual",
    "13767": "has_ttm",
    "13770": "available_since",
    "13771": "note",
    # Additional metadata flags
    "13791": "is_percentage",
    "13792": "is_per_share",
    "13785": "normalization",
    "13769": "has_chart",
    "13822": "has_ranking",
    "13823": "has_comparison",
    "13772": "formula",
    "13773": "description",
    "13870": "unit",
    "13774": None,  # drop: a date (2/80), meaning unconfirmed
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
    # 13898 is populated (numeric, ~4/5 rows) but its meaning is unconfirmed
    # (looks like a period change %); dropped pending an authoritative source
    # rather than guessed.
    "13898": None,
}

# bportfolios()
PORTFOLIO_LIST_FIELDS: dict[str, str] = {
    "10087": "broker_id",
    "13784": "last_updated",
    "10044": "portfolio_name",
}

# bportfolio(broker_id)
# Tag meanings re-derived from live broker-27 rows (65 rows) cross-checked
# against docs/legacy/fields.md. The held ticker is 10068 (the lib-wide ticker
# tag), NOT 13902. The B3 classification columns (sector/subsector/segment and
# their ids) describe the held stock; 12063 (NFANT) is its trade name.
# Fundamentals 13918/13965/13991/13982/13956 are documented in fields.md.
# IMPORTANT: AETP tags are ENDPOINT-SPECIFIC, not global. 13022 is
# total_analysts in CONSENSUS_FIELDS but the buy/neutral recommendation here, so
# a tag's meaning in another map is NOT authoritative. The themed-portfolio
# metrics below are confirmed EMPIRICALLY against this endpoint's live values:
#   13022 -> recommendation ("COMPRA"/"NEUTRA"/...), themed-portfolio rows only.
#   13025 -> target_price: 7/8 rows within 20% of the stock's consensus target.
#   13895 -> dy_pct: matches the stock's 12-month dividend yield (several near
#            exact, e.g. ALOS3 10.0 vs 9.87, ITSA4 9.1 vs 9.37, SBSP3 4.3 vs 4.23).
# 13902 ("10"/"20" portfolio-type code) and 13732 ("N"/"S" flag, redundant with
# portfolio_name) stay dropped — no confirmable meaning, not guessed.
PORTFOLIO_FIELDS: dict[str, str | None] = {
    "10087": "broker_id",
    "13784": "date",
    "10068": "ticker",
    "10044": "portfolio_name",
    "12063": "company",  # NFANT: trade name of the held ticker
    # B3 classification of the held ticker
    "13702": "sector",  # SETB3
    "13798": "sector_id",
    "13703": "subsector",  # SSETB3
    "13799": "subsector_id",
    "13704": "segment",  # SEGB3
    "13800": "segment_id",
    # Fundamentals (sparse; documented in fields.md)
    "13918": "avg_volume_week",  # VMDUSEM: weekly avg volume
    "13965": "eps_quarter",  # LPATC: EPS quarter (consolidated)
    "13991": "eps_12m",  # LPAAC: EPS 12m accumulated
    "13982": "ev_ebitda_12m",  # EVEBDAC: EV/EBITDA 12m accumulated
    "13956": "ev_ebitda_quarter",  # EVEBDTC: EV/EBITDA quarter (consolidated)
    # Themed-portfolio metrics (populated only on the non-PADRAO rows)
    "13022": "recommendation",  # COMPRA/NEUTRA/...
    "13025": "target_price",  # broker target; ~consensus target (7/8 within 20%)
    "13895": "dy_pct",  # 12-month dividend yield (empirical match to bdy)
    # Undocumented tags with unconfirmable meaning — dropped, not guessed
    "13902": None,  # drop: "10"/"20" portfolio-type code, unconfirmed
    "13732": None,  # drop: "N"/"S" flag, redundant with portfolio_name
}


# bfund_holders(ticker_or_cvm) — top investment funds holding a company.
# Tag meanings derived from live cvm=9512 rows: 13154 is the administrator and
# 13144 the manager (CAIXA PETROBRAS fund: 13154=CAIXA ECONOMICA FEDERAL,
# 13144=Caixa DTVM, matching the fund's public records); 10055 is the asset's
# share of the fund's equity (95.4 for that dedicated single-stock fund);
# 13102 is a 14-digit zero-padded CNPJ kept as string by the leading-zero
# guard. 13855/13856 are the position's reference year/month.
FUND_HOLDER_FIELDS: dict[str, str] = {
    "13169": "fund_id",
    "13855": "ref_year",
    "13856": "ref_month",
    "12088": "fund_name",
    "12063": "fund_trade_name",
    "13102": "cnpj",
    "13154": "administrator",
    "13144": "manager",
    "13117": "category",
    "13167": "position_value",
    "13166": "position_quantity",
    "10055": "pct_of_fund",
}

# bfree_float(ticker_or_cvm) — share classes with free float and units
# composition. 12073/12075 reproduces 13827 (free-float %) on every live row
# (PETR, SANB); a unit row (e.g. SANB11) leaves the share counts blank and
# fills 13831/13832 with the ON/PN quantities composing one unit. 12072 is
# blank in all live samples — dropped, not guessed.
FREE_FLOAT_FIELDS: dict[str, str | None] = {
    "305": "ticker",
    "12071": "share_type",
    "12075": "total_shares",
    "12073": "float_shares",
    "12074": "treasury_shares",
    "13827": "float_pct",
    "13831": "unit_on",
    "13832": "unit_pn",
    "12072": None,  # drop: blank in all live samples, meaning unconfirmed
}


# bshareholder_dates(ticker_or_cvm) — shareholder-composition dates. Field
# meanings derived empirically from live PETR/VALE rows: 13784 is always
# January 1st of the base year (12 distinct values across 106 rows) while
# 13815 holds the actual position dates (all distinct, 2015->today).
SHAREHOLDER_DATES_FIELDS: dict[str, str] = {
    "13784": "reference_date",
    "13815": "position_date",
}

# bfilings(ticker_or_cvm, start, end) — financial-statement PDFs. 10057/10058
# echo the requested window (dropped); 13802 is the filing date and 13140 the
# S3 link to the PDF.
FILINGS_FIELDS: dict[str, str | None] = {
    "10057": None,  # drop: echo of the requested start date
    "10058": None,  # drop: echo of the requested end date
    "13802": "date",
    "13140": "url",
}

# bsector_members(sector_id) — every company classified under a B3 sector.
# Mirrors the bcompany list fields plus the B3 hierarchy of the sector and the
# reporting period the row reflects. 13824 is the company logo URL (as in the
# company list); 12088 is the trade name, 13112 the corporate name.
SECTOR_MEMBERS_FIELDS: dict[str, str] = {
    "13004": "cvm_code",
    "12088": "trade_name",
    "13112": "corporate_name",
    "13102": "cnpj",
    "13798": "sector_id",
    "13702": "sector",
    "13799": "subsector_id",
    "13703": "subsector",
    "13800": "segment_id",
    "13704": "segment",
    "13008": "ref_year",
    "13009": "ref_quarter",
    "13265": "period_start",
    "13266": "period_end",
    "13824": "logo_url",
}

# bstatement_dates(ticker_or_cvm) — the dates of a company's most recent annual
# (DFP) and quarterly (ITR) financial statements and when each was disclosed.
# The response carries a second, duplicate block (13750-13759/14081/14082)
# splitting individual vs consolidated views whose assignment is not confirmed
# from the wire, so it is dropped rather than guessed; the kept block is the
# headline last-statement summary. 13006 is the basis of the latest statement
# (C=consolidated, I=individual) and 13007 its type (A=annual, T=quarterly).
STATEMENT_DATES_FIELDS: dict[str, str | None] = {
    "13740": "annual_period_start",
    "13741": "annual_period_end",
    "14079": "annual_disclosed",
    "13744": "quarter_period_start",
    "13745": "quarter_period_end",
    "13747": "quarter",
    "14080": "quarter_disclosed",
    "13006": "basis",
    "13007": "last_type",
    "14083": "last_disclosed",
    # Dropped: the duplicate individual/consolidated block and the redundant
    # year/fiscal-period echoes — kept fields fully describe the last filings.
    "13742": None,
    "13743": None,
    "13746": None,
    "13748": None,
    "13749": None,
    "13825": None,
    "13781": None,
    "13750": None,
    "13751": None,
    "13752": None,
    "13753": None,
    "14081": None,
    "13754": None,
    "13755": None,
    "13756": None,
    "13757": None,
    "13758": None,
    "13759": None,
    "14082": None,
}

# bfund_list(query) — the legacy fund universe (autocomplete dump). 305 is the
# "<id>.ANBIMA" symbol bfund_history/bfund_returns consume; 13103 the bare
# ANBIMA id, 13102 the CNPJ (zero-padded, kept string), 13174 the ANBIMA class.
# The alternate codes (13169 "FI<id>", 13158 "C0000<id>") duplicate the id and
# are dropped; 13154 (administrator) is blank across the dump.
FUND_LIST_FIELDS: dict[str, str | None] = {
    "12088": "name",
    "13112": "legal_name",
    "13103": "anbima_id",
    "13102": "cnpj",
    "305": "symbol",
    "13174": "anbima_class",
    "13154": None,  # drop: administrator, blank across the dump
    "13115": None,  # drop: unconfirmed flag
    "13169": None,  # drop: "FI<id>" code, redundant with symbol/anbima_id
    "13158": None,  # drop: "C0000<id>" code, redundant
    "12069": None,  # drop: blank
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
    """Empty-frame schema from a field map: object dtype, datetime64 for dates.

    Fields mapped to None are dropped from the populated frame, so they are
    excluded from the schema too. Date-named columns (see ``is_date_column``)
    are typed ``datetime64[ns]`` to match the populated frame, where
    ``finalize_frame`` coerces them.
    """
    return {
        name: ("datetime64[ns]" if is_date_column(name) else "object")
        for name in fields.values()
        if name is not None
    }


# Numeric time-series (paired with an empty DatetimeIndex)
MACRO_SCHEMA: dict[str, str] = {"close": "float64"}
FUND_HISTORY_SCHEMA: dict[str, str] = {
    "close": "float64",
    "net_asset": "float64",
    "inflows": "float64",
    "outflows": "float64",
    "total_assets": "float64",
    "quote_holders": "float64",
    "open": "float64",
    "high": "float64",
    "low": "float64",
}
TREASURY_HISTORY_SCHEMA: dict[str, str] = {
    "close": "float64",
    "high": "float64",
    "open": "float64",
    "low": "float64",
    "calendar_days": "float64",
    "working_days": "float64",
    "expiration_date": "datetime64[ns]",
    "unit_price": "float64",
    "stddev": "float64",
}
ACCRUAL_SCHEMA: dict[str, str] = {"accumulated": "float64"}
UNIT_PRICE_SCHEMA: dict[str, str] = {
    "accumulated_return": "float64",
    "unit_price": "float64",
    "change_pct": "float64",
}
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
    "ticker": "object",
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
    "date": "datetime64[ns]",
}
SNAPSHOT_SCHEMA: dict[str, str] = {
    "ticker": "object",
    "date": "datetime64[ns]",
    "time": "object",
    "close": "float64",
    "low": "float64",
    "high": "float64",
    "open": "float64",
    "volume": "float64",
    "trades": "float64",
    "turnover": "float64",
    "open_interest": "float64",
}
FIRST_CLOSE_SCHEMA: dict[str, str] = {
    "ticker": "object",
    "date": "datetime64[ns]",
    "close": "float64",
}
TREASURY_LAST_SCHEMA: dict[str, str] = {
    "ticker": "object",
    "date": "datetime64[ns]",
    "rate": "float64",
    "unit_price": "float64",
}
FUND_RETURNS_SCHEMA: dict[str, str] = {
    "ticker": "object",
    "return_1d": "float64",
    "return_1m": "float64",
    "return_3m": "float64",
    "return_6m": "float64",
    "return_12m": "float64",
    "return_18m": "float64",
    "return_2y": "float64",
    "return_3y": "float64",
    "return_5y": "float64",
}
STATS_SCHEMA: dict[str, str] = {
    "ticker": "object",
    "bid": "float64",
    "bid_date": "datetime64[ns]",
    "ask": "float64",
    "ask_date": "datetime64[ns]",
    "last_dividend": "float64",
    "last_dividend_date": "datetime64[ns]",
    "dividend_yield_pct": "float64",
    "shares_outstanding": "float64",
    "low_52w": "float64",
    "low_52w_date": "datetime64[ns]",
    "high_52w": "float64",
    "high_52w_date": "datetime64[ns]",
    "turnover_last": "float64",
    "avg_turnover_30d": "float64",
    "avg_turnover_100d": "float64",
    "avg_turnover_180d": "float64",
    "source": "object",
    "net_assets": "float64",
    "avg_trades_180d": "float64",
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
FUND_HOLDER_SCHEMA = _object_schema(FUND_HOLDER_FIELDS)
# Shared by bportfolios_with and bportfolio(date=...). Spelled out (not
# _object_schema) so the empty frame matches the populated frames' column
# order, which follows the server's tag order rather than the field map's.
PORTFOLIO_WITH_SCHEMA: dict[str, str] = {
    col: ("datetime64[ns]" if is_date_column(col) else "object")
    for col in (
        "broker_id",
        "date",
        "ticker",
        "portfolio_name",
        "recommendation",
        "avg_volume_week",
        "target_price",
        "eps_quarter",
        "eps_12m",
        "ev_ebitda_quarter",
        "ev_ebitda_12m",
        "dy_pct",
        "company",
        "sector_id",
        "sector",
        "subsector_id",
        "subsector",
        "segment_id",
        "segment",
    )
}
SHAREHOLDER_DATES_SCHEMA = _object_schema(SHAREHOLDER_DATES_FIELDS)
FILINGS_SCHEMA = _object_schema(FILINGS_FIELDS)
SECTOR_MEMBERS_SCHEMA = _object_schema(SECTOR_MEMBERS_FIELDS)
STATEMENT_DATES_SCHEMA = _object_schema(STATEMENT_DATES_FIELDS)
FUND_LIST_SCHEMA = _object_schema(FUND_LIST_FIELDS)

# Single-entity snapshots returned as a one-row DataFrame (RangeIndex)
QUOTE_SCHEMA = _object_schema(QUOTE_FIELDS)
SHARES_SCHEMA = _object_schema(SHARES_FIELDS)
CONSENSUS_SCHEMA: dict[str, str] = {
    "ticker": "object",
    **{name: "float64" for name in CONSENSUS_FIELDS.values()},
}

# bhistory(fields="ohlcv") — one trading day of OHLCV per request
# (DatetimeIndex; ticker added by the core)
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

# bhistory(fields="close") — daily close history, flat/long (DatetimeIndex;
# ticker inserted by the vectorizer). net_asset populates for funds only.
BHISTORY_SCHEMA: dict[str, str] = {
    "close": "float64",
    "settle": "float64",
    "settle_rate": "float64",
    "yield": "float64",
    "net_asset": "float64",
}
