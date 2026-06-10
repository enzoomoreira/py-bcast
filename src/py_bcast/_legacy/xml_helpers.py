"""Pure helpers for ContentProxy XML responses (BaseHistoricaNumerica).

The I/O side (``content_proxy_get``) lives in the twin trees
``_legacy/_async/`` (source) and ``_legacy/_sync/`` (generated); this module
keeps the shared parsing and error-classification logic both import.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from .._core.exceptions import (
    ContentProxyError,
    NotFoundError,
    is_no_records,
    is_not_found,
)
from .._core.logging import get_logger

logger = get_logger(__name__)


def raise_for_content_proxy_status(
    root: ET.Element,
    endpoint: str,
    params: dict[str, str],
) -> None:
    """Classify a ContentProxy STATUS != success response.

    Maps the server MESSAGE to the unified error policy:
        - unknown symbol ("não existe")          -> NotFoundError
        - valid query, no rows ("não foram ...")  -> return (benign; caller
          gets a zero-TICK root and yields an empty DataFrame with schema)
        - anything else                           -> ContentProxyError

    A ``success`` status is a no-op.
    """
    if root.findtext("STATUS") == "success":
        return
    msg = root.findtext("MESSAGE") or "Unknown error"
    if is_not_found(msg):
        raise NotFoundError(params.get("305") or params.get("10113"), kind="symbol")
    if not is_no_records(msg):
        logger.error("ContentProxy error on %s: %s", endpoint, msg)
        raise ContentProxyError(
            f"ContentProxy error on {endpoint}: {msg}",
            endpoint=endpoint,
            server_message=msg,
        )
    logger.debug("ContentProxy no records on %s: %s", endpoint, msg)


def parse_ticks(root: ET.Element, sort_by: str = "") -> list[dict[str, str]]:
    """Parse <TICK> elements from XML root into a list of dicts.

    Args:
        root: XML root element containing .//TICK elements
        sort_by: If non-empty, sort results by this key (e.g. "dat")

    Returns:
        List of dicts with lowercased tag names as keys.
    """
    rows = [
        {child.tag.lower(): (child.text or "") for child in tick}
        for tick in root.findall(".//TICK")
    ]
    if sort_by:
        rows.sort(key=lambda r: r.get(sort_by, ""))
    return rows
