"""
py_bcast — Python client for AE Broadcast market data.

A professional, blpapi-like interface for Agência Estado's Broadcast terminal:
- Real-time streaming via DDE (bdp, bdps, subscribe)
- Historical data via HTTP (bdh, bdh_ohlcv, bdt)
- Instrument database search (bsearch, InstrumentDB)

Quick Start:
    from py_bcast import bdp, bdh, bdt, bsearch

    # Real-time quote (requires bcsys32.exe running)
    price = bdp("PETR4", "ULT")

    # Historical daily data
    data = bdh("PETR4", "20260101", "20260520")

    # Tick data (international instruments)
    ticks = bdt("USDBRL", "20260519100000", "20260519110000")

    # Search 600K+ instruments
    bsearch("PETR", exchange="BVMF")
"""

from .client import BroadcastClient, bdp, bdps
from .historical import bdh, bdh_ohlcv, bdt
from .instruments import InstrumentDB, bsearch

__all__ = [
    "BroadcastClient",
    "bdp",
    "bdps",
    "bdh",
    "bdh_ohlcv",
    "bdt",
    "InstrumentDB",
    "bsearch",
]

__version__ = "0.2.0"
