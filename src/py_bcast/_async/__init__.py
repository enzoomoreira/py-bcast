"""Async API for py_bcast.

Provides async versions of all public data-fetching functions,
using ``httpx.AsyncClient`` with connection pooling, caching,
and rate limiting shared with the sync path.

Usage::

    import asyncio
    from py_bcast._async import abhistory, abmacro

    async def main():
        data = await abhistory("PETR4", "20260501", "20260519")
        fx = await abmacro("USDBRL", "20260101", "20260519")

    asyncio.run(main())
"""

from .historical import abhistory, abclose, abdi, abdt, abticks, abfirst_close
from .macro import (
    abmacro,
    abreturn,
    abvolume,
    abinflation,
    abstats,
    abfx,
    absnapshot,
)
from .fixedincome import abtreasury, abtreasury_history, abaccrual, absavings
from .funds import abfund_history, abfund_returns
from .fundamental import (
    abconsensus,
    abcompany,
    abquote,
    abtickers,
    abshares,
    abfree_float,
    abfund_holders,
    abshareholder_dates,
    abfilings,
    abindices,
    absectors,
    abindicators,
    abindicator_meta,
)
from .events import (
    abcalendar,
    abdividends,
    abdy,
    abportfolio,
    abportfolios_with,
)
from .news import abnews, abnews_recent, abnews_multimedia
from .credit import abcds
from .plus import (
    abtrades,
    abinfo,
    abindex_members,
    ablogo,
    abfunds,
    abfund,
    absections,
    abheadlines,
    abnews_content,
    abcorpevents,
    abindexes,
    abholidays,
)

__all__ = [
    "abhistory",
    "abclose",
    "abdi",
    "abdt",
    "abticks",
    "abfirst_close",
    "abmacro",
    "abreturn",
    "abvolume",
    "abinflation",
    "abstats",
    "abfx",
    "absnapshot",
    "abtreasury",
    "abtreasury_history",
    "abaccrual",
    "absavings",
    "abfund_history",
    "abfund_returns",
    "abconsensus",
    "abcompany",
    "abquote",
    "abtickers",
    "abshares",
    "abfree_float",
    "abfund_holders",
    "abshareholder_dates",
    "abfilings",
    "abindices",
    "absectors",
    "abindicators",
    "abindicator_meta",
    "abcalendar",
    "abdividends",
    "abdy",
    "abportfolio",
    "abportfolios_with",
    "abnews",
    "abnews_recent",
    "abnews_multimedia",
    "abcds",
    "abtrades",
    "abinfo",
    "abindex_members",
    "ablogo",
    "abfunds",
    "abfund",
    "absections",
    "abheadlines",
    "abnews_content",
    "abcorpevents",
    "abindexes",
    "abholidays",
]
