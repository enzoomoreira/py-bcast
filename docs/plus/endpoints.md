# Catalogo de Endpoints — Terminal Novo (Broadcast+.exe)

Catalogo completo de todos os endpoints REST e WebSocket descobertos via scan de memoria do `Broadcast+.exe` + probe HTTP sistematico com JWT valido (2026-05-25/27). Adapters verificados ao vivo em 2026-06-10.

**Legenda:**
- Implementado — adapter na lib disponivel
- Confirmado — endpoint testado, retorna dados, sem adapter ainda
- A confirmar — endpoint existe, params a testar
- Bloqueado — restricao de plano/assinatura ou permissao de conta
- Interno — uso exclusivo do terminal (telemetria, logs)

**Base URL:** `https://svc.aebroadcast.com.br:44761`

---

## 1. Autenticacao (`/authentication/v1/`)

| Endpoint | Metodo | Status | Descricao |
|---|---|---|---|
| `/authentication/v1/key-exchange` | POST | Confirmado | Troca de chave publica ECDH P-384 |
| `/authentication/v1/login` | POST | Confirmado | Login com senha criptografada AES-GCM |
| `/authentication/v1/refresh` | POST | Confirmado | Refresh de JWT com refreshToken |
| `/authentication/v1/logout` | POST | Confirmado | Encerrar sessao |
| `/authentication/v1/keep` | GET | Confirmado | Keep-alive / validar JWT |
| `/authentication/v1/permissions` | POST | Confirmado | 429 permissoes da conta (produtos, exchanges, servicos) |
| `/authentication/v1/urltoken` | POST | — | Token para URL externa |
| `/authentication/v1/login/secure-external-login` | POST | — | Login externo (SSO) |
| `/authentication/v1/password/options` | GET | — | Opcoes de senha |
| `/authentication/v1/password/reset` | POST | — | Reset de senha |
| `/authentication/v1/password/change` | POST | — | Trocar senha |

**Nota:** `/authentication/v1/permissions` requer POST (GET retorna 405).

---

## 2. Stock — Cotacoes e Dados de Mercado (`/stock/v1/`)

### 2.1 Instrumentos e Cotacoes

| Endpoint | Metodo | Status | Body / Params | Descricao |
|---|---|---|---|---|
| `/stock/v1/quote/symbol` | POST | **Implementado** (`binfo`) | `{"Symbols": ["PETR4"]}` | Metadata de instrumento: nome, tipo, exchange, flags — **nunca retorna preco, preco via WS** |
| `/stock/v1/timesAndTrades` | POST | **Implementado** (`btrades`) | `{"Symbol": "PETR4", "Date": "20260526"}` | Times & Trades intraday (max 500/chamada) |
| `/stock/v1/logo/{symbol}` | GET | **Implementado** (`blogo`) | `?v=7.4.4&width=48&maxHeight=48&crop=true` | Logo PNG do instrumento (2-4KB) |

### 2.2 Eventos Corporativos

| Endpoint | Metodo | Status | Body / Params | Descricao |
|---|---|---|---|---|
| `/stock/v1/corporateevents/{symbol}` | POST | **Implementado** (`bcorpevents`) | `{}` ou `{"StartDate":..., "EndDate":...}` | JCP, dividendos, splits, fatores de ajuste (add_factor, calculated_factor, multiplicative_factor) |

### 2.3 Dados de Referencia

| Endpoint | Metodo | Status | Descricao |
|---|---|---|---|
| `/stock/v1/fields` | GET | Confirmado (83KB) | Todos os campos com nome, tipo, descricao |
| `/stock/v1/markets` | GET | Confirmado | Tipos de mercado (A Vista, Futuro, etc.) |
| `/stock/v1/exchanges` | GET | Confirmado | Bolsas com delay em minutos |
| `/stock/v1/instrumentTypes` | GET | Confirmado | Tipos de instrumento (Acao, Fundo, RF, etc.) |
| `/stock/v1/brokerages` | GET | Confirmado | Lista de corretoras |
| `/stock/v1/indexes` | GET | **Implementado** (`bindexes`) | Codigos de todos os indices disponiveis |
| `/stock/v1/indexes/{index}` | GET | **Implementado** (`bindex_members`) | Composicao de indice com pesos de relevancia |
| `/stock/v1/datetime` | GET | Confirmado | Timestamp Unix do servidor |
| `/stock/v1/calendar` | GET | Confirmado | Calendario com tabelas de feriados por pais |
| `/stock/v1/calendar/tables` | GET | **Implementado** (`bholidays`) | Catalogo de tabelas de feriados (id + nome por pais/bolsa) |
| `/stock/v1/calendar/holidays` | POST | Bloqueado (param nao descoberto) | Feriados de uma tabela/ano — servidor ignora todo filtro testado (27 variantes); parametro de filtro nao descoberto |

### 2.4 Historico (restricao de assinatura)

| Endpoint | Metodo | Status | Descricao |
|---|---|---|---|
| `/stock/v1/historical/symbol` | POST | Bloqueado | OHLCV diario/semanal/mensal/intraday — erro bh_88063 |
| `/stock/v1/historical/tickbytick/symbol` | POST | Bloqueado | Tick-by-tick historico — mesmo erro bh_88063 |

### 2.5 Alertas (interno)

| Endpoint | Metodo | Status | Descricao |
|---|---|---|---|
| `/stock/v1/alert/save` | POST | Interno | Salvar alerta de cotacao (uso do terminal) |

---

## 3. Noticias (`/news/v1/`, `/news/v2/`)

| Endpoint | Metodo | Status | Body / Params | Descricao |
|---|---|---|---|---|
| `/news/v1/sections` | GET | **Implementado** (`bsections`) | — | 121 secoes/categorias de noticias |
| `/news/v1/headlines` | POST | **Implementado** (`bheadlines`) | `{"Sections": [10], "PageSize": 100, "CurrentPage": 1}` | Headlines paginadas; o cliente pagina internamente |
| `/news/v2/headlines` | POST | Confirmado | `{"Sections": [10]}` | Headlines paginadas v2 (100/pagina por padrao) |
| `/news/v1/content/{id}` | GET | **Implementado** (`bnews_content`) | — | Corpo HTML + tagging (authors, entities, locations, topics, subjects) |
| `/news/v1/alert/save` | POST | Interno | — | Salvar alerta de noticia (uso do terminal) |

**Paths inexistentes (404 confirmado):** `/news/v2/content/{id}`, `/news/v1/search`, `/news/news`, `/news/article`.

---

## 4. Fundos (`/funds/v1/`)

| Endpoint | Metodo | Status | Body / Params | Descricao |
|---|---|---|---|---|
| `/funds/v1/search` | POST | **Implementado** (`bfunds`) | `{"Query": "Petrobras", "Count": 50}` | Busca de fundos (minimo 3 chars no Query) |
| `/funds/v1/{id}` | GET | **Implementado** (`bfund`) | — | Detalhes de um fundo pelo ID numerico |
| `/funds/v1/custom-benchmark` | GET | Confirmado | — | Benchmarks customizaveis (CDI, PRE, IGP-M, IPCA) |

---

## 5. FIT — Ferramenta de Triagem (`/fit/v1/`)

| Endpoint | Metodo | Status | Body | Descricao |
|---|---|---|---|---|
| `/fit/v1/table` | POST | Confirmado | `{}` | Tabela de triagem (screener) — retorna estrutura vazia sem filtro configurado na UI; sem adapter |
| `/fit/v1/filter/{id}` | GET | Confirmado | — | Resultados de um filtro salvo pelo ID |

---

## 6. Storage e Configuracao (`/storage/v1/`)

| Endpoint | Metodo | Status | Descricao |
|---|---|---|---|
| `/storage/v1/generic-config/menu` | GET | Confirmado | Configuracao do menu da aplicacao |
| `/storage/v1/generic-config/modules` | GET | Confirmado | Modulos habilitados |
| `/storage/v1/generic-config/webtools` | GET | Confirmado | Ferramentas web disponiveis |

---

## 7. Marketplace (`/marketplace/v1/`)

| Endpoint | Metodo | Status | Descricao |
|---|---|---|---|
| `/marketplace/v1/products` | GET | Confirmado | Produtos complementares do marketplace |

---

## 8. Push Notifications (`/push/v1/`)

| Endpoint | Metodo | Status | Body | Descricao |
|---|---|---|---|---|
| `/push/v1/register` | POST | — | `{tokenId, deviceId, type}` | Registrar para push |
| `/push/v1/unregister` | POST | — | `{...}` | Cancelar push |

---

## 9. Telemetria e Logs (interno)

| Endpoint | Metodo | Descricao |
|---|---|---|
| `/analytics/v1/register/batch` | POST | Eventos de analytics (uso interno do terminal) |
| `/applicationlogs/v1/register` | POST | Logs da aplicacao (uso interno) |

---

## 10. WebSocket Channels

| Canal | URL | Auth | Status | Uso |
|-------|-----|------|--------|-----|
| Stock | `wss://svc.aebroadcast.com.br:44761/stock/ws` | JWT via msg `initialData` | **Implementado** | Cotacoes (`subscribe`), market stats (`subscribe_market`) |
| Stock — Book | `wss://svc.aebroadcast.com.br:44761/stock/ws` | JWT via msg `initialData` | Bloqueado (sem permissao "BOOK" na conta) | Book de ofertas (`startStreamBook`) — `success: false` |
| News | `wss://svc.aebroadcast.com.br:44761/news/ws` | JWT via msg `initialData` | Confirmado | Noticias ao vivo + tagging |
| Push | `wss://svc.aebroadcast.com.br:44761/push/ws` | JWT via msg `initialData` | Confirmado | Push notifications |

**Keep-alive:** ping/pong a cada 10 segundos. Ver protocolo detalhado em [`internals.md §4-5`](./internals.md).

**Acoes WS implementadas em `BroadcastPlusClient`:** `startStreamQuote`/`stopStreamQuote`, `startStreamMarket`/`stopStreamMarket`, `addFields`, `ping`/`pong`, `updateToken`.

**Acoes WS nao implementadas:** `startStreamBook`/`stopStreamBook` — conta sem permissao "BOOK".

---

## 11. Paths Inexistentes (404 Confirmado)

```
GET /macroeconomic/macroeconomic       -> 404
GET /corporate-events/corporate-events -> 404
GET /historical-data/historical-data   -> 404
GET /news/news                         -> 404
GET /news/article                      -> 404
GET /news/layers                       -> 404
GET /news/fast                         -> 404
GET /funds/funds                       -> 404
GET /portfolio/portfolio               -> 404
GET /players/v1/...                    -> 404
GET /visaoempresa/v1/...               -> 404
GET /curve/v1/...                      -> 404
```

---

## 12. Zero Sobreposicao com ContentProxy

Todos os paths do ContentProxy retornam 404 no servidor Plus (verificado em 2026-05-25):

```
GET https://svc.aebroadcast.com.br:44761/BaseHistoricaNumerica/HistoricoFechamentos -> 404
GET https://svc.aebroadcast.com.br:44761/aefundamental/consenso                    -> 404
GET https://svc.aebroadcast.com.br:44761/aetp/output/fundamental/empresa/metadado  -> 404
GET https://svc.aebroadcast.com.br:44761/CentralMultimidia/...                     -> 404
```

Cada funcao da lib precisa de adapter dedicado para o backend Plus.

---

## 13. Mapeamento de Funcionalidades vs Terminal Antigo

| Funcao py-bcast | Endpoint Antigo (ContentProxy) | Endpoint Plus | Status Plus |
|---|---|---|---|
| `bdp()` / `BroadcastClient` | DDE `BC/COT/TICKER.FIELD` | WS `startStreamQuote` | **Implementado via `BroadcastPlusClient`** |
| `BroadcastClient.snapshot()` | DDE `BC/ATIVO/TICKER` | `POST /stock/v1/quote/symbol` | **Implementado via `binfo`** |
| `bdh()` | `BaseHistoricaNumerica/HistoricoFechamentos` | `POST /stock/v1/historical/symbol` | Bloqueado — bh_88063 (restricao de assinatura) |
| `bdi()` | `BaseHistoricaNumerica/HistoricoIntraday` | `POST /stock/v1/timesAndTrades` | **Implementado via `btrades`** — 500 trades/chamada |
| `bdt()` | `BaseHistoricaNumerica/HistoricoTick` | `POST /stock/v1/historical/tickbytick/symbol` | Bloqueado — mesmo bh_88063 |
| `bmacro()` | `BaseHistoricaNumerica/MacroEconomicos` | Sem equivalente mapeado | Bloqueado |
| `bconsensus()` | `aefundamental/consenso` (binary SOH) | Sem equivalente mapeado | Bloqueado |
| `bcompany()` | `aetp/output/fundamental/empresa` (binary SOH) | Sem equivalente mapeado | Bloqueado |
| `bindices()` | `aetp/output/ativos/indice` (binary SOH) | `GET /stock/v1/indexes` | **Implementado via `bindexes`** |
| `bsectors()` | `aetp/output/fundamental/setor` (binary SOH) | `GET /stock/v1/instrumentTypes` | Confirmado — tipos de instrumento |
| `bcalendar()` | `aetp/output/fundamental/calendario` (binary SOH) | `GET /stock/v1/calendar/tables` | **Implementado via `bholidays`** (catalogo; datas bloqueadas) |
| `bdividends()` | `aetp/output/fundamental/eventos/jcp-dividendos` | `POST /stock/v1/corporateevents/{symbol}` | **Implementado via `bcorpevents`** — inclui fatores de ajuste |
| `bnews()` / `bnews_recent()` | `CentralMultimidia/` (sem auth) | `POST /news/v1/headlines` + `GET /news/v1/content/{id}` | **Implementado via `bsections`/`bheadlines`/`bnews_content`** |
| `bsearch()` | `aetp_17.dat` (arquivo local XOR) | `POST /stock/v1/quote/symbol/search` | **Implementado com routing automatico** |

### Novas Capacidades (sem equivalente no terminal antigo)

| Endpoint Plus | Funcao | Descricao |
|---|---|---|
| `GET /stock/v1/indexes/{index}` | `bindex_members` | Composicao de indice com pesos de relevancia (IBOV: 79 membros, IFIX: 107) |
| `GET /stock/v1/logo/{symbol}` | `blogo` | Logo PNG do instrumento (2-4KB) |
| `POST /funds/v1/search` | `bfunds` | Busca de fundos por nome (min. 3 chars) |
| `GET /funds/v1/{id}` | `bfund` | Detalhe de fundo — rentabilidade, taxas, CNPJ, ANBIMA |
| WS `startStreamMarket` | `subscribe_market` | Tabelas ao vivo da Bovespa (maiores altas/baixas, volume, Ibovespa) |
| WS `startStreamBook` | — | Book de ofertas — bloqueado por permissao de conta |
| `GET /marketplace/v1/products` | — | Produtos complementares do marketplace |
| `POST /news/v2/headlines` | — | Headlines v2 (100/pagina por padrao) |
| `POST /authentication/v1/permissions` | — | 429 permissoes da conta por produto/servico/exchange |
