"""EndpointSpec instances — the declarative catalog the executors serve.

One :class:`EndpointSpec` per tabular endpoint. New endpoints (roadmap C) are
added here as data, not as a new sync function + a mirrored async function.
Endpoints are migrated family by family; this module grows as each lands.
"""

from __future__ import annotations

from .columns import (
    CDI_SCHEMA,
    CONSENSUS_FIELDS,
    CONSENSUS_SCHEMA,
    CONTENT_PROXY_RENAME,
    INDICATOR_HISTORY_FIELDS,
    INDICATOR_HISTORY_SCHEMA,
    INFLATION_SCHEMA,
    MACRO_SCHEMA,
    RETURN_SCHEMA,
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

# binflation / abinflation — current inflation indices (single, no params).
SPEC_BINFLATION = EndpointSpec(
    transport="cp_ticks",
    path="BaseHistoricaNumerica/Inflacao",
    index=Index.RANGE,
    rename=CONTENT_PROXY_RENAME,
    schema=INFLATION_SCHEMA,
    timeout=15,
)
