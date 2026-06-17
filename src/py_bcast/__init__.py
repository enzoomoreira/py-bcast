"""
py_bcast — Python client for AE Broadcast market data.

A professional, blpapi-like interface for Agência Estado's Broadcast terminal:
- Real-time streaming via DDE (bdp — one or many tickers)
- Historical data via HTTP (bhistory, bclose, bdt, bdi, bticks, bfirst_close)
- Macroeconomic series (bmacro, breturn, bvolume, binflation, binflation_history)
- Fundamental data (bconsensus, bindicators, bcompany, bstatement_dates)
- Corporate events (bcalendar, bdividends, bdy)
- Reference data (bindices, bsectors, bsector_members, bquote, btickers, bshares)
- Broker portfolios (bportfolio, bportfolios_with)
- News and multimedia (bnews, bnews_recent, bnews_multimedia)
- Credit: CDS term-structure curves and indices via Markit (bcds, bcds_indices)
- Broadcast+ reference: instrument metadata, index composition, logos, broker and exchange registries (binfo, bindex_members, bindexes, blogo, bbrokers, bexchanges)
- Broadcast+ funds: investment-fund search and detail (bfunds, bfund)
- Broadcast+ news: sections, headlines, article content with tagging (bsections, bheadlines, bnews_content)
- Broadcast+ corporate events with adjustment factors (bcorpevents)
- Broadcast+ holiday-table catalog (bholidays)
- Instrument database search (bsearch, InstrumentDB)

Quick Start:
    from py_bcast import bdp, bhistory, bdi, bmacro, bconsensus, bsearch

    # Real-time quote (requires bcsys32.exe running)
    price = bdp("PETR4", "ULT")

    # Historical daily data (close or OHLCV)
    data = bhistory("PETR4", "20260101", "20260520")

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
from ._plus.realtime_async import BroadcastPlusAsyncClient
from ._plus.intraday import btrades
from ._plus.reference import (
    binfo,
    bindex_members,
    bbrokers,
    bexchanges,
    blogo,
    bindexes,
    bholidays,
)
from ._plus.funds import bfunds, bfund
from ._plus.news import bsections, bheadlines, bnews_content
from ._plus.corporate import bcorpevents
from .historical import bhistory, bclose, bdi, bdt, bticks, bfirst_close
from .fundamental import (
    bconsensus,
    bcompany,
    bindices,
    bsectors,
    bsector_members,
    bquote,
    btickers,
    bshares,
    bfree_float,
    bfund_holders,
    bshareholder_dates,
    bstatement_dates,
    bfilings,
    bindicators,
    bindicator_meta,
    bcalendar,
    bdividends,
    bdy,
    bportfolio,
    bportfolios_with,
)
from .instruments import InstrumentDB, bsearch
from .ticker import Ticker
from . import accessor as _accessor  # noqa: F401 — registers the .bcast DataFrame accessor
from .macro import (
    bmacro,
    breturn,
    bvolume,
    binflation,
    binflation_history,
    bstats,
    bfx,
    bsnapshot,
)
from .fixedincome import btreasury, btreasury_history, baccrual, bsavings, bunit_price
from .funds import bfund_history, bfund_returns, bfund_list
from .credit import bcds, bcds_indices
from .news import bnews, bnews_recent, bnews_multimedia, MULTIMEDIA_CATEGORIES
from ._legacy.session import discover_session_token, clear_token_cache
from ._plus.session import discover_plus_token, clear_plus_token_cache
from ._legacy._sync.resolve import resolve_cvm, resolve_indicator
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
    "BroadcastPlusAsyncClient",
    "bdp",
    "bhistory",
    "bclose",
    "bdi",
    "bdt",
    "bticks",
    "bfirst_close",
    # Broadcast+ data functions
    "btrades",
    "binfo",
    "bindex_members",
    "bbrokers",
    "bexchanges",
    "bindexes",
    "blogo",
    "bfunds",
    "bfund",
    "bsections",
    "bheadlines",
    "bnews_content",
    "bcorpevents",
    "bholidays",
    "bconsensus",
    "InstrumentDB",
    "bsearch",
    "Ticker",
    # Macro / Fixed Income
    "bmacro",
    "breturn",
    "bvolume",
    "binflation",
    "bstats",
    "bfx",
    "bsnapshot",
    "binflation_history",
    "btreasury",
    "btreasury_history",
    "baccrual",
    "bsavings",
    "bunit_price",
    "bfund_history",
    "bfund_returns",
    "bfund_list",
    # Reference Data
    "bcompany",
    "bindices",
    "bsectors",
    "bsector_members",
    "bquote",
    "btickers",
    "bshares",
    "bfree_float",
    "bfund_holders",
    "bshareholder_dates",
    "bstatement_dates",
    "bfilings",
    "bindicators",
    "bindicator_meta",
    # Events / Dividends / Portfolios
    "bcalendar",
    "bdividends",
    "bdy",
    "bportfolio",
    "bportfolios_with",
    # News / Multimedia
    "bcds",
    "bcds_indices",
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

__version__ = "0.8.1"
