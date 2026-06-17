# Broadcast Field Reference (Terminal Antigo)

**Source**: `camposbc.tab` — complete field mapping: BC_ID ↔ AETP_ID ↔ DDE_KEY

## Column Meanings

| Column | Description |
|--------|-------------|
| `BC_ID` | Internal field index (0-based) |
| `AETP_ID` | AETP binary protocol attribute number |
| `KEY` | DDE field name — used in `=BC("TICKER", "KEY")` and `TICKER.KEY` |
| `TYPE` | F=Float, V=Variation%, I=Integer, Q=Quantity, T=Text, H=Time, D=Date, O=Offset |
| `DESCRIPTION` | Portuguese description |

---

## All Fields

BC_ID |  AETP_ID | KEY            | TYPE   | DESCRIPTION
------+----------+----------------+--------+---------------------------------------------------
    0 |          | ATIVO          | T      | Código do ativo
    1 |     2663 | ULT            | F      | Valor da última cotação
    2 |    10066 | HOR            | H      | Hora da última cotação
    3 |          | VAR            | V      | Variação sobre último fechamento
    4 |      278 | MAX            | F      | Valor máximo no dia
    5 |      327 | MIN            | F      | Valor mínimo no dia
    6 |      407 | ABE            | F      | Valor de abertura no dia
    7 |     2663 | FEC            | F      | Valor do último fechamento
    8 |          | OCP            | F      | Oferta de compra
    9 |          | OVD            | F      | Oferta de venda
   10 |      901 | NEG            | I      | Número de negócios
   11 |          | QUL            | Q      | Quantidade do último negócio
   12 |      494 | MED            | F      | Valor médio no dia
   13 |          | VOC            | Q      | Volume da oferta de compra
   14 |          | VOV            | Q      | Volume da oferta de venda
   15 |      475 | QTT            | Q      | Quantidade total no dia
   16 |      475 | CNG            | I      | Número de contratos negociados
   17 |      406 | CAB            | I      | Número de contratos em aberto
   18 |      458 | AJU            | F      | Valor do último ajuste
   19 |          | HOC            | H      | Hora da oferta de compra
   20 |          | HOV            | H      | Hora da oferta de venda
   21 |          | TND            | I      | Seta de tendência
   22 |          | DIF            | O      | Variação nominal (diferença)
   23 |          | PCT            | V      | Variação porcentual
   24 |          | PEX            | F      | Preço de exercício
   25 |          | DFC            | D      | Data do último fechamento
   26 |          | CCP            | T      | Código da corretora de compra
   27 |          | QCC            | Q      | Quantidade de compra da corretora
   28 |          | CVD            | T      | Código da corretora de venda
   29 |          | QCV            | Q      | Quantidade de venda da corretora
   30 |          | TLN            | Q      | Tamanho do lote de negociação
   31 |          | DUT            | I      | Dias úteis
   32 |          | DCR            | I      | Dias corridos
   33 |          | YLD            | F      | Yield
   34 |          | QTR            | Q      | Quantidade teórica
   35 |          | PTR            | F      | Preço teórico
   36 |          | FCE            | F      | Fechamento eletrônico
   37 |          | DFE            | D      | Data do fechamento eletrônico
   38 |      474 | VTT            | Q      | Volume total
   39 |          | VPR            | Q      | Volume projetado
   40 |          | QPR            | Q      | Quantidade projetada
   41 |          | DVC            | D      | Data de vencimento
   42 |          | NCC            | T      | Corretora de compra no negócio
   43 |          | NCV            | T      | Corretora da venda no negócio
   44 |      476 | DRF            | D      | Data de referência
   45 |          | AJA            | F      | Ajuste anterior
   46 |          | OSI            | F      | Limite de oscilação mínimo
   47 |          | OSA            | F      | Limite de oscilação máximo
   48 |          | EST            | T      | Estado
   49 |          | NSQ            | I      | Número de saques
   50 |          | PJU            | F      | Preço justo
   51 |          | VIM            | Q      | Volatilidade implícita
   52 |          | VHI            | F      | Volatilidade histórica
   53 |          | DEL            | F      | Delta
   54 |          | GAM            | F      | Gamma
   55 |          | VEG            | F      | Vega
   56 |          | THE            | F      | Theta
   57 |          | RHO            | F      | Rho
   58 |          | INC            | F      | Indexador de Correção
   59 |    14127 | RPRC           | F      | Preço de Referência
   60 |          | PDI            | F      | Peso Diário
   61 |          | LMI            | F      | Limite móvel mínimo
   62 |          | LMA            | F      | Limite móvel máximo
   63 |          | RLM            | F      | Referência do limite móvel
   64 |          | ENI            | T      | Estado de Negociação do Instrumento
   65 |          | PRV            | T      | Provedor
   66 |          | PRZ            | I      | Prazo
   67 |          | DAJ            | D      | Data do ajuste
   68 |          | DAA            | D      | Data do ajuste anterior
   69 |          | VOR            | Q      | Volume em Reais
   70 |      459 | AJUT           | F      | Valor do ajuste em taxa
   71 |          | AJAT           | F      | Valor do ajuste anterior em taxa
   72 |          | INI0           | F      | Taxa mínima indicativa D0
   73 |          | INS0           | F      | Taxa máxima indicativa D0
   74 |          | INI1           | F      | Taxa mínima indicativa D+1
   75 |          | INS1           | F      | Taxa máxima indicativa D+1
   76 |          | DEM            | D      | Data de Emissão
   77 |          | SLC            | I      | Código Selic
   78 |          | DVP            | F      | Desvio Padrão
   79 |          | PU             | F      | Preço Unitário
   80 |          | TXA            |        | Taxa Anual de Juros
   81 |          | TXP            | F      | Taxa paga
   82 |          | VEX            | F      | Valor extrínseco
   83 |          | FHA            | F      | Fechamento anterior
   84 |          | DTA            | D      | Data do fechamento anterior
   85 |          | CPM            | F      | CUPOM
   86 |          | ISIN           | T      | ISIN
   87 |    13122 | CAPT           | Q      | Captação
   88 |    13126 | RESG           | Q      | Resgate
   89 |    13125 | PATR           | Q      | Patrimônio líquido
   90 |    13124 | QCOT           | Q      | Quantidade de cotistas
   91 |          | VOL1M          | F      | Volatilidade 1 mês
   92 |          | VOL6M          | F      | Volatilidade 6 meses
   93 |          | VOL1A          | F      | Volatilidade 1 ano
   94 |          | VOL2A          | F      | Volatilidade 2 anos
   95 |          | VOL3A          | F      | Volatilidade 3 anos
   96 |          | VOL4A          | F      | Volatilidade 4 anos
   97 |          | VOL5A          | F      | Volatilidade 5 anos
   98 |          | SINAL          | V      | Seta de variação
   99 |          | HRF            | U      | Hora UTC da última cotação
  100 |          | ATZ            | I      | Tempo de diferimento (minutos)
  101 |          | TZDIF          | I      | Diferença em minutos para UTC
  102 |          | HRS            | U      | Hora UTC da última atualização
  103 |          |                |        | NÃO UTILIZAR
  104 |          |                |        | NÃO UTILIZAR
  105 |          |                |        | NÃO UTILIZAR
  106 |          |                |        | NÃO UTILIZAR
  107 |          |                |        | NÃO UTILIZAR
  108 |          | HO1            | H      | T&T: Hora -1
  109 |          | HO2            | H      | T&T: Hora -2
  110 |          | HO3            | H      | T&T: Hora -3
  111 |          | HO4            | H      | T&T: Hora -4
  112 |          | AN1            | F      | T&T: Último -1
  113 |          | AN2            | F      | T&T: Último -2
  114 |          | AN3            | F      | T&T: Último -3
  115 |          | AN4            | F      | T&T: Último -4
  116 |          | VO1            | Q      | T&T: Quantidade -1
  117 |          | VO2            | Q      | T&T: Quantidade -2
  118 |          | VO3            | Q      | T&T: Quantidade -3
  119 |          | VO4            | Q      | T&T: Quantidade -4
  120 |          |                |        | NÃO UTILIZAR
  121 |          |                |        | NÃO UTILIZAR
  122 |          | HORABR         | H      | Hora da última (fuso Brasília)
  123 |          | CLIPE          | I      | Clipe de notícias
  124 |          | DESCR          | T      | Descrição do ativo
  125 |          | NOM            | T      | Nome do ativo
  126 |          | NADA           |        | Deixa a coluna vazia
  127 |          | INVALIDO       |        | MARCADOR DE CAMPO INVÁLIDO
  128 |          | VARMES         | V      | Variação no mês
  129 |          | VAR1MES        | V      | Variação em 1 mês
  130 |          | VARANO         | V      | Variação no ano
  131 |          | VAR1ANO        | V      | Variação em 1 ano
  132 |          | VARSEM         | V      | Variação na semana
  133 |          | VAR1SEM        | V      | Variação em 1 semana
  134 |          | VAR6MESES      | V      | Variação em 6 meses
  135 |          | VAR2ANOS       | V      | Variação em 2 anos
  136 |          | VAR3ANOS       | V      | Variação em 3 anos
  137 |          | VAR4ANOS       | V      | Variação em 4 anos
  138 |          | VAR5ANOS       | V      | Variação em 5 anos
  139 |          | FECMES         | F      | Fechamento do mês anterior
  140 |          | FEC1MES        | F      | Fechamento há 1 mês
  141 |          | FECANO         | F      | Fechamento ano anterior
  142 |          | FEC1ANO        | F      | Fechamento há 1 ano
  143 |          | FECSEM         | F      | Fechamento da semana anterior
  144 |          | FEC1SEM        | F      | Fechamento há 1 semana
  145 |          | FEC6MESES      | F      | Fechamento há 6 meses
  146 |          | FEC2ANOS       | F      | Fechamento há 2 anos
  147 |          | FEC3ANOS       | F      | Fechamento há 3 anos
  148 |          | FEC4ANOS       | F      | Fechamento há 4 anos
  149 |          | FEC5ANOS       | F      | Fechamento há 5 anos
  150 |          | TIPIN          | T      | Tipo de instrumento
  151 |          | DUC            | D      | Data da última cotação
  152 |    13585 | ULCP           | F      | Última oferta de compra
  153 |    13586 | DULCP          | D      | Data da última oferta de compra
  154 |    13587 | ULVD           | F      | Última oferta de venda
  155 |    13588 | DULVD          | D      | Data da última oferta de venda
  156 |    13589 | ULDV           | F      | Último dividendo
  157 |    13590 | DULDV          | D      | Data do último dividendo
  158 |    13591 | DVYLD          | V      | Taxa de retorno últimos 12 meses
  159 |    13592 | QTCT           | I      | Quantidade de cotas emitidas
  160 |    13593 | DAVL           | D      | Data de atualização de cotas
  161 |    13594 | MIN1ANO        | F      | Mínima em 1 ano
  162 |    13595 | DMIN1ANO       | D      | Data da mínima 1 ano
  163 |    13596 | MAX1ANO        | F      | Máxima 1 ano
  164 |    13597 | DMAX1ANO       | D      | Data da máxima 1 ano
  165 |    13598 | VFULT          | F      | Volume negociado último dia útil
  166 |    13599 | VM30D          | F      | Média volume negociado últimos 30 dias
  167 |    13600 | VM100D         | F      | Média volume negociado últimos 100 dias
  168 |    13601 | VM180D         | F      | Média volume negociado últimos 180 dias
  169 |    13602 | FNT            | T      | Ambiente de negociação
  170 |    13603 | PLIQ           | F      | Patrimônio líquido
  171 |          | TOF            | T      | Tipo da oferta: C(ompra) ou V(enda)
  172 |          | IAJ            | T      | Indicador de ajuste
  173 |          | HEL            | H      | Horário de encerramento do leilão
  174 |          | IPR            | T      | Indicador de pregão
  175 |          | MRC            | T      | Mercadoria
  176 |          | MSGS           | T      | Mensagem de status via provedor
  177 |          | CDC            | I      | Casas decimais
  178 |          | TCK            | F      | Ticker size
  179 |          | CPMFQ          | T      | Coupom Frequency
  180 |          | YLDA           | F      | Yield Ask
  181 |          | YLDB           | F      | Yield Bid
  182 |          | YLDV           | F      | Yield Vencimento
  183 |          | YLDW           | F      | Yield to Worst
  184 |          | SPD            | F      | Spread
  185 |          | SPDV           | F      | Spread Vencimento
  186 |    13664 | MCAP           | F      | Market Cap - Valor de Mercado
  187 |    13608 | ANODEM         | T      | Ano Demonstrativo
  188 |    13624 | ATVCC          | F      | Ativo Circulante Consolidado
  189 |    13625 | ATVCI          | I      | Ativo Circulante Individual
  190 |    13699 | ATVTC          | F      | Ativo Total Consolidado
  191 |    13700 | ATVTI          | F      | Ativo Total Individual
  192 |    13620 | CAPPC          | V      | Capital Próprio Consolidado
  193 |    13621 | CAPPI          | V      | Capital Próprio Individual
  194 |    13697 | CAPTC          | V      | Capital de Terceiros Consolidado
  195 |    13698 | CAPTI          | V      | Capital de Terceiros Individual
  196 |    13612 | DDEM           | D      | Data de atualização do demonstrativo
  197 |    13616 | DISPC          | F      | Disponibilidade Consolidado
  198 |    13617 | DISPI          | F      | Disponibilidade Individual
  199 |    13652 | DIVBC          | F      | Dívida Bruta Consolidado
  200 |    13653 | DIVBI          | F      | Dívida Bruta Individual
  201 |    13630 | DIVLC          | F      | Dívida Líquida Consolidado
  202 |    13631 | DIVLI          | F      | Dívida Líquida Individual
  203 |    13611 | DPER           | D      | Último dia do período do demonstrativo
  204 |    13686 | DQTCT          | D      | Data Última Cota
  205 |    13634 | EBTC           | F      | EBIT Consolidado
  206 |    13636 | EBTDC          | F      | EBITDA Consolidado
  207 |    13637 | EBTDI          | F      | EBITDA Individual
  208 |    13635 | EBTI           | F      | EBIT Individual
  209 |    13670 | ENDVC          | F      | Endividamento Consolidado
  210 |    13671 | ENDVI          | F      | Endividamento Individual
  211 |    13640 | ETPVLC         | F      | Valor da Empresa Consolidado
  212 |    13645 | ETPVLI         | F      | Valor da Empresa Individual
  213 |    13641 | EVEBC          | F      | EV/EBIT Consolidado
  214 |    13644 | EVEBDC         | F      | EV/EBITDA Consolidado
  215 |    13643 | EVEBDI         | F      | EV/EBITDA Individual
  216 |    13642 | EVEBI          | F      | EV/EBIT Individual
  217 |    13662 | FINAC          | F      | Financiamento Consolidado
  218 |    13663 | FINAI          | F      | Financiamento Individual
  219 |    13660 | GAFC           | F      | Grau de Alavancagem Consolidado
  220 |    13661 | GAFI           | F      | Grau de Alavancagem Individual
  221 |    13682 | GAOC           | F      | Grau de Alav. Oper. Consolidado
  222 |    13683 | GAOI           | F      | Grau de Alav. Oper. Individual
  223 |    13695 | IMPC           | V      | Impostos Consolidado
  224 |    13696 | IMPI           | V      | Impostos Individual
  225 |    13658 | INVEC          | F      | Investimento Consolidado
  226 |    13659 | INVEI          | F      | Investimento Individual
  227 |    13628 | LIQCC          | F      | Liquidez Corrente Consolidado
  228 |    13629 | LIQCI          | F      | Liquidez Corrente Individual
  229 |    13650 | LIQGC          | F      | Liquidez Geral Consolidado
  230 |    13651 | LIQGI          | F      | Liquidez Geral Individual
  231 |    13656 | LIQIC          | F      | Liquidez Imediata Consolidado
  232 |    13657 | LIQII          | F      | Liquidez Imediata Individual
  233 |    13632 | LIQSC          | F      | Liquidez Seca Consolidado
  234 |    13633 | LIQSI          | F      | Liquidez Seca Individual
  235 |    13693 | LPAC           | F      | Lucro Ação Consolidado
  236 |    13694 | LPAI           | F      | Lucro Ação Individual
  237 |    13676 | LUCLC          | F      | Lucro Líquido Consolidado
  238 |    13677 | LUCLI          | F      | Lucro Líquido Individual
  239 |    13654 | MARBC          | V      | Margem Bruta Consolidado
  240 |    13655 | MARBI          | V      | Margem Bruta Individual
  241 |    13638 | MAREC          | V      | Margem EBITDA Consolidado
  242 |    13639 | MAREI          | V      | Margem EBITDA Individual
  243 |    13674 | MARLC          | V      | Margem Líquida Consolidado
  244 |    13675 | MARLI          | V      | Margem Líquida Individual
  245 |    13684 | MAROC          | V      | Margem Operacional Consolidado
  246 |    13685 | MAROI          | V      | Margem Operacional Individual
  247 |    13667 | MCAPL          |        | Valor de Mercado Líquido
  248 |    13668 | MCAPU1         |        | Valor de Mercado Unit - Modelo 1
  249 |    13669 | MCAPU2         |        | Valor de Mercado Unit - Modelo 2
  250 |    13665 | MVAC           | F      | Valor de Mercado Agregado Consolidado
  251 |    13666 | MVAI           | F      | Valor de Mercado Agregado Individual
  252 |    13680 | OPERC          | F      | Operacional Consolidado
  253 |    13681 | OPERI          | F      | Operacional Individual
  254 |    13626 | PASCC          | F      | Passivo Circulante Consolidado
  255 |    13627 | PASCI          | F      | Passivo Circulante Individual
  256 |    13672 | PATRC          | F      | Patrimônio Líquido Consolidado
  257 |    13673 | PATRI          | F      | Patrimônio Líquido Individual
  258 |    13691 | QTC            | Q      | Qtd. de Cotas Total
  259 |    13687 | QTCON          | Q      | Qtd. de Cotas ON
  260 |    13688 | QTCOT          | Q      | Qtd. de Cotas ON em Tesouraria
  261 |    13689 | QTCPN          | Q      | Qtd. de Cotas PN
  262 |    13690 | QTCPT          | Q      | Qtd. de Cotas PN em Tesouraria
  263 |    13692 | QTCTT          | Q      | Qtd. de Cotas Total em Tesouraria
  264 |    13678 | RECLC          | F      | Receita Líquida Consolidado
  265 |    13679 | RECLI          | F      | Receita Líquida Individual
  266 |    13618 | RESBC          | F      | Resultado Bruto Consolidado
  267 |    13619 | RESBI          | F      | Resultado Bruto Individual
  268 |    13614 | ROAC           | V      | Retorno sobre Ativo Total Consolidado
  269 |    13615 | ROAI           | V      | Retorno sobre Ativo Total Individual
  270 |    13646 | ROEC           | V      | Retorno sobre Patrimônio Consolidado
  271 |    13647 | ROEI           | V      | Retorno sobre Patrimônio Individual
  272 |    13610 | TPPER          | T      | Tipo de Período
  273 |    13609 | TRIM           | T      | Trimestre
  274 |    13613 | TRIMF          | T      | Trimestre Fiscal
  275 |    13622 | VCXC           | F      | Variação de Caixa Consolidado
  276 |    13623 | VCXI           | F      | Variação de Caixa Individual
  277 |    13648 | VPAC           | F      | Valor Patrimonial Ação Consolidado
  278 |    13649 | VPAI           | F      | Valor Patrimonial Ação Individual
  279 |    13004 | CDCVM          | T      | Código CVM
  280 |    13705 | CACION         | T      | Controle Acionário
  281 |    12063 | NFANT          | T      | Nome Fantasia
  282 |    13702 | SETB3          | T      | Setor de Atuação B3
  283 |    13703 | SSETB3         | T      | Subsetor de Atuação B3
  284 |    13704 | SEGB3          | T      | Segmento B3
  285 |    12087 | SETCVM         | T      | Setor CVM
  286 |          | SETAE          | T      | Setor de Atuação AE
  287 |          | SSETAE         | T      | Subsetor de Atuação AE
  288 |          | SEGAE          | T      | Segmento AE
  289 |    13701 | MCAPT          | F      | Market Cap - Valor de Mercado
  290 |    13872 | QTCOC          | Q      | Quantidade de Cotas em Circulação ON
  291 |    13873 | QTCPC          | Q      | Quantidade de Cotas em Circulação PN
  292 |    13874 | QTCCT          | Q      | Quantidade de Cotas Total em Circulação
  293 |    13875 | FFON           | V      | FreeFloat ON
  294 |    13876 | FFPN           | V      | FreeFloat PN
  295 |    13877 | FFT            | V      | FreeFloat Total
  296 |    13878 | DIVT           | F      | Dividendos Total
  297 |    13879 | INVIN          | Q      | Quantidade de Investidores Institucionais
  298 |    13880 | INVPF          | Q      | Quantidade de Investidores PF
  299 |    13881 | INVPJ          | Q      | Quantidade de Investidores PJ
  300 |    13882 | INVT           | Q      | Quantidade de Investidores Totais
  301 |    13883 | RATLC          | I      | Resultados Antes Tributação Participação Consolidado
  302 |    13884 | RATLI          | I      | Resultados Antes Tributação Participação Individual
  303 |    13885 | IRCSC          | I      | Imposto de Renda e Contribuição Social Consolidado
  304 |    13886 | IRCSI          | I      | Imposto de Renda e Contribuição Social Individual
  305 |    13887 | CSTC           | I      | Custo Consolidado
  306 |    13888 | CSTI           | I      | Custo Individual
  307 |    13889 | PSVC           | I      | Passivos Consolidado
  308 |    13890 | PSVI           | d      | Passivos Individual
  309 |    13891 | PAYOC          | V      | Payout Consolidado
  310 |    13892 | PAYOI          | V      | Payout Individual
  311 |          | VAR2MESES      | V      | Variação em 2 meses
  312 |          | FEC2MESES      | F      | Fechamento há 2 meses
  313 |          | VAR3MESES      | V      | Variação em 3 meses
  314 |          | FEC3MESES      | F      | Fechamento há 3 meses
  315 |          | VAR4MESES      | V      | Variação em 4 meses
  316 |          | FEC4MESES      | F      | Fechamento há 4 meses
  317 |          | VAR5MESES      | V      | Variação em 5 meses
  318 |          | FEC5MESES      | F      | Fechamento há 5 meses
  319 |          | DIFSEM         | O      | Variação Nominal na semana (diferença)
  320 |          | DIF1SEM        | O      | Variação Nominal em 1 semana (diferença)
  321 |          | DIFMES         | O      | Variação Nominal no mês (diferença)
  322 |          | DIF1MES        | O      | Variação Nominal em 1 mês (diferença)
  323 |          | DIF2MESES      | O      | Variação Nominal em 2 meses (diferença)
  324 |          | DIF3MESES      | O      | Variação Nominal em 3 meses (diferença)
  325 |          | DIF4MESES      | O      | Variação Nominal em 4 meses (diferença)
  326 |          | DIF5MESES      | O      | Variação Nominal em 5 meses (diferença)
  327 |          | DIF6MESES      | O      | Variação Nominal em 6 meses (diferença)
  328 |          | DIFANO         | O      | Variação Nominal no ano (diferença)
  329 |          | DIF1ANO        | O      | Variação Nominal em 1 ano (diferença)
  330 |          | DIF2ANOS       | O      | Variação Nominal em 2 anos (diferença)
  331 |          | DIF3ANOS       | O      | Variação Nominal em 3 anos (diferença)
  332 |          | DIF4ANOS       | O      | Variação Nominal em 4 anos (diferença)
  333 |          | DIF5ANOS       | O      | Variação Nominal em 5 anos (diferença)
  334 |    13916 | VARDIA1        | V      | Variação em percentual desde o primeiro dia de cotação
  335 |    13917 | QNM180D        | Q      | Quantidade de Negócios Médios nos últimos 180 dias
  336 |    13918 | VMDUSEM        | Q      | Volume Médio na semana até D-1, dias úteis.
  337 |    13919 | VMSEM          | Q      | Volume Médio na semana até D-1, dias com cotação.
  338 |    13920 | VMDU1SEM       | Q      | Volume Médio 1 Semana até D-1, dias úteis.
  339 |    13921 | VM1SEM         | Q      | Volume Médio 1 Semana até D-1, dias com cotação.
  340 |    13922 | VMDUMES        | Q      | Volume Médio no mês até D-1, dias úteis.
  341 |    13923 | VMMES          | Q      | Volume Médio no mês até D-1, dias com cotação.
  342 |    13924 | VMDU1MES       | Q      | Volume Médio no último mês até D-1, dias úteis.
  343 |    13925 | VM1MES         | Q      | Volume Médio no último mês  até D-1, dias com cotação.
  344 |    13926 | VMDU2MESES     | Q      | Volume Médio nos últimos 2 meses até D-1, dias úteis.
  345 |    13927 | VM2MESES       | Q      | Volume Médio nos últimos 2 meses  até D-1, dias com cotação.
  346 |    13928 | VMDU3MESES     | Q      | Volume Médio nos últimos 3 meses até D-1, dias úteis.
  347 |    13929 | VM3MESES       | Q      | Volume Médio nos últimos 3 meses  até D-1, dias com cotação.
  348 |    13930 | VMDU4MESES     | Q      | Volume Médio nos últimos 4 meses até D-1, dias úteis.
  349 |    13931 | VM4MESES       | Q      | Volume Médio nos últimos 4 meses  até D-1, dias com cotação.
  350 |    13932 | VMDU5MESES     | Q      | Volume Médio nos últimos 5 meses até D-1, dias úteis.
  351 |    13933 | VM5MESES       | Q      | Volume Médio nos últimos 5 meses  até D-1, dias com cotação.
  352 |    13934 | VMDU6MESES     | Q      | Volume Médio nos últimos 6 meses até D-1, dias úteis.
  353 |    13935 | VM6MESES       | Q      | Volume Médio nos últimos 6 meses até D-1, dias com cotação.
  354 |    13936 | VMDUANO        | Q      | Volume Médio no ano até D-1, dias úteis.
  355 |    13937 | VMANO          | Q      | Volume Médio no ano até D-1, dias com cotação.
  356 |    13938 | VMDU1ANO       | Q      | Volume Médio em 1 ano até D-1, dias úteis.
  357 |    13939 | VM1ANO         | Q      | Volume Médio em 1 ano até D-1, dias com cotação.
  358 |    13940 | VMDU2ANOS      | Q      | Volume Médio em 2 anos até D-1, dias úteis.
  359 |    13941 | VM2ANOS        | Q      | Volume Médio em 2 anos até D-1, dias com cotação.
  360 |    13942 | VMDU3ANOS      | Q      | Volume Médio em 3 anos até D-1, dias úteis.
  361 |    13943 | VM3ANOS        | Q      | Volume Médio em 3 anos até D-1, dias com cotação.
  362 |    13944 | VMDU4ANOS      | Q      | Volume Médio em 4 anos até D-1, dias úteis.
  363 |    13945 | VM4ANOS        | Q      | Volume Médio em 4 anos até D-1, dias com cotação.
  364 |    13946 | VMDU5ANOS      | Q      | Volume Médio em 5 anos até D-1, dias úteis.
  365 |    13947 | VM5ANOS        | Q      | Volume Médio em 5 anos até D-1, dias com cotação.
  366 |    13948 | DEPC           | I      | Soma das Depreciações e Amortizações Consolidado
  367 |    13949 | DEPI           | I      | Soma das Depreciações e Amortizações Individual
  368 |    13950 | RECLTC         | F      | Receita Líquida do Trimestre Consolidado
  369 |    13951 | CSTTC          | F      | Custos do Trimestre Consolidado
  370 |    13952 | RESBTC         | F      | Resultado Bruto do Trimestre Consolidado
  371 |    13953 | EBTTC          | F      | EBIT do Trimestre Consolidado
  372 |    13954 | EBTDTC         | F      | EBITDA do Trimestre Consolidado
  373 |    13955 | EVEBTC         | F      | VF/EBIT do Trimestre Consolidado
  374 |    13956 | EVEBDTC        | F      | VF/EBITDA do Trimestre Consolidado
  375 |    13957 | RATLTC         | F      | RATL do Trimestre Consolidado
  376 |    13958 | IRCSTC         | F      | IRCSL do Trimestre Consolidado
  377 |    13959 | LUCLTC         | F      | Lucro Líquido do Trimestre Consolidado
  378 |    13960 | GAFTC          | F      | GAF do Trimestre Consolidado
  379 |    13961 | GAOTC          | F      | GAO do Trimestre Consolidado
  380 |    13962 | IMPTC          | V      | Impostos do Trimestre Consolidado
  381 |    13963 | ROETC          | V      | ROE do Trimestre Consolidado
  382 |    13964 | ROATC          | V      | ROA do Trimestre Consolidado
  383 |    13965 | LPATC          | F      | LPA do Trimestre Consolidado
  384 |    13966 | MARLTC         | V      | Margem Líquida do Trimestre Consolidado
  385 |    13967 | MAROTC         | V      | Margem Operacional do Trimestre Consolidado
  386 |    13968 | MARETC         | V      | Margem EBITDA do Trimestre Consolidado
  387 |    13969 | MARBTC         | V      | Margem Bruta do Trimestre Consolidado
  388 |    13970 | PAYOTC         | V      | Payout do Trimestre Consolidado
  389 |    13971 | OPERTC         | F      | Operacional do Trimestre Consolidado
  390 |    13972 | INVETC         | F      | Investimento do Trimestre Consolidado
  391 |    13973 | FINATC         | F      | Financiamento do Trimestre Consolidado
  392 |    13974 | VCXTC          | F      | Variação de Caixa do Trimestre Consolidado
  393 |    13975 | DEPTC          | F      | Depreciação do Trimestre Consolidado
  394 |    13976 | RECLAC         | F      | Receita Líquida Acumulado 12 meses Consolidado
  395 |    13977 | CSTAC          | F      | Custos Acumulado 12 meses Consolidado
  396 |    13978 | RESBAC         | F      | Resultado Bruto Acumulado 12 meses Consolidado
  397 |    13979 | EBTAC          | F      | EBIT Acumulado 12 meses Consolidado
  398 |    13980 | EBTDAC         | F      | EBITDA Acumulado 12 meses Consolidado
  399 |    13981 | EVEBAC         | F      | VF/EBIT Acumulado 12 meses Consolidado
  400 |    13982 | EVEBDAC        | F      | VF/EBITDA Acumulado 12 meses Consolidado
  401 |    13983 | RATLAC         | F      | RATL Acumulado 12 meses Consolidado
  402 |    13984 | IRCSAC         | F      | IRCSL Acumulado 12 meses Consolidado
  403 |    13985 | LUCLAC         | F      | Lucro Líquido Acumulado 12 meses Consolidado
  404 |    13986 | GAFAC          | F      | GAF Acumulado 12 meses Consolidado
  405 |    13987 | GAOAC          | F      | GAO Acumulado 12 meses Consolidado
  406 |    13988 | IMPAC          | V      | Impostos Acumulado 12 meses Consolidado
  407 |    13989 | ROEAC          | V      | ROE Acumulado 12 meses Consolidado
  408 |    13990 | ROAAC          | V      | ROA Acumulado 12 meses Consolidado
  409 |    13991 | LPAAC          | F      | LPA Acumulado 12 meses Consolidado
  410 |    13992 | MARLAC         | V      | Margem Líquida Acumulado 12 meses Consolidado
  411 |    13993 | MAROAC         | V      | Margem Operacional Acumulado 12 meses Consolidado
  412 |    13994 | MAREAC         | V      | Margem EBITDA Acumulado 12 meses Consolidado
  413 |    13995 | MARBAC         | V      | Margem Bruta Acumulado 12 meses Consolidado
  414 |    13996 | PAYOAC         | V      | Payout Acumulado 12 meses Consolidado
  415 |    13997 | OPERAC         | F      | Operacional Acumulado 12 meses Consolidado
  416 |    13998 | INVEAC         | F      | Investimento Acumulado 12 meses Consolidado
  417 |    13999 | FINAAC         | F      | Financiamento Acumulado 12 meses Consolidado
  418 |    14000 | VCXAC          | F      | Variação de Caixa Acumulado 12 meses Consolidado
  419 |    14001 | DEPAC          | F      | Depreciação Acumulado 12 meses Consolidado
  420 |    14002 | RECLTI         | F      | Receita Líquida do Trimestre Individual
  421 |    14003 | CSTTI          | F      | Custos do Trimestre Individual
  422 |    14004 | RESBTI         | F      | Resultado Bruto do Trimestre Individual
  423 |    14005 | EBTTI          | F      | EBIT do Trimestre Individual
  424 |    14006 | EBTDTI         | F      | EBITDA do Trimestre Individual
  425 |    14007 | EVEBTI         | F      | VF/EBIT do Trimestre Individual
  426 |    14008 | EVEBDTI        | F      | VF/EBITDA do Trimestre Individual
  427 |    14009 | RATLTI         | F      | RATL do Trimestre Individual
  428 |    14010 | IRCSTI         | F      | IRCSL do Trimestre Individual
  429 |    14011 | LUCLTI         | F      | Lucro Líquido do Trimestre Individual
  430 |    14012 | GAFTI          | F      | GAF do Trimestre Individual
  431 |    14013 | GAOTI          | F      | GAO do Trimestre Individual
  432 |    14014 | IMPTI          | V      | Impostos do Trimestre Individual
  433 |    14015 | ROETI          | V      | ROE do Trimestre Individual
  434 |    14016 | ROATI          | V      | ROA do Trimestre Individual
  435 |    14017 | LPATI          | F      | LPA do Trimestre Individual
  436 |    14018 | MARLTI         | V      | Margem Líquida do Trimestre Individual
  437 |    14019 | MAROTI         | V      | Margem Operacional do Trimestre Individual
  438 |    14020 | MARETI         | V      | Margem EBITDA do Trimestre Individual
  439 |    14021 | MARBTI         | V      | Margem Bruta do Trimestre Individual
  440 |    14022 | PAYOTI         | V      | Payout do Trimestre Individual
  441 |    14023 | OPERTI         | F      | Operacional do Trimestre Individual
  442 |    14024 | INVETI         | F      | Investimento do Trimestre Individual
  443 |    14025 | FINATI         | F      | Financiamento do Trimestre Individual
  444 |    14026 | VCXTI          | F      | Variação de Caixa do Trimestre Individual
  445 |    14027 | DEPTI          | F      | Depreciação do Trimestre Individual
  446 |    14028 | RECLAI         | F      | Receita Líquida Acumulado 12 meses Individual
  447 |    14029 | CSTAI          | F      | Custos Acumulado 12 meses Individual
  448 |    14030 | RESBAI         | F      | Resultado Bruto Acumulado 12 meses Individual
  449 |    14031 | EBTAI          | F      | EBIT Acumulado 12 meses Individual
  450 |    14032 | EBTDAI         | F      | EBITDA Acumulado 12 meses Individual
  451 |    14033 | EVEBAI         | F      | VF/EBIT Acumulado 12 meses Individual
  452 |    14034 | EVEBDAI        | F      | VF/EBITDA Acumulado 12 meses Individual
  453 |    14035 | RATLAI         | F      | RATL Acumulado 12 meses Individual
  454 |    14036 | IRCSAI         | F      | IRCSL Acumulado 12 meses Individual
  455 |    14037 | LUCLAI         | F      | Lucro Líquido Acumulado 12 meses Individual
  456 |    14038 | GAFAI          | F      | GAF Acumulado 12 meses Individual
  457 |    14039 | GAOAI          | F      | GAO Acumulado 12 meses Individual
  458 |    14040 | IMPAI          | V      | Impostos Acumulado 12 meses Individual
  459 |    14041 | ROEAI          | V      | ROE Acumulado 12 meses Individual
  460 |    14042 | ROAAI          | V      | ROA Acumulado 12 meses Individual
  461 |    14043 | LPAAI          | F      | LPA Acumulado 12 meses Individual
  462 |    14044 | MARLAI         | V      | Margem Líquida Acumulado 12 meses Individual
  463 |    14045 | MAROAI         | V      | Margem Operacional Acumulado 12 meses Individual
  464 |    14046 | MAREAI         | V      | Margem EBITDA Acumulado 12 meses Individual
  465 |    14047 | MARBAI         | V      | Margem Bruta Acumulado 12 meses Individual
  466 |    14048 | PAYOAI         | V      | Payout Acumulado 12 meses Individual
  467 |    14049 | OPERAI         | F      | Operacional Acumulado 12 meses Individual
  468 |    14050 | INVEAI         | F      | Investimento Acumulado 12 meses Individual
  469 |    14051 | FINAAI         | F      | Financiamento Acumulado 12 meses Individual
  470 |    14052 | VCXAI          | F      | Variação de Caixa Acumulado 12 meses Individual
  471 |    14053 | DEPAI          | F      | Depreciação Acumulado 12 meses Individual
  472 |    14054 | VOLDIARIA      | V      | Volatilidade ao dia, considerando um período de 1 ano
  473 |    14055 | VOLSEM         | V      | Volatilidade na semana
  474 |    14056 | VOL1SEM        | V      | Volatilidade na última semana
  475 |    14057 | VOLMES         | V      | Volatilidade no mês
  476 |    14058 | VOL1MES        | V      | Volatilidade em 1 mês
  477 |    14059 | VOL2MESES      | V      | Volatilidade em 2 meses
  478 |    14060 | VOL3MESES      | V      | Volatilidade em 3 meses
  479 |    14061 | VOL4MESES      | V      | Volatilidade em 4 meses
  480 |    14062 | VOL5MESES      | V      | Volatilidade em 5 meses
  481 |    14063 | VOL6MESES      | V      | Volatilidade em 6 meses
  482 |    14064 | VOLANO         | V      | Volatilidade no Ano
  483 |    14065 | VOL1ANO        | V      | Volatilidade em 1 ano
  484 |    14066 | VOL2ANOS       | V      | Volatilidade em 2 anos
  485 |    14067 | VOL3ANOS       | V      | Volatilidade em 3 anos
  486 |    14068 | VOL4ANOS       | V      | Volatilidade em 4 anos
  487 |    14069 | VOL5ANOS       | V      | Volatilidade em 5 anos
  488 |    14074 | ULDY           | V      | Último dividend yield (DY)
  489 |    14075 | DV12M          | F      | Soma dos dividendos nos útlimos 12 meses
  490 |    14076 | DVANO          | F      | Soma dos dividendos no ano corrente
  491 |          |                |        | NÃO UTILIZAR
  492 |          |                |        | NÃO UTILIZAR
  493 |    13830 | FFL            | V      | Free float
  494 |    13064 | RSCD           | V      | Risco ao dia
  495 |    13065 | RSCA           | V      | Risco ao ano
  496 |    13066 | BTAE           | V      | Beta AE
  497 |    13067 | CORIBV         | V      | Correlação IBOV
  498 |    13063 | KECP           | V      | KECAPM
  499 |    13068 | V1D95          | V      | Var 1 dia 95%
  500 |    13069 | V1D99          | V      | Var 1 dia 99%
  501 |    13070 | DPN            | D      | Data Primeiro Negócio
  502 |    13071 | PLC            | F      | PL Consolidado
  503 |    13072 | PLI            | F      | PL Individual
  504 |    13073 | PVPAC          | F      | Preço/VPA Consolidado
  505 |    13074 | PVPAI          | F      | Preço/VPA Individual
  506 |    13075 | DIFDIA1        | O      | Variação em pontos desde o primeiro dia de cotação
  507 |    13076 | VARD           | O      | Variação Diferencial
  508 |    13077 | VARP           | V      | Variação Percentual
  509 |    13078 | FECDIA1        | F      | Fechamento do primeiro dia de cotação
  510 |    13079 | DUR            | F      | Duration
  511 |    13080 | MESP           | I      | Mês
  512 |    13081 | ANOP           | I      | Ano
  513 |    13082 | MESB           | I      | Mês Base
  514 |    13083 | ANOB           | I      | Ano Base
  515 |    13084 | PISO           | F      | Piso
  516 |    13085 | TETO           | F      | Teto
  517 |    13086 | QINST          | I      | Quantidade de Instituições
  518 |    13087 | ULTR           | F      | Preço - Último Pregão Regular
  519 |    13088 | PUOP           | I      | P.U OPERAÇÃO
  520 |    13089 | PUIND          | I      | P.U INDICATIVO
  521 |    13090 | PUP            | F      | PU PAR
  522 |    13091 | PUMAX          | F      | PU MAX
  523 |    13092 | PUMIN          | F      | PU MIN
  524 |    13093 | PUVAR          | F      | % PU PAR
  525 |    13094 | TXIND          | T      | Taxa Indicativa
  526 |    13095 | TXC            | I      | Taxa de Compra
  527 |    13096 | TXV            | I      | Taxa de Venda
  528 |    13097 | IND            | T      | Indexador
  529 |    13098 | VNE            | I      | VNE
  530 |    13099 | VNA            | I      | VNA
  531 |    13100 | DDIA           | F      | Duration Dias
  532 |    13101 | DANO           | F      | Duration Ano
  533 |    13102 | DEV            | T      | Devedor
  534 |    13103 | RAT            | T      | Rating
  535 |    13104 | CLA            | T      | Classe
  536 |    13105 | SECON          | T      | Setor Econômico
  537 |    13106 | AMRTZ          | I      | Amortização
  538 |    13107 | EXPJUR         | I      | Expectativa de Juros
  539 |    13108 | MOE            | T      | Moeda do Preço
  540 |    13109 | INVMIN         | F      | Investimento Mínimo
  541 |    13110 | REFBND         | T      | ReferenceBond
  542 |    13111 | SREFBND        | I      | SpreadToReferenceBond
  543 |    13112 | ISSUER         | T      | Issuer
  544 |    13113 | LCL            | T      | Localização
  545 |    13114 | CLAPOB         | T      | Classificação de prioridade da obrigação
  546 |    13115 | EVCRED         | T      | Eventos de crédito
  547 |    13116 | VOL5C          | F      | Volatilidade 5C
  548 |    13117 | VOL5CS         | F      | Volatilidade 5C Strike
  549 |    13118 | VOL5P          | F      | Volatilidade 5P
  550 |    13119 | VOL5PS         | F      | Volatilidade 5P Strike
  551 |    13120 | VOL10C         | F      | Volatilidade 10C
  552 |    13121 | VOL10CS        | F      | Volatilidade 10C Strike
  553 |    13122 | VOL10P         | F      | Volatilidade 10P
  554 |    13123 | VOL10PS        | F      | Volatilidade 10P Strike
  555 |    13124 | VOL15C         | F      | Volatilidade 15C
  556 |    13125 | VOL15CS        | F      | Volatilidade 15C Strike
  557 |    13126 | VOL15P         | F      | Volatilidade 15P
  558 |    13127 | VOL15PS        | F      | Volatilidade 15P Strike
  559 |    13128 | VOL20C         | F      | Volatilidade 20C
  560 |    13129 | VOL20CS        | F      | Volatilidade 20C Strike
  561 |    13130 | VOL20P         | F      | Volatilidade 20P
  562 |    13131 | VOL20PS        | F      | Volatilidade 20P Strike
  563 |    13132 | VOL25C         | F      | Volatilidade 25C
  564 |    13133 | VOL25CS        | F      | Volatilidade 25C Strike
  565 |    13134 | VOL25P         | F      | Volatilidade 25P
  566 |    13135 | VOL25PS        | F      | Volatilidade 25P Strike
  567 |    13136 | VOL30C         | F      | Volatilidade 30C
  568 |    13137 | VOL30CS        | F      | Volatilidade 30C Strike
  569 |    13138 | VOL30P         | F      | Volatilidade 30P
  570 |    13139 | VOL30PS        | F      | Volatilidade 30P Strike
  571 |    13140 | VOL35C         | F      | Volatilidade 35C
  572 |    13141 | VOL35CS        | F      | Volatilidade 35C Strike
  573 |    13142 | VOL35P         | F      | Volatilidade 35P
  574 |    13143 | VOL35PS        | F      | Volatilidade 35P Strike
  575 |    13144 | VOL40C         | F      | Volatilidade 40C
  576 |    13145 | VOL40CS        | F      | Volatilidade 40C Strike
  577 |    13146 | VOL40P         | F      | Volatilidade 40P
  578 |    13147 | VOL40PS        | F      | Volatilidade 40P Strike
  579 |    13148 | VOL45C         | F      | Volatilidade 45C
  580 |    13149 | VOL45CS        | F      | Volatilidade 45C Strike
  581 |    13150 | VOL45P         | F      | Volatilidade 45P
  582 |    13151 | VOL45PS        | F      | Volatilidade 45P Strike
  583 |    13152 | VOL50C         | F      | Volatilidade 50C
  584 |    13153 | VOL50CS        | F      | Volatilidade 50C Strike
  585 |    13154 | VOL50P         | F      | Volatilidade 50P
  586 |    13155 | VOL50PS        | F      | Volatilidade 50P Strike
  587 |    13156 | VOLATM         | F      | Volatilidade ATM
  588 |    13157 | VOLATMS        | F      | Volatilidade ATM Strike
  589 |    13158 | CLSF           | T      | Classificação
  590 |    13159 | REFD           | D      | Data Referencial
  591 |    13160 | REUNE          | F      | % REUNE
  592 |    13161 | TXF            | F      | Taxa de Financiamento
  593 |    13162 | VIN            | F      | Valor intrínseco
  594 |    13163 | CNPJ           | T      | CNPJ
  595 |    13164 | CVMFND         | T      | Código CVM Fundo
  596 |    13165 | DINI           | D      | Data Início Atividades
  597 |    13166 | RFREE          | F      | Taxa Risk Free
  598 |    13167 | SCCIR          | F      | Spread Crédito com IR
  599 |    13168 | SCSIR          | F      | Spread Crédito sem IR
  600 |    13169 | TNEG           | T      | Tipo Negócio
  601 |    13170 | CTP            | T      | Código Cetip
  602 |    13171 | TQLC           | Q      | Quantidade total de compra em aberto
  603 |    13172 | TQLV           | Q      | Quantidade total de venda em aberto
  604 |    13173 | TOLC           | Q      | Total de ofertas de compra
  605 |    13174 | TOLV           | Q      | Total de ofertas de venda
  606 |    13175 | UNI            | T      | Unidade de Medida
  607 |    13176 | PUULT          | F      | PU Último
  608 |    13177 | PUMTM          | F      | PU Marcação a Mercado
  609 |    13188 | PUMED          | F      | PU Médio
  610 |    13178 | PUFEC          | F      | PU Fechamento
  611 |    13179 | PUABE          | F      | PU Abertura
  612 |    13180 | PUOCP          | F      | PU Oferta de Compra
  613 |    13181 | PUOVD          | F      | PU Oferta de Venda
  614 |    13182 | PUTR           | F      | PU Teórico
  615 |    13183 | QMR            | Q      | Quantidade Máxima RFQ
  616 |    13184 | QMV            | Q      | Quantida de Máxima Voice
  617 |    13185 | LLI            | F      | Limite de Leilão Inferior
  618 |    13186 | LLA            | F      | Limite de Leilão Superior
  619 |    13187 | LRI            | F      | Limite de Rejeição Inferior
  620 |    13188 | LRA            | F      | Limite de Rejeição Superior
  621 |    13189 | TIPO           | T      | Tipo de Ativo
  622 |    13190 | TPRE           | T      | Tipo de Preço
  623 |    13191 | SPDT           | T      | SubTipo de Produto
  624 |    13192 | VTMIN          | F      | Variação Mínima Taxa
  625 |    13193 | LIQ            | T      | Liquidação
  626 |    13194 | PBR            | F      | Preço Bruto
  627 |    13195 | PEQ            | F      | Taxa/Preço equivalente
  628 |    13196 | TIR            | F      | Taxa interna de retorno
  629 |    13197 | DURM           | F      | Duração modificada
  630 |    13198 | CNVX           | F      | Convexidade
  631 |    13199 | MRGM           | F      | Margem
  632 |    13200 | BETA0          | F      | Valor beta0
  633 |    13201 | BETA1          | F      | Valor beta1
  634 |    13202 | BETA2          | F      | Valor beta2
  635 |    13203 | BETA3          | F      | Valor beta3
  636 |    13204 | FLXTT          | F      | Fluxo total
  637 |    13205 | SAMR           | F      | Saldo a amortizar
  638 |    13206 | PDT            | T      | Produto
  639 |    13207 | LSI            | F      | Limite Estático Inferior
  640 |    13208 | LSA            | F      | Limite Estático Superior
  641 |    13209 | FHE            | F      | Fator Hedge
  642 |    13210 | QLO            | F      | Quantidade Mínima Ordem
  643 |    13211 | QHO            | F      | Quantidade Máxima Ordem


**Total: 644 fields**
