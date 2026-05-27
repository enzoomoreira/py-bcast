"""Instrument database — search 600K+ instruments from local cache."""

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from .._core.constants import (
    INSTRUMENT_DB_FILENAME,
    INSTRUMENT_DB_RELPATH,
    INSTRUMENT_DB_XOR_KEY,
    normalize_exchange,
)
from .._core.logging import get_logger

logger = get_logger(__name__)

# Stable column order for any bsearch / lookup result. Plus-only or
# legacy-only columns are filled with pd.NA when the active backend
# doesn't provide them.
INSTRUMENT_COLUMNS = [
    "ticker",
    "name",
    "exchange",
    "backend",
    "full_symbol",
    "isin",
    "cvm_code",
    "type_id",
    "market_id",
    "exchange_id",
    "has_intraday",
    "has_daily",
    "is_realtime",
]

_DTYPES: dict[str, str] = {
    "ticker": "string",
    "name": "string",
    "exchange": "string",
    "backend": "category",
    "full_symbol": "string",
    "isin": "string",
    "cvm_code": "Int64",
    "type_id": "Int64",
    "market_id": "Int64",
    "exchange_id": "Int64",
    "has_intraday": "boolean",
    "has_daily": "boolean",
    "is_realtime": "boolean",
}


def _empty_record(backend: str) -> dict[str, Any]:
    """Build a record dict with every column set to None, except `backend`."""
    rec: dict[str, Any] = dict.fromkeys(INSTRUMENT_COLUMNS)
    rec["backend"] = backend
    return rec


def _to_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Materialize a list of normalized records into a typed DataFrame."""
    df = pd.DataFrame(rows, columns=INSTRUMENT_COLUMNS)
    return df.astype(_DTYPES)


class InstrumentDB:
    """Local instrument database parsed from bcsys32's aetp_17.dat.

    The file is XOR(0xAE)-encoded TSV containing 600K+ instruments
    from 30+ exchanges worldwide.

    Usage::

        db = InstrumentDB.get()
        db.search("PETR", exchange="BVMF")   # -> pd.DataFrame
        db.lookup("PETR4")                    # -> dict | None
        len(db)                               # 623247
        db.exchanges                          # {"PR": 189985, ...}
    """

    _instance: InstrumentDB | None = None
    _instruments: list[dict[str, str]]
    _loaded: bool = False

    def __init__(self):
        self._instruments = []

    @classmethod
    def get(cls) -> InstrumentDB:
        """Singleton accessor — loads DB on first call."""
        if cls._instance is None:
            cls._instance = cls()
        if not cls._instance._loaded:
            cls._instance._load()
        return cls._instance

    def _load(self):
        data_dir = Path(os.environ.get("APPDATA", "")) / INSTRUMENT_DB_RELPATH
        aetp_path = data_dir / INSTRUMENT_DB_FILENAME

        if not aetp_path.exists():
            logger.error("Instrument database not found: %s", aetp_path)
            raise FileNotFoundError(
                f"Instrument database not found: {aetp_path}\n"
                "Ensure Broadcast terminal (bcsys32.exe) has been run at least once."
            )

        raw = aetp_path.read_bytes()
        decoded = bytes([b ^ INSTRUMENT_DB_XOR_KEY for b in raw])
        text = decoded.decode("latin-1")
        lines = text.split("\n")

        tags = lines[0].strip().split("\t")
        idx_305 = tags.index("305") if "305" in tags else None
        idx_10068 = tags.index("10068") if "10068" in tags else None
        idx_10045 = tags.index("10045") if "10045" in tags else None
        idx_303 = tags.index("303") if "303" in tags else None
        idx_10092 = tags.index("10092") if "10092" in tags else None

        col_indices = [
            i
            for i in [idx_305, idx_10068, idx_10045, idx_303, idx_10092]
            if i is not None
        ]
        max_idx = max(col_indices)

        for line in lines[1:]:
            if not line.strip():
                continue
            fields = line.split("\t")
            if len(fields) <= max_idx:
                continue

            full_sym = fields[idx_305] if idx_305 is not None else ""
            ticker = fields[idx_10068] if idx_10068 is not None else ""
            name = fields[idx_10045] if idx_10045 is not None else ""
            isin = fields[idx_303] if idx_303 is not None else ""

            exchange = ""
            if "." in full_sym:
                exchange = full_sym.rsplit(".", 1)[-1]

            self._instruments.append(
                {
                    "ticker": ticker,
                    "full_symbol": full_sym,
                    "name": name,
                    "isin": isin,
                    "exchange": exchange,
                }
            )

        self._loaded = True
        logger.info(
            "Instrument database loaded: %d instruments", len(self._instruments)
        )

    def _to_record(self, inst: dict[str, str]) -> dict[str, Any]:
        """Convert internal storage dict to a unified-schema record."""
        rec = _empty_record("legacy")
        rec["ticker"] = inst["ticker"]
        rec["name"] = inst["name"]
        rec["exchange"] = inst["exchange"]
        rec["full_symbol"] = inst["full_symbol"]
        rec["isin"] = inst["isin"]
        return rec

    def search(
        self,
        query: str,
        exchange: str | None = None,
        max_results: int = 20,
    ) -> pd.DataFrame:
        """Search instruments by ticker, name, or ISIN.

        Args:
            query: Search string (case-insensitive).
            exchange: Filter by exchange code (e.g. "BVMF", "CME", "ICEEU").
            max_results: Maximum results to return.

        Returns:
            DataFrame with columns defined in INSTRUMENT_COLUMNS. Plus-only
            columns are pd.NA for legacy results.
        """
        q = query.upper()
        exact: list[dict[str, str]] = []
        starts_with: list[dict[str, str]] = []
        contains: list[dict[str, str]] = []

        for inst in self._instruments:
            if exchange and inst["exchange"].upper() != exchange.upper():
                continue

            ticker_up = inst["ticker"].upper()
            if ticker_up == q:
                exact.append(inst)
            elif ticker_up.startswith(q):
                starts_with.append(inst)
            elif (
                q in ticker_up or q in inst["name"].upper() or q in inst["isin"].upper()
            ):
                contains.append(inst)
                if len(contains) >= max_results * 10:
                    break

        starts_with.sort(key=lambda r: (not r["ticker"].isalnum(), len(r["ticker"])))
        contains.sort(key=lambda r: (not r["ticker"].isalnum(), len(r["ticker"])))

        ranked = (exact + starts_with + contains)[:max_results]
        return _to_frame([self._to_record(i) for i in ranked])

    def lookup(self, ticker: str) -> dict[str, Any] | None:
        """Exact ticker lookup. Returns a unified-schema dict or None."""
        t = ticker.upper()
        for inst in self._instruments:
            if inst["ticker"].upper() == t:
                return self._to_record(inst)
        return None

    @property
    def exchanges(self) -> dict[str, int]:
        """Exchange -> instrument count mapping, sorted by count descending."""
        return dict(Counter(i["exchange"] for i in self._instruments).most_common())

    def __len__(self) -> int:
        return len(self._instruments)


def bsearch(
    query: str,
    exchange: str | None = None,
    max_results: int = 20,
) -> pd.DataFrame:
    """Search for instruments by ticker, name, or ISIN.

    Routes automatically to the active backend (see ``_core.routing``).
    The return schema is the same for both backends — columns specific to
    one backend appear as ``pd.NA`` in rows from the other.

    Columns:
        Always present:
            ``ticker``, ``name``, ``exchange`` (legacy code), ``backend``.
        Legacy-only (NA on Plus):
            ``full_symbol``, ``isin``.
        Plus-only (NA on legacy):
            ``cvm_code``, ``type_id``, ``market_id``, ``exchange_id``,
            ``has_intraday``, ``has_daily``, ``is_realtime``.

    Args:
        query: Search string (case-insensitive).
        exchange: Filter by exchange code. Legacy filters in-memory;
                  Plus ignores this (server-side search).
        max_results: Maximum number of results to return.

    Returns:
        DataFrame with stable columns. Empty DataFrame on no matches.

    Example::

        >>> from py_bcast import bsearch, configure
        >>> bsearch("PETR", exchange="BVMF")           # legacy
        >>> configure(terminal="plus")
        >>> bsearch("PETRO", max_results=5)             # plus
    """
    from .._core.routing import get_active_terminal

    if get_active_terminal() == "plus":
        return _bsearch_plus(query, max_results)
    return InstrumentDB.get().search(query, exchange=exchange, max_results=max_results)


def _bsearch_plus(query: str, max_results: int) -> pd.DataFrame:
    """Search instruments via the Broadcast+ REST API."""
    from .._plus.http import plus_request

    r = plus_request(
        "post",
        "/stock/v1/quote/symbol/search",
        json={"query": query, "limit": max_results},
    )
    data = r.json()
    symbols = data.get("symbols") or []

    rows: list[dict[str, Any]] = []
    for s in symbols[:max_results]:
        exch = s.get("exchange") or {}
        rec = _empty_record("plus")
        rec["ticker"] = s.get("code", "")
        rec["name"] = s.get("description", "")
        rec["exchange"] = normalize_exchange(exch.get("name", ""))
        rec["exchange_id"] = exch.get("id")
        rec["cvm_code"] = s.get("cvmCode")
        rec["type_id"] = s.get("typeId")
        rec["market_id"] = s.get("marketId")
        rec["has_intraday"] = s.get("hasIntraday")
        rec["has_daily"] = s.get("hasDaily")
        rec["is_realtime"] = s.get("isRealTime")
        rows.append(rec)

    return _to_frame(rows)
