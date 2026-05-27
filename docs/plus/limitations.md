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

**Diagnostico:** testadas 14+ variacoes de parametros (`Resolution`, `StartDate`, `EndDate`, `Adjusted`, `Type`, `Fields`, `Count`, etc.). Todos retornam o mesmo erro. O codigo `bh_88063` sugere que o plano da conta nao inclui acesso a historico OHLCV — a "data de inicio do historico" nunca e configurada para esta assinatura.

**Nao e um problema de parametros — provavelmente restricao de assinatura.**

**Alternativa:** continuar usando `bdh()` / `bdi()` via ContentProxy legado, que funciona corretamente e nao tem essa restricao.

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

**Consequencia:** o `BroadcastPlusClient` (a implementar) precisa gerenciar um loop de keepalive (`{"action": "ping"}` / `{"action": "pong"}`) ativo enquanto a conexao estiver aberta.

---

## Token Expira Mid-Session (WebSocket)

O servidor WebSocket pode enviar `{"action": "requireUpdateToken"}` quando o JWT esta proximo de expirar. O cliente precisa responder com `{"action": "updateToken", "token": "<novo_JWT>"}`.

**Consequencia:** o `BroadcastPlusClient` precisa lidar com o ciclo de refresh de token dentro da conexao WebSocket, nao apenas no inicio.

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
