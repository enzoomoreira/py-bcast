"""
py_bcast — Python client for AE Broadcast market data.

A professional, blpapi-like interface for Agência Estado's Broadcast terminal:
- Real-time streaming via DDE (bdp — one or many tickers)
- Historical data via HTTP (bdh, bdh_ohlcv, bdt, bdi)
- Macroeconomic series (bmacro, bdi_cdi, breturn, bvolume, binflation)
- Fundamental data (bconsensus, bindicators, bcompany)
- Corporate events (bcalendar, bdividends, bdy)
- Reference data (bindices, bsectors, bquote, btickers, bshares)
- Broker portfolios (bportfolios, bportfolio)
- News and multimedia (bnews, bnews_recent, bnews_multimedia)
- Instrument database search (bsearch, InstrumentDB)

Quick Start:
    from py_bcast import bdp, bdh, bdi, bmacro, bconsensus, bsearch

    # Real-time quote (requires bcsys32.exe running)
    price = bdp("PETR4", "ULT")

    # Historical daily data
    data = bdh("PETR4", "20260101", "20260520")

    # Intraday 2-min bars (ALL instruments!)
    bars = bdi("PETR4", "20260519")

    # Macroeconomic series (FX, indices, rates)
    fx = bmacro("USDBRL", "20260101", "20260520")

    # Analyst consensus
    consensus = bconsensus("PETR4")

    # Dividends history
    from py_bcast import bdividends
    divs = bdividends("PETR4")

    # News articles (no auth required!)
    from py_bcast import bnews, bnews_recent
    article = bnews(56134402)
    latest = bnews_recent(5)

    # Search 600K+ instruments
    bsearch("PETR", exchange="BVMF")
"""

from .realtime import BroadcastClient, bdp
from ._plus.realtime import BroadcastPlusClient
from ._plus.intraday import btrades
from .historical import bdh, bdh_ohlcv, bdi, bdt
from .fundamental import (
    bconsensus,
    bcompany,
    bindices,
    bsectors,
    bquote,
    btickers,
    bshares,
    bindicators,
    bindicator_meta,
    bcalendar,
    bdividends,
    bdy,
    bportfolios,
    bportfolio,
)
from .instruments import InstrumentDB, bsearch
from .macro import bmacro, bdi_cdi, breturn, bvolume, binflation
from .news import bnews, bnews_recent, bnews_multimedia, MULTIMEDIA_CATEGORIES
from ._core.session import discover_session_token, clear_token_cache
from ._plus.session import discover_plus_token, clear_plus_token_cache
from ._core.resolve import resolve_cvm, resolve_indicator
from ._core.exceptions import (
    PyBcastError,
    SessionError,
    ContentProxyError,
    ProtocolError,
    DDEError,
    DDEAdviseError,
    ValidationError,
    NotFoundError,
    BroadcastPlusError,
    BroadcastPlusAuthError,
)
from ._core.constants import DMLERR_ADVACKTIMEOUT, DMLERR_NAMES
from ._core.logging import configure_logging
from ._core.config import configure, get_settings, Settings
from ._core.cache import invalidate as cache_invalidate
from . import _async as async_api

__all__ = [
    "BroadcastClient",
    "BroadcastPlusClient",
    "bdp",
    "bdh",
    "bdh_ohlcv",
    "bdi",
    "bdt",
    # Broadcast+ data functions
    "btrades",
    "bconsensus",
    "InstrumentDB",
    "bsearch",
    # Macro / Fixed Income
    "bmacro",
    "bdi_cdi",
    "breturn",
    "bvolume",
    "binflation",
    # Reference Data
    "bcompany",
    "bindices",
    "bsectors",
    "bquote",
    "btickers",
    "bshares",
    "bindicators",
    "bindicator_meta",
    # Events / Dividends / Portfolios
    "bcalendar",
    "bdividends",
    "bdy",
    "bportfolios",
    "bportfolio",
    # News / Multimedia
    "bnews",
    "bnews_recent",
    "bnews_multimedia",
    "MULTIMEDIA_CATEGORIES",
    "discover_session_token",
    "clear_token_cache",
    # Broadcast+ session
    "discover_plus_token",
    "clear_plus_token_cache",
    "resolve_cvm",
    "resolve_indicator",
    # Exceptions
    "PyBcastError",
    "SessionError",
    "ContentProxyError",
    "ProtocolError",
    "DDEError",
    "DDEAdviseError",
    "ValidationError",
    "NotFoundError",
    "BroadcastPlusError",
    "BroadcastPlusAuthError",
    # DDE constants
    "DMLERR_ADVACKTIMEOUT",
    "DMLERR_NAMES",
    # Logging
    "configure_logging",
    # Configuration
    "configure",
    "get_settings",
    "Settings",
    "cache_invalidate",
    # Async API namespace
    "async_api",
]

__version__ = "0.5.0"
