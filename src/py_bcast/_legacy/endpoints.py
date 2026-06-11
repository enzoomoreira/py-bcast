"""EndpointSpec instances — the declarative catalog the executors serve.

One :class:`EndpointSpec` per tabular endpoint. New endpoints (roadmap C) are
added here as data, not as a new sync function + a mirrored async function.
Endpoints are migrated family by family; this module grows as each lands.
"""

from __future__ import annotations

from .columns import (
    CALENDAR_FIELDS,
    CALENDAR_SCHEMA,
    CDI_SCHEMA,
    COMPANY_DETAIL_FIELDS,
    COMPANY_LIST_FIELDS,
    COMPANY_LIST_SCHEMA,
    CONSENSUS_FIELDS,
    CONSENSUS_SCHEMA,
    CONTENT_PROXY_RENAME,
    DIVIDEND_FIELDS,
    DIVIDEND_SCHEMA,
    DY_FIELDS,
    DY_SCHEMA,
    ACCRUAL_SCHEMA,
    BHISTORY_SCHEMA,
    FILINGS_FIELDS,
    FILINGS_SCHEMA,
    FIRST_CLOSE_RENAME,
    FIRST_CLOSE_SCHEMA,
    PORTFOLIO_WITH_SCHEMA,
    SHAREHOLDER_DATES_FIELDS,
    SHAREHOLDER_DATES_SCHEMA,
    SNAPSHOT_RENAME,
    SNAPSHOT_SCHEMA,
    FREE_FLOAT_FIELDS,
    FUND_HISTORY_RENAME,
    FUND_HISTORY_SCHEMA,
    FUND_HOLDER_FIELDS,
    FUND_HOLDER_SCHEMA,
    FUND_RETURNS_RENAME,
    FUND_RETURNS_SCHEMA,
    TREASURY_HISTORY_SCHEMA,
    TREASURY_LAST_RENAME,
    TREASURY_LAST_SCHEMA,
    INDEX_FIELDS,
    INDEX_SCHEMA,
    INDICATOR_HISTORY_FIELDS,
    INDICATOR_HISTORY_SCHEMA,
    INDICATOR_META_FIELDS,
    INDICATOR_META_SCHEMA,
    INFLATION_SCHEMA,
    INTRADAY_BAR_SCHEMA,
    MACRO_SCHEMA,
    PORTFOLIO_FIELDS,
    PORTFOLIO_LIST_FIELDS,
    PORTFOLIO_LIST_SCHEMA,
    RETURN_SCHEMA,
    SECTOR_FIELDS,
    SECTOR_SCHEMA,
    SECTOR_MEMBERS_FIELDS,
    SECTOR_MEMBERS_SCHEMA,
    SHARES_FIELDS,
    SHARES_SCHEMA,
    STATEMENT_DATES_FIELDS,
    STATEMENT_DATES_SCHEMA,
    STATS_RENAME,
    STATS_SCHEMA,
    TICK_SCHEMA,
    TICKER_FIELDS,
    UNIT_PRICE_RENAME,
    UNIT_PRICE_SCHEMA,
    FUND_LIST_FIELDS,
    FUND_LIST_SCHEMA,
    VOLUME_RENAME,
    VOLUME_SCHEMA,
)
from .output import Index
from .spec import EndpointSpec, ParamBind

# bindicators / abindicators — daily indicator history.
# Vectorizes over ticker_or_cvm; the entity tag (13004) resolves a ticker to
# its CVM (digit passthrough), the indicator (13760) resolves a name to its ID
# once, and the window is two date tags. The endpoint echoes the per-row share
# class as the ticker (10068 -> ticker in INDICATOR_HISTORY_FIELDS), so the
# vectorizer does not insert one.
SPEC_BINDICATORS = EndpointSpec(
    transport="aetp",
    path="fundamental/indicador/historico-diario",
    index=Index.RANGE,
    rename=INDICATOR_HISTORY_FIELDS,
    schema=INDICATOR_HISTORY_SCHEMA,
    params=(
        ParamBind("ticker_or_cvm", "13004", "cvm"),
        ParamBind("indicator", "13760", "indicator"),
        ParamBind("start_date", "10057", "date"),
        ParamBind("end_date", "10058", "date"),
    ),
    vectorize_over="ticker_or_cvm",
)

# bconsensus / abconsensus — analyst consensus (binary transport).
# The path is templated with the queried ticker; 13004 is stamped with today's
# date; 10023 is constant. Soft policy: a ticker with no coverage yields an
# empty (schema-typed) record, not an error. The endpoint does not echo a
# ticker, so the vectorizer inserts the queried symbol.
SPEC_BCONSENSUS = EndpointSpec(
    transport="binary",
    path="aefundamental/{ticker}/consenso",
    index=Index.RECORD,
    rename=CONSENSUS_FIELDS,
    schema=CONSENSUS_SCHEMA,
    static_params={"10023": "4"},
    params=(
        ParamBind("ticker", "10068", "none"),
        ParamBind("", "13004", "today"),
    ),
    vectorize_over="ticker",
    timeout=15,
)

# ── fundamental reference (aetp) ──────────────────────────────────────────
# bcompany splits into two specs the wrapper picks between by ``cvm_code``:
# the full list (soft) vs one company's detail (fail-fast). DETAIL stamps the
# CVM code straight into 13004 (no resolution — it already is the code).
SPEC_BCOMPANY_LIST = EndpointSpec(
    transport="aetp",
    path="fundamental/empresa/metadado",
    index=Index.RANGE,
    rename=COMPANY_LIST_FIELDS,
    schema=COMPANY_LIST_SCHEMA,
)

SPEC_BCOMPANY_DETAIL = EndpointSpec(
    transport="aetp",
    path="fundamental/empresa",
    index=Index.RANGE,
    rename=COMPANY_DETAIL_FIELDS,
    empty_ok=False,
    params=(ParamBind("cvm_code", "13004", "none"),),
)

# bindices / bsectors / bindicator_meta — full catalogs, no params, soft.
SPEC_BINDICES = EndpointSpec(
    transport="aetp",
    path="ativos/indice",
    index=Index.RANGE,
    rename=INDEX_FIELDS,
    schema=INDEX_SCHEMA,
)

SPEC_BSECTORS = EndpointSpec(
    transport="aetp",
    path="fundamental/setor",
    index=Index.RANGE,
    rename=SECTOR_FIELDS,
    schema=SECTOR_SCHEMA,
)

SPEC_BINDICATOR_META = EndpointSpec(
    transport="aetp",
    path="fundamental/indicador/metadado",
    index=Index.RANGE,
    rename=INDICATOR_META_FIELDS,
    schema=INDICATOR_META_SCHEMA,
)

# btickers — all share classes for a company. Vectorizes over the lookup id
# (13004 resolves a ticker to its CVM, digit passthrough). Fail-fast. The
# endpoint echoes 10068 -> ticker (the company's symbols), so no insert.
SPEC_BTICKERS = EndpointSpec(
    transport="aetp",
    path="fundamental/ativo/simbolo",
    index=Index.RANGE,
    rename=TICKER_FIELDS,
    empty_ok=False,
    params=(ParamBind("ticker_or_cvm", "13004", "cvm"),),
    vectorize_over="ticker_or_cvm",
)

# bfree_float — share classes with free float and units composition.
# Fail-fast: every listed company has share rows, so a no-records reply means
# the identifier does not resolve to a company. Echoes 305 -> ticker, so the
# vectorizer does not insert one.
SPEC_BFREE_FLOAT = EndpointSpec(
    transport="aetp",
    path="fundamental/empresa/acao",
    index=Index.RANGE,
    rename=FREE_FLOAT_FIELDS,
    empty_ok=False,
    params=(ParamBind("ticker_or_cvm", "13004", "cvm"),),
    vectorize_over="ticker_or_cvm",
)

# bfund_holders — top investment funds holding a company. Vectorizes over the
# ticker/CVM identifier (13004, resolved); the endpoint does not echo a
# ticker, so the vectorizer inserts the queried one. Soft: a company no fund
# holds yields an empty (schema-typed) block.
SPEC_BFUND_HOLDERS = EndpointSpec(
    transport="aetp",
    path="fundamental/carteira/top-fundos",
    index=Index.RANGE,
    rename=FUND_HOLDER_FIELDS,
    schema=FUND_HOLDER_SCHEMA,
    params=(ParamBind("ticker_or_cvm", "13004", "cvm"),),
    vectorize_over="ticker_or_cvm",
)

# bshares — shares outstanding, one record per ticker. Fail-fast; echoes
# 10068 -> ticker, so the vectorizer does not insert one.
SPEC_BSHARES = EndpointSpec(
    transport="aetp",
    path="fundamental/ativo/quantidade",
    index=Index.RECORD,
    rename=SHARES_FIELDS,
    schema=SHARES_SCHEMA,
    empty_ok=False,
    params=(ParamBind("ticker", "10068", "none"),),
    vectorize_over="ticker",
)

# ── fundamental events (aetp) ─────────────────────────────────────────────
# bcalendar — corporate-events calendar over a date window. Single request.
SPEC_BCALENDAR = EndpointSpec(
    transport="aetp",
    path="fundamental/calendario-eventos-corporativos",
    index=Index.RANGE,
    rename=CALENDAR_FIELDS,
    schema=CALENDAR_SCHEMA,
    params=(
        ParamBind("start_date", "10057", "date"),
        ParamBind("end_date", "10058", "date"),
    ),
)

# bdividends — dividend/JCP history. The ticker lands in two tags: 13004 (its
# CVM, resolved) and 10068 (the literal symbol). The endpoint does not echo a
# ticker, so the vectorizer inserts the queried one. BYCVM is the wrapper's
# override path: a caller-supplied CVM is stamped straight into 13004 (no
# resolution), honored only for a single ticker.
SPEC_BDIVIDENDS = EndpointSpec(
    transport="aetp",
    path="fundamental/empresa/eventos/jcp-dividendos",
    index=Index.RANGE,
    rename=DIVIDEND_FIELDS,
    schema=DIVIDEND_SCHEMA,
    params=(
        ParamBind("ticker", "13004", "cvm"),
        ParamBind("ticker", "10068", "none"),
    ),
    vectorize_over="ticker",
)

SPEC_BDIVIDENDS_BYCVM = EndpointSpec(
    transport="aetp",
    path="fundamental/empresa/eventos/jcp-dividendos",
    index=Index.RANGE,
    rename=DIVIDEND_FIELDS,
    schema=DIVIDEND_SCHEMA,
    params=(
        ParamBind("cvm_code", "13004", "none"),
        ParamBind("ticker", "10068", "none"),
    ),
    vectorize_over="ticker",
)

# bdy — dividend-yield series over a date window (10029=1 selects the series).
# Same dual ticker tags + BYCVM override as bdividends. RangeIndex is the
# deliberate contract (decided 2026-06-10): the per-company blocks overlap in
# dates, so a DatetimeIndex would be non-unique.
SPEC_BDY = EndpointSpec(
    transport="aetp",
    path="fundamental/empresa/eventos/dividend-yield",
    index=Index.RANGE,
    rename=DY_FIELDS,
    schema=DY_SCHEMA,
    static_params={"10029": "1"},
    params=(
        ParamBind("ticker", "13004", "cvm"),
        ParamBind("ticker", "10068", "none"),
        ParamBind("start_date", "10057", "date"),
        ParamBind("end_date", "10058", "date"),
    ),
    vectorize_over="ticker",
)

SPEC_BDY_BYCVM = EndpointSpec(
    transport="aetp",
    path="fundamental/empresa/eventos/dividend-yield",
    index=Index.RANGE,
    rename=DY_FIELDS,
    schema=DY_SCHEMA,
    static_params={"10029": "1"},
    params=(
        ParamBind("cvm_code", "13004", "none"),
        ParamBind("ticker", "10068", "none"),
        ParamBind("start_date", "10057", "date"),
        ParamBind("end_date", "10058", "date"),
    ),
    vectorize_over="ticker",
)

# bportfolios_with — full portfolios of every broker whose recommended
# portfolio contains the queried ticker. Single request, single ticker (the
# rows echo 10068 -> ticker as the portfolio's per-row stock, NOT the query,
# so a multi-query would be indistinguishable). Same field set as bportfolio.
# Soft: a ticker no portfolio holds yields an empty (schema-typed) frame.
SPEC_BPORTFOLIOS_WITH = EndpointSpec(
    transport="aetp",
    path="fundamental/empresa/carteira-recomendada/ticker",
    index=Index.RANGE,
    rename=PORTFOLIO_FIELDS,
    schema=PORTFOLIO_WITH_SCHEMA,
    params=(ParamBind("ticker", "10113", "none"),),
)

# bshareholder_dates — dates of the available shareholder compositions.
# Vectorizes over the ticker/CVM identifier; the endpoint does not echo a
# ticker, so the vectorizer inserts the queried one. Soft.
SPEC_BSHAREHOLDER_DATES = EndpointSpec(
    transport="aetp",
    path="fundamental/acionista/datas",
    index=Index.RANGE,
    rename=SHAREHOLDER_DATES_FIELDS,
    schema=SHAREHOLDER_DATES_SCHEMA,
    params=(ParamBind("ticker_or_cvm", "13004", "cvm"),),
    vectorize_over="ticker_or_cvm",
)

# bfilings — financial-statement PDFs (S3 links) over a date window.
# Vectorizes over the ticker/CVM identifier; no ticker echo, so the
# vectorizer inserts the queried one. Soft: a window with no filings is a
# legitimate empty.
SPEC_BFILINGS = EndpointSpec(
    transport="aetp",
    path="fundamental/arquivos/demonstrativos",
    index=Index.RANGE,
    rename=FILINGS_FIELDS,
    schema=FILINGS_SCHEMA,
    params=(
        ParamBind("ticker_or_cvm", "13004", "cvm"),
        ParamBind("start_date", "13916", "date"),
        ParamBind("end_date", "13917", "date"),
    ),
    vectorize_over="ticker_or_cvm",
)

# bportfolio(date=...) — the broker's portfolio AS OF a date. Despite the
# "mudancas" path, the endpoint returns the composition in force on the
# requested date (the latest revision <= date, whose real date the rows
# echo in 13784). A date before the first revision yields no records, which
# is indistinguishable from an unknown broker — hence soft with schema.
SPEC_BPORTFOLIO_AT = EndpointSpec(
    transport="aetp",
    path="fundamental/empresa/carteira-recomendada/mudancas",
    index=Index.RANGE,
    rename=PORTFOLIO_FIELDS,
    schema=PORTFOLIO_WITH_SCHEMA,
    params=(
        ParamBind("broker_id", "10087", "none"),
        ParamBind("date", "13784", "date"),
    ),
)

# bportfolios — brokers that publish model portfolios. Single request.
SPEC_BPORTFOLIOS = EndpointSpec(
    transport="aetp",
    path="fundamental/empresa/carteira-recomendada/corretoras",
    index=Index.RANGE,
    rename=PORTFOLIO_LIST_FIELDS,
    schema=PORTFOLIO_LIST_SCHEMA,
)

# bportfolio — one broker's latest recommended portfolios. Fail-fast; echoes
# 10068 -> ticker (the held stock), so it is single-shot (no vectorize).
SPEC_BPORTFOLIO = EndpointSpec(
    transport="aetp",
    path="fundamental/empresa/carteira-recomendada/ultima",
    index=Index.RANGE,
    rename=PORTFOLIO_FIELDS,
    empty_ok=False,
    params=(ParamBind("broker_id", "10087", "none"),),
)

# ── macro / fixed-income (ContentProxy cp_ticks) ──────────────────────────
# bmacro / abmacro — macro & index series. Vectorizes over the symbol (305),
# which the endpoint does not echo, so the vectorizer inserts it.
SPEC_BMACRO = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/MacroEconomicos",
    index=Index.DATETIME,
    rename=CONTENT_PROXY_RENAME,
    schema=MACRO_SCHEMA,
    cp_sort_by="dat",
    params=(
        ParamBind("ticker", "305", "none"),
        ParamBind("start_date", "DataInicio", "date"),
        ParamBind("end_date", "DataFim", "date"),
    ),
    vectorize_over="ticker",
)

# bdi_cdi / abdi_cdi — accumulated CDI series (single request, no symbol).
SPEC_BDI_CDI = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/DiCetipAcumulado",
    index=Index.DATETIME,
    rename=CONTENT_PROXY_RENAME,
    schema=CDI_SCHEMA,
    cp_sort_by="dat",
    params=(
        ParamBind("start_date", "DataInicio", "date"),
        ParamBind("end_date", "DataFim", "date"),
    ),
)

# breturn / abreturn — adjusted daily returns. Vectorizes over the symbol.
SPEC_BRETURN = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/RetornoDiario",
    index=Index.DATETIME,
    rename=CONTENT_PROXY_RENAME,
    schema=RETURN_SCHEMA,
    cp_sort_by="dat",
    params=(
        ParamBind("ticker", "305", "none"),
        ParamBind("start_date", "DataInicio", "date"),
        ParamBind("end_date", "DataFim", "date"),
    ),
    vectorize_over="ticker",
)

# bvolume / abvolume — average-volume stats. Single request, multi-symbol in
# one tag (10113 join); echoes symbol -> ticker via VOLUME_RENAME.
SPEC_BVOLUME = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/VolumesMedios",
    index=Index.RANGE,
    rename=VOLUME_RENAME,
    schema=VOLUME_SCHEMA,
    params=(ParamBind("tickers", "10113", "join"),),
    timeout=15,
)

# bfund_history — investment-fund quota history. Accepts exchange tickers and
# ANBIMA fund ids ("214248.ANBIMA"); vectorizes over the symbol (305), which
# the endpoint does not echo, so the vectorizer inserts it. 1789 is the
# optional end date (absent -> through today).
SPEC_BFUND_HISTORY = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/Fundos",
    index=Index.DATETIME,
    rename=FUND_HISTORY_RENAME,
    schema=FUND_HISTORY_SCHEMA,
    cp_sort_by="dat",
    params=(
        ParamBind("fund", "305", "none"),
        ParamBind("start_date", "961", "date"),
        ParamBind("end_date", "1789", "date"),
    ),
    vectorize_over="fund",
)

# bfund_returns — per-window fund returns (1d/1m/3m/6m/12m/18m/2y/3y/5y).
# Vectorizes over the symbol; echoes symbol -> ticker, so no insert. "n/d"
# cells are missing-value sentinels (coerce to NaN).
SPEC_BFUND_RETURNS = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/FundosRentabilidade",
    index=Index.RANGE,
    rename=FUND_RETURNS_RENAME,
    schema=FUND_RETURNS_SCHEMA,
    params=(ParamBind("fund", "305", "none"),),
    vectorize_over="fund",
)

# btreasury — last treasury prices (taxa % a.a. + PU). Single request,
# multi-symbol in one tag (10113 join, ".ANBIMA" ids); echoes the bare symbol
# -> ticker. Unknown symbols are omitted (soft).
SPEC_BTREASURY = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/TitulosPublicosUltimos",
    index=Index.RANGE,
    rename=TREASURY_LAST_RENAME,
    schema=TREASURY_LAST_SCHEMA,
    params=(ParamBind("symbols", "10113", "join"),),
)

# btreasury_history — OTC treasury yield history (".TRDM" symbols; values are
# trading yields % a.a., not prices). Vectorizes over the symbol (305), which
# the endpoint does not echo. Trading is sparse — quiet papers return few or
# zero rows.
SPEC_BTREASURY_HISTORY = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/TitulosPublicos",
    index=Index.DATETIME,
    rename=CONTENT_PROXY_RENAME,
    schema=TREASURY_HISTORY_SCHEMA,
    cp_sort_by="dat",
    params=(
        ParamBind("symbol", "305", "none"),
        ParamBind("start_date", "961", "date"),
        ParamBind("end_date", "1789", "date"),
    ),
    vectorize_over="symbol",
)

# baccrual — business-day accrual of a fixed annual rate (13539 = % a.a.,
# compounded over working days/252; verified live: rate=100 over 15 du ->
# 2**(15/252)-1 = 4.21%). Single request; acum -> accumulated.
SPEC_BACCRUAL = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/CalculoTaxaPre",
    index=Index.DATETIME,
    rename=CONTENT_PROXY_RENAME,
    schema=ACCRUAL_SCHEMA,
    cp_sort_by="dat",
    params=(
        ParamBind("rate", "13539", "none"),
        ParamBind("start_date", "961", "date"),
        ParamBind("end_date", "1789", "date"),
    ),
)

# bsavings — accumulated poupanca return over a window. Uses DataInicio/
# DataFim (961 breaks this endpoint with HTTP 500). Single request.
SPEC_BSAVINGS = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/CalculoPoupanca",
    index=Index.DATETIME,
    rename=CONTENT_PROXY_RENAME,
    schema=ACCRUAL_SCHEMA,
    cp_sort_by="dat",
    params=(
        ParamBind("start_date", "DataInicio", "date"),
        ParamBind("end_date", "DataFim", "date"),
    ),
)

# bfx — spot currency conversion (server-side calculation, 1 tick LAST).
# Date params are inert (always the current rate). The facade unwraps the
# single cell to a float; an unknown currency replies "Símbolo inválido",
# which the transport maps to NotFoundError.
SPEC_BFX = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/ConversorMoedas",
    index=Index.RANGE,
    rename=CONTENT_PROXY_RENAME,
    params=(
        ParamBind("from_currency", "Instrumento", "none"),
        ParamBind("to_currency", "Instrumento2", "none"),
        ParamBind("amount", "Valor", "none"),
    ),
)

# bstats / abstats — per-asset market statistics (bid/ask at the close, last
# dividend, dividend yield, 52-week range, average turnover; FIIs add net
# assets). Despite the endpoint name, any B3 symbol works. Single request,
# multi-symbol in one tag (10113 join); echoes cod_broad -> ticker; unknown
# symbols are omitted (soft).
SPEC_BSTATS = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/FIIAnbimaBovespa",
    index=Index.RANGE,
    rename=STATS_RENAME,
    schema=STATS_SCHEMA,
    params=(ParamBind("tickers", "10113", "join"),),
    timeout=15,
)

# bsnapshot — latest intraday session snapshot per symbol (near-real-time
# OHLC, volume, trades). Single request, multi-symbol in one tag (10113
# join); echoes symbol -> ticker; unknown symbols are omitted (soft).
SPEC_BSNAPSHOT = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/UltimosIntraday",
    index=Index.RANGE,
    rename=SNAPSHOT_RENAME,
    schema=SNAPSHOT_SCHEMA,
    params=(ParamBind("tickers", "10113", "join"),),
    timeout=15,
)

# bfirst_close — the symbol's first historical close (adjusted). Takes only
# the bare B3 ticker via the Instrumento param (suffixed forms do not
# resolve). Vectorizes over the ticker; echoes symbol -> ticker, so no
# insert. An unknown ticker replies success with zero ticks (soft).
SPEC_BFIRST_CLOSE = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/FechamentoPrimeiro",
    index=Index.RANGE,
    rename=FIRST_CLOSE_RENAME,
    schema=FIRST_CLOSE_SCHEMA,
    params=(ParamBind("ticker", "Instrumento", "none"),),
    vectorize_over="ticker",
)

# binflation / abinflation — current inflation indices (single, no params).
SPEC_BINFLATION = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/Inflacao",
    index=Index.RANGE,
    rename=CONTENT_PROXY_RENAME,
    schema=INFLATION_SCHEMA,
    timeout=15,
)

# bhistory(fields="close") / bclose — adjusted daily close history over a
# window, one request per ticker (HistoricoDiarioSimbolos serves the whole
# window at once; verified value-identical to the old per-day
# HistoricoFechamentos loop). The echoed symbol is the server's internal
# resolved form (PETR4.BVMF, X:SUSDBRL.GTISFX) — dropped, so the vectorizer
# inserts the caller's own ticker. 1789 is the optional end date.
SPEC_BHISTORY = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/HistoricoDiarioSimbolos",
    index=Index.DATETIME,
    rename={**CONTENT_PROXY_RENAME, "symbol": None},
    schema=BHISTORY_SCHEMA,
    cp_sort_by="dat",
    params=(
        ParamBind("ticker", "10113", "none"),
        ParamBind("start_date", "961", "date"),
        ParamBind("end_date", "1789", "date"),
    ),
    vectorize_over="ticker",
)

# ── historical intraday (ContentProxy cp_ticks) ───────────────────────────
# bdt / abdt — tick-by-tick over a UTC datetime window. The default end
# (start + 1h) is computed by the wrapper, not a resolve policy. The API
# returns newest first (cp_reverse restores chronological order). Vectorizes
# over the symbol (305), which the endpoint does not echo.
SPEC_BDT = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/HistoricoTick",
    index=Index.DATETIME_TIME,
    rename=CONTENT_PROXY_RENAME,
    schema=TICK_SCHEMA,
    cp_reverse=True,
    timeout=60,
    time_col="hor",
    params=(
        ParamBind("ticker", "305", "none"),
        ParamBind("start", "10071", "datetime"),
        ParamBind("end", "10072", "datetime"),
    ),
    vectorize_over="ticker",
)

# bdi / abdi — intraday 2-minute bars from a date to now (10029=4 selects
# bars). Tag 10074 wants YYYYMMDDHHMM where the HHMM tail is required but
# ignored; the wrapper stamps the "0000" suffix, so the bind is verbatim.
SPEC_BDI = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/HistoricoIntraday",
    index=Index.DATETIME_TIME,
    rename=CONTENT_PROXY_RENAME,
    schema=INTRADAY_BAR_SCHEMA,
    static_params={"10029": "4"},
    cp_reverse=True,
    timeout=60,
    time_col="hor",
    params=(
        ParamBind("ticker", "305", "none"),
        ParamBind("bar_start", "10074", "none"),
    ),
    vectorize_over="ticker",
)

# ── fundamental screening / metadata (aetp) ───────────────────────────────
# bsector_members — every company classified under a B3 sector. Single request
# keyed by the top-level sector id (13798); subsector/segment ids return empty.
# The rows do not echo a ticker (the entity is the company's CVM), so no insert.
# Soft: an unpopulated sector id is a legitimate empty frame.
SPEC_BSECTOR_MEMBERS = EndpointSpec(
    transport="aetp",
    path="fundamental/empresa/setores",
    index=Index.RANGE,
    rename=SECTOR_MEMBERS_FIELDS,
    schema=SECTOR_MEMBERS_SCHEMA,
    params=(ParamBind("sector_id", "13798", "none"),),
)

# bstatement_dates — the dates of a company's latest annual (DFP) and quarterly
# (ITR) statements. Vectorizes over the ticker/CVM identifier (13004, resolved);
# the endpoint does not echo a ticker, so the vectorizer inserts the queried
# one. Fail-fast: an unknown identifier yields no record.
SPEC_BSTATEMENT_DATES = EndpointSpec(
    transport="aetp",
    path="fundamental/demonstrativo/ultimo",
    index=Index.RANGE,
    rename=STATEMENT_DATES_FIELDS,
    schema=STATEMENT_DATES_SCHEMA,
    empty_ok=False,
    params=(ParamBind("ticker_or_cvm", "13004", "cvm"),),
    vectorize_over="ticker_or_cvm",
)

# bfund_list — the legacy fund universe (autocomplete dump, ~45k rows). Binary
# transport, no entity params; the facade filters by name client-side. The
# server caches the dump (it serves the whole catalog every call).
SPEC_BFUND_LIST = EndpointSpec(
    transport="binary",
    path="contentProxyOutput/ContentProxyServlet/Fundos/Fundo/buscarFundosAutoComplete",
    index=Index.RANGE,
    rename=FUND_LIST_FIELDS,
    schema=FUND_LIST_SCHEMA,
    static_params={"10023": "4"},
)

# bunit_price — CalculoPreco daily unit-price (PU) + accumulated-return series
# for a fixed-income reference symbol (".ANBIMA"/".TRDM"). Vectorizes over the
# symbol (305), which the endpoint does not echo. 1789 is the optional end date.
SPEC_BUNIT_PRICE = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/CalculoPreco",
    index=Index.DATETIME,
    rename=UNIT_PRICE_RENAME,
    schema=UNIT_PRICE_SCHEMA,
    cp_sort_by="dat",
    params=(
        ParamBind("symbol", "305", "none"),
        ParamBind("start_date", "961", "date"),
        ParamBind("end_date", "1789", "date"),
    ),
    vectorize_over="symbol",
)

# binflation_history — CalculoInflacao accumulated-inflation series for a macro
# inflation symbol (e.g. "AEIPCA", "AEIGPM"). Same accumulated shape as
# baccrual/bsavings (dat -> DatetimeIndex, acum -> accumulated). Vectorizes over
# the symbol (305), which the endpoint does not echo.
SPEC_BINFLATION_HISTORY = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/CalculoInflacao",
    index=Index.DATETIME,
    rename=CONTENT_PROXY_RENAME,
    schema=ACCRUAL_SCHEMA,
    cp_sort_by="dat",
    params=(
        ParamBind("symbol", "305", "none"),
        ParamBind("start_date", "961", "date"),
        ParamBind("end_date", "1789", "date"),
    ),
    vectorize_over="symbol",
)
