"""News via Broadcast+ REST: section catalog, headlines, article content.

A Broadcast+ capability distinct from the legacy ``bnews`` (which fetches one
CentralMultimidia article by a 56M-range id). The Plus feed is section-based:
``bsections`` lists sections, ``bheadlines`` pulls paginated headlines, and
``bnews_content`` returns an article's body with structured tagging (authors,
entities, topics, subjects).
"""

from __future__ import annotations

import pandas as pd

from .._core.normalize import ensure_id_list
from .._core.validation import validate_params
from ._sync.news import content_core, headlines_core, sections_core


def bsections() -> pd.DataFrame:
    """List available Broadcast+ news sections.

    Requires Broadcast+ backend — configure(terminal='plus'),
    configure(terminal='auto') with Broadcast+.exe running, or
    configure(plus_login=..., plus_password=...) for headless login.

    Returns:
        Flat DataFrame with columns: id (section id, for ``bheadlines``), name,
        service, minutes, is_top_news, is_most_read, is_consolidated.

    Example:
        >>> from py_bcast import bsections, configure
        >>> configure(terminal="plus")
        >>> bsections()[["id", "name"]].head()
    """
    return sections_core()


@validate_params
def bheadlines(sections: int | list[int], count: int = 50) -> pd.DataFrame:
    """Fetch recent news headlines for one or more sections via Broadcast+.

    Requires Broadcast+ backend (see ``bsections``).

    Args:
        sections: One section id or a list (from ``bsections``).
        count: Maximum number of headlines to return, newest first (the client
            walks pages of 100 server-side until reached or the feed ends).

    Returns:
        Flat DataFrame, newest first, with columns: id (content id, for
        ``bnews_content``), time (Sao Paulo tz-aware), title, sentiment,
        section_id, section_name, service, is_fast, is_highlight. Empty
        DataFrame with the same schema if the sections have no headlines.

    Example:
        >>> from py_bcast import bheadlines, configure
        >>> configure(terminal="plus")
        >>> bheadlines(10, count=20)[["time", "title", "sentiment"]]
    """
    return headlines_core([int(s) for s in ensure_id_list(sections)], count)


@validate_params
def bnews_content(content_id: int | str) -> dict:
    """Fetch a Broadcast+ article's body and structured tagging by id.

    Requires Broadcast+ backend (see ``bsections``).

    Args:
        content_id: Content id (the ``id`` column from ``bheadlines``).

    Returns:
        dict with keys: id, title, time, sentiment, section_id, section_name,
        body (HTML), has_audio, has_pdf, has_video, and tagging (a dict of
        authors, entities, locations, topics, subjects).

    Raises:
        NotFoundError: If the id does not exist or is not accessible.

    Example:
        >>> from py_bcast import bnews_content, configure
        >>> configure(terminal="plus")
        >>> art = bnews_content("56345310")
        >>> art["tagging"]["entities"]
    """
    return content_core(content_id)
