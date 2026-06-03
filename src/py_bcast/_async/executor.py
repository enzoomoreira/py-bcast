"""Async executor for :class:`EndpointSpec`-driven endpoints.

Async twin of ``_legacy/executor.py``: same spec, same param-binding and
finalize logic, but awaiting the async transports/resolvers. Keeping both
executors is the only sync/async duplication that remains — it is fixed
(~one file each) and does not grow per endpoint.
"""

from __future__ import annotations

import datetime
from typing import Any

import httpx
import pandas as pd

from .._core.constants import BASE_URL
from .._core.dates import to_date_str, to_datetime_str
from .._core.exceptions import ProtocolError, is_no_records
from .._core.normalize import ensure_id_list, ensure_list
from .._core.retry import http_retry
from .._legacy.aetp import rows_to_dicts
from .._legacy.binary import parse_binary_response
from .._legacy.http import get_async_http_client, get_session_token
from .._legacy.multi import vectorize_async
from .._legacy.output import Index, finalize_frame
from .._legacy.resolve import aresolve_cvm, aresolve_indicator
from .._legacy.spec import EndpointSpec, Resolve
from .._legacy.xml_helpers import parse_ticks
from ._helpers import async_aetp_request, async_content_proxy_get


async def _aresolve_cvm_or_int(value: Any, session_token: str | None) -> int:
    """Ticker-or-CVM identifier -> CVM code (digit passthrough else resolve)."""
    if isinstance(value, int) or str(value).isdigit():
        return int(value)
    return await aresolve_cvm(str(value), session_token)


async def _acoerce_bind(resolve: Resolve, raw: Any, session_token: str | None) -> str:
    """Async transform of a bound value per its resolve policy."""
    if resolve == "none":
        return str(raw)
    if resolve == "cvm":
        return str(await _aresolve_cvm_or_int(raw, session_token))
    if resolve == "indicator":
        return str(await aresolve_indicator(raw, session_token))
    if resolve == "date":
        return to_date_str(raw)
    if resolve == "datetime":
        return to_datetime_str(raw)
    if resolve == "join":
        return ";".join(ensure_list(raw))
    raise ValueError(f"unknown resolve policy: {resolve!r}")


async def _abuild_params(
    spec: EndpointSpec, inputs: dict[str, Any], session_token: str | None
) -> dict[str, str]:
    """Async mirror of ``_build_params`` (awaits CVM/indicator resolution)."""
    params = dict(spec.static_params)
    for bind in spec.params:
        if bind.resolve == "today":
            params[bind.tag] = datetime.date.today().strftime("%Y%m%d")
            continue
        raw = inputs.get(bind.arg)
        if raw is None:
            continue
        params[bind.tag] = await _acoerce_bind(bind.resolve, raw, session_token)
    return params


@http_retry
async def _abinary_fetch(
    s: httpx.AsyncClient, path: str, params: dict[str, str], timeout: int
) -> httpx.Response:
    """Isolated async HTTP GET for the binary transport (retry-decorated)."""
    return await s.get(f"{BASE_URL}/{path}", params=params, timeout=timeout)


async def _abinary_rows(
    spec: EndpointSpec,
    params: dict[str, str],
    inputs: dict[str, Any],
    session_token: str | None,
) -> list[dict[str, str]]:
    """Async fetch+parse for a templated binary endpoint (e.g. consensus)."""
    token = get_session_token(session_token)
    s = get_async_http_client()
    params["10039"] = token
    path = spec.path.format(**inputs)

    r = await _abinary_fetch(s, path, params, spec.timeout)
    try:
        parsed = parse_binary_response(r.content)
    except ProtocolError as exc:
        if is_no_records(exc.error_tag):
            return []
        raise
    return rows_to_dicts(parsed)


async def _afetch_rows(
    spec: EndpointSpec,
    params: dict[str, str],
    inputs: dict[str, Any],
    session_token: str | None,
) -> list[dict[str, str]]:
    """Dispatch to the spec's async transport and return raw row dicts."""
    if spec.transport == "aetp":
        parsed = await async_aetp_request(
            spec.path, params, session_token, empty_ok=spec.empty_ok
        )
        return rows_to_dicts(parsed)
    if spec.transport == "cp_ticks":
        root = await async_content_proxy_get(
            spec.path, params, session_token=session_token, timeout=spec.timeout
        )
        rows = parse_ticks(root, sort_by=spec.cp_sort_by or "")
        if spec.cp_reverse:
            rows.reverse()
        return rows
    if spec.transport == "binary":
        return await _abinary_rows(spec, params, inputs, session_token)
    raise ValueError(f"unknown transport: {spec.transport!r}")


async def _arun_single(
    spec: EndpointSpec, inputs: dict[str, Any], session_token: str | None
) -> pd.DataFrame:
    """Serve one (non-vectorized) async request and finalize its frame."""
    params = await _abuild_params(spec, inputs, session_token)
    rows = await _afetch_rows(spec, params, inputs, session_token)
    if spec.index is Index.RECORD:
        record = rows[0] if rows else {}
        return finalize_frame(
            record, index=Index.RECORD, rename=spec.rename, schema=spec.schema
        )
    return finalize_frame(
        rows,
        index=spec.index,
        rename=spec.rename,
        schema=spec.schema,
        date_col=spec.date_col,
        time_col=spec.time_col,
    )


async def arun_spec(
    spec: EndpointSpec, *, session_token: str | None = None, **inputs: Any
) -> pd.DataFrame:
    """Async twin of ``run_spec`` (see its docstring).

    Vectorized items run concurrently via ``vectorize_async``.
    """
    if spec.vectorize_over is None:
        return await _arun_single(spec, inputs, session_token)

    items = ensure_id_list(inputs[spec.vectorize_over])

    def one(item: Any) -> Any:
        local = dict(inputs)
        local[spec.vectorize_over] = item
        return _arun_single(spec, local, session_token)

    return await vectorize_async(items, one)
