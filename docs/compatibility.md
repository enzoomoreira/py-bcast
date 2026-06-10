# Feature Compatibility — Legacy vs Plus

Mapeamento cruzado de funcionalidades entre os dois backends. Mostra o que cada terminal suporta, qual endpoint corresponde a qual funcao da lib, e o status atual de implementacao no Plus.

> Endpoints confirmados via probe HTTP sistematico com JWT valido (2026-05-25/27).
> Catalogo detalhado por backend: [`legacy/endpoints.md`](./legacy/endpoints.md) | [`plus/endpoints.md`](./plus/endpoints.md)

---

## Mapeamento de Funcoes

| Funcao py-bcast | Endpoint Legacy | Endpoint Plus | Status Plus |
|---|---|---|---|
| `bdp()` / `BroadcastClient` | DDE `BC/COT/TICKER.FIELD` | WS `startStreamQuote` | **Implementado via `BroadcastPlusClient`** |
| `BroadcastClient.snapshot()` | DDE `BC/ATIVO/TICKER` | `POST /stock/v1/quote/symbol` | Confirmado — retorna metadata; preco via WS |
| `bdh()` | `BaseHistoricaNumerica/HistoricoFechamentos` | `POST /stock/v1/historical/symbol` | Bloqueado — erro bh_88063 (restricao de assinatura) |
| `bdi()` | `BaseHistoricaNumerica/HistoricoIntraday` | `POST /stock/v1/timesAndTrades` | **Implementado via `btrades()`** — 500 trades/chamada |
| `bdt()` | `BaseHistoricaNumerica/HistoricoTick` | `POST /stock/v1/historical/tickbytick/symbol` | A confirmar — endpoint existe, params a testar |
| `bmacro()` | `BaseHistoricaNumerica/MacroEconomicos` | Sem equivalente | Sem suporte no Plus |
| `bconsensus()` | `aefundamental/consenso` | Sem equivalente | Sem suporte no Plus |
| `bcompany()` | `aetp/output/fundamental/empresa` | Sem equivalente | Sem suporte no Plus |
| `bindices()` | `aetp/output/ativos/indice` | `GET /stock/v1/indexes` | Confirmado — lista de codigos de indices |
| `bsectors()` | `aetp/output/fundamental/setor` | `GET /stock/v1/instrumentTypes` | Confirmado — tipos de instrumento |
| `bcalendar()` | `aetp/output/fundamental/calendario` | `GET /stock/v1/calendar` | Confirmado — feriados por pais |
| `bdividends()` | `aetp/output/fundamental/eventos/jcp-dividendos` | `POST /stock/v1/corporateevents/{symbol}` | Confirmado — JCP + dividendos + fatores de ajuste |
| `bdy()` | `aetp/output/fundamental/eventos/dividend-yield` | incluido em `corporateevents` | A implementar |
| `bnews()` / `bnews_recent()` | `CentralMultimidia/` (sem auth) | `POST /news/v1/headlines` + `GET /news/v1/content/{id}` | Confirmado — 121 secoes, tagging rico |
| `bsearch()` | `aetp_17.dat` (arquivo local) | `POST /stock/v1/quote/symbol/search` | **Implementado com routing automatico** — schema unificado em `pd.DataFrame` |
| `bportfolios()` / `bportfolio()` | `aetp/output/fundamental/empresa/carteira-recomendada` | Sem equivalente | Sem suporte no Plus |
| `bmacro()` / `bdi_cdi()` | `BaseHistoricaNumerica/DiCetipAcumulado` | Sem equivalente | Sem suporte no Plus |

---

## Capacidades Exclusivas do Plus

Endpoints que nao tem equivalente no Terminal Antigo:

| Endpoint Plus | Descricao |
|---|---|
| `GET /stock/v1/indexes/{index}` | Composicao de indice com pesos de relevancia (IBOV: 79 membros, IFIX: 107) |
| `GET /stock/v1/logo/{symbol}` | Logo PNG do instrumento (2-4KB) |
| `GET /stock/v1/fields` | Todos os campos com nome, tipo, descricao (83KB) |
| `POST /funds/v1/search` + `GET /funds/v1/{id}` | Fundos de investimento: rentabilidade, taxas, CNPJ, ANBIMA, gestor |
| `POST /fit/v1/table` + `GET /fit/v1/filter/{id}` | Screener/triagem de acoes com filtros salvos na conta |
| `GET /marketplace/v1/products` | Produtos complementares do marketplace |
| `POST /news/v2/headlines` | Headlines v2 (100/pagina, mesmo schema) |
| `POST /authentication/v1/permissions` | 429 permissoes da conta por produto/servico/exchange |
| WS `startStreamBook` | Book de ofertas em tempo real |
| WS `startStreamMarket` | Estatisticas de mercado em tempo real |

---

## Capacidades Exclusivas do Legacy

Funcionalidades que existem apenas no Terminal Antigo e nao tem plano de suporte no Plus:

| Funcao | Endpoint Legacy | Motivo |
|--------|----------------|--------|
| `bmacro()` | `MacroEconomicos` | Sem endpoint de macro series no Plus |
| `bconsensus()` | `aefundamental/consenso` | Sem endpoint de consenso no Plus |
| `bcompany()` | `aetp/output/fundamental/empresa` | Sem endpoint de dados de empresa no Plus |
| `bportfolios()` / `bportfolio()` | `aetp/output/carteira-recomendada` | Sem equivalente no Plus |
| `bdi_cdi()` | `DiCetipAcumulado` | Sem endpoint de CDI acumulado no Plus |
| `breturn()` | `RetornoDiario` | Sem endpoint de retorno diario no Plus |
| `bvolume()` | `VolumesMedios` | Sem endpoint de volumes medios no Plus |
| `binflation()` | `Inflacao` | Sem endpoint de indices de inflacao no Plus |
| `bindicators()` | `IndicadorHistoricoDiario` | Sem endpoint de indicadores fundamentalistas no Plus |
| `bcds()` | `MarkitOutput2/CDS` | Sem endpoint de CDS/credito no Plus |
| `InstrumentDB` / `bsearch()` (busca local) | `aetp_17.dat` | Arquivo local do bcsys32; Plus usa `quote/symbol` para lookup pontual |

---

## Comparacao Tecnica dos Backends

| Aspecto | Terminal Antigo | Terminal Novo |
|---------|----------------|---------------|
| Protocolo tempo real | DDE (DDEML, Win32) | WebSocket JSON |
| Auth tempo real | BCAA session (mem scan de bcsys32.exe) | JWT Bearer (mem scan de Broadcast+.exe) |
| Auth HTTP | Tag `10039` no query string | Header `Authorization: Bearer <JWT>` |
| Formato HTTP | XML + binary SOH | JSON |
| Paginacao | Nao | Sim (`currentPage`, `pageCount`, `remaining`) |
| Refresh de token | Manual (re-scan) | Auto-refresh via `refreshToken` |
| Ambiente headless | `BROADCAST_SESSION` env var | `BROADCAST_PLUS_TOKEN` env var |
| Configuracao headless | — | `configure(plus_login=..., plus_password=...)` |
| Dados historicos | `bdh()`, `bdi()`, `bdt()` | Historico bloqueado (bh_88063), T&T via `timesAndTrades` |
| Banco de instrumentos | `aetp_17.dat` (623K, local) | Lookup via `quote/symbol` (online) |
