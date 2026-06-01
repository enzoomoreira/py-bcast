"""Async API for py_bcast.

Provides async versions of all public data-fetching functions,
using ``httpx.AsyncClient`` with connection pooling, caching,
and rate limiting shared with the sync path.

Usage::

    import asyncio
    from py_bcast._async import abdh, abmacro

    async def main():
        data = await abdh("PETR4", "20260501", "20260519")
        fx = await abmacro("USDBRL", "20260101", "20260519")

    asyncio.run(main())
"""

from .historical import abdh, abdh_ohlcv, abdi, abdt
from .macro import abmacro, abdi_cdi, abreturn, abvolume, abinflation
from .fundamental import abconsensus, abcompany, abquote, abtickers, abshares
from .news import abnews, abnews_recent, abnews_multimedia

__all__ = [
    "abdh",
    "abdh_ohlcv",
    "abdi",
    "abdt",
    "abmacro",
    "abdi_cdi",
    "abreturn",
    "abvolume",
    "abinflation",
    "abconsensus",
    "abcompany",
    "abquote",
    "abtickers",
    "abshares",
    "abnews",
    "abnews_recent",
    "abnews_multimedia",
]
