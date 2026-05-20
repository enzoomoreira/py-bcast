"""Instrument database — search 600K+ instruments from local cache."""

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

from .._core.constants import INSTRUMENT_DB_FILENAME, INSTRUMENT_DB_RELPATH, INSTRUMENT_DB_XOR_KEY


class InstrumentDB:
    """
    Local instrument database parsed from bcsys32's aetp_17.dat.

    The file is XOR(0xAE)-encoded TSV containing 600K+ instruments
    from 30+ exchanges worldwide.

    Usage:
        db = InstrumentDB.get()
        db.search("PETR", exchange="BVMF")
        db.lookup("PETR4")
        len(db)        # 623247
        db.exchanges   # {"PR": 189985, "BVMF": 138181, ...}
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
            raise FileNotFoundError(
                f"Instrument database not found: {aetp_path}\n"
                "Ensure Broadcast terminal (bcsys32.exe) has been run at least once."
            )

        raw = aetp_path.read_bytes()
        decoded = bytes([b ^ INSTRUMENT_DB_XOR_KEY for b in raw])
        text = decoded.decode("latin-1")
        lines = text.split('\n')

        tags = lines[0].strip().split('\t')
        idx_305 = tags.index("305") if "305" in tags else None
        idx_10068 = tags.index("10068") if "10068" in tags else None
        idx_10045 = tags.index("10045") if "10045" in tags else None
        idx_303 = tags.index("303") if "303" in tags else None
        idx_10092 = tags.index("10092") if "10092" in tags else None

        col_indices = [i for i in [idx_305, idx_10068, idx_10045, idx_303, idx_10092] if i is not None]
        max_idx = max(col_indices)

        for line in lines[1:]:
            if not line.strip():
                continue
            fields = line.split('\t')
            if len(fields) <= max_idx:
                continue

            full_sym = fields[idx_305] if idx_305 is not None else ""
            ticker = fields[idx_10068] if idx_10068 is not None else ""
            name = fields[idx_10045] if idx_10045 is not None else ""
            isin = fields[idx_303] if idx_303 is not None else ""

            exchange = ""
            if "." in full_sym:
                exchange = full_sym.rsplit(".", 1)[-1]

            self._instruments.append({
                "ticker": ticker,
                "full_symbol": full_sym,
                "name": name,
                "isin": isin,
                "exchange": exchange,
            })

        self._loaded = True

    def search(
        self,
        query: str,
        exchange: str | None = None,
        max_results: int = 20,
    ) -> list[dict[str, str]]:
        """
        Search instruments by ticker, name, or ISIN.

        Args:
            query: Search string (case-insensitive).
            exchange: Filter by exchange (e.g., "BVMF", "GTISFX", "CME").
            max_results: Maximum results to return.

        Returns:
            List of dicts: {ticker, full_symbol, name, isin, exchange}
        """
        q = query.upper()
        exact = []
        starts_with = []
        contains = []

        for inst in self._instruments:
            if exchange and inst["exchange"].upper() != exchange.upper():
                continue

            ticker_up = inst["ticker"].upper()
            if ticker_up == q:
                exact.append(inst)
            elif ticker_up.startswith(q):
                starts_with.append(inst)
            elif q in ticker_up or q in inst["name"].upper() or q in inst["isin"].upper():
                contains.append(inst)
                if len(contains) >= max_results * 10:
                    break

        starts_with.sort(key=lambda r: (not r["ticker"].isalnum(), len(r["ticker"])))
        contains.sort(key=lambda r: (not r["ticker"].isalnum(), len(r["ticker"])))

        return (exact + starts_with + contains)[:max_results]

    def lookup(self, ticker: str) -> dict[str, str] | None:
        """Exact ticker lookup. Returns first match or None."""
        t = ticker.upper()
        for inst in self._instruments:
            if inst["ticker"].upper() == t:
                return inst
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
) -> list[dict[str, str]]:
    """
    Search the local instrument database (600K+ instruments, 30+ exchanges).

    Args:
        query: Search string — matches ticker, name, or ISIN.
        exchange: Filter by exchange (e.g., "BVMF", "GTISFX", "ICEEU").
        max_results: Max results.

    Returns:
        List of instrument dicts: {ticker, full_symbol, name, isin, exchange}

    Example:
        >>> bsearch("PETR", exchange="BVMF")
        [{'ticker': 'PETR3', ...}, {'ticker': 'PETR4', ...}]
        >>> bsearch("VIX", exchange="CBOEI")
        [{'ticker': 'VIX', 'full_symbol': 'I:VIX.CBOEI', ...}]
    """
    return InstrumentDB.get().search(query, exchange=exchange, max_results=max_results)
