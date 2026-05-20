"""
py_bcast — Python client for AE Broadcast market data.

A professional, blpapi-like interface for Agência Estado's Broadcast terminal:
- Real-time streaming via DDE (bdp, bdps, subscribe)
- Historical data via HTTP (bdh, bdh_ohlcv, bdt, bdi)
- Fundamental data (bconsensus)
- Instrument database search (bsearch, InstrumentDB)

Quick Start:
    from py_bcast import bdp, bdh, bdi, bdt, bconsensus, bsearch

    # Real-time quote (requires bcsys32.exe running)
    price = bdp("PETR4", "ULT")

    # Historical daily data
    data = bdh("PETR4", "20260101", "20260520")

    # Intraday 2-min bars (ALL instruments!)
    bars = bdi("PETR4", "20260519")

    # Tick data (international instruments)
    ticks = bdt("USDBRL", "20260519100000", "20260519110000")

    # Analyst consensus
    consensus = bconsensus("PETR4")

    # Search 600K+ instruments
    bsearch("PETR", exchange="BVMF")
"""

from .client import BroadcastClient, bdp, bdps
from .historical import bdh, bdh_ohlcv, bdi, bdt
from .fundamental import bconsensus
from .instruments import InstrumentDB, bsearch

__all__ = [
    "BroadcastClient",
    "bdp",
    "bdps",
    "bdh",
    "bdh_ohlcv",
    "bdi",
    "bdt",
    "bconsensus",
    "InstrumentDB",
    "bsearch",
]

__version__ = "0.3.0"
