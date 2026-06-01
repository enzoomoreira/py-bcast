# Terminal Novo — Internals (Broadcast+.exe)

Documentacao tecnica interna do backend `Broadcast+.exe` v7.4.4 + `svc.aebroadcast.com.br:44761`.

Cobre: infraestrutura de rede, protocolo de autenticacao ECDH/JWT, mecanica REST, protocolo WebSocket, configuracoes da aplicacao, metodologia de descoberta e schemas detalhados de todos os endpoints testados.

**Metodo de descoberta:** o `app.asar` usa content-addressable storage criptografado (offsets/sizes falsos), tornando analise estatica inviavel. Todos os endpoints foram descobertos via scan de memoria do `Broadcast+.exe` em execucao + probe HTTP sistematico com JWT valido (2026-05-25/27).

---

## Contexto Tecnico

| | Terminal Antigo | Terminal Novo |
|---|---|---|
| **Processo** | `bcsys32.exe` | `Broadcast+.exe` |
| **Tecnologia** | Java/Win32 nativo | Electron 7.4.4 (Chromium + Node.js) |
| **App ID** | — | `br.com.ae.broadcastnt.pro` (`broadcast-nt`) |
| **Versao** | x36 (legado) | 7.4.4 |
| **Dados em tempo real** | DDE (Windows IPC) | WebSocket |
| **API HTTP** | `http://cp.ae.com.br:44780` (ContentProxy nginx) | `https://svc.aebroadcast.com.br:44761` (Apache HTTPS) |
| **Autenticacao** | BCAA token hex (33 chars) no query string `10039` | JWT Bearer no header `Authorization` |
| **Resposta HTTP** | XML + binary SOH | JSON |

> Ambos os servidores rodam em paralelo. Zero sobreposicao de endpoints — paths do ContentProxy retornam 404 no servidor Plus.

---

## 1. Infraestrutura de Rede

```
Broadcast+.exe
├── HTTPS REST  ->  https://svc.aebroadcast.com.br:44761  (Apache)
├── WSS         ->  wss://svc.aebroadcast.com.br:44761/stock/ws
├── WSS         ->  wss://svc.aebroadcast.com.br:44761/news/ws
├── WSS         ->  wss://svc.aebroadcast.com.br:44761/push/ws
├── HTTPS       ->  https://broadcastaddin.aebroadcast.com.br  (Office Add-in / WebRTC)
├── HTTPS       ->  https://chat.aebroadcast.com.br  (AE Chat — app Ionic)
└── HTTPS       ->  https://gestaoinvestimentos.aebroadcast.com.br  (Gestao de investimentos)
```

**IP resolvido:** `200.196.201.134:44761`

---

## 2. Autenticacao

### 2.1 Fluxo Completo (ECDH + AES-GCM)

```
1. POST /authentication/v1/key-exchange
   Body: {"publicKey": "<P-384 SPKI DER em base64>"}
   Resposta: {"publicKey": "<server P-384 pub key>", "sessionId": "<base64>"}

2. Derivar AES key:
   shared_bits = ECDH(client_private, server_public)   # 48 bytes (P-384)
   aes_key     = SHA-256(shared_bits)                  # 32 bytes

3. Criptografar senha:
   iv          = os.urandom(12)
   ciphertext  = AES-GCM-256(password.encode(), key=aes_key, nonce=iv)
   session_bytes = base64.b64decode(sessionId)
   encrypted_pw  = base64.b64encode(session_bytes + iv + ciphertext)

4. POST /authentication/v1/login
   Body: {
     "login":         "usuario@email.com.br",   # lowercase obrigatorio
     "password":      "<encrypted_pw>",
     "applicationId": "broadcast-nt"
   }
   Sucesso: {
     "success": true,
     "token":          "<JWT>",
     "refreshToken":   "<refresh_string>",
     "sessionId":      "...",
     "chatToken":      "...",
     "userProfile":    {...},
     "newPasswordRequired": false
   }
   Erro:    {"success": false, "code": "400", "message": "Dados de acesso invalidos"}
```

### 2.2 Refresh de Token

```
POST /authentication/v1/refresh
Body: {"token": "<JWT_atual>", "refreshToken": "<refresh_string>"}
Resposta: {"token": "<novo_JWT>", "refreshToken": "<novo_refresh>"}
```

### 2.3 Headers Padrao (todas as requisicoes autenticadas)

```http
Authorization: Bearer <JWT>
x-version: 7.4.4
accept: application/json
content-type: application/json
```

### 2.4 Respostas de Erro de Auth

```json
// Dados invalidos (credenciais erradas) — HTTP 200
{"success": false, "code": "400", "message": "Dados de acesso invalidos"}

// Token invalido/expirado — HTTP 401
{"success": false, "code": 401, "message": "Token de autorizacao invalido ou expirado"}
```

### 2.5 Cadeia de Autenticacao da Lib

Implementada em `src/py_bcast/_plus/session.py`. Prioridade de resolucao:

| # | Mecanismo | Cenario |
|---|-----------|---------|
| 1 | `BROADCAST_PLUS_TOKEN` env var | CI/headless — JWT injetado externamente |
| 2 | Cache in-memory do processo | Evita re-scan a cada chamada |
| 3 | Auto-refresh via `refreshToken` | Transparente, sem interacao do usuario |
| 4 | Scan de memoria do `Broadcast+.exe` | Requer terminal rodando — simetrico ao bcsys32 |
| 5 | Login ECDH (`configure(plus_login=..., plus_password=...)`) | Headless sem terminal |
| 6 | `BroadcastPlusAuthError` | Toda a cadeia falhou |

**Tokens sao mantidos apenas em memoria** — sem persistencia em disco.

### 2.6 Credenciais Persistidas pelo Terminal

O terminal armazena credenciais no IndexedDB do Electron (Chromium):
- Path: `%APPDATA%\Broadcast+\IndexedDB\file__0.indexeddb.leveldb\`
- Campo `login`: texto plano (`usuario@email.com.br`)
- Campo `password`: encriptado com `electron.safeStorage` (Windows DPAPI)
- O JWT/refreshToken nao e persistido em disco — existe so em memoria durante a sessao

---

## 3. Convencoes REST

- Todos os campos no body sao **PascalCase** (`Symbol`, `StartDate`, `Sections`, etc.)
- Campos obrigatorios ausentes retornam HTTP 400 com `{"message": "O campo X e obrigatorio"}`
- Respostas com paginacao: `{currentPage, count, pageCount, remaining, remainingPages, ...}`
- **Path vs Body:** o path `quote/symbol` usa `symbol` singular (nome do endpoint), mas o campo no body e `Symbols` (plural, array). Convencoes distintas: singular no path, plural no body.

---

## 4. WebSocket — `/stock/ws`

URL: `wss://svc.aebroadcast.com.br:44761/stock/ws`

**Sem auth no header HTTP** — o JWT e enviado na mensagem `initialData` apos conectar.

### 4.1 Handshake de Autenticacao

```json
// 1. Server -> Client (imediato apos conexao)
{"action": "requireInitialData"}

// 2. Client -> Server
{
  "action": "initialData",
  "token":  "<JWT>",
  "fields": ["COD","ULT","VAR","ABE","MAX","MIN","HOR","NOM","DSC","TND","ATZ","EST","PTR"]
}

// 3. Server -> Client
{"action": "initialData", "success": true}
// ou
{"action": "initialData", "success": false}  // token invalido -> reconectar
```

### 4.2 Quotes em Tempo Real

```json
// Subscribe
{"action": "startStreamQuote", "symbols": ["PETR4", "IBOV", "USDBRL"]}

// Unsubscribe
{"action": "stopStreamQuote", "symbols": ["PETR4"]}

// Adicionar campos extras (apos subscribe)
{"action": "addFields", "fields": ["QTT", "VOL", "NEG"], "symbols": null}

// Remover campos
{"action": "removeFields", "fields": ["QTT"]}

// Push do server (a cada atualizacao)
{
  "action": "streamQuote",
  "data": {
    "COD":  "PETR4",
    "ATIVO": "PETR4",
    "CODG": "PETR4",
    "ULT":  "44.60",
    "VAR":  "-1.23",
    "ABE":  "45.00",
    "MAX":  "45.10",
    "MIN":  "44.50",
    "HOR":  "15:19"
  }
}
```

**Campos padrao (`fields` no initialData):**

| Campo | Descricao |
|---|---|
| `COD` | Codigo do ativo |
| `ULT` | Ultimo preco |
| `VAR` | Variacao percentual |
| `ABE` | Abertura |
| `MAX` | Maxima |
| `MIN` | Minima |
| `HOR` | Horario do ultimo negocio |
| `NOM` | Nome do ativo |
| `DSC` | Descricao |
| `TND` | Tendencia |
| `ATZ` | Atualizacao |
| `EST` | Status |
| `PTR` | Patrimonio? |

> Os nomes de campos sao identicos aos do DDE antigo (`ULT`, `VAR`, `ABE`, etc.) — mesma simbologia, protocolo diferente.

### 4.3 Book de Ofertas

```json
// Subscribe (por simbolo, nao lista)
{"action": "startStreamBook", "symbol": "PETR4"}

// Unsubscribe
{"action": "stopStreamBook", "symbol": "PETR4"}

// Push do server
{"action": "streamBook", "data": {"COD": "PETR4", "CODG": "PETR4", ...}}
```

### 4.4 Estatisticas de Mercado

```json
// Subscribe
{"action": "startStreamMarket", "id": "<market_id>", "requestId": "<market_id>"}

// Unsubscribe
{"action": "stopStreamMarket", "id": "<market_id>"}

// Push
{"action": "streamMarket", ...}
```

### 4.5 Keep-Alive

```json
// Client -> Server
{"action": "ping"}

// Server -> Client
{"action": "pong"}

// Server tambem pode iniciar:
{"action": "ping"}   // Client responde com {"action": "pong"}
```

**Intervalo:** 10 segundos (`webSocketKeepAliveInterval = 10000`)

### 4.6 Refresh de Token via WebSocket

```json
// Server -> Client (quando token proximo de expirar)
{"action": "requireUpdateToken"}

// Client -> Server
{"action": "updateToken", "token": "<novo_JWT>"}

// Server -> Client
{"action": "updateToken", "success": true}
// ou false -> Client reconecta
```

---

## 5. WebSocket — `/news/ws`

URL: `wss://svc.aebroadcast.com.br:44761/news/ws`

Mesmo mecanismo de auth que `/stock/ws`.

```json
// Subscribe a secoes de noticias
{"action": "startStreamNews", "sections": ["<section_id>", ...]}

// Unsubscribe
{"action": "stopStreamNews", "sections": ["<section_id>"]}

// Subscribe a tagging (associacao de noticias a tickers)
{"action": "startStreamNewsTagging", "sections": ["<section_id>"]}

// Unsubscribe tagging
{"action": "stopStreamNewsTagging", "sections": ["<section_id>"]}
```

---

## 6. Configuracoes da App

```javascript
applicationId    = "broadcast-nt"
production       = true
version          = "7.4.4"
apiRootProd      = "https://svc.aebroadcast.com.br:44761"
apiRootWsProd    = "wss://svc.aebroadcast.com.br:44761"
webRtcProd       = "https://broadcastaddin.aebroadcast.com.br/web-rtc"
keepAliveInterval          = 10000   // ms — HTTP keep-alive
webSocketKeepAliveInterval = 10000   // ms — WS ping interval
```

---

## 7. Reutilizacao do Core da Lib

Analise de quais componentes sao reutilizaveis pelo backend Plus. A reorg que extraiu o protocolo
Legacy para `_legacy/` materializou esta analise: o genuinamente compartilhado ficou em `_core/`; o
acoplado ao ContentProxy/bcsys32 foi para `_legacy/` (o Plus nunca importa de la — usa seus proprios
`_plus/http.py` e `_plus/session.py`).

| Componente | Reutilizavel? | Observacoes |
|---|---|---|
| `_core/cache.py` | Sim | Cache TTL agnostico de protocolo |
| `_core/ratelimit.py` | Sim | Rate limiter agnostico |
| `_core/retry.py` | Sim | `@http_retry` funciona para qualquer httpx call (unico `_core` que o Plus importa) |
| `_core/logging.py` | Sim | `get_logger()` e generico |
| `_core/validation.py` | Sim | `Ticker`, `DateParam`, etc. |
| `_core/dates.py` | Sim | Conversoes de data |
| `_core/normalize.py` | Sim | `ensure_list()` etc. |
| `_core/config.py` | Expandido | `Settings` recebeu `plus_login`, `plus_password` (repr=False) |
| `_legacy/output.py` | Nao | Construtores de DataFrame acoplados aos schemas Legacy (`columns.py`); o Plus monta o seu proprio em `btrades` |
| `_legacy/http.py` | Nao | Cliente ContentProxy Legacy (`get_http_client`, `base_params`); o Plus usa `_plus/http.py` |
| `_legacy/session.py` | Nao | BCAA token discovery especifico do bcsys32.exe |
| `_legacy/binary.py` | Nao | Parser de binary SOH especifico do ContentProxy |
| `_legacy/xml_helpers.py` | Nao | Parser XML especifico do ContentProxy |
| `realtime/client.py` | Nao | DDE e exclusivo do bcsys32.exe |
| `instruments/db.py` | Nao | `aetp_17.dat` e instalado pelo bcsys32 |
| `_plus/session.py` | N/A | **Novo** — JWT auth chain (env var / mem scan / ECDH) |
| `_plus/http.py` | N/A | **Novo** — singleton client + `plus_request()` com 401-refresh |

---

## 8. Schemas Detalhados

### 8.1 Cotacoes e Instrumentos

**`POST /stock/v1/quote/symbol`** — metadata de instrumento(s)

```json
// Request — "Symbols" e plural e obrigatorio (singular "Symbol" retorna 400)
{"Symbols": ["PETR4", "VALE3", "IBOV"]}

// Response
{
  "forbidden": [],
  "notFound": [],
  "success": true,
  "data": [{
    "hasBook": true, "hasDaily": true, "hasIntraday": true,
    "isDelay": false, "isRealTime": true, "isSequential": false, "isSnapshot": false,
    "code": "PETR4",
    "description": "PETROLEO BRASILEIRO S.A. PETROBRAS, PN, A Vista",
    "cvmCode": 9512,
    "decimalPlaces": 2,
    "marketId": 1,
    "typeId": 1,
    "expirationDate": 0,
    "flag": "5008",
    "graphicType": "A",
    "marketDescription": "A Vista",
    "typeDescription": "Acao",
    "exchange": {"id": 1, "name": "Bovespa", "delay": 15},
    "currency": {"id": 2, "name": "Real", "shortName": "BRL"},
    "timeZone": {"id": 1, "offset": -180, "name": "America/Sao_Paulo"}
  }]
}
// Retorna metadata do instrumento, nao preco. Preco em tempo real via WebSocket.
```

**`POST /stock/v1/corporateevents/{symbol}`** — eventos corporativos

```json
// Request — body pode ser vazio ou ter filtro de datas
{"StartDate": "2026-01-01T00:00:00", "EndDate": "2026-12-31T00:00:00"}

// Response
{
  "data": [{
    "shouldAdjustPrice": true,
    "shouldAdjustVolume": false,
    "addFactor": 0.258319,
    "calculatedFactor": 0.994581,
    "multiplicativeFactor": 0,
    "effectiveDate": 1779246000000,
    "executionDate": 1776913200000,
    "meetingDate": 1772766000000,
    "legalType": "Outros",
    "previousSymbol": "",
    "type": "JCP - 15% IR ate 2025 - 17,5% IR "
  }],
  "symbol": {...},
  "success": true
}
```

**`GET /stock/v1/indexes/{index}`** — composicao de indice

```json
// Response — array com peso de cada membro
[
  {"relevance": 2.88836, "symbol": "ABEV3"},
  {"relevance": 4.0628,  "symbol": "AXIA3"}
]
// Testado: IBOV (79 membros), IFIX (107 membros)
```

**`GET /stock/v1/indexes`** — lista de indices disponiveis

```json
["AGFS", "BDRX", "GPTW", "IBBC", "IBOV", "IBRA", "IFIX", "IFNC", "IGCT",
 "IGCX", "IGNM", "IMAT", "IMOB", "INDX", "ISEE", "ITAG", "IVBX", "MLCX",
 "SMLL", "UTIL", ...]
```

**`GET /stock/v1/logo/{symbol}`** — logo PNG

```
Response: imagem PNG (Content-Type: image/png)
Params opcionais: ?v=7.4.4&width=48&maxHeight=48&crop=true
Tamanho tipico: 2-4KB
```

### 8.2 Historico (provavelmente restricao de assinatura)

**`POST /stock/v1/historical/symbol`** — OHLCV historico

```json
// Request (campos obrigatorios mapeados)
{
  "Symbol": "PETR4",
  "Resolution": "D",
  "StartDate": "2026-04-01T00:00:00",
  "EndDate": "2026-05-27T00:00:00"
}

// Valores de Resolution testados (todos aceitos pelo validador):
// "D", "W", "M", "1", "5", "15", "30", "60", "d", "w", "m", "1D", "daily", "weekly"

// Response — independente do range de datas ou resolution
{
  "data": [],
  "symbol": {...},
  "success": false,
  "code": "bh_88063",
  "message": "Datas inicial e final da consulta anteriores a data de inicio do historico"
}
```

**Diagnostico:** o endpoint existe e aceita os parametros corretamente (sem 400). O erro `bh_88063` indica provavelmente que a conta nao tem acesso a dados historicos OHLCV no plano Broadcast+ atual. **Nao e um problema de parametros — provavelmente restricao de assinatura.**

### 8.3 Noticias

**`GET /news/v1/sections`** — secoes de noticias

```json
// Response — array com 121 secoes
[
  {"id": 5,   "name": "Release", "isTopNews": false, "isConsolidated": false, "isMostRead": false},
  {"id": 10,  "name": "Financas", ...},
  {"id": 748, "name": "Podcast", ...}
]
```

**`POST /news/v1/headlines`** — headlines paginadas

```json
// Request
{"Sections": [10], "Count": 50}    // Sections obrigatorio

// Response
{
  "currentPage": 1,
  "pageCount": 5,
  "count": 50,
  "remaining": 200,
  "remainingPages": 4,
  "headlines": [{
    "id": "56205521",
    "title": "Sinal positivo no exterior pode estimular Ibovespa...",
    "time": 1779892102000,
    "isFast": false,
    "isHighlight": false,
    "sentiment": 1,
    "section": {"id": 10, "name": "Financas", "service": "Financas", "minutes": 30},
    "feedbackStatus": {"feedbackType": 0, "time": 0},
    "readStatus": {"isRead": false, "time": 0},
    "saveStatus": {"isSaved": false, "time": 0}
  }],
  "forbidden": [],
  "notFound": [],
  "success": true
}
```

**`POST /news/v2/headlines`** — mesma estrutura, 100 headlines/pagina por padrao.

**`GET /news/v1/content/{id}`** — conteudo do artigo

```json
// Response
{
  "hasAudio": false,
  "hasPdf": false,
  "hasVideo": false,
  "body": "<HTML do artigo>",
  "headline": {
    "id": "56205521",
    "title": "...",
    "time": 1779892102000,
    "section": {...},
    "sentiment": 1
  },
  "tagging": {
    "authors": ["Maria Regina Silva", "Flavio Leonel"],
    "entities": ["Petrobras", "Vale"],
    "locations": [],
    "mainTopics": ["Desvalorizacao do petroleo", "Impacto no Ibovespa"],
    "subjects": ["Mercado financeiro", "Indices de acoes"]
  },
  "success": true
}
```

### 8.4 Fundos

**`POST /funds/v1/search`** — busca de fundos

```json
// Request
{"Query": "Petrobras"}    // minimo 3 caracteres

// Response
{
  "funds": [{
    "id": 779,
    "symbol": "FI779",
    "cnpj": "56573470000107",
    "company": "ITAU FUNDO DE ACOES ...",
    "tradingName": "...",
    "manager": "...",
    "administrator": "...",
    "isActive": true,
    "isOpen": true,
    "isExclusive": false,
    "minimumInvestment": 100.0,
    "additionalInvestment": 100.0,
    "managementFee": 2.0,
    "quota": 45123.45,
    "netWorth": 1200000000.0,
    "lastQuoteDate": 1779246000000,
    "begin": 963198000000,
    "end": 0,
    "dailyPercentageProfitability": 0.15,
    "monthlyPercentageProfitability": 2.3,
    "oneMonthPercentageProfitability": 2.3,
    "threeMonthsPercentageProfitability": 7.1,
    "sixMonthsPercentageProfitability": 14.2,
    "oneYearPercentageProfitability": 28.5,
    "annualPercentageProfitability": 12.0,
    "twoYearsPercentageProfitability": 55.0,
    "threeYearsPercentageProfitability": 90.0,
    "fiveYearsPercentageProfitability": 180.0,
    "eighteenMonthsPercentageProfitability": 42.0,
    "anbimaClass": {"id": 4, "description": "..."},
    "anbimaCategory": {"id": 45, "description": "..."},
    "anbimaSubcategory": {"id": 69, "description": "..."},
    "performanceIndicator": "CDI",
    "performanceDescription": "100% CDI",
    "qualifiedInvestorType": "-",
    "status": "ATIVA"
  }],
  "success": true
}
```

**`GET /funds/v1/{id}`** — retorna o mesmo schema para um fundo especifico.

**`GET /funds/v1/custom-benchmark`** — benchmarks customizaveis

```json
[
  {"benchmarkId": 1, "benchmarkTypeId": 1, "name": "Padrao", "symbol": ""},
  {"benchmarkId": 2, "benchmarkTypeId": 2, "name": "CDI", "symbol": "AECTIP",
   "canChangeFactor": true, "canChangeRate": true,
   "factorMinValue": 50, "factorMaxValue": 200,
   "rateMinValue": 0, "rateMaxValue": 1000},
  {"benchmarkId": 3, "benchmarkTypeId": 3, "name": "PRE", "symbol": "",
   "canChangeFactor": false, "canChangeRate": true,
   "rateMinValue": 0.01, "rateMaxValue": 1000},
  {"benchmarkId": 4, "benchmarkTypeId": 5, "name": "IGP-M", "symbol": "AEIIGP"},
  {"benchmarkId": 5, "benchmarkTypeId": 5, "name": "IPCA",  "symbol": "AEIICA"}
]
```

### 8.5 Times & Trades

**`POST /stock/v1/timesAndTrades`** — ticks intraday

```json
// Request
{"Symbol": "PETR4", "Date": "20260526"}

// Response (max 500 por chamada, mais recentes do dia)
{"data": [{
  "isTrade": true,
  "last": 43.4,
  "sequence": 47317,
  "size": 100,
  "unixTime": 1779742741630,
  "tendency": 0,
  "ask": {"price": 0, "size": 0, "exchangeId": "3"},
  "bid": {"price": 0, "size": 0, "exchangeId": "3"}
}]}
```

### 8.6 Permissoes da Conta

**`POST /authentication/v1/permissions`** — 429 permissoes por produto/servico

```json
// Response
{
  "permissions": [{
    "id": 4,
    "exchangeId": 0,
    "product": {"id": 1, "name": "BOLSAS"},
    "category": "BOVESPA",
    "service": "BOVESPA 2",
    "type": "S"
  }]
}
// type: "S"=stream, "B"=broadcast, "F"=?, "W"=web
// products: "BOLSAS", "BOLSAS_DIFERIDO", "BROADCAST", "PAGINAS_DIFERIDO"
```
