# Known Limitations — Terminal Novo (Broadcast+.exe)

Limitacoes e blockers conhecidos do backend `Broadcast+.exe` + `svc.aebroadcast.com.br:44761`.

Para limitacoes do Terminal Antigo, ver [`../legacy/limitations.md`](../legacy/limitations.md).

---

## Historico OHLCV Bloqueado (bh_88063)

**Endpoint:** `POST /stock/v1/historical/symbol`

O endpoint existe e aceita os parametros corretamente, mas retorna sempre:

```json
{
  "data": [],
  "success": false,
  "code": "bh_88063",
  "message": "Datas inicial e final da consulta anteriores a data de inicio do historico"
}
```

**Diagnostico:** testadas 14+ variacoes de parametros (`Resolution`, `StartDate`, `EndDate`, `Adjusted`, `Type`, `Fields`, `Count`, etc.). Todos retornam o mesmo erro. O codigo `bh_88063` indica que o plano da conta nao inclui acesso a historico OHLCV.

**Nao e um problema de parametros — restricao de assinatura.**

**Alternativa:** continuar usando `bdh()` / `bdi()` via ContentProxy legado.

---

## Tick-by-tick Historico Bloqueado (bh_88063)

**Endpoint:** `POST /stock/v1/historical/tickbytick/symbol`

Mesma restricao do historico OHLCV — o endpoint retorna o erro `bh_88063` independente dos parametros. Restricao de assinatura, nao de parametros.

---

## Book de Ofertas Bloqueado (sem permissao de conta)

**Acao WS:** `startStreamBook` / `stopStreamBook`

O `startStreamBook` responde `success: false` para esta conta. A causa e verificavel via `POST /authentication/v1/permissions`: das 429 permissoes retornadas, nenhuma contem a string `"BOOK"`. O book de ofertas e um modulo de assinatura separado nao incluso no plano atual.

**Nao e um problema de implementacao — e limitacao de plano, identica ao bloqueio do historico OHLCV.**

Se o plano for ampliado para incluir book, o adapter pode ser adicionado a `BroadcastPlusClient` (e ao twin async) sem alteracoes de protocolo.

---

## Feriados por Tabela — Parametro de Filtro Nao Descoberto

**Endpoint:** `POST /stock/v1/calendar/holidays`

O endpoint aceita qualquer body sem erro HTTP, mas ignora todos os filtros testados — responde sempre "Nenhum filtro de tabela de feriados aplicado." Foram testadas 27 variantes de payload incluindo todas as combinacoes de `tableId`, `TableId`, `id`, `Id`, `year`, `Year`, `table`, `Table`, `calendarId`, `code`, e variantes com e sem outros campos.

**Consequencia:** `bholidays()` expoe apenas o catalogo de tabelas (`GET /stock/v1/calendar/tables`). As datas de feriados em si nao estao acessiveis ate que o parametro de filtro correto seja descoberto.

**Status:** parametro a revisitar em versoes futuras ou quando documentacao oficial estiver disponivel.

---

## app.asar Criptografado (Discovery via Memory Scan)

O `app.asar` do `Broadcast+.exe` usa content-addressable storage criptografado com offsets/sizes falsos. Analise estatica do arquivo e inviavel.

**Consequencia:** todos os endpoints, schemas e configuracoes da aplicacao precisam ser descobertos via:
1. Scan de memoria do processo `Broadcast+.exe` em execucao
2. Probe HTTP sistematico com JWT valido

**Impacto na lib:** o scan de memoria e a metodologia padrao para descobrir novas versoes do terminal. Quando o Broadcast+ for atualizado (nova versao, novos endpoints), o scan precisa ser re-executado.

---

## Credenciais via DPAPI (Windows-only)

O terminal armazena a senha do usuario no IndexedDB do Electron usando `electron.safeStorage` (Windows DPAPI). A senha so pode ser decriptada no mesmo perfil de usuario Windows que criptografou.

**Consequencia:** a autenticacao headless via `configure(plus_login=..., plus_password=...)` funciona em qualquer maquina (a senha e enviada em plaintext para o endpoint de login com ECDH). Mas a recuperacao de credenciais do IndexedDB nao e suportada pela lib — o usuario precisa fornecer explicitamente via `configure()` ou `BROADCAST_PLUS_TOKEN`.

---

## JWT Apenas em Memoria

O JWT e o refreshToken do Broadcast+ **nao sao persistidos em disco** pelo terminal. Existem apenas em memoria enquanto o processo esta rodando.

**Consequencias:**
- A cada restart do `Broadcast+.exe`, um novo JWT e gerado
- O scan de memoria precisa ser re-executado apos restart do terminal
- `clear_plus_token_cache()` forca o re-scan na proxima chamada
- Em ambientes headless sem terminal, usar `BROADCAST_PLUS_TOKEN` ou `configure(plus_login=..., plus_password=...)`

---

## WebSocket Requer Keepalive Ativo

O WebSocket `/stock/ws` e `/news/ws` encerram a conexao se o cliente nao enviar ping a cada 10 segundos (`webSocketKeepAliveInterval = 10000`).

O `BroadcastPlusClient` e o `BroadcastPlusAsyncClient` gerenciam automaticamente o loop de keepalive (`{"action": "ping"}` / `{"action": "pong"}`) enquanto a conexao estiver aberta — nenhuma acao adicional e necessaria por parte do chamador.

---

## Token Expira Mid-Session (WebSocket)

O servidor WebSocket pode enviar `{"action": "requireUpdateToken"}` quando o JWT esta proximo de expirar. O cliente precisa responder com `{"action": "updateToken", "token": "<novo_JWT>"}`.

O `BroadcastPlusClient` e o `BroadcastPlusAsyncClient` tratam esse ciclo automaticamente: ao receber `requireUpdateToken`, chamam `refresh_plus_token()` e enviam o novo JWT sem interromper o stream.

---

## Campos Plus Podem Mudar entre Versoes

Os endpoints, schemas e o `applicationId` foram mapeados para a versao `7.4.4`. Versoes futuras do terminal podem introduzir novos endpoints ou alterar schemas existentes.

**Campos que podem mudar:**
- `x-version: 7.4.4` no header — pode precisar ser atualizado
- `applicationId = "broadcast-nt"` — fixo nas constantes do codigo
- Schemas JSON dos endpoints (novos campos adicionados ou removidos)

**Mitigacao:** a descoberta via memory scan e re-executavel a qualquer momento para mapear uma nova versao.

---

## bmacro, bconsensus, bcompany sem Equivalente Plus

As seguintes funcoes nao tem endpoint correspondente mapeado no backend Plus:

| Funcao | Motivo |
|--------|--------|
| `bmacro()` | Sem endpoint de macro series no Plus |
| `bconsensus()` | Sem endpoint de consenso de analistas no Plus |
| `bcompany()` | Sem endpoint de dados de empresa no Plus |

Essas funcoes continuarao dependentes do Terminal Antigo (ContentProxy). Nao ha perspectiva de equivalente no Plus com base nos endpoints descobertos.
