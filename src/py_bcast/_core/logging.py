"""Centralized logging for py_bcast.

Library users see no output by default (NullHandler). Call
``configure_logging()`` for quick console diagnostics.
"""

from __future__ import annotations

import logging
import sys

_LIB_ROOT = "py_bcast"

# Attach NullHandler so logs are silently discarded unless the
# application configures logging.
logging.getLogger(_LIB_ROOT).addHandler(logging.NullHandler())


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the ``py_bcast`` namespace.

    Usage inside any module::

        from py_bcast._core.logging import get_logger
        logger = get_logger(__name__)
    """
    return logging.getLogger(f"{_LIB_ROOT}.{name}" if not name.startswith(_LIB_ROOT) else name)


def configure_logging(
    level: int | str = logging.DEBUG,
    fmt: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
) -> None:
    """Enable console logging for py_bcast with a single call.

    Parameters
    ----------
    level : int | str
        Logging level (e.g. ``"DEBUG"``, ``logging.INFO``).
    fmt : str
        Log format string.
    """
    root = logging.getLogger(_LIB_ROOT)
    root.setLevel(level)

    # Avoid adding duplicate handlers on repeated calls
    if not any(isinstance(h, logging.StreamHandler) and h.stream is sys.stderr for h in root.handlers):
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(fmt))
        root.addHandler(handler)
