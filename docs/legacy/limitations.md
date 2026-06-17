# Known Limitations — Terminal Antigo (bcsys32.exe)

Limitacoes e endpoints bloqueados do backend `bcsys32.exe` + ContentProxy `cp.ae.com.br:44780`.

Para limitacoes do Terminal Novo, ver [`../plus/limitations.md`](../plus/limitations.md).

> **Re-verificacao empirica de 2026-06-02.** As limitacoes abaixo foram re-verificadas contra o
> terminal ao vivo. A varredura original (2025-05-20) cometeu 4 erros sistematicos que produziram
> tanto bloqueios falsos quanto "confirmados" falsos — uteis de conhecer ao revisar este catalogo:
> (1) params errados (fuso BRT vs UTC; `BR` vs data; `IPCA` vs `AEIPCA`; param obrigatorio ausente)
> -> falso-negativo; (2) contar bytes/linhas sem validar celulas -> falso-positivo (header de erro
> ou casca vazia lidos como dados); (3) simbolo "pelado" resolve para instrumento errado
> (`LTN` -> `LTN.NYSE`) -> vazio enganoso; (4) param documentado quebra (ex.: `114` com `961` ->
> HTTP 500). Os erros (3) e (4) afetam usuarios da lib hoje e estao detalhados abaixo.

---

## Blocked Endpoint Groups

### AEInstrumentos (100% blocked)

ALL endpoints return `ErrorCode=88007, Tipo de resposta indisponivel ou invalido`.
Uses a proprietary binary protocol that rejects both `TipoResposta=xml` and requests without it.
These are only accessible from the Java/Swing desktop terminal.

Affected: EventoServlet, InstrumentoServlet, BolsaServlet, MercadoServlet, SimbologiaServlet, SetorServlet, CorretoraServlet, IndicesServlet, and ~40 more.

**Workaround**: Many equivalent datasets exist via `aetp/output/fundamental/` (see [`endpoints.md`](./endpoints.md) section 5).

### AEContent / News (100% blocked)

Same error 88007. News content requires the proprietary binary framing.

### contentProxyOutput / Fundos CVM (mostly broken — NOT 100%)

Most CVM-fund endpoints return HTTP 500 with Java/JBoss stack traces (the Tomcat backend is
crashed/misconfigured). But this is **not uniform** — re-verification (2026-06-02) found at least
two endpoints in this group alive and returning binary SOH data over `HTTP 200`:
- **ClasseAnbima (120)** — 11 rows (Anbima fund classes).
- **BuscarFundosAutoComplete (116)** — ~1MB+ fund autocomplete dataset.

The 2025 scan generalized an observed 500 to the whole group. Check per-endpoint before assuming
it's blocked. See [`endpoints.md`](./endpoints.md) section 7.

### GraphQL Backend (aetp/output/fundamental/indicador/*)

The financial indicators backend (P/L, ROE, Divida Liquida, EBITDA multiples, etc.) is hosted on AWS (`ab684f71...elb.us-east-1.amazonaws.com`) and is **offline**.

Affected endpoints: IndicadorPeriodo (166), IndicadorHistorico (167), IndicadorTicker (168), IndicadorTickerFixo (170), DemonstrativoFiltros (182), ComposicaoIndices (214).

**Not affected** (these work despite sharing the same path prefix):
- IndicadorMetadado (165) — returns 80 indicator definitions
- IndicadorHistoricoDiario (171) — returns daily Market Cap, Beta, etc.

### Financial statements (DRE / BP / FC, P/L, ROE) do not exist via legacy

Verified 2026-06-02. There is **no usable source of historical financial statements or financial
ratios** over the old terminal's HTTP API. Two independent dead ends combine:

- **EmpresasHistorico (154) is an empty shell.** It returns `HTTP 200`/`STATUS=success` with a
  222-column schema (DRE/BP/FC) and up to 7776 rows (one per trading day), but a full scan of all
  rows finds **zero populated financial cells** — only `DAT` is filled, `QUARTER`/`FISCAL_QUARTER`
  come back as `nanT`, every `ASSET_RETURN`/`BOOK_BALANCE`/`CAPITAL`/`EBITDA`/... is blank. The
  ~1.2MB the 2025 scan recorded was a wide schema times empty rows, not data. Correct params are
  `305`=ticker + `961`=start; the empty result is a server-side emptied dataset, not a param gap.
- **The GraphQL indicators backend is offline** (166/167/182/214 → "Bad Request" via the AETP
  front; see above).

So legacy fundamentals are limited to **analyst consensus** (`bconsensus`), **daily indicators**
(market cap / beta via 171), **dividends/corporate events**, and **metadata**. For actual
financial statements and ratios, investigate the **Plus** backend
([`../plus/`](../plus/limitations.md)).

---

## Tick Data — TimesTrades (bticks) Retention

`bticks()` usa o endpoint TimesTrades (41) com a mesma convencao de fuso UTC que `bdt`.
Retencao observada em testes ao vivo (2026-06-10): somente a **sessao corrente** retorna dados;
dias anteriores retornam vazio mesmo quando o pregao negociou. O dado e denso para papeis
liquidos (~2k rows por 5 minutos em PETR4). Mantenha janelas curtas.

```python
# Somente janelas do dia corrente retornam dados
df = bticks("PETR4", "20260610130000", "20260610131000")   # sessao de hoje: funciona
df = bticks("PETR4", "20260609130000", "20260609131000")   # D-1: vazio
```

Para tick-by-tick de instrumentos internacionais (FX, metais, energia, indices globais) com
retencao mais longa, use `bdt`.

---

## Tick Data (bdt) Restrictions

`bdt()` works for **both B3/BVMF and international instruments**. PETR4, VALE3 and
IBOV all return ticks over plain HTTP — there is no AETP pre-registration step (a
single `HistoricoTick` GET returns `STATUS=success` with thousands of `<TICK>`
elements). The two real restrictions are the request window's time zone and how
far back tick history is retained.

### The window is interpreted in UTC

The server clock is **UTC**, while B3's floor session runs 10:00–17:00 in Brasília
time (BRT, UTC−3). So the regular session appears in the `10071`/`10072` params —
and in the returned `hor` timestamps — as **13:00–20:00 UTC**. After-hours trading
extends past 20:00 UTC.

If you pass a Brasília-clock window (e.g. start = `...100000`, "10:00") you land in
B3 pre-market (07:00 BRT) and get **0 ticks** even though the floor traded that day.

Verified on 2026-06-02 — same ticker, same day, only the window changes:

| Window (params, UTC) | Brasília equivalent | PETR4 ticks |
|----------------------|---------------------|-------------|
| `100000`–`110000` | 07:00–08:00 BRT (pre-market) | 0 |
| `130000`–`140000` | 10:00–11:00 BRT (floor open) | 24,585 |

```python
# WRONG — Brasília-clock window, falls in pre-market -> empty
bdt("PETR4", "20260601100000", "20260601110000")   # -> []

# RIGHT — UTC window covering the B3 floor open
bdt("PETR4", "20260601130000", "20260601140000")    # -> ~24.6k ticks
```

International feeds (FX, metals, energy, foreign indices/treasuries) trade close to
24h, so they return data at almost any hour — which historically masked this time
zone trap.

### B3 tick history is limited and irregular (best effort)

Tick retention for B3 instruments is short and patchy. Recent trading days return
ticks, but older dates can come back empty **even when the floor traded** (confirmed
via `bhistory`). This is server-side retention/availability, not a client problem and not
a pre-registration requirement.

Observed on 2026-06-02 (PETR4/VALE3, `bhistory` confirms the floor traded):

| Date | Floor traded? | Tick data? |
|------|---------------|------------|
| 2026-06-01 | yes | yes |
| 2026-05-29 | yes | **no** |
| 2026-05-15 | yes | **no** |
| 2026-05-08 | yes | yes |
| 2026-05-01 | no (holiday) | no |
| 2026-04-01 | yes | **no** |

International instruments retain tick history much longer (USDBRL verified back to
roughly two months). Treat B3 tick availability as **best effort**: assume recent
sessions work and check older dates case by case. The exact retention horizon is
not mapped.

---

## Parameter Gotchas

### MacroEconomicos — Symbols Are NOT Obvious

The `MacroEconomicos` endpoint (id=95) uses internal AE symbols, NOT the common names.
Also uses `DataInicio`/`DataFim` params (NOT tag `961`):

```python
bmacro("AEIPCA", "20250101", "20260520")   # correct
bmacro("IPCA", "20250101", "20260520")     # won't work
```

| Wrong | Right | Data |
|-------|-------|------|
| `SELIC` | `AESLIC` | Taxa SELIC (reuniao COPOM) |
| `CDI` | `AECTIP` | CDI CETIP diario |
| `IPCA` | `AEIPCA` | IPCA mensal |
| `IGPM` | `AEIGPM` | IGP-M mensal |
| `INPC` | `AEINPC` | INPC mensal |

Standard market symbols (USDBRL, IBOV, SPX, GOLD, WTI, DI1F27) work directly.

The same AE symbol family applies to **CalculoInflacao (145)**: `305=AEIPCA` returns the series,
while `305=IPCA` errors with "simbolo nao existe na base de instrumentos" (verified 2026-06-02).

### Tesouro symbols — bare LTN/NTNB resolves to the WRONG instrument

The Tesouro Nacional (Brazilian government bonds) lives under TWO exchanges in the instrument
master, and the bare ticker resolves to neither. Passing `305=LTN` resolves to **`LTN.NYSE`** (a
US stock), which returns `STATUS=success` with an **empty** `<TICKS>` — the same misleading-empty
trap as `HistoricoTick`. You must use the suffixed symbol, and the suffix that populates differs
by endpoint (verified 2026-06-02):

| Suffix | What it is | Populates |
|--------|------------|-----------|
| `.ANBIMA` | Daily reference prices (ex.: `LTN260701.ANBIMA`, `NTNB270515.ANBIMA`) | CalculoPreco (135), TitulosPublicosUltimos (141) |
| `.TRDM` | Trademate / OTC desk (ex.: `LTNF28.TRDM`, `NTNBK27.TRDM`) | TitulosPublicos (77); also 135 |

```python
# WRONG — bare ticker resolves to LTN.NYSE -> success but empty
# 305=LTN

# RIGHT — TitulosPublicos (77) populates via .TRDM
# 305=LTNF28.TRDM  -> 1 tick OHLC + WORKING_DAYS + EXPIRATION_DATE

# RIGHT — CalculoPreco (135) / TitulosPublicosUltimos (141) populate via .ANBIMA
# 305=LTN260701.ANBIMA -> PU series (LAST, ACUM, VAR)
```

Note: for endpoint 77, `.ANBIMA` returns `success` with 0 ticks — only `.TRDM` carries its OHLC.

### TimesTrades / HistoricoTick — 14-digit datetime

Both use `YYYYMMDDHHMMSS` (14 digits), not 12. The clock is **UTC** (for B3, the
floor session is 13:00–20:00 UTC; see [Tick Data (bdt) Restrictions](#tick-data-bdt-restrictions)).

```
10071=20250519130000  <- start (13:00:00 UTC = 10:00 BRT)
10072=20250519140000  <- end   (14:00:00 UTC = 11:00 BRT)
```

### HistoricoData — Tag 10077, NOT 961

For single-date OHLCV, use tag `10077` (not `961` which is for series start):
```
305=PETR4&10077=20250519
```

### CalculoPoupanca (114) — use DataInicio/DataFim, NOT 961

The 2025 catalog listed `961`=start for CalculoPoupanca, but passing `961` returns **HTTP 500**
(JBoss error report). It only works with `DataInicio`/`DataFim` (verified 2026-06-02 →
`sym=AENPOP.AETAXAS`, 22 daily `DAT`/`ACUM` ticks):
```
DataInicio=20260501&DataFim=20260602   # works
961=20260501                            # -> HTTP 500
```

### FundosIndicadores (81) — Benchmark Nao Informado

Avancos em 2026-06-10: `961` satisfaz a data e o servidor passa a responder "Benchmark nao
informado". Todas as combinacoes testadas de nome/valor de tag para o benchmark (inclusive
`Benchmark=`, `13486=`) foram recusadas. O param correto nao foi descoberto.

### FechamentoFormula (83) — DataInicio Rejeitado Como Ausente

Inconsistencia server-side: `Instrumentos`/`12004` sao aceitos (o servidor valida o simbolo),
mas `DataInicio` e sempre rejeitado como "campo obrigatorio nao encontrado" mesmo quando enviado
nos formatos `YYYYMMDD` e `dd/MM/yyyy`.

### TabelaRetorno / TabelaRentabilidade (138/139) e CalculoCarteira (144) — Tipo de Calculo

Os tres endpoints respondem "Tipo de calculo nao enviado" a todas as chaves testadas: `10029`,
`TipoCalculo`, `TipoDeCalculo`, `Tipo`, `TipoRetorno`, `12004`, `13539`. O enum correto
provavelmente so existe no cliente Java do Add-In Excel.

### Players — Server Bug

The Players endpoint (id=40) has a server-side SQL bug:
```
field BVMF was not found in the tick descriptor
```
This is an OneTick query issue on the server, not a client problem.

---

## B3 Historical — Choosing an Endpoint

`bhistory()` / `bclose()` (daily) and `bdi()` (intraday bars) work for ALL instruments and have full
history. `bdt()` (tick-by-tick, internacional) and `bticks()` (times-and-trades B3) also work,
but only with UTC windows and subject to retention limits.

```python
# Daily closing prices (all instruments, full history)
data = bhistory("PETR4", "20250501", "20250520")

# Daily OHLCV range
ohlcv = bhistory("PETR4", "20250501", "20250520", fields="ohlcv")

# Intraday 2-min bars (all instruments)
bars = bdi("PETR4", "20260601")

# Times-and-trades B3 — somente sessao corrente, janela UTC
# (13:00-20:00 UTC = B3 floor 10:00-17:00 BRT)
ticks = bticks("PETR4", "20260610130000", "20260610131000")

# Tick-by-tick internacional (FX, metais, energia) — retencao mais longa
fx_ticks = bdt("USDBRL", "20260601130000", "20260601140000")
```

For older dates with no tick retention, fall back to `bdi()` for intraday detail.

---

## DDE Requirements

- `bcsys32.exe` must be running on the same machine
- Only works on Windows (DDE is a Windows-only protocol)
- Requires `pywin32` (installed automatically as a dependency of `py-bcast`)

---

## Dynamic Futures Contracts

Tickers like `WDOM25`, `WINM25`, `DOLM25` are **not in aetp_17.dat** — they're generated dynamically by the terminal for active futures contracts. They exist in the DDE namespace (and `bctab.cache`) but not in the static instrument master file.

To access these via DDE: `bdp("WDOM25", "ULT")` works normally.

---

## Binary SOH Protocol Decoder

The decoder in `src/py_bcast/_legacy/binary.py` (`parse_binary_response()`) handles:
- SOH (0x01) record separator
- NULL (0x00) field separator
- STX (0x02) "same as previous row" compression
- ETX (0x03) stream terminator
- Metadata records (record[1] with N key-value pairs, not just error code)
- Error detection via presence of tag `10037` in the raw data

This decoder works for ALL `aefundamental/` and `aetp/output/` responses. No additional protocol work is needed to implement new endpoints from these groups.

---

## AETP TCP:8100 (Not Mapped)

The terminal also opens an AETP TCP binary protocol on port 8100, separate from the
ContentProxy HTTP API this library uses. Its purpose is not mapped, and **it is not
required for any HTTP endpoint we support** — in particular it is **not** related to
B3 tick data, which flows over plain HTTP (see
[Tick Data (bdt) Restrictions](#tick-data-bdt-restrictions)).

A candidate frame header was observed but not verified end to end:
```
Offset  Size  Description
0x00    4     Magic: 1a fe ce fa
0x04    4     Payload length (uint32 LE)
0x08    1     Checksum (XOR of all payload bytes)
0x09    N     Payload
```

This protocol is left unmapped; nothing in the current client depends on it.
