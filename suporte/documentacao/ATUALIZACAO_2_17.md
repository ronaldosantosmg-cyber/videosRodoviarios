# Atualização 2.17 (não validada pelo gate completo)

Problema: a "Atualização completa" parava em 25% (Geometria pronta) e a barra não andava.

Diagnóstico: com o DXF TH53 a geometria, os fluxos e o editor concluem em ~38 s sem travar. A etapa seguinte (download de ladrilhos de imagem e rasterização da prévia) não informava andamento, e sem rede rápida ficava minutos parada.

Correção:
- `progress_pulse.py`: batimento que move a barra (26% a 92%) e mostra os segundos decorridos, mantendo o sinal de vida do supervisor.
- `detail.prefetch`: progresso a cada ~0,4 s e orçamento de 120 s; esgotado, segue sem a imagem detalhada (modo offline) em vez de ficar parado.
- Worker: pulso encerrado em sucesso, erro ou cancelamento.
- Teste novo: `tests/test_v14246_progresso_longo.py`.
