# Known Limitations

## Blocked Endpoint Groups

### AEInstrumentos (100% blocked)

ALL endpoints return `ErrorCode=88007, Tipo de resposta indisponível ou inválido`.  
Uses a proprietary binary protocol that rejects both `TipoResposta=xml` and requests without it.  
These are only accessible from the Java/Swing desktop terminal.

Affected: EventoServlet, InstrumentoServlet, BolsaServlet, MercadoServlet, SimbologiaServlet, SetorServlet, CorretoraServlet, IndicesServlet, and ~40 more.

**Workaround**: Many equivalent datasets exist via `aetp/output/fundamental/` (see compatibility.md section 5).

### AEContent / News (100% blocked)

Same error 88007. News content requires the proprietary binary framing.

### contentProxyOutput / Fundos CVM (100% broken)

All ~30 endpoints return HTTP 500 with Java stack traces.  
The Tomcat backend for CVM fund data is crashed/misconfigured.

### GraphQL Backend (aetp/output/fundamental/indicador/*)

The financial indicators backend (P/L, ROE, Dívida Líquida, EBITDA multiples, etc.) is hosted on AWS (`ab684f71...elb.us-east-1.amazonaws.com`) and is **offline**.

Affected endpoints: IndicadorPeriodo (166), IndicadorHistorico (167), IndicadorTicker (168), IndicadorTickerFixo (170), DemonstrativoFiltros (182), ComposicaoIndices (214).

**Not affected** (these work despite sharing the same path prefix):
- IndicadorMetadado (165) — returns 80 indicator definitions ✅
- IndicadorHistoricoDiario (171) — returns daily Market Cap, Beta, etc. ✅

---

## Tick Data (bdt) Restrictions

`bdt()` works **only for international instruments** — those on feeds that don't require server-side query registration:

| Feed | Exchange | Examples |
|------|----------|----------|
| GTISFX | ICE Data Services FX | USDBRL, EURUSD, GBPUSD |
| GTISME | ICE Metals | GOLD, SILVER |
| GTISEN | ICE Energy | WTI |
| BER | Berlim | DAX |
| FTSE | London | FTSE |
| CBOEI | CBOE Indices | VIX |
| ICEUS | ICE US | DXY |
| TPGB | Treasury/Bonds | US10Y, US2Y |

**B3/BVMF instruments (PETR4, VALE3, WDOM25, etc.) return 0 ticks** — the server requires a `HistoricoTick` query to be registered via the AETP binary protocol before data flows. This registration is done automatically by the terminal UI but we cannot replicate it via HTTP.

---

## Parameter Gotchas

### MacroEconomicos — Symbols Are NOT Obvious

The `MacroEconomicos` endpoint (id=95) uses internal AE symbols, NOT the common names.
Also uses `DataInicio`/`DataFim` params (NOT tag `961`):

```python
bmacro("AEIPCA", "20250101", "20260520")   # ← correct
bmacro("IPCA", "20250101", "20260520")     # ← won't work
```

| Wrong ❌ | Right ✅ | Data |
|----------|----------|------|
| `SELIC` | `AESLIC` | Taxa SELIC (reunião COPOM) |
| `CDI` | `AECTIP` | CDI CETIP diário |
| `IPCA` | `AEIPCA` | IPCA mensal |
| `IGPM` | `AEIGPM` | IGP-M mensal |
| `INPC` | `AEINPC` | INPC mensal |

Standard market symbols (USDBRL, IBOV, SPX, GOLD, WTI, DI1F27) work directly.

### TimesTrades / HistoricoTick — 14-digit datetime

Both use `YYYYMMDDHHMMSS` (14 digits), not 12.

```
10071=20250519100000  ← start (10:00:00)
10072=20250519110000  ← end   (11:00:00)
```

### HistoricoData — Tag 10077, NOT 961

For single-date OHLCV, use tag `10077` (not `961` which is for series start):
```
305=PETR4&10077=20250519
```

### Players — Server Bug

The Players endpoint (id=40) has a server-side SQL bug:
```
field BVMF was not found in the tick descriptor
```
This is an OneTick query issue on the server, not a client problem.

---

## Workarounds for B3 Historical

Use `bdh()` for daily data or `bdi()` for intraday — both work for ALL instruments:

```python
# Daily closing prices (all instruments)
data = bdh("PETR4", "20250501", "20250520")

# Intraday 2-min bars (all instruments!)
bars = bdi("PETR4", "20250519")  # works!

# Tick data does NOT work for B3
ticks = bdt("PETR4", "20250519100000", "20250519110000")  # → []
```

---

## DDE Requirements

- `bcsys32.exe` must be running on the same machine
- Only works on Windows (DDE is a Windows-only protocol)
- The `pywin32` package must be installed (`pip install pywin32`)

---

## Protocol Exploration Status

| Protocol | Status | Notes |
|----------|--------|-------|
| DDE (Service=BC) | ✅ Fully working | Real-time + snapshot |
| HTTP BaseHistoricaNumerica | ✅ Working | ~18 endpoints, 9 implemented |
| HTTP aefundamental | ✅ Partial | Consensus + binary parser |
| HTTP aetp/output | ✅ **~40 working, 14 implemented** | Binary SOH, richest data source |
| HTTP IntegracaoTabelas | ✅ Partial | 4 commodity/formula endpoints |
| HTTP AEInstrumentos | ❌ 100% blocked | `PROPRIETARY` — error 88007 |
| HTTP AEContent | ❌ 100% blocked | `PROPRIETARY` — error 88007 |
| HTTP contentProxyOutput | ❌ 100% broken | `DEAD_BACKEND` — all HTTP 500 |
| HTTP MarkitOutput2 | ❌ Mostly broken | Only ListaTipoCDS works |
| AETP TCP:8100 | ❌ Not cracked | Binary protocol, custom framing |
| SPC .NET (AESpcNET.dll) | ❌ Dead end | Server doesn't route data to external clients |
| RTD COM | ❌ Not available | Broadcast has no RTD server (uses DDE) |

---

## Dynamic Futures Contracts

Tickers like `WDOM25`, `WINM25`, `DOLM25` are **not in aetp_17.dat** — they're generated dynamically by the terminal for active futures contracts. They exist in the DDE namespace (and `bctab.cache`) but not in the static instrument master file.

To access these via DDE: `bdp("WDOM25", "ULT")` works normally.

---

## Binary SOH Protocol Decoder

The decoder in `src/py_bcast/fundamental.py` (`_parse_binary_response()`) handles:
- SOH (0x01) record separator
- NULL (0x00) field separator
- STX (0x02) "same as previous row" compression
- ETX (0x03) stream terminator
- Metadata records (record[1] with N key-value pairs, not just error code)
- Error detection via presence of tag `10037` in the raw data

This decoder works for ALL `aefundamental/` and `aetp/output/` responses. No additional protocol work is needed to implement new endpoints from these groups.
