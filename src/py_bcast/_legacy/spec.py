"""Declarative endpoint descriptors for the spec-driven executor.

An :class:`EndpointSpec` captures everything the sync and async executors need
to serve one legacy tabular endpoint: transport, path, how public-function
arguments map to request tags (:class:`ParamBind`), the output index policy,
rename/schema, error policy, and whether the call vectorizes over one argument.

Endpoints whose response parsing is bespoke (the OHLCV leg of ``bhistory``
builds rows from XML by hand) or that are non-tabular (``bnews*``/``bsearch``)
are intentionally NOT modeled here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .output import Index

Transport = Literal["aetp", "cp_ticks", "binary"]
"""Which request/parse path the executor dispatches to."""

Resolve = Literal["none", "cvm", "indicator", "date", "datetime", "join", "today"]
"""How a bound argument value is transformed before landing in its tag."""


@dataclass(frozen=True)
class ParamBind:
    """Map one public-function argument to a request tag.

    ``resolve`` transforms the value before it is written to ``tag``:

    - ``none``: ``str(value)``.
    - ``cvm``: ticker/CVM identifier -> CVM code (digit passthrough, else
      ``resolve_cvm``).
    - ``indicator``: indicator name/ID -> numeric ID.
    - ``date`` / ``datetime``: -> ``YYYYMMDD`` / ``YYYYMMDDHHMMSS``.
    - ``join``: ``";".join(list)`` for a single-shot multi-symbol tag.
    - ``today``: current date ``YYYYMMDD``, ignoring the bound value (use a
      sentinel ``arg`` such as ``""`` — the value is never read).
    """

    arg: str
    tag: str
    resolve: Resolve = "none"


@dataclass(frozen=True)
class EndpointSpec:
    """Everything the executor needs to serve one tabular endpoint.

    The same spec drives both the sync (``run_spec``) and async (``arun_spec``)
    executors; the only sync/async difference lives in those two executors, not
    here.
    """

    transport: Transport
    path: str
    index: Index
    rename: dict[str, str | None] | None = None
    schema: dict[str, str] | None = None
    # Constant request tags (e.g. {"10029": "1"}), merged before the binds.
    static_params: dict[str, str] = field(default_factory=dict)
    params: tuple[ParamBind, ...] = ()
    # aetp/binary error policy: False -> NotFoundError on a no-records reply.
    empty_ok: bool = True
    # Name of the argument vectorized over (one request per item, blocks
    # concatenated). None -> a single request.
    vectorize_over: str | None = None
    # cp_ticks knobs.
    cp_sort_by: str | None = None
    cp_reverse: bool = False
    timeout: int = 30
    # Datetime index column names (DATETIME / DATETIME_TIME policies).
    date_col: str = "dat"
    time_col: str | None = None
    # When set, the (UTC) datetime index is localized to UTC and converted to
    # this IANA timezone (e.g. "America/Sao_Paulo" for the intraday endpoints,
    # whose wire timestamps are UTC). None -> naive index.
    index_tz: str | None = None
