"""Reference data via aetp/output HTTP API (binary protocol)."""

from __future__ import annotations

from ._constants import BASE_URL
from ._http import create_http_session, get_session_token
from .fundamental import _parse_binary_response


def _aetp_request(
    path: str,
    params: dict[str, str],
    session_token: str | None = None,
) -> dict:
    """Make a request to aetp/output/* and decode binary response."""
    token = get_session_token(session_token)
    s = create_http_session()

    params.setdefault("10023", "4")
    params["10039"] = token

    r = s.get(
        f"{BASE_URL}/aetp/output/{path}",
        params=params,
        timeout=30,
        verify=False,
    )

    return _parse_binary_response(r.content)


def _rows_to_dicts(parsed: dict) -> list[dict[str, str]]:
    """Convert parsed binary response to list of dicts."""
    fields = parsed["fields"]
    results = []
    prev_values: list[str] = [""] * len(fields)

    for row in parsed["rows"]:
        record = {}
        for i, tag in enumerate(fields):
            val = row[i] if i < len(row) else ""
            # \x02 means "same as previous row"
            if val == "\x02":
                val = prev_values[i]
            record[tag] = val
            prev_values[i] = val
        results.append(record)

    return results


def bcompany(
    cvm_code: str | int | None = None,
    session_token: str | None = None,
) -> list[dict[str, str]]:
    """
    Fetch company metadata from the fundamental database.

    Without cvm_code: returns all ~1020 companies (EmpresaMetadado).
    With cvm_code: returns detailed data for one company (EmpresaDados).

    Args:
        cvm_code: CVM numeric code (e.g., 9512 for PETR, 4170 for VALE).
                  If None, returns the full list.
        session_token: BCAA session token

    Returns:
        List of dicts with company data.
        Full list fields: 13004 (CVM), 13003 (name), 13786 (ticker), etc.
        Detail fields: CNPJ, sector, foundation date, etc.

    Example:
        >>> companies = bcompany()  # all companies
        >>> petr = bcompany(9512)   # Petrobras detail
    """
    if cvm_code is None:
        parsed = _aetp_request(
            "fundamental/empresa/metadado", {}, session_token
        )
    else:
        parsed = _aetp_request(
            "fundamental/empresa",
            {"13004": str(cvm_code)},
            session_token,
        )

    return _rows_to_dicts(parsed)


def bindices(
    session_token: str | None = None,
) -> list[dict[str, str]]:
    """
    Fetch list of B3 market indices.

    Uses aetp/output/fundamental/Indices. Returns ~37 indices
    (IBOV, IBRX, SMLL, IDIV, etc.).

    Args:
        session_token: BCAA session token

    Returns:
        List of dicts with index information.

    Example:
        >>> indices = bindices()
        >>> for idx in indices:
        ...     print(idx)
    """
    parsed = _aetp_request("ativos/indice", {}, session_token)
    return _rows_to_dicts(parsed)


def bsectors(
    session_token: str | None = None,
) -> list[dict[str, str]]:
    """
    Fetch B3 sector/subsector/segment classification.

    Uses aetp/output/fundamental/SetorSubsetorSegmento. Returns ~38 sectors.

    Args:
        session_token: BCAA session token

    Returns:
        List of dicts with sector classification hierarchy.

    Example:
        >>> sectors = bsectors()
        >>> for s in sectors[:5]:
        ...     print(s)
    """
    parsed = _aetp_request(
        "fundamental/setor", {}, session_token
    )
    return _rows_to_dicts(parsed)


def bquote(
    ticker: str,
    session_token: str | None = None,
) -> dict[str, str]:
    """
    Fetch current quote (price, volume) for a symbol via aetp.

    Uses aetp/output/fundamental/AtivoCotacao.

    Args:
        ticker: Symbol (e.g., "PETR4", "VALE3")
        session_token: BCAA session token

    Returns:
        Dict with quote fields (price, volume, quantity, etc.).
        Empty dict if not found.

    Example:
        >>> q = bquote("PETR4")
        >>> print(q)
    """
    try:
        parsed = _aetp_request(
            "fundamental/ativo/cotacao",
            {"10068": ticker},
            session_token,
        )
    except RuntimeError:
        return {}

    rows = _rows_to_dicts(parsed)
    return rows[0] if rows else {}


def btickers(
    cvm_code: str | int,
    session_token: str | None = None,
) -> list[dict[str, str]]:
    """
    Fetch all tickers (stocks/units) for a company by CVM code.

    Uses aetp/output/fundamental/AtivoSimbolo.

    Args:
        cvm_code: CVM numeric code (e.g., 9512 for Petrobras)
        session_token: BCAA session token

    Returns:
        List of dicts with ticker information.

    Example:
        >>> tickers = btickers(9512)  # PETR3, PETR4
    """
    parsed = _aetp_request(
        "fundamental/ativo/simbolo",
        {"13004": str(cvm_code)},
        session_token,
    )
    return _rows_to_dicts(parsed)


def bshares(
    ticker: str,
    session_token: str | None = None,
) -> dict[str, str]:
    """
    Fetch shares outstanding for a ticker.

    Uses aetp/output/fundamental/AtivoQuantidade.

    Args:
        ticker: Symbol (e.g., "PETR4")
        session_token: BCAA session token

    Returns:
        Dict with shares data. Empty dict if not found.

    Example:
        >>> data = bshares("PETR4")
    """
    parsed = _aetp_request(
        "fundamental/ativo/quantidade",
        {"10068": ticker},
        session_token,
    )

    rows = _rows_to_dicts(parsed)
    return rows[0] if rows else {}


def bindicators(
    cvm_code: str | int,
    indicator_id: str | int,
    start_date: str,
    end_date: str,
    session_token: str | None = None,
) -> list[dict[str, str]]:
    """
    Fetch daily indicator history for a company.

    Uses aetp/output/fundamental/IndicadorHistoricoDiario.
    Known indicator IDs: 32 = Market Cap, 52 = Beta.

    Args:
        cvm_code: CVM numeric code (e.g., 9512 for Petrobras)
        indicator_id: Indicator ID (e.g., 32 for Market Cap, 52 for Beta)
        start_date: Start date as YYYYMMDD
        end_date: End date as YYYYMMDD
        session_token: BCAA session token

    Returns:
        List of dicts with daily indicator values.

    Example:
        >>> mcap = bindicators(9512, 32, "20260101", "20260519")
        >>> for r in mcap[-3:]:
        ...     print(r)
    """
    parsed = _aetp_request(
        "fundamental/indicador/historico-diario",
        {
            "13004": str(cvm_code),
            "13760": str(indicator_id),
            "10057": start_date,
            "10058": end_date,
        },
        session_token,
    )
    return _rows_to_dicts(parsed)


def bindicator_meta(
    session_token: str | None = None,
) -> list[dict[str, str]]:
    """
    Fetch metadata for all available fundamental indicators.

    Uses aetp/output/fundamental/IndicadorMetadado. Returns ~80 indicators
    with their IDs, names, and categories.

    Args:
        session_token: BCAA session token

    Returns:
        List of dicts with indicator metadata.

    Example:
        >>> meta = bindicator_meta()
        >>> for m in meta[:5]:
        ...     print(m)
    """
    parsed = _aetp_request("fundamental/indicador/metadado", {}, session_token)
    return _rows_to_dicts(parsed)
