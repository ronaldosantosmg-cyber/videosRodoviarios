# Atualização 2.60 (não validada pelo gate completo)

## Por que demorava (medido nos seus logs e no projeto TH-57)

1. **Toda atualização invalidava todos os caches.** A "assinatura" da geometria incluía o hash de *todo* o código; mudar qualquer arquivo (inclusive tela, texturas, IA) forçava reler o DXF e recalcular tudo na abertura (~5,5 min no seu log).
2. A análise (`analyze`) não usava o cache de geometria: relia o DXF (17–18 s) em toda abertura.
3. Água/hidrografia alocava matrizes enormes (> 5 GB de pico): agora processa em blocos.
4. Cada polígono criava máscaras do tamanho do mapa inteiro (~40 s): agora usa só a janela do polígono.
5. Distância de Hausdorff (fluxos/pedestres) por GEOS: 15–25 s; agora via STRtree (60 mil pontos: 0,6 s contra 19,8 s, valores idênticos).
6. Quadro de visão geral (~66 s): quase tudo era a checagem de colisão dos veículos criando milhares de polígonos shapely e 6 interpolações por pose; agora 1 interpolação e varredura direta pelos cantos (resultado geométrico idêntico, coberto por teste).

## O que mudou na 2.60
- Cache de geometria assinado só pelo código que de fato afeta a geometria (`dependencies.geometry_cache_key`); atualizações de tela/textura/IA não recalculam mais.
- `analyze` aproveita o cache; água em blocos; máscara por ROI; Hausdorff rápido; varredura de colisão vetorizada.
- Pacote **leve** (`base_version`): só os arquivos alterados, verificação em segundos em vez de 40–75 s.

## Medição (nuvem, TH-57, não no seu PC)
Abertura fria ~100 s (antes ~330 s); com cache quente: Scene ~28 s + quadro ~30–40 s. Pico de memória 2,6 GB.

## Limites
Ainda não validado pelo gate completo; 3 falhas em testes de tráfego já estavam na linha-base provisória. O restante do tempo é a simulação de tráfego, que continua sendo o maior custo. Faltam: refresh automático na abertura quando os artefatos estão válidos e redução do polling.
