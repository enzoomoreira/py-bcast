# Notas de Protocolo — Tentativas de Exploração

Registro das abordagens testadas antes de descobrir que DDE é o caminho correto.
Mantido como referência caso alguém queira revisitar BCH/BCS ou futuros no futuro.

## Cronologia

1. **COM Registry scan** → Encontrou Bloomberg.Rtd e Bofaddin.RtdServer (ambos Bloomberg, não Broadcast)
2. **DDE probe inicial** → Testou apps/tópicos errados (Broadcast/PETR4, BRTDDE, etc.)
3. **Análise de instalação** → Mapeou DLLs .NET (AESpcNET), XLL, configs
4. **AETP TCP client** → Conectou porta 8100, decodificou header, nunca recebeu dados
5. **RTD COM** → Segfault ao implementar IRTDUpdateEvent; Bofaddin = Bloomberg
6. **SPC .NET** (7 iterações) → Conecta, aceita subscriptions, nunca entrega dados
7. **MITM SPC** → Proxy TCP entre client e server para capturar protocolo
8. **Protocol test** → Testou 7 formatos de mensagem TCP; server crashou
9. **XLL extraction** → Extraiu PEs embeddados, analisou ASM, encontrou DDE strings
10. **DDE com campos corretos** → **SUCESSO** com Service=BC, Topic=COT, Item=TICKER.FIELD

## AETP (TCP:8100)

### Header
```
Offset  Size  Description
0x00    4     Magic: 1a fe ce fa
0x04    4     Payload length (uint32 LE)
0x08    1     Checksum (XOR de todos os bytes do payload)
0x09    N     Payload
```

### Observações
- Server envia LOGON_OK após conexão (~200 bytes)
- Subscriptions são aceitas silenciosamente mas nunca geram push
- Byte 0x0A na posição errada causa crash do server
- O protocolo serve para comunicação interna entre componentes do terminal

## SPC .NET Interface

### Assinaturas descobertas via reflection
```
ISimpleProtocolClient CreateSpcInstance(String clientId, ConnectionStatusCallback)
ISimpleProtocolClient CreateSpcInstance(String clientId, String extraParams, ConnectionStatusCallback)
Void StartAdvise(String service, String topic, String item, AdviseCallback, BoolResponseCallback)
Void StopAdvise(String service, String topic, String item, AdviseCallback, BoolResponseCallback)
Void Request(String service, String topic, String item, TextResponseCallback)
Void Request(String service, String topic, String item, BinaryResponseCallback)
Void Execute(String service, String topic, String command, TextResponseCallback)
Void Poke(String service, String topic, String item, String data, BoolResponseCallback)
Void Dispose()
Void SetLogInfo(Action<String> logCallback)
```

### Comportamento
- `CreateSpcInstance` → status "Initialized", nunca "SessionOnline"
- `StartAdvise("BC|COT", "PETR4", "ULT", ...)` → BoolCallback retorna True, AdviseCallback nunca é chamado
- `Request` → TextResponseCallback nunca é chamado
- `Execute` → Retorna "NOK=Falha na execução do comando (AESPS)"

## DDE — O Que Funciona

### Discovery path
O XLL `Broadcast.AddIn64.xll` implementa a fórmula `=BC("PETR4";"ULT")` que internamente faz:
1. DDE Connect: Service="BC", Topic="COT"
2. DDE Advise: Item="PETR4.ULT"
3. Recebe callbacks via Windows messages

### Formato correto
- **Separador**: ponto (`.`) entre ticker e campo — `PETR4.ULT`
- **Não funciona**: barra (`/`), pipe (`|`), ponto-e-vírgula (`;`)
- **Campos**: siglas de 3 letras (ULT, VAR, MAX, MIN, ABE, FEC, OCP, OVD, NEG, QUL, MED, QTT, NOM, HOR)

## Possibilidades Futuras

### BCH via HTTP
- Endpoint provável: `wsbf.aebroadcast.com.br:44780`
- Auth: provavelmente token/sessão do terminal
- Poderia ser interceptado com Fiddler/mitmproxy durante uso do Excel BCH

### Futuros BM&F
- Tickers WDOM25, WINM25, DOLFUT retornam N/A
- Pode ser restrição de assinatura ou tópico DDE diferente
- Testar com painel de futuros aberto no terminal
