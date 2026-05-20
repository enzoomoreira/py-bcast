# broadcast-intercept

Cliente Python para dados de mercado do terminal **AE Broadcast** (Agência Estado / Broadcast+), oferecendo cotações em tempo real via DDE e dados históricos via HTTP ContentProxy.

Funciona como alternativa ao Bloomberg `blpapi`/`xbbg` — conecta programaticamente ao terminal Broadcast já em execução para extrair cotações da B3 e outros mercados.

## Requisitos

- Windows 10/11
- Python 3.12+ com `pywin32`, `requests`
- Terminal Broadcast rodando (`bcsys32.exe` ativo)

```bash
pip install pywin32 requests
```

## Uso Rápido

```python
from broadcast import BroadcastClient, bdp, bdps, bdh, bdh_ohlcv

# One-shot (estilo bdp do Bloomberg)
price = bdp("PETR4", "ULT")        # '44,60'
data = bdp("PETR4", ["ULT", "VAR", "MAX", "MIN", "FEC", "NOM"])

# Batch (múltiplos ativos)
result = bdps(
    ["PETR4", "VALE3", "ITUB4", "IBOV", "USDBRL"],
    ["ULT", "VAR"]
)

# Snapshot completo (todos os campos de uma vez)
with BroadcastClient() as bc:
    snap = bc.snapshot("PETR4")  # ~47 campos

# Streaming em tempo real
with BroadcastClient() as bc:
    bc.subscribe(
        ["PETR4", "VALE3", "IBOV"],
        ["ULT", "VAR", "NEG"],
        callback=lambda ticker, field, value: print(f"{ticker}.{field} = {value}")
    )
    bc.run(duration=60)

# Dados históricos (estilo BDH do Bloomberg)
import os
os.environ["BROADCAST_SESSION"] = "<session_token>"

data = bdh(["PETR4", "VALE3"], "20260501", "20260519")
for sym, rows in data.items():
    for row in rows:
        print(f"{sym} {row['date']}: {row['last']}")

# OHLCV completo (single day)
candle = bdh_ohlcv("PETR4", "20260519")
# {'open': '45.99', 'high': '46.3', 'low': '45.59', 'last': '46.09', ...}
```

## Ativos Suportados

| Classe         | Exemplos                          | Status |
|---------------|-----------------------------------|--------|
| Ações B3       | PETR4, VALE3, ITUB4, BBDC4, B3SA3 | OK |
| FIIs           | HGLG11, MXRF11                    | OK |
| BDRs           | AAPL34, MSFT34                    | OK |
| Índices        | IBOV, IFIX, SMLL, IDIV           | OK |
| Câmbio         | USDBRL, EURBRL                    | OK |
| DI Futuro      | DI1F27 (vencimentos selecionados) | Parcial |
| Mini Dólar/Índice | WDOM25, WINM25               | N/A* |
| Dólar/Índice Cheio | DOLFUT, INDFUT              | N/A* |

\* Futuros BM&F retornam N/A — provavelmente requer assinatura específica no terminal.

## Campos Principais

| Campo | Descrição |
|-------|-----------|
| ULT   | Último preço |
| VAR   | Variação % |
| MAX   | Máxima do dia |
| MIN   | Mínima do dia |
| ABE   | Abertura |
| FEC   | Fechamento anterior |
| OCP   | Oferta de compra (bid) |
| OVD   | Oferta de venda (ask) |
| NEG   | Número de negócios |
| QTT   | Quantidade total negociada |
| NOM   | Nome do ativo |
| HOR   | Hora da última cotação |

Veja `docs/fields.md` para a lista completa.

## Limitações

- **HistoricoDiario (OHLCV range)**: Requer query pré-registrada via protocolo AETP binário. Workaround: usar `bdh()` para fechamentos em range + `bdh_ohlcv()` por dia.
- **Book de ofertas (LIVRO)**: Tópico DDE aceita conexão mas retorna vazio.
- **Futuros BM&F**: Maioria retorna N/A (possível restrição de assinatura).
- **Session token**: `bdh()`/`bdh_ohlcv()` requerem token BCAA extraído do processo (expira periodicamente).
- **Requer message pump**: O streaming (`bc.run()`) bloqueia a thread para processar mensagens Windows.

## Arquitetura

Veja `docs/architecture.md` para detalhes técnicos dos protocolos DDE e ContentProxy HTTP.

## Estrutura do Projeto

```
broadcast.py              # Cliente principal (DDE real-time + HTTP histórico)
test_broadcast_client.py  # Teste de integração DDE
docs/
  architecture.md        # Arquitetura completa (DDE, ContentProxy, AETP)
  fields.md              # Referência completa de campos DDE (56 campos)
  services.xml           # Registry original de 213 serviços HTTP
  services_parsed.json   # services.xml parseado como JSON
  chm_extracted/         # Documentação original do Broadcast+ (HTML)
research/
  contentproxy_client.py # Client HTTP standalone (referência)
  parse_services_xml.py  # Parser de services.xml
  parse_camposbc.py      # Parser de camposbc.tab → fields.md
  generate_fields_doc.py # Gerador de docs/fields.md
  dde_advise_test.py     # Teste standalone de streaming DDEML
  dde_all_topics.py      # Mapeamento de tópicos DDE
  dde_explore_topics.py  # Exploração profunda de tópicos/itens
  dde_tickers.py         # Descoberta de tickers válidos
  analyze_aetp.py        # Análise de arquivos binários AETP
  probe_aetp_tcp.py      # Exploração do protocolo AETP TCP
  test_bdh.py            # Teste de integração bdh/bdh_ohlcv
  protocol_notes.md      # Notas sobre protocolos testados
```
