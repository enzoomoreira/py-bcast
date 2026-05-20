# Arquitetura — Broadcast DDE Client

## Visão Geral das Camadas

O ecossistema Broadcast+ tem **três caminhos de dados distintos**, cada um usado por
um componente diferente:

```
                          ┌─────────────────────────────────────┐
                          │        bcsys32.exe (Terminal)        │
                          │                                      │
  ┌──────────────────┐    │  ┌─────────┐    ┌─────────────────┐ │
  │  broadcast.py    │    │  │  DDE    │    │  SPC/.NET/AETP  │ │
  │  (este projeto)  │    │  │ Server  │    │  (interno)      │ │
  └────────┬─────────┘    │  └────┬────┘    └────────┬────────┘ │
           │              │       │                   │          │
           │ [1] DDE      └───────┼───────────────────┼──────────┘
           │ Service=BC           │                   │
           │ Topic=COT ──────────►│          TCP:8100 │
           │ Item=PETR4.ULT       │          (AETP)   │
           │ ✅ IMPLEMENTADO      │                   │
           │                      │                   │
           │              ┌───────┴───────────────────┴──────────┐
           │              │         Broadcast Backend Servers      │
           │              │   wsbf.aebroadcast.com.br             │
           │              │     :44780  Dados/BCH (HTTP)          │
           │              │     :44783  HubFIX (SOAP/ASMX)        │
           │              └────────────────────┬──────────────────┘
           │                                   │
           │                    ┌──────────────┘
           │                    │
  ┌────────┴─────────┐  ┌───────┴──────────────────────────────────┐
  │  Excel + XLL     │  │  [2] HTTP ContentProxy                   │
  │  Broadcast.      ├─►│  cp.ae.com.br:44780                      │
  │  AddIn64.xll     │  │  Usado por =BCH() e =BCS()               │
  └──────────────────┘  │  ✅ IMPLEMENTADO (bdh/bdh_ohlcv)         │
                        └──────────────────────────────────────────┘

  [3] Protocolo AETP (TCP:8100) — usado internamente pelo terminal
      para receber todos os dados que aparecem na tela (cotações,
      notícias, etc.). Explorado mas não decifrado.
      ❌ NÃO IMPLEMENTADO (caminho mais complexo)
```

### Resumo dos Caminhos

| # | Canal | Usado por | Status | Dados disponíveis |
|---|-------|-----------|--------|-------------------|
| 1 | DDE (BC/COT, BC/ATIVO) | Excel `=BC()` | **✅ Implementado** | Cotações tempo real, snapshot 56 campos |
| 2 | HTTP ContentProxy `:44780` | Excel `=BCH()`, `=BCS()` | **✅ Implementado** | Histórico fechamentos, OHLCV diário |
| 3 | AETP TCP:8100 | bcsys32 interno | **❌ Parcialmente explorado** | Tudo que o terminal mostra (notícias, etc.) |

## Protocolo DDE

O terminal Broadcast expõe dados via **Windows DDE (Dynamic Data Exchange)** — o mesmo mecanismo usado pelo Excel add-in `Broadcast.AddIn64.xll`.

### Endereçamento

- **Service**: `BC` (fixo)
- **Topic**: `COT` (cotações em tempo real) ou `ATIVO` (snapshot)
- **Item**: `TICKER.CAMPO` (ponto como separador)

### Modos de Operação

| Modo | DDE Operation | Uso |
|------|--------------|-----|
| Request | `DdeClientTransaction(XTYP_REQUEST)` | One-shot: pega valor atual |
| Advise | `DdeClientTransaction(XTYP_ADVSTART)` | Streaming: push em cada tick |
| Snapshot | Request no topic ATIVO | Todos os campos de uma vez |

### Tópicos DDE Disponíveis

| Topic | Status | Uso |
|-------|--------|-----|
| COT | **Funciona** | Cotações tempo real (TICKER.CAMPO) |
| ATIVO | **Funciona** | Snapshot completo (item = ticker) |
| DOLAR | Conecta, sem itens | Formato de item desconhecido |
| LIVRO | Conecta, retorna vazio | Book de ofertas (possivelmente requer assinatura) |
| ONLINE | Conecta, NOK | Status |

### Implementação Python

O client usa duas camadas:

1. **pywin32 `dde` module** — para Request (simples, alto nível)
2. **ctypes DDEML** — para Advise/streaming (requer message pump e callback com tipos 64-bit corretos)

Detalhe importante: em Windows x64, os handles DDE (HDDEDATA, HCONV, HSZ) são ponteiros de 8 bytes. Usar `ctypes.c_ssize_t` no callback, não `c_void_p` ou `c_ulong`.

## O Que NÃO Funciona

### SPC (.NET wrapper via TCP:8100)

- `AESpcNET.dll` / `AESpcNETWrapper64.dll` provê interface .NET
- Conecta a bcsys32:8100, status fica "Initialized" (nunca "SessionOnline")
- `StartAdvise` retorna True mas **nunca entrega dados**
- `Request` nunca chama o callback
- Execute retorna "NOK=Falha na execução do comando (AESPS)"

**Conclusão**: O SPC server em bcsys32 não roteia dados para clientes externos. Serve apenas para comunicação interna.

### RTD (Real-Time Data COM)

- `Bofaddin.RtdServer` (CLSID `{BF41DD5C-B719-4034-8A47-B423B4577FD3}`) — é o RTD da **Bloomberg**, não do Broadcast
- `Bloomberg.Rtd` (CLSID `{CD6BE101-83F1-4300-887A-5ABFF8A10227}`) — Bloomberg explícito
- O Broadcast **não tem** RTD server próprio. As fórmulas `=BC()` usam DDE internamente

### TCP Direto (AETP, porta 8100)

- Protocolo: magic `1a fe ce fa` + uint32 LE payload_len + checksum (XOR)
- Server aceita conexão e envia LOGON_OK
- Subscriptions nunca geram data push
- Múltiplas tentativas de formato causaram crash no server

### Dados Históricos (BCH/BCS) → ContentProxy HTTP

- **Resolvido**: Endpoint HTTP em `cp.ae.com.br:44780` (nginx → Java backends)
- Implementado em `broadcast.py` via funções `bdh()` e `bdh_ohlcv()`
- Formato: `=BCH("PETR4";"ULT";"01/06/2016";"30/06/2016")`

## ContentProxy HTTP API

### Infraestrutura

```
nginx (port 44780)
├── /BaseHistoricaNumerica/   → JBoss Web/3.0.0-CR2 (historical data)
├── /AEInstrumentos/output/   → Servlet container (instruments, bolsas)
├── /AEContent/output/        → News content
├── /contentProxyOutput/      → Funds data
├── /aetp/output/             → Fundamentals, funds carteira
├── /aefundamental/           → Corporate fundamentals
├── /ConfigFerramentas/       → Query configurations
├── /bcaa/ws/platform/        → Spring Boot (auth service)
└── /aeterminal/              → Apache static (services.xml, global.xml)
```

### Autenticação

| Mecanismo | Quando usar |
|-----------|-------------|
| Tag `10039` na query string | **Bypass nginx** — preferido para GET |
| Basic Auth `broad:@&Br0@dc@st` | Fallback quando 10039 não está na URL |
| BCAA session token | Obtido via `/bcaa/ws/platform/logon` PUT |

### Endpoints Funcionais

| Endpoint | Params | Retorna |
|----------|--------|---------|
| `HistoricoFechamentos` | 10113=SYMs(;sep), DatasTolerancia=DATEs(;sep) | LAST, SETTLE por dia/símbolo |
| `HistoricoData` | 305=TICKER, 10077=DATE | OHLCV completo (single day) |

### Tags (parâmetros numéricos)

| Tag | Nome | Valor/Formato |
|-----|------|---------------|
| 10023 | Plataforma | `4` (fixo) |
| 10039 | Session | BCAA session token hex |
| 305 | Symbol | Ticker (ex: `PETR4`) |
| 10077 | Data | `YYYYMMDD` (single date) |
| 10113 | Symbols | Tickers separados por `;` |
| 1789 | DataInicio/Precisao | `YYYYMMDD` ou precision level |
| 961 | DataFim (HistoricoDiario) | `YYYYMMDD` — requer query pré-registrada |
| 10029 | DataInicio | `YYYYMMDD` |
| TipoResposta | Response format | `xml` (somente para BaseHistoricaNumerica) |
| Precisao | Casas decimais | `0`–`5` |
| DatasTolerancia | Dates list | Datas separadas por `;` |

### Endpoints Bloqueados

| Endpoint | Erro | Motivo |
|----------|------|--------|
| `HistoricoDiario` | Query=NONE (bh_88029) | Requer query pré-registrada via AETP protocol |
| `HistoricoUltimosPregoes` | Query=NONE | Mesmo mecanismo |
| `AEInstrumentos/*Servlet` | 88007 | TipoResposta incompatível (não é XML) |

### services.xml

Registro de 213 serviços em `http://cp.ae.com.br:44780/aeterminal/services.xml`.
Formato:
```xml
<service id='13'>
    <name>HistoricoData</name>
    <protocol>cp</protocol>
    <url>^(server)/BaseHistoricaNumerica/HistoricoData</url>
    <callback>historical</callback>
    <requiredTag>305</requiredTag>
    <requiredTag>10023</requiredTag>
    <requiredTag>10039</requiredTag>
    <requiredTag>10077</requiredTag>
    <isCached>false</isCached>
</service>
```
`^(server)` = `http://cp.ae.com.br` (de global.xml)

## Endpoints Descobertos

| Endpoint | Porta | Uso | Status |
|----------|-------|-----|--------|
| localhost (bcsys32) | 8100 | SPC/AETP (não funcional para dados) | ❌ |
| cp.ae.com.br | 44780 | ContentProxy — histórico, instrumentos | ✅ |
| wsbf.aebroadcast.com.br | 44780 | Alias/antigo do ContentProxy | ✅ |
| wsbf.aebroadcast.com.br | 44783 | HubFIX ASMX (risco, OMS) | ❌ |
| xmpp.ae.com.br | 44761 | Chat (XMPP) | ❌ |

## Formato de Dados

- Números usam **vírgula** como separador decimal (locale pt-BR): `44,60`
- Datas em formato `dd/mm/yyyy`: `19/05/2026`
- Horas em formato `HH:MM`: `15:19`
- Variação em percentual com sinal: `-3,2328`
