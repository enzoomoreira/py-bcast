# Roadmap — Terminal Novo (Broadcast+.exe)

Backlog de adapters e funcionalidades para o backend Plus. Endpoints confirmados via probe HTTP com JWT valido (2026-05-25/27); adapters verificados ao vivo em 2026-06-10.

Ver [`endpoints.md`](./endpoints.md) para o catalogo completo de endpoints com status.
Ver [`limitations.md`](./limitations.md) para blockers conhecidos.

---

## Ja Implementado

| Funcao | Modulo | Endpoint |
|--------|--------|----------|
| `BroadcastPlusClient` | `_plus/realtime.py` | WS `/stock/ws` — quote streaming, market stats, auth refresh, ping/pong, reconexao |
| `BroadcastPlusAsyncClient` | `_plus/realtime_async.py` | Twin asyncio do `BroadcastPlusClient` |
| `btrades(ticker, date)` | `_plus/intraday.py` | `POST /stock/v1/timesAndTrades` — ultimos 500 trades |
| `abtrades(ticker, date)` | `_async/plus.py` (via `py_bcast.async_api`) | Twin async do `btrades` |
| `binfo(symbols)` | `_plus/reference.py` | `POST /stock/v1/quote/symbol` — metadata de instrumento (nunca preco) |
| `bindexes()` | `_plus/reference.py` | `GET /stock/v1/indexes` — lista de codigos de indices |
| `bindex_members(index)` | `_plus/reference.py` | `GET /stock/v1/indexes/{index}` — composicao com pesos |
| `blogo(symbol)` | `_plus/reference.py` | `GET /stock/v1/logo/{symbol}` — bytes PNG do logo |
| `bholidays()` | `_plus/reference.py` | `GET /stock/v1/calendar/tables` — catalogo de tabelas de feriados |
| `bfunds(query)` | `_plus/funds.py` | `POST /funds/v1/search` — busca de fundos (min. 3 chars) |
| `bfund(id)` | `_plus/funds.py` | `GET /funds/v1/{id}` — detalhe de fundo por id numerico |
| `bsections()` | `_plus/news.py` | `GET /news/v1/sections` — 121 secoes de noticias |
| `bheadlines(sections, count)` | `_plus/news.py` | `POST /news/v1/headlines` — manchetes paginadas |
| `bnews_content(id)` | `_plus/news.py` | `GET /news/v1/content/{id}` — corpo HTML + tagging |
| `bcorpevents(symbol)` | `_plus/corporate.py` | `POST /stock/v1/corporateevents/{symbol}` — eventos corporativos com fatores de ajuste |
| `bsearch()` (routing Plus) | `instruments/db.py` | `POST /stock/v1/quote/symbol/search` |
| `get_plus_token()` / `discover_plus_token()` | `_plus/session.py` | Auth chain ECDH + memory scan + refresh |
| `plus_request()` | `_plus/_async/transport.py` (fonte) -> `_plus/_sync/transport.py` (gerado) | Helper REST com 401-refresh automatico |

**Market streaming:** `subscribe_market(market_ids, callback)` e `unsubscribe_market(...)` sao metodos de `BroadcastPlusClient` e `BroadcastPlusAsyncClient`. Tabelas fixas da Bovespa: 0 maiores altas (a vista), 1 maiores baixas (a vista), 2 maiores altas (indice), 3 maiores baixas (indice), 4 mais negociadas por volume financeiro, 5 volume negociado, 6 evolucao do Ibovespa.

**Book streaming:** `startStreamBook` responde `success: false` para esta conta — sem a permissao "BOOK" nas 429 permissoes da assinatura. Nao implementado; limitacao de plano.

---

## Bloqueado ou Parametros Nao Descobertos

| Funcionalidade | Endpoint | Motivo |
|----------------|----------|--------|
| Historico OHLCV | `POST /stock/v1/historical/symbol` | Restricao de assinatura — erro bh_88063 |
| Tick-by-tick historico | `POST /stock/v1/historical/tickbytick/symbol` | Mesma restricao bh_88063 |
| Book de ofertas | WS `startStreamBook` | Sem permissao "BOOK" na conta (429 permissoes, nenhuma e BOOK) |
| Feriados por tabela | `POST /stock/v1/calendar/holidays` | Parametro de filtro nao descoberto — 27 variantes de payload testadas, servidor ignora todos os filtros e responde "Nenhum filtro de tabela de feriados aplicado." |
| Screener FIT | `POST /fit/v1/table` | Retorna estrutura vazia sem filtro configurado na UI do terminal; sem adapter |

---

## Nao Implementavel (sem perspectiva)

| Funcao | Motivo |
|--------|--------|
| `bdh_plus()` | Bloqueado por plano — bh_88063. Alternativa: manter `bdh()` via ContentProxy legado |
| `bmacro_plus()` | Sem endpoint de macro series mapeado no Plus |
| `bconsensus_plus()` | Sem endpoint de consenso de analistas no Plus |
| `bcompany_plus()` | Sem endpoint de dados de empresa no Plus |
