# Catalogo de Endpoints — Terminal Novo (Broadcast+.exe)

Catalogo completo de todos os endpoints REST e WebSocket descobertos via scan de memoria do `Broadcast+.exe` + probe HTTP sistematico com JWT valido (2026-05-25/27).

**Legenda:**
- Confirmado — endpoint testado, retorna dados
- A implementar — endpoint mapeado, sem adapter na lib ainda
- A confirmar — endpoint existe, params a testar
- Bloqueado — restricao de plano/assinatura
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
| `/stock/v1/quote/symbol` | POST | Confirmado | `{"Symbols": ["PETR4"]}` | Metadata de instrumento(s): nome, tipo, exchange, flags — **nao retorna preco, preco via WS** |
| `/stock/v1/timesAndTrades` | POST | Confirmado | `{"Symbol": "PETR4", "Date": "20260526"}` | Times & Trades intraday (max 500/chamada) |
| `/stock/v1/logo/{symbol}` | GET | Confirmado | `?v=7.4.4&width=48&maxHeight=48&crop=true` | Logo PNG do instrumento (2-4KB) |

### 2.2 Eventos Corporativos

| Endpoint | Metodo | Status | Body / Params | Descricao |
|---|---|---|---|---|
| `/stock/v1/corporateevents/{symbol}` | POST | Confirmado | `{}` ou `{"StartDate":..., "EndDate":...}` | JCP, dividendos, splits, fatores de ajuste |

### 2.3 Dados de Referencia

| Endpoint | Metodo | Status | Descricao |
|---|---|---|---|
| `/stock/v1/fields` | GET | Confirmado (83KB) | Todos os campos com nome, tipo, descricao |
| `/stock/v1/markets` | GET | Confirmado | Tipos de mercado (A Vista, Futuro, etc.) |
| `/stock/v1/exchanges` | GET | Confirmado | Bolsas com delay em minutos |
| `/stock/v1/instrumentTypes` | GET | Confirmado | Tipos de instrumento (Acao, Fundo, RF, etc.) |
| `/stock/v1/brokerages` | GET | Confirmado | Lista de corretoras |
| `/stock/v1/indexes` | GET | Confirmado | Codigos de todos os indices disponiveis |
| `/stock/v1/indexes/{index}` | GET | Confirmado | Composicao de indice com pesos de relevancia |
| `/stock/v1/datetime` | GET | Confirmado | Timestamp Unix do servidor |
| `/stock/v1/calendar` | GET | Confirmado | Calendario com tabelas de feriados por pais |
| `/stock/v1/calendar/tables` | GET | Confirmado | 49 tabelas de feriados (id + nome) |
| `/stock/v1/calendar/holidays` | POST | Confirmado | Feriados de uma tabela/ano (params a determinar) |

### 2.4 Historico (provavelmente restricao de assinatura)

| Endpoint | Metodo | Status | Descricao |
|---|---|---|---|
| `/stock/v1/historical/symbol` | POST | Bloqueado | OHLCV diario/semanal/mensal/intraday — erro bh_88063 |
| `/stock/v1/historical/tickbytick/symbol` | POST | A confirmar | Tick-by-tick historico — nao testado apos correcao de params |

### 2.5 Alertas (interno)

| Endpoint | Metodo | Status | Descricao |
|---|---|---|---|
| `/stock/v1/alert/save` | POST | Interno | Salvar alerta de cotacao (uso do terminal) |

---

## 3. Noticias (`/news/v1/`, `/news/v2/`)

| Endpoint | Metodo | Status | Body / Params | Descricao |
|---|---|---|---|---|
| `/news/v1/sections` | GET | Confirmado (121 secoes) | — | Lista de secoes/categorias de noticias |
| `/news/v1/headlines` | POST | Confirmado | `{"Sections": [10], "Count": 50}` | Headlines paginadas (`Sections` obrigatorio) |
| `/news/v2/headlines` | POST | Confirmado | `{"Sections": [10]}` | Headlines paginadas v2 (100/pagina por padrao) |
| `/news/v1/content/{id}` | GET | Confirmado | — | Conteudo do artigo: body HTML + tagging de entidades/topicos |
| `/news/v1/alert/save` | POST | Interno | — | Salvar alerta de noticia (uso do terminal) |

**Paths inexistentes (404 confirmado):** `/news/v2/content/{id}`, `/news/v1/search`, `/news/news`, `/news/article`.

---

## 4. Fundos (`/funds/v1/`)

| Endpoint | Metodo | Status | Body / Params | Descricao |
|---|---|---|---|---|
| `/funds/v1/search` | POST | Confirmado | `{"Query": "Petrobras", "Count": 50}` | Busca de fundos (minimo 3 chars no Query) |
| `/funds/v1/{id}` | GET | Confirmado | — | Detalhes de um fundo pelo ID numerico |
| `/funds/v1/custom-benchmark` | GET | Confirmado | — | Benchmarks customizaveis (CDI, PRE, IGP-M, IPCA) |

---

## 5. FIT — Ferramenta de Triagem (`/fit/v1/`)

| Endpoint | Metodo | Status | Body | Descricao |
|---|---|---|---|---|
| `/fit/v1/table` | POST | Confirmado | `{}` | Tabela de triagem (screener) com colunas e linhas — requer filtro configurado no terminal |
| `/fit/v1/filter/{id}` | GET | Confirmado | — | Resultados de um filtro salvo pelo ID |

**Nota:** retorna estrutura vazia sem filtro configurado na UI do Broadcast+.

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

| Canal | URL | Auth | Uso |
|-------|-----|------|-----|
| Stock | `wss://svc.aebroadcast.com.br:44761/stock/ws` | JWT via msg `initialData` | Cotacoes, book, mercado |
| News | `wss://svc.aebroadcast.com.br:44761/news/ws` | JWT via msg `initialData` | Noticias ao vivo + tagging |
| Push | `wss://svc.aebroadcast.com.br:44761/push/ws` | JWT via msg `initialData` | Push notifications |

**Keep-alive:** ping/pong a cada 10 segundos. Ver protocolo detalhado em [`internals.md §4-5`](./internals.md).

---

## 11. Paths Inexistentes (404 Confirmado)

Paths identificados em hipoteses anteriores e confirmados como inexistentes no servidor atual:

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
| `bdp()` / `BroadcastClient` | DDE `BC/COT/TICKER.FIELD` | WS `startStreamQuote` | A implementar |
| `BroadcastClient.snapshot()` | DDE `BC/ATIVO/TICKER` | `POST /stock/v1/quote/symbol` | Confirmado (metadata; preco via WS) |
| `bdh()` | `BaseHistoricaNumerica/HistoricoFechamentos` | `POST /stock/v1/historical/symbol` | Bloqueado — bh_88063 (plano nao inclui historico) |
| `bdi()` | `BaseHistoricaNumerica/HistoricoIntraday` | `POST /stock/v1/timesAndTrades` | Confirmado (500 trades/chamada) |
| `bdt()` | `BaseHistoricaNumerica/HistoricoTick` | `POST /stock/v1/historical/tickbytick/symbol` | A confirmar (endpoint existe, params a testar) |
| `bmacro()` | `BaseHistoricaNumerica/MacroEconomicos` | Sem equivalente mapeado | Bloqueado |
| `bconsensus()` | `aefundamental/consenso` (binary SOH) | Sem equivalente mapeado | Bloqueado |
| `bcompany()` | `aetp/output/fundamental/empresa` (binary SOH) | Sem equivalente mapeado | Bloqueado |
| `bindices()` | `aetp/output/ativos/indice` (binary SOH) | `GET /stock/v1/indexes` | Confirmado — lista de codigos |
| `bsectors()` | `aetp/output/fundamental/setor` (binary SOH) | `GET /stock/v1/instrumentTypes` | Confirmado — tipos de instrumento |
| `bcalendar()` | `aetp/output/fundamental/calendario` (binary SOH) | `GET /stock/v1/calendar` | Confirmado — feriados por pais |
| `bdividends()` | `aetp/output/fundamental/eventos/jcp-dividendos` | `POST /stock/v1/corporateevents/{symbol}` | Confirmado — JCP + dividendos + fatores |
| `bnews()` / `bnews_recent()` | `CentralMultimidia/` (sem auth) | `POST /news/v1/headlines` + `GET /news/v1/content/{id}` | Confirmado (121 secoes, tagging) |
| `bsearch()` | `aetp_17.dat` (arquivo local XOR) | `POST /stock/v1/quote/symbol` | Confirmado (`forbidden`/`notFound` para validacao) |

### Novas Capacidades (sem equivalente no terminal antigo)

| Endpoint Plus | Descricao |
|---|---|
| `GET /stock/v1/indexes/{index}` | Composicao de indice com pesos de relevancia (IBOV: 79 membros, IFIX: 107) |
| `GET /stock/v1/logo/{symbol}` | Logo PNG do instrumento |
| `POST /funds/v1/search` + `GET /funds/v1/{id}` | Dados completos de fundos (rentabilidade, taxas, CNPJ, ANBIMA) |
| `POST /fit/v1/table` + `GET /fit/v1/filter/{id}` | Screener/triagem de acoes com filtros da conta |
| `GET /marketplace/v1/products` | Produtos complementares do marketplace |
| `POST /news/v2/headlines` | Headlines v2 (100/pagina por padrao) |
| `POST /authentication/v1/permissions` | 429 permissoes da conta por produto/servico/exchange |
