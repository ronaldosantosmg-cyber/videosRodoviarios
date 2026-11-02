# Atualização 2.21 (não validada pelo gate completo)
- Sentido Crescente/Decrescente do eixo (Circulação > Sentido da via) agora orienta as faixas da seção cadastrada sobre ele. Antes o eixo substituído pela seção era ignorado e o seletor ficava travado.
  Precedência: nós de entrada/saída e sentido próprio da rota vencem; depois o do eixo.
  Seção de um só sentido percorrida ao contrário é espelhada e renumerada. O cache de faixas considera o sentido herdado.
- "Salvar e fechar" bloqueado por "O giro só se aplica a eixos classificados como rotatória": giro em eixo que não é rotatória é zerado (modelo) e a tela não o envia mais.
