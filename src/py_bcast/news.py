"""News and multimedia content via CentralMultimidia HTTP API."""

from __future__ import annotations

import re
from typing import Optional

from ._constants import BASE_URL
from ._http import create_http_session


# ─────────────────────────────────────────────────────────────────────────────
# Multimedia category IDs (from /CentralMultimidia/ page config)
# ─────────────────────────────────────────────────────────────────────────────

MULTIMEDIA_CATEGORIES = {
    566: "Comentário Agrícola",
    567: "Comentário Financeiro",
    748: "Podcast",
    848: "Comentário Político",
    849: "Cabeça de Gestor",
    857: "E-Investidor-Mídia",
    858: "Ágora-Mídia",
    897: "Tendências Online - Videos",
    898: "Tendências Online - Podcasts",
    997: "Itau BBA - Podcast Prosa Agro",
    1020: "Bradesco - Podcast Insights",
    1104: "Bradesco Asset",
    1105: "Bradesco Asset Cenário",
    1133: "Capital Insights",
    1160: "Crédito Privado 360",
}

_HANDLER_PATH = "/CentralMultimidia/Handlers/MultimediaCenterHandler.ashx"
_CONTENT_PATH = "/CentralMultimidia/Default.aspx/GetVideoContent"


def bnews(news_id: int | str) -> dict:
    """
    Fetch a single news article/content by its numeric ID.

    Works for ALL content types: text news, podcasts, press releases,
    Dow Jones newswires, multimedia, etc. IDs are sequential (currently
    in the 56M range).

    Returns
    -------
    dict with keys:
        - title: Article headline
        - content: HTML body text
        - files: list of dicts with keys (filename, extension, url)
    Empty dict if the ID does not exist.

    Example
    -------
    >>> from py_bcast import bnews
    >>> article = bnews(56134402)
    >>> print(article["title"])
    'Fique de Olho: Azzas contrata Itaú BBA ...'
    """
    s = create_http_session()
    r = s.post(
        f"{BASE_URL}{_CONTENT_PATH}",
        json={"videoId": str(news_id)},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json().get("d")
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


def bnews_latest(count: int = 10) -> list[dict]:
    """
    Fetch the most recent news articles by scanning backwards from the
    current ID ceiling.

    Parameters
    ----------
    count : int
        Number of articles to return (default 10, max 100).

    Returns
    -------
    list of dicts, each with keys: id, title, content, files.
    Ordered most-recent first.

    Example
    -------
    >>> from py_bcast import bnews_latest
    >>> for article in bnews_latest(5):
    ...     print(f"[{article['id']}] {article['title'][:60]}")
    """
    count = min(count, 100)
    ceiling = _find_latest_id()
    if ceiling is None:
        return []

    results = []
    miss_count = 0
    nid = ceiling
    while len(results) < count and miss_count < 20:
        article = bnews(nid)
        if article:
            article["id"] = nid
            results.append(article)
            miss_count = 0
        else:
            miss_count += 1
        nid -= 1

    return results


def bnews_search(category: int, days_ago: int = 60, limit: int = 20) -> list[dict]:
    """
    List multimedia/podcast content from a specific category.

    Parameters
    ----------
    category : int
        Category ID (see MULTIMEDIA_CATEGORIES for available IDs).
    days_ago : int
        How many days back to search (default 60).
    limit : int
        Max results to return (default 20).

    Returns
    -------
    list of dicts with keys: id, title, date, time.

    Example
    -------
    >>> from py_bcast import bnews_search, MULTIMEDIA_CATEGORIES
    >>> items = bnews_search(748)  # Podcasts
    >>> for item in items[:3]:
    ...     print(f"[{item['id']}] {item['date']} {item['title'][:50]}")
    """
    s = create_http_session()
    r = s.get(
        f"{BASE_URL}{_HANDLER_PATH}",
        params={
            "category": str(category),
            "daysAgo": str(days_ago),
            "limit": str(limit),
        },
        timeout=10,
    )
    r.raise_for_status()

    results = []
    # Parse XML response
    items = re.findall(
        r"<File><Id>(\d+)</Id><Title><!\[CDATA\[(.*?)\]\]></Title>"
        r"<Date>(.*?)</Date><Time>(.*?)</Time></File>",
        r.text,
    )
    for fid, title, date, time_ in items:
        results.append({
            "id": int(fid),
            "title": title,
            "date": date,
            "time": time_,
        })

    return results


def _find_latest_id() -> Optional[int]:
    """Binary search for the latest valid news ID."""
    s = create_http_session()
    # Start from a known-good ID and search upward
    lo, hi = 56_000_000, 58_000_000

    # Verify lo is valid
    r = s.post(
        f"{BASE_URL}{_CONTENT_PATH}",
        json={"videoId": str(lo)},
        headers={"Content-Type": "application/json"},
        timeout=5,
    )
    if r.status_code != 200:
        return None
    data = r.json().get("d")
    if not data or not data.get("Title"):
        return None

    while hi - lo > 1:
        mid = (lo + hi) // 2
        r = s.post(
            f"{BASE_URL}{_CONTENT_PATH}",
            json={"videoId": str(mid)},
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        if r.status_code == 200:
            d = r.json().get("d")
            if d and d.get("Title"):
                lo = mid
            else:
                hi = mid
        else:
            hi = mid

    return lo
