# API Reference — Terminal Novo (Broadcast+.exe)

Referencia da API publica da lib para o backend do Terminal Novo (`Broadcast+.exe` + `svc.aebroadcast.com.br:44761`).

Para a API do Terminal Antigo, ver [`../legacy/api.md`](../legacy/api.md).

> **Status (2026-06-10):** autenticacao, streaming WebSocket (`BroadcastPlusClient`), times & trades (`btrades`), `bsearch`, e todos os adapters REST (metadata, indices, logos, fundos, noticias, eventos corporativos, feriados) implementados e verificados ao vivo.

---

## Roteamento de Backend

A lib detecta automaticamente qual backend usar (Plus se disponivel, caso contrario Legacy). Para forcar:

```python
from py_bcast import configure

configure(terminal="plus")    # forcar Plus
configure(terminal="legacy")  # forcar Legacy
configure(terminal="auto")    # detectar (padrao)
```

Funcoes que usam routing automatico: `bsearch()`.

---

## Streaming em Tempo Real

### `BroadcastPlusClient`

WebSocket client para `wss://svc.aebroadcast.com.br:44761/stock/ws`. Autenticacao automatica via `initialData`, ping/pong de keep-alive a cada 10s, refresh transparente de token quando o servidor pede, reconexao com backoff exponencial.

```python
from py_bcast import BroadcastPlusClient

def on_quote(data: dict) -> None:
    print(data["COD"], data["ULT"], data["VAR"])

with BroadcastPlusClient() as client:
    client.subscribe(["PETR4", "VALE3"], callback=on_quote)
    client.run(duration=60)   # bloqueia por 60s
```

Campos default do handshake `initialData`: `COD, ULT, VAR, ABE, MAX, MIN, HOR, NOM, DSC, TND, ATZ, EST, PTR`. Para adicionais, passe `fields=[...]` em `subscribe()`.

**Metodos:**

| Metodo | Descricao |
|--------|-----------|
| `subscribe(tickers, callback, fields=None)` | Inscreve para quote updates. Pode ser chamado antes ou depois de `run()`. |
| `unsubscribe(tickers)` | Para o stream dos tickers. |
| `unsubscribe_all()` | Para todos os streams de quote. |
| `subscribe_market(market_ids, callback)` | Inscreve para tabelas de market stats (ver abaixo). |
| `unsubscribe_market(market_ids=None)` | Cancela inscricao de market stats. `None` cancela todas. |
| `run(duration=None)` | Inicia o stream e bloqueia ate `duration` segundos (ou `stop()`). |
| `run_async(duration=None)` | Inicia em thread daemon. Retorna o `Thread`. |
| `stop()` | Para o stream e fecha o WebSocket. |

A callback de quote recebe um dict com os campos do tick — incluindo o codigo do ticker em `data["COD"]`. Valores numericos (precos, percentuais) vem parseados como `float`; codigos, nomes e horarios ficam string.

#### `subscribe_market(market_ids, callback)`

Inscreve para tabelas de estatisticas de mercado da Bovespa. Ids fixos do servidor:

| Id | Tabela |
|----|--------|
| 0 | Maiores altas — mercado a vista |
| 1 | Maiores baixas — mercado a vista |
| 2 | Maiores altas — indices |
| 3 | Maiores baixas — indices |
| 4 | Mais negociadas por volume financeiro |
| 5 | Volume negociado |
| 6 | Evolucao do Ibovespa |

Um unico `callback` recebe atualizacoes de todas as tabelas subscritas. O servidor nao repete o id numerico em cada push apos o primeiro — roteie por `header` / `type` no payload:

```python
def on_market(data: dict) -> None:
    print(data["header"], data["columns"])
    for row in data["rows"]:
        print(row)  # celulas numericas ja parseadas de BR para float

with BroadcastPlusClient() as client:
    client.subscribe_market([0, 1], callback=on_market)
    client.run(duration=30)
```

O payload de cada push contem: `header` (titulo da tabela), `columns` (nomes das colunas), `rows` (lista de linhas; celulas numericas parseadas para `float`), `type` e `id`.

Subscricoes de market stats sao re-enviadas automaticamente apos reconexao, assim como as de quote.

### `BroadcastPlusAsyncClient`

Twin asyncio do `BroadcastPlusClient` — mesmo protocolo e ciclo de vida (auth chain, ping/pong de aplicacao, refresh de token, reconexao com backoff), mas tudo roda no event loop do chamador, sem threads. As partes bloqueantes da cadeia de auth (memory scan / login ECDH) rodam em `asyncio.to_thread`.

```python
import asyncio
from py_bcast import BroadcastPlusAsyncClient

async def on_quote(data: dict) -> None:
    print(data["COD"], data["ULT"], data["VAR"])

async def main() -> None:
    async with BroadcastPlusAsyncClient() as client:
        await client.subscribe(["PETR4", "VALE3"], callback=on_quote)
        await client.run(duration=60)

asyncio.run(main())
```

Diferencas vs o sync: `subscribe`/`unsubscribe`/`unsubscribe_all`/`subscribe_market`/`unsubscribe_market`/`stop` sao corotinas (`await`); `run(duration=None)` e uma corotina que ocupa a task ate `duration` ou `stop()` — para streamar em paralelo com outro trabalho, use `asyncio.create_task(client.run())`. A callback pode ser uma funcao comum ou uma coroutine function (awaited no task do stream). Nao ha `run_async()` — em asyncio, `create_task` cumpre esse papel.

---

## Dados Intraday

### `btrades(ticker, date)`

Times & trades — os ultimos 500 trades de um ticker em uma data. Endpoint `POST /stock/v1/timesAndTrades`.

```python
from py_bcast import btrades, configure

configure(terminal="plus")
df = btrades("PETR4", "20260525")
print(df[["price", "size", "tendency"]].head())
```

**Retorna:** `pd.DataFrame` com `DatetimeIndex` em fuso `America/Sao_Paulo` e colunas:

| Coluna | Descricao |
|--------|-----------|
| `ticker` | Ticker consultado (primeira coluna) |
| `price` | Preco do trade |
| `size` | Quantidade |
| `tendency` | 0 = inalterado, 1 = alta, -1 = baixa |
| `sequence` | Numero de sequencia do servidor |
| `is_trade` | True para trade real (vs. quote) |
| `ask_price` / `ask_size` | Melhor venda no momento do trade |
| `ask_broker_id` | Id da **corretora** do lado da venda (`Int64`); join com `bbrokers()` |
| `bid_price` / `bid_size` | Melhor compra no momento do trade |
| `bid_broker_id` | Id da **corretora** do lado da compra (`Int64`); join com `bbrokers()` |

Sem trades retorna `pd.DataFrame()` vazio. API limita a 500 trades por chamada (mais recentes); ordenado cronologicamente (oldest first) no DataFrame.

O twin async `abtrades(ticker, date)` tem a mesma assinatura e o mesmo retorno:

```python
import asyncio
from py_bcast import async_api

df = asyncio.run(async_api.abtrades("PETR4", "20260525"))
```

---

## Dados de Referencia

### `binfo(symbols)`

Metadata de instrumento via `POST /stock/v1/quote/symbol`. Nunca retorna preco — preco e exclusivamente via `BroadcastPlusClient`.

```python
from py_bcast import binfo, configure

configure(terminal="plus")
df = binfo(["PETR4", "USDBRL"])
print(df[["name", "type", "currency"]])
```

**Retorna:** `pd.DataFrame` com uma linha por simbolo resolvido e colunas: `ticker, name, type, market, exchange, exchange_id, cvm_code, currency, decimal_places, flag, graphic_type, has_book, has_daily, has_intraday, is_realtime, is_delay, timezone`.

Simbolos desconhecidos sao omitidos; uma requisicao com todos os simbolos desconhecidos retorna DataFrame vazio com o mesmo schema.

O twin async `abinfo(symbols)` esta disponivel em `py_bcast.async_api`.

### `bindexes()`

Lista de codigos de indice disponiveis via `GET /stock/v1/indexes`. Alimenta `bindex_members`.

```python
from py_bcast import bindexes, configure

configure(terminal="plus")
print(bindexes()["code"].tolist())
# ['IBOV', 'IFIX', 'SMLL', ...]
```

**Retorna:** `pd.DataFrame` de uma coluna `code` com os codigos disponíveis.

### `bindex_members(index)`

Composicao de um indice com pesos de relevancia via `GET /stock/v1/indexes/{index}`.

```python
from py_bcast import bindex_members, configure

configure(terminal="plus")
df = bindex_members("IBOV")
print(df.sort_values("relevance", ascending=False).head())
```

**Args:** `index` — codigo do indice (ex.: `"IBOV"`, `"IFIX"`, `"SMLL"`). Ver `bindexes()` para os codigos validos.

**Retorna:** `pd.DataFrame` com colunas `index` (codigo consultado), `ticker`, `relevance` (peso de participacao). Uma linha por membro.

**Levanta:** `NotFoundError` se o codigo de indice nao existe.

O twin async `abindex_members(index)` esta disponivel em `py_bcast.async_api`.

### `bbrokers()`

Registro de corretoras (id -> nome curto) via `GET /stock/v1/brokerages`. Os ids estao no mesmo espaco das colunas `ask_broker_id`/`bid_broker_id` de `btrades`, entao os dois frames fazem join por id de corretora.

```python
from py_bcast import bbrokers, configure

configure(terminal="plus")
df = bbrokers()
print(df.head())
```

**Retorna:** `pd.DataFrame` com colunas `id` (`Int64`) e `name` (nome curto). Uma linha por corretora.

O twin async `abbrokers()` esta disponivel em `py_bcast.async_api`.

### `bexchanges()`

Registro de bolsas/venues via `GET /stock/v1/exchanges`. Os ids decodificam a coluna `exchange_id` de `binfo`.

```python
from py_bcast import bexchanges, configure

configure(terminal="plus")
df = bexchanges()
print(df.head())
```

**Retorna:** `pd.DataFrame` com colunas `id` (`Int64`), `name` e `delay` (atraso do feed em minutos, `Int64`; 0 = tempo real). Uma linha por bolsa.

O twin async `abexchanges()` esta disponivel em `py_bcast.async_api`.

### `blogo(symbol)`

Bytes PNG do logo de um instrumento via `GET /stock/v1/logo/{symbol}`.

```python
from py_bcast import blogo, configure

configure(terminal="plus")
open("petr4.png", "wb").write(blogo("PETR4"))
```

**Retorna:** `bytes` — PNG bruto (tipicamente 2-4 KB).

**Levanta:** `NotFoundError` se o simbolo nao tem logo.

O twin async `ablogo(symbol)` esta disponivel em `py_bcast.async_api`.

### `bholidays()`

Catalogo de tabelas de feriados (paises/bolsas) via `GET /stock/v1/calendar/tables`.

```python
from py_bcast import bholidays, configure

configure(terminal="plus")
df = bholidays()
print(df[df["name"] == "Brasil"])
```

**Retorna:** `pd.DataFrame` com colunas `id` (id da tabela) e `name` (pais/bolsa).

**Nota:** este endpoint expoe apenas o catalogo de tabelas. As datas de feriados em si (endpoint `POST /stock/v1/calendar/holidays`) nao estao acessiveis — o servidor ignora todo parametro de filtro testado (27 variantes). Ver [`limitations.md`](./limitations.md).

O twin async `abholidays()` esta disponivel em `py_bcast.async_api`.

---

## Fundos de Investimento

### `bfunds(query)`

Busca de fundos por nome via `POST /funds/v1/search`.

```python
from py_bcast import bfunds, configure

configure(terminal="plus")
print(bfunds("Verde")[["id", "company", "quota", "profit_1y"]].head())
```

**Args:** `query` — string de busca (o servidor exige pelo menos 3 caracteres).

**Retorna:** `pd.DataFrame` com uma linha por fundo encontrado, 36 colunas incluindo: `id` (chave para `bfund`), `symbol`, `cnpj`, `company`, `manager`, `administrator`, `status`, `quota`, `net_worth`, taxas, classificacao ANBIMA, janelas de rentabilidade (`profit_daily` ate `profit_5y`, `profit_annual`), e datetimes `begin`/`end`/`last_quote_date` localizados em `America/Sao_Paulo` (epoch zero vira `NaT`). DataFrame vazio com o mesmo schema se nenhum fundo encontrado.

O twin async `abfunds(query)` esta disponivel em `py_bcast.async_api`.

### `bfund(fund_id)`

Detalhe de um fundo pelo id numerico via `GET /funds/v1/{id}`.

```python
from py_bcast import bfund, configure

configure(terminal="plus")
row = bfund(779).iloc[0]
print(row[["company", "manager", "net_worth"]])
```

**Args:** `fund_id` — id numerico (coluna `id` do resultado de `bfunds`).

**Retorna:** `pd.DataFrame` de uma linha com o mesmo schema de `bfunds`.

**Levanta:** `NotFoundError` se o id nao existe.

O twin async `abfund(fund_id)` esta disponivel em `py_bcast.async_api`.

---

## Noticias

### `bsections()`

Catalogo de secoes de noticias via `GET /news/v1/sections`.

```python
from py_bcast import bsections, configure

configure(terminal="plus")
print(bsections()[["id", "name"]].head())
```

**Retorna:** `pd.DataFrame` com colunas: `id` (id da secao, para `bheadlines`), `name`, `service`, `minutes`, `is_top_news`, `is_most_read`, `is_consolidated`.

O twin async `absections()` esta disponivel em `py_bcast.async_api`.

### `bheadlines(sections, count=50)`

Manchetes recentes de uma ou mais secoes via `POST /news/v1/headlines`.

```python
from py_bcast import bheadlines, configure

configure(terminal="plus")
print(bheadlines(10, count=20)[["time", "title", "sentiment"]])
```

**Args:**
- `sections` — id de secao ou lista de ids (de `bsections`).
- `count` — maximo de manchetes a retornar, mais recentes primeiro. O cliente percorre paginas de 100 no servidor ate atingir `count` ou o feed acabar.

**Retorna:** `pd.DataFrame` com colunas: `id` (id de conteudo, para `bnews_content`), `time` (tz-aware `America/Sao_Paulo`), `title`, `sentiment`, `section_id`, `section_name`, `service`, `is_fast`, `is_highlight`. DataFrame vazio com o mesmo schema se a secao nao tem manchetes.

**Nota:** este feed e distinto do `bnews` legado (CentralMultimidia, ids no range 56M).

O twin async `abheadlines(sections, count)` esta disponivel em `py_bcast.async_api`.

### `bnews_content(content_id)`

Corpo e tagging de um artigo via `GET /news/v1/content/{id}`.

```python
from py_bcast import bnews_content, configure

configure(terminal="plus")
art = bnews_content("56345310")
print(art["tagging"]["entities"])
```

**Args:** `content_id` — id do conteudo (coluna `id` de `bheadlines`).

**Retorna:** `dict` com chaves: `id`, `title`, `time`, `sentiment`, `section_id`, `section_name`, `body` (HTML), `has_audio`, `has_pdf`, `has_video`, e `tagging` (dict com `authors`, `entities`, `locations`, `topics`, `subjects`).

**Levanta:** `NotFoundError` se o id nao existe ou nao e acessivel (403/404).

O twin async `abnews_content(content_id)` esta disponivel em `py_bcast.async_api`.

---

## Eventos Corporativos

### `bcorpevents(symbol)`

Eventos corporativos com fatores de ajuste via `POST /stock/v1/corporateevents/{symbol}`.

```python
from py_bcast import bcorpevents, configure

configure(terminal="plus")
df = bcorpevents("PETR4")
print(df[["type", "effective_date", "calculated_factor"]])
```

**Args:** `symbol` — codigo do instrumento (ex.: `"PETR4"`).

**Retorna:** `pd.DataFrame` com colunas: `ticker`, `type`, `legal_type`, `effective_date`, `execution_date`, `meeting_date` (todas tz-aware `America/Sao_Paulo`), `previous_symbol`, `should_adjust_price`, `should_adjust_volume`, `add_factor`, `calculated_factor`, `multiplicative_factor`. Linhas ordenadas por `effective_date` decrescente. DataFrame vazio com o mesmo schema se o simbolo existe mas nao tem eventos.

**Diferenca vs `bdividends`:** o `bcorpevents` inclui os fatores de ajuste de preco/volume (`add_factor`, `calculated_factor`, `multiplicative_factor`) que o `bdividends` legado nao expoe.

**Levanta:** `NotFoundError` se o simbolo nao existe.

O twin async `abcorpevents(symbol)` esta disponivel em `py_bcast.async_api`.

---

## Instrument Search

`bsearch()` roteia automaticamente para o backend Plus quando ativo. Schema unificado com o Legacy (campos Plus-only sao preenchidos, campos Legacy-only ficam `pd.NA`). Ver [`../legacy/api.md`](../legacy/api.md) para detalhes do schema.

```python
from py_bcast import bsearch, configure

configure(terminal="plus")
df = bsearch("PETR", max_results=5)
# Colunas: ticker, name, exchange, backend, cvm_code, has_intraday, has_daily, ...
```

Endpoint: `POST /stock/v1/quote/symbol/search`. Exchange names retornados pelo Plus sao normalizados para codigos Legacy via `normalize_exchange()`.

---

## Autenticacao

### `discover_plus_token()`

Forca o scan de memoria do `Broadcast+.exe` para obter o JWT atual. Util para diagnostico ou pre-carregamento explicito.

```python
from py_bcast import discover_plus_token

token = discover_plus_token()   # requer Broadcast+.exe rodando
print(token[:20] + "...")       # "eyJhbGciOiJFUzI1..."
```

Levanta `BroadcastPlusAuthError` se o terminal nao estiver rodando ou o JWT nao for encontrado em memoria.

### `clear_plus_token_cache()`

Forca re-autenticacao na proxima chamada. Util quando o terminal e reiniciado e o token em cache fica obsoleto.

```python
from py_bcast import clear_plus_token_cache

clear_plus_token_cache()   # proxima chamada vai re-escanear Broadcast+.exe
```

---

## Configuracao

### `configure(**kwargs)`

Configuracoes Plus passadas junto das configuracoes gerais:

```python
from py_bcast import configure

# Headless sem terminal rodando
configure(
    plus_login="usuario@email.com.br",
    plus_password="senha"
)

# Ou via env var (recomendado para CI/producao)
# BROADCAST_PLUS_TOKEN=<JWT>  -- define no ambiente antes de importar
```

**Campos Plus em `Settings`:**

| Campo | Descricao |
|-------|-----------|
| `plus_login` | Email do usuario Broadcast+ |
| `plus_password` | Senha (nao aparece em `repr(Settings)`) |

### Variaveis de Ambiente

| Variavel | Descricao |
|----------|-----------|
| `BROADCAST_PLUS_TOKEN` | JWT injetado externamente — bypassa toda a cadeia de auth; ideal para CI/headless |

---

## Excecoes

| Excecao | Levantada quando |
|---------|-----------------|
| `BroadcastPlusError` | Erro generico no backend Plus |
| `BroadcastPlusAuthError` | Toda a cadeia de auth falhou — sem token disponivel |
| `NotFoundError` | Simbolo, indice, id ou conteudo nao existe (ou sem permissao) |

```python
from py_bcast import BroadcastPlusError, BroadcastPlusAuthError

try:
    token = discover_plus_token()
except BroadcastPlusAuthError:
    print("Broadcast+.exe nao esta rodando e nenhum token foi configurado")
```

---

## Acesso de Baixo Nivel

Para probing e implementacao de novos adapters:

### `plus_request(method, path, **kwargs)`

Faz uma requisicao autenticada ao backend Plus com 401-refresh automatico.

```python
from py_bcast._plus._sync.transport import plus_request

# GET
resp = plus_request("GET", "/stock/v1/indexes")
print(resp.json())   # ["IBOV", "IFIX", "SMLL", ...]

# POST
resp = plus_request("POST", "/stock/v1/quote/symbol",
                    json={"Symbols": ["PETR4"]})
data = resp.json()["data"][0]
print(data["description"])
```

A variante async (`await plus_request(...)`) vive em `py_bcast._plus._async.transport`.

### `get_plus_http_client()`

Retorna o singleton `httpx.Client` configurado para o backend Plus.

```python
from py_bcast._plus.http import get_plus_http_client

client = get_plus_http_client()
# client.base_url = "https://svc.aebroadcast.com.br:44761"
```
