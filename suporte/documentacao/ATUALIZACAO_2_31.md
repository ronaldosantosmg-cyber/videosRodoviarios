# Atualização 2.31 (não validada pelo gate completo)
- Seção nova recorta a anterior: cadastrar pista simples dentro de eixo duplicado (ou o inverso) não dá mais "seções sobrepostas"; o trecho é dividido automaticamente (backend e janela de Seções).
- Eixo misto (trechos de um sentido + trechos de dois sentidos): sentido explícito continua orientando; testes cobrindo transições simples/dupla.
- Propriedades: campos internos somente leitura.
- Mudar só o sentido das vias invalida apenas trânsito/apresentação; geometria e vetores do DXF e imagens não são reprocessados (verificado por revisões).
