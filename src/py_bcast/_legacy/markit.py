"""Pure helpers for the MarkitOutput2 CDS endpoints (credit data).

The I/O side lives in the twin trees ``_legacy/_async/markit.py`` (source) and
``_legacy/_sync/markit.py`` (generated); this module keeps the shared parsing,
entity resolution, and row shaping both import. The wire format is ContentProxy
XML with ``RESPONSE > LIST_RECORD > RECORD`` rows (not the ``TICK`` format of
BaseHistoricaNumerica), with BR-formatted decimals ("135,30").

Endpoint map (see docs/legacy/endpoints.md sec. 8):
    ListaDatas   (13336=C)            -> available dates + per-type flags
    ListaCDS     (10047=date)         -> entities with their (tier, docclause)
    CDS          (10047/13339/13349/13350/13351) -> one term-structure record
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .._core.exceptions import ValidationError
from .._core.normalize import parse_br_number
from .resolve_state import _strip_accents

CDS_TENORS = ("6M", "1Y", "2Y", "3Y", "4Y", "5Y", "7Y", "10Y")

# Term-structure record metadata -> output column.
_CURVE_META_FIELDS = {
    "REGIAO": "region",
    "PAIS": "country",
    "SETOR": "sector",
    "MOEDA": "currency",
    "STANDARD_RECOVERY": "recovery",
    "COMPOSITE_CURVE_RATING": "curve_rating",
    "COMPOSITE_DEPTH_5Y": "depth_5y",
    "RATING_IMPLICITO": "implied_rating",
    "LIQUIDITY_SCORE": "liquidity_score",
}

CDS_ENTITY_SCHEMA: dict[str, str] = {
    "date": "datetime64[ns]",
    "entity": "object",
    "name": "object",
    "cds_type": "object",
    "tier": "object",
    "docclause": "object",
}

CDS_CURVE_SCHEMA: dict[str, str] = {
    "date": "datetime64[ns]",
    "entity": "object",
    "name": "object",
    "cds_type": "object",
    "tier": "object",
    "docclause": "object",
    "tenor": "object",
    "spread": "float64",
    "change_day": "float64",
    "change_month": "float64",
    "bid_ask": "float64",
    "region": "object",
    "country": "object",
    "sector": "object",
    "currency": "object",
    "recovery": "float64",
    "curve_rating": "object",
    "depth_5y": "float64",
    "implied_rating": "object",
    "liquidity_score": "float64",
}


CDS_INDEX_SCHEMA: dict[str, str] = {
    "date": "datetime64[ns]",
    "name": "object",
    "redcode": "object",
    "maturity": "object",
    "composite_price": "float64",
    "bid_ask_price": "float64",
    "composite_spread": "float64",
    "bid_ask_spread": "float64",
    "change_day": "float64",
    "change_month": "float64",
    "depth": "float64",
}

# MarkitOutput2/Indices RECORD field -> output column. The textual fields keep
# their raw Markit values (the maturity stays the "dd-Mon-yy" form the feed
# emits); the rest are BR-formatted decimals parsed at shaping time.
_INDEX_TEXT_FIELDS = {"NOME": "name", "REDCODE": "redcode", "MATURITY": "maturity"}
_INDEX_NUM_FIELDS = {
    "COMPOSITE_PRICE": "composite_price",
    "BID_ASK_PRICE": "bid_ask_price",
    "COMPOSITE_SPREAD": "composite_spread",
    "BID_ASK_SPREAD": "bid_ask_spread",
    "VAR_DIA": "change_day",
    "VAR_MES": "change_month",
    "DEPTH": "depth",
}


def markit_records(root: ET.Element) -> list[dict[str, str]]:
    """Parse ``LIST_RECORD > RECORD`` rows into dicts (tag -> text).

    A benign no-records response carries no LIST_RECORD element and yields [].
    """
    container = root.find("LIST_RECORD")
    if container is None:
        return []
    return [{child.tag: (child.text or "") for child in record} for record in container]


def normalize_cds_type(cds_type: str) -> str:
    """Validate and normalize the CDS type flag (S=sovereign, C=corporate)."""
    normalized = str(cds_type).strip().upper()
    if normalized not in ("S", "C"):
        raise ValidationError(
            f"cds_type must be 'S' (sovereign) or 'C' (corporate), got {cds_type!r}"
        )
    return normalized


def to_iso_date(yyyymmdd: str) -> str:
    """Convert the lib-standard YYYYMMDD date string to Markit's YYYY-MM-DD."""
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}"


def latest_markit_date(date_rows: list[dict[str, str]]) -> str | None:
    """Most recent ListaDatas date overall (used by the CDS index listing).

    ISO dates order lexicographically, so ``max`` is the latest regardless of
    server order. The index feed is not split by sovereign/corporate type.
    """
    dates = [r["DATA"] for r in date_rows if r.get("DATA")]
    return max(dates) if dates else None


def index_records_to_rows(
    records: list[dict[str, str]], date_iso: str
) -> list[dict[str, object]]:
    """Shape MarkitOutput2/Indices RECORD rows into the public columns.

    The ``date`` column carries the resolved ISO date (the per-record DATA is
    the localized "dd-Mon-yy" form); numeric fields are BR-formatted decimals.
    """
    rows: list[dict[str, object]] = []
    for record in records:
        row: dict[str, object] = {"date": date_iso}
        for src, out in _INDEX_TEXT_FIELDS.items():
            row[out] = record.get(src) or ""
        for src, out in _INDEX_NUM_FIELDS.items():
            row[out] = parse_br_number(record.get(src) or "")
        rows.append(row)
    return rows


def latest_cds_date(date_rows: list[dict[str, str]], cds_type: str) -> str | None:
    """Most recent ListaDatas date carrying data for the given CDS type.

    Each row has DATA (ISO) plus per-type availability flags. ISO dates order
    lexicographically, so ``max`` is the latest regardless of server order.
    """
    flag = "SOBERANO" if cds_type == "S" else "CORPORATIVO"
    dates = [r["DATA"] for r in date_rows if r.get(flag) == "1" and r.get("DATA")]
    return max(dates) if dates else None


def _norm(value: str) -> str:
    return _strip_accents(value).strip().upper()


def match_cds_entities(
    entity_rows: list[dict[str, str]],
    entity: str,
    cds_type: str,
    tier: str | None,
    docclause: str | None,
) -> list[dict[str, str]]:
    """Filter ListaCDS rows down to the requested entity/type (and overrides).

    ``entity`` matches the IDCDS code or the display NOME, case- and
    accent-insensitively ("Alemanha" == "ALEMANHA").
    """
    wanted = _norm(entity)
    matches = [
        r
        for r in entity_rows
        if r.get("TIPOCDS") == cds_type
        and (_norm(r.get("IDCDS", "")) == wanted or _norm(r.get("NOME", "")) == wanted)
    ]
    if tier is not None:
        matches = [r for r in matches if r.get("TIER", "").upper() == tier.upper()]
    if docclause is not None:
        matches = [
            r for r in matches if r.get("DOCCLAUSE", "").upper() == docclause.upper()
        ]
    return matches


def pick_cds_entity(matches: list[dict[str, str]], entity: str) -> dict[str, str]:
    """Disambiguate multiple (tier, docclause) listings for one entity.

    Some entities list more than one doc clause for the same tier (e.g.
    Germany under both CR and CR14). The ISDA 2014 Definitions clauses
    (``*14``) are the current market standard, so when exactly one ``*14``
    listing exists it wins; any remaining ambiguity requires an explicit
    ``tier``/``docclause`` from the caller.
    """
    if len(matches) == 1:
        return matches[0]
    modern = [m for m in matches if m.get("DOCCLAUSE", "").upper().endswith("14")]
    if len(modern) == 1:
        return modern[0]
    options = [
        f"(tier={m.get('TIER')!r}, docclause={m.get('DOCCLAUSE')!r})" for m in matches
    ]
    raise ValidationError(
        f"CDS entity {entity!r} is ambiguous; pass tier=/docclause= to pick one "
        f"of: {', '.join(options)}"
    )


def entity_rows_to_records(
    entity_rows: list[dict[str, str]], date_iso: str
) -> list[dict[str, str]]:
    """Shape ListaCDS rows into the public entity-listing columns."""
    return [
        {
            "date": date_iso,
            "entity": r.get("IDCDS", ""),
            "name": r.get("NOME", ""),
            "cds_type": r.get("TIPOCDS", ""),
            "tier": r.get("TIER", ""),
            "docclause": r.get("DOCCLAUSE", ""),
        }
        for r in entity_rows
    ]


def curve_record_to_rows(
    record: dict[str, str],
    chosen: dict[str, str],
    date_iso: str,
) -> list[dict[str, Any]]:
    """Explode the single CDS term-structure record into one row per tenor.

    BR-formatted decimals are parsed here (``parse_br_number``); bare-integer
    fields (e.g. COMPOSITE_DEPTH_5Y) pass through as strings and are coerced by
    ``finalize_frame``.
    """
    meta = {
        out: parse_br_number(record.get(src, ""))
        for src, out in _CURVE_META_FIELDS.items()
    }
    rows: list[dict[str, Any]] = []
    for tenor in CDS_TENORS:
        rows.append(
            {
                "date": date_iso,
                "entity": chosen.get("IDCDS", ""),
                "name": chosen.get("NOME", ""),
                "cds_type": chosen.get("TIPOCDS", ""),
                "tier": chosen.get("TIER", ""),
                "docclause": chosen.get("DOCCLAUSE", ""),
                "tenor": tenor,
                "spread": parse_br_number(record.get(f"SPREAD_{tenor}", "")),
                "change_day": parse_br_number(record.get(f"VAR_DIA_{tenor}", "")),
                "change_month": parse_br_number(record.get(f"VAR_MES_{tenor}", "")),
                "bid_ask": parse_br_number(record.get(f"BID_ASK_{tenor}", "")),
                **meta,
            }
        )
    return rows
