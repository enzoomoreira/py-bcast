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
    FREE_FLOAT_FIELDS,
    FUND_HOLDER_FIELDS,
    FUND_HOLDER_SCHEMA,
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
    SHARES_FIELDS,
    SHARES_SCHEMA,
    STATS_RENAME,
    STATS_SCHEMA,
    TICK_SCHEMA,
    TICKER_FIELDS,
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
# Same dual ticker tags + BYCVM override as bdividends. RangeIndex is preserved
# (the docstring says DatetimeIndex but the code uses RangeIndex; fixing that
# is a separate behavior-change pass, not this migration).
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

# binflation / abinflation — current inflation indices (single, no params).
SPEC_BINFLATION = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/Inflacao",
    index=Index.RANGE,
    rename=CONTENT_PROXY_RENAME,
    schema=INFLATION_SCHEMA,
    timeout=15,
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
