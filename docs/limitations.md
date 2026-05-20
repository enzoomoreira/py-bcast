# Known Limitations

## Blocked Endpoints

| Endpoint | Error | Root Cause |
|----------|-------|------------|
| `HistoricoDiario` | `Query=NONE (bh_88029)` | Requires pre-registered query via AETP protocol |
| `HistoricoUltimosPregoes` | `Query=NONE` | Same mechanism |
| `AEInstrumentos/*` | Error 88007 | Proprietary binary protocol, not XML |
| `AEContent/*` (News) | Error 88007 | Binary-only protocol, no XML/JSON support |
| `aefundamental/marketcap` | No data | Returns wrong instrument or "not found" |
| `aefundamental/indicadores` | 404 | Endpoints don't exist on server |
| `aefundamental/demonstracao` | Backend error | GraphQL backend (AWS) unreachable |
| `contentProxyOutput/Fundos` | 500 | Server error |

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

## Workaround for B3 Historical

Use `bdh()` for daily data or `bdi()` for intraday — both work for ALL instruments:

```python
# Daily closing prices (all instruments)
data = bdh("PETR4", "20260501", "20260520")

# Intraday 2-min bars (all instruments!)
bars = bdi("PETR4", "20260519")  # works!

# Tick data does NOT work for B3
ticks = bdt("PETR4", "20260519100000", "20260519110000")  # → []
```

## DDE Requirements

- `bcsys32.exe` must be running on the same machine
- Only works on Windows (DDE is a Windows-only protocol)
- The `pywin32` package must be installed (`pip install pywin32`)

## Protocol Exploration Status

| Protocol | Status | Notes |
|----------|--------|-------|
| DDE (Service=BC) | ✅ Fully working | Real-time + snapshot |
| HTTP ContentProxy | ✅ Working | Daily, intraday OHLCV, tick (intl) |
| HTTP aefundamental | ✅ Partial | Analyst consensus works; marketcap/indicadores blocked |
| AEContent binary | ❌ Blocked | Proprietary framing, no XML/JSON support |
| AETP TCP:8100 | ❌ Not cracked | Binary protocol, custom framing |
| SPC .NET (AESpcNET.dll) | ❌ Dead end | Server doesn't route data to external clients |
| RTD COM | ❌ Not available | Broadcast has no RTD server (Excel uses DDE internally) |

## Dynamic Futures Contracts

Tickers like `WDOM25`, `WINM25`, `DOLM25` are **not in aetp_17.dat** — they're generated dynamically by the terminal for active futures contracts. They exist in the DDE namespace (and `bctab.cache`) but not in the static instrument master file.

To access these via DDE: `bdp("WDOM25", "ULT")` works normally.
