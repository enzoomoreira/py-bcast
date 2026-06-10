# Roadmap — Terminal Novo (Broadcast+.exe)

Backlog de adapters e funcionalidades a implementar para o backend Plus. Endpoints todos confirmados via probe HTTP com JWT valido (2026-05-25/27).

Ver [`endpoints.md`](./endpoints.md) para o catalogo completo de endpoints com status.
Ver [`limitations.md`](./limitations.md) para blockers conhecidos.

---

## Ja Implementado

| Funcao | Modulo | Endpoint |
|--------|--------|----------|
| `BroadcastPlusClient` | `_plus/realtime.py` | WS `/stock/ws` — quote streaming com auth refresh, ping/pong, reconnect |
| `BroadcastPlusAsyncClient` | `_plus/realtime_async.py` | Twin asyncio do `BroadcastPlusClient` (lib `websockets`, sem threads) |
| `btrades(ticker, date)` | `_plus/intraday.py` | `POST /stock/v1/timesAndTrades` — ultimos 500 trades |
| `abtrades(ticker, date)` | `_async/plus.py` (via `py_bcast.async_api`) | Twin async do `btrades` — mesma assinatura e retorno |
| `bsearch()` (routing Plus) | `instruments/db.py` | `POST /stock/v1/quote/symbol/search` |
| `get_plus_token()` / `discover_plus_token()` | `_plus/session.py` | Auth chain ECDH + memory scan + refresh |
| `plus_request()` | `_plus/_async/transport.py` (fonte) -> `_plus/_sync/transport.py` (gerado) | Helper REST com 401-refresh automatico |

Ainda nao implementadas as acoes WS de **book** (`startStreamBook`) e **market stats** (`startStreamMarket`); apenas `startStreamQuote` esta exposto.

---

## Prioridade Alta — Funcionalidades Essenciais

### 1. `bquote_plus(symbols)` — Metadata de Instrumento

**Modulo:** `src/py_bcast/_plus/quotes.py`
**Endpoint:** `POST /stock/v1/quote/symbol`

Retorna metadata do instrumento (nome, tipo, exchange, flags, cvmCode). Nao retorna preco — preco e exclusivamente via WebSocket.

Schema de request/response: [`internals.md §8.1`](./internals.md)

### 2. Streaming de Book e Market Stats

**Modulo:** `src/py_bcast/_plus/realtime.py` (extensao do `BroadcastPlusClient`)

Acoes WS adicionais ainda nao expostas:
- `startStreamBook` / `stopStreamBook` — book de ofertas
- `startStreamMarket` / `stopStreamMarket` — estatisticas agregadas de mercado

---

## Prioridade Media — Dados de Referencia e Conteudo

### 4. `bnews_plus(sections, count)` + `bnews_content_plus(id)` — Noticias

**Modulo:** `src/py_bcast/_plus/news.py`
**Endpoints:**
- `POST /news/v1/headlines` — headlines paginadas
- `GET /news/v1/content/{id}` — conteudo completo com tagging

Diferenca vs Legacy: o Plus inclui `tagging` rico (autores, entidades, topicos, localizacoes, sentimento). A CentralMultimidia legada nao tem tagging estruturado.

### 5. `bindices_plus()` + `bindex_composition_plus(index)` — Indices

**Modulo:** `src/py_bcast/_plus/reference.py`
**Endpoints:**
- `GET /stock/v1/indexes` — lista de codigos de indices
- `GET /stock/v1/indexes/{index}` — composicao com pesos de relevancia

A composicao de indices e uma capacidade **nova** sem equivalente no Terminal Antigo.

### 6. `bcalendar_plus()` — Feriados

**Modulo:** `src/py_bcast/_plus/reference.py`
**Endpoints:**
- `GET /stock/v1/calendar` — calendario de feriados por pais
- `GET /stock/v1/calendar/tables` — 49 tabelas

### 7. `bdividends_plus(symbol)` — Eventos Corporativos

**Modulo:** `src/py_bcast/_plus/corporate.py`
**Endpoint:** `POST /stock/v1/corporateevents/{symbol}`

Retorna JCP, dividendos, splits com fatores de ajuste (`addFactor`, `calculatedFactor`, `multiplicativeFactor`). O schema Plus e diferente do legado — inclui fatores de ajuste que o legado nao tem.

---

## Prioridade Baixa — Capacidades Plus-Exclusive

### 8. `bfunds_plus(query)` + `bfund_plus(id)` — Fundos de Investimento

**Modulo:** `src/py_bcast/_plus/funds.py`
**Endpoints:**
- `POST /funds/v1/search` — busca por nome (minimo 3 chars)
- `GET /funds/v1/{id}` — detalhes pelo ID numerico

Sem equivalente no Terminal Antigo. Schema completo: [`internals.md §8.4`](./internals.md)

Retorna: rentabilidade (diaria, mensal, anual, 2a, 3a, 5a), taxas, patrimonio, cota, categorias ANBIMA, CNPJ, gestor, administrador.

### 9. `blogo_plus(symbol)` — Logo do Instrumento

**Modulo:** a definir
**Endpoint:** `GET /stock/v1/logo/{symbol}`

Retorna PNG binario. Content-Type: `image/png`. Sem equivalente no Terminal Antigo.

---

## A Confirmar (Endpoint Existe, Params Nao Testados)

| Endpoint | Descricao | Proximo Passo |
|----------|-----------|---------------|
| `POST /stock/v1/historical/tickbytick/symbol` | Tick-by-tick historico | Testar com `Symbol` + `Resolution` no body — pode ter mesma restricao de plano que o historico OHLCV |
| `POST /stock/v1/calendar/holidays` | Feriados de uma tabela/ano | Mapear parametros obrigatorios |
| `POST /fit/v1/table` | Screener configurado via UI | Verificar schema de filtros customizados |

---

## Nao Implementavel (sem perspectiva)

| Funcao | Motivo |
|--------|--------|
| `bdh_plus()` | Bloqueado por plano — bh_88063. Alternativa: manter `bdh()` via ContentProxy legado |
| `bmacro_plus()` | Sem endpoint de macro series mapeado no Plus |
| `bconsensus_plus()` | Sem endpoint de consenso de analistas no Plus |
| `bcompany_plus()` | Sem endpoint de dados de empresa no Plus |
