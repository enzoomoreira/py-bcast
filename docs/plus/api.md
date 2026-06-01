# API Reference — Terminal Novo (Broadcast+.exe)

Referencia da API publica da lib para o backend do Terminal Novo (`Broadcast+.exe` + `svc.aebroadcast.com.br:44761`).

Para a API do Terminal Antigo, ver [`../legacy/api.md`](../legacy/api.md).

> **Status (2026-05-27):** autenticacao + streaming WebSocket (`BroadcastPlusClient`) + times & trades (`btrades`) + `bsearch` (via routing) implementados. Demais adapters no [`roadmap.md`](./roadmap.md).

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

**Methods:**

| Method | Description |
|--------|-------------|
| `subscribe(tickers, callback, fields=None)` | Inscreve para quote updates. Pode ser chamado antes ou depois de `run()`. |
| `unsubscribe(tickers)` | Para o stream dos tickers. |
| `unsubscribe_all()` | Para todos os streams. |
| `run(duration=None)` | Inicia o stream e bloqueia ate `duration` segundos (ou `stop()`). |
| `run_async(duration=None)` | Inicia em thread daemon. Retorna o `Thread`. |
| `stop()` | Para o stream e fecha o WebSocket. |

A callback recebe um dict com os campos do tick — incluindo o codigo do ticker em `data["COD"]`, util quando subscribed em multiplos tickers com a mesma callback. Valores numericos (precos, percentuais) vem parseados como `float`; codigos, nomes e horarios ficam string.

---

## Dados Intraday

### `btrades(ticker, date)`

Times & trades — os ultimos 500 trades de um ticker em uma data. Endpoint `POST /stock/v1/timesAndTrades`.

```python
from py_bcast import btrades, configure

configure(terminal="plus")
df = btrades("PETR4", "20260525")
print(df[["last", "size", "tendency"]].head())
```

**Retorna:** `pd.DataFrame` com `DatetimeIndex` em fuso `America/Sao_Paulo` e colunas:

| Coluna | Descricao |
|--------|-----------|
| `last` | Preco do trade |
| `size` | Quantidade |
| `tendency` | 0 = inalterado, 1 = alta, -1 = baixa |
| `sequence` | Numero de sequencia do servidor |
| `is_trade` | True para trade real (vs. quote) |
| `ask_price` / `ask_size` | Melhor venda no momento do trade |
| `ask_exchange_id` | Codigo da venue da venda (string identificador) |
| `bid_price` / `bid_size` | Melhor compra no momento do trade |
| `bid_exchange_id` | Codigo da venue da compra (string identificador) |

Sem trades retorna `pd.DataFrame()` vazio. API limita a 500 trades por chamada (mais recentes); ordenado em ordem cronologica (oldest first) no DataFrame.

---

## Instrument Search

`bsearch()` roteia automaticamente para o backend Plus quando ativo. Schema unificado com o Legacy (campos Plus-only sao preenchidos, campos Legacy-only ficam `pd.NA`). Ver [`../legacy/api.md`](../legacy/api.md) para detalhes do schema.

```python
from py_bcast import bsearch, configure

configure(terminal="plus")
df = bsearch("PETR", max_results=5)
# Colunas: ticker, name, exchange, backend, cvm_code, has_intraday, has_daily, ...
```

Endpoint: `POST /stock/v1/quote/symbol/search`. Exchange names retornados pelo Plus (e.g. `"Bovespa"`) sao normalizados para codigos Legacy (`"BVMF"`) via `normalize_exchange()`.

---

## Autenticacao

### `discover_plus_token()`

Forca o scan de memoria do `Broadcast+.exe` para obter o JWT atual. Util para diagnostico ou pre-carregamento explicito.

```python
from py_bcast import discover_plus_token

token = discover_plus_token()   # requer Broadcast+.exe rodando
print(token[:20] + "...")       # "eyJhbGciOiJFUzI1..."
```

Raises `BroadcastPlusAuthError` se o terminal nao estiver rodando ou o JWT nao for encontrado em memoria.

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

```python
from py_bcast import BroadcastPlusError, BroadcastPlusAuthError

try:
    token = discover_plus_token()
except BroadcastPlusAuthError:
    print("Broadcast+.exe nao esta rodando e nenhum token foi configurado")
```

---

## Acesso de Baixo Nivel

Para probing e implementacao de novos adapters enquanto as funcoes de alto nivel nao existem:

### `plus_request(method, path, **kwargs)`

Faz uma requisicao autenticada ao backend Plus com 401-refresh automatico.

```python
from py_bcast._plus.http import plus_request

# GET
resp = plus_request("GET", "/stock/v1/indexes")
print(resp.json())   # ["IBOV", "IFIX", "SMLL", ...]

# POST
resp = plus_request("POST", "/stock/v1/quote/symbol",
                    json={"Symbols": ["PETR4"]})
data = resp.json()["data"][0]
print(data["description"])   # "PETROLEO BRASILEIRO S.A. PETROBRAS, PN, A Vista"
```

### `get_plus_http_client()`

Retorna o singleton `httpx.Client` configurado para o backend Plus. Util para chamadas customizadas ou testes.

```python
from py_bcast._plus.http import get_plus_http_client

client = get_plus_http_client()
# client.base_url = "https://svc.aebroadcast.com.br:44761"
```

---

## Adapters Planejados (ainda nao implementados)

Ver [`roadmap.md`](./roadmap.md) para a lista completa e prioridade. Quando implementados, serao documentados neste arquivo.

| Funcao planejada | Endpoint | Prioridade |
|-----------------|----------|-----------|
| `bquote_plus(symbols)` | `POST /stock/v1/quote/symbol` | Alta |
| `bnews_plus(sections, count)` | `POST /news/v1/headlines` | Media |
| `bnews_content_plus(id)` | `GET /news/v1/content/{id}` | Media |
| `bindices_plus()` | `GET /stock/v1/indexes` | Media |
| `bindex_composition_plus(index)` | `GET /stock/v1/indexes/{index}` | Media |
| `bcalendar_plus()` | `GET /stock/v1/calendar` | Media |
| `bdividends_plus(symbol)` | `POST /stock/v1/corporateevents/{symbol}` | Media |
| `bfunds_plus(query)` | `POST /funds/v1/search` | Baixa |
| `bfund_plus(id)` | `GET /funds/v1/{id}` | Baixa |
