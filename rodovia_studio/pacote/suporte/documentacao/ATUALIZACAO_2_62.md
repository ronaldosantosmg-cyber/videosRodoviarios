# Atualização 2.62 (não validada pelo gate completo)

## Balanço da tela que movia objetos (gravação de tela de 31/10)
Causa: ao abrir ou fechar o painel Propriedades, o canvas muda de largura. `resizeCanvas` reescalava o zoom (k=w/largura) e mantinha o centro, e em seguida a restauração de viewport reancorava o mapa no ponto do cursor. O mapa mudava de zoom e deslizava a cada abertura/fechamento; o clique ou arrasto seguinte caía em outro objeto.

Correção:
- Redimensionar não altera zoom nem posição do mapa (só recorta/amplia a área visível); apenas a mudança de densidade de pixels do monitor reescala.
- A restauração após resize/regeneração só preserva a seleção, sem recentrar nem reancorar.
- Cliques nos 350 ms seguintes a uma mudança de layout são ignorados.
- Zona morta de 5 px no arrasto de objetos e vértices: tremor da mão não move mais nada.
Teste: `test_v14294_redimensionar_sem_balancar.py` (node). Não validado em navegador real.
