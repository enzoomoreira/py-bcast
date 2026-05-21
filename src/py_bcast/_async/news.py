"""Async news functions."""

from __future__ import annotations

import asyncio
import json
from typing import Optional

from .._core.constants import BASE_URL
from .._core.http import get_async_http_client
from .._core.logging import get_logger
from .._core.ratelimit import rate_limit_async

logger = get_logger(__name__)

_CONTENT_PATH = "/CentralMultimidia/Default.aspx/GetVideoContent"
_HANDLER_PATH = "/CentralMultimidia/Handlers/MultimediaCenterHandler.ashx"


def _decode_json(r) -> dict:
    """Decode JSON from response, handling latin-1 encoded bodies."""
    try:
        return r.json()
    except (UnicodeDecodeError, ValueError):
        text = r.content.decode("latin-1")
        return json.loads(text)


async def abnews(news_id: int | str) -> dict:
    """Async version of ``bnews``. Fetch a single news article."""
    s = get_async_http_client()
    await rate_limit_async()
    r = await s.post(
        f"{BASE_URL}{_CONTENT_PATH}",
        json={"videoId": str(news_id)},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    r.raise_for_status()
    data = _decode_json(r).get("d")
    if not data or not data.get("Title"):
        return {}

    files = []
    for f in data.get("FileCollection") or []:
        files.append({
            "filename": f.get("FileName", ""),
            "extension": f.get("Extension", ""),
            "url": f.get("Url") or f.get("FilePath", ""),
        })

    return {
        "title": data.get("Title", ""),
        "content": data.get("Content", ""),
        "files": files,
    }


async def abnews_latest(count: int = 10) -> list[dict]:
    """Async version of ``bnews_latest``.

    Uses asyncio.gather for parallel fetches — significantly faster
    than the sequential sync version.
    """
    count = min(count, 100)
    ceiling = await _async_find_latest_id()
    if ceiling is None:
        return []

    # Fetch in parallel batches
    batch_size = 10
    results = []
    miss_count = 0
    nid = ceiling

    while len(results) < count and miss_count < 20:
        batch_ids = list(range(nid, max(nid - batch_size, nid - (count - len(results)) - 20), -1))
        tasks = [abnews(bid) for bid in batch_ids]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        for bid, article in zip(batch_ids, batch_results):
            if isinstance(article, Exception):
                miss_count += 1
                continue
            if article:
                article["id"] = bid
                results.append(article)
                miss_count = 0
            else:
                miss_count += 1
            if len(results) >= count:
                break

        nid = batch_ids[-1] - 1
        if not batch_ids:
            break

    return results[:count]


async def abnews_search(category: int, days_ago: int = 60, limit: int = 20) -> list[dict]:
    """Async version of ``bnews_search``."""
    import re
    s = get_async_http_client()
    await rate_limit_async()
    r = await s.get(
        f"{BASE_URL}{_HANDLER_PATH}",
        params={"category": str(category), "daysAgo": str(days_ago), "limit": str(limit)},
        timeout=10,
    )
    r.raise_for_status()

    results = []
    items = re.findall(
        r"<File><Id>(\d+)</Id><Title><!\[CDATA\[(.*?)\]\]></Title>"
        r"<Date>(.*?)</Date><Time>(.*?)</Time></File>",
        r.text,
    )
    for fid, title, date, time_ in items:
        results.append({"id": int(fid), "title": title, "date": date, "time": time_})
    return results


async def _async_find_latest_id() -> Optional[int]:
    """Async binary search for the latest valid news ID."""
    s = get_async_http_client()
    lo, hi = 56_100_000, 56_500_000

    await rate_limit_async()
    r = await s.post(
        f"{BASE_URL}{_CONTENT_PATH}",
        json={"videoId": str(lo)},
        headers={"Content-Type": "application/json"},
        timeout=5,
    )
    if r.status_code != 200:
        return None
    data = _decode_json(r).get("d")
    if not data or not data.get("Title"):
        return None

    while hi - lo > 1:
        mid = (lo + hi) // 2
        await rate_limit_async()
        try:
            r = await s.post(
                f"{BASE_URL}{_CONTENT_PATH}",
                json={"videoId": str(mid)},
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
        except Exception:
            hi = mid
            continue
        if r.status_code == 200:
            d = _decode_json(r).get("d")
            if d and d.get("Title"):
                lo = mid
            else:
                hi = mid
        else:
            hi = mid

    return lo
