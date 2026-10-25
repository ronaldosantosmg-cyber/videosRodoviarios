# Rodovia Studio 1.42.18

## Fontes de tráfego e indicação de sentido

Somente camadas designadas **Eixo** e trajetórias escolhidas explicitamente alimentam o tráfego. O pavimento não gera mais eixos por esqueleto, mesmo quando uma configuração antiga contém derive_traffic_paths=true. Bordos, hachuras e linhas de referência não são eixos automaticamente. KMZ sem designação explícita continua disponível como referência geográfica; para circular, designe-o como eixo/sentido ou selecione uma rota.

Uma linha selecionada como rota com sentido definido funciona mesmo se não houver camada Eixo no DXF. Trajetórias manuais usam a ordem dos pontos quando não houver outro sentido explícito. As linhas originais permanecem intactas.

A indicação de sentido entre início e fim é projetada no eixo e altera somente o intervalo correspondente. O motor subdivide a derivação, aplica o sentido real e recalcula automaticamente depois de concluir a edição. Intervalos menores que 5 m, sem associação ou equidistantes de duas pistas ficam pendentes de conferência. Em pistas paralelas, indique a faixa correta ou selecione explicitamente a linha. Uma inversão incompatível com o restante da via não cria retornos de 180° nem atalhos: revise as conexões na central Corrigir fluxos.

## Camadas gráficas

Canvas de interação com dois caches auxiliares: fundo aéreo e projeto técnico, agora incluindo marcações e hachuras. O fundo é reutilizado quando só a configuração técnica muda. Edição, desfazer, câmera e novos ladrilhos invalidam os dados pertinentes. Durante o arraste de pan as marcações usam o desenho direto do editor, preservando a sequência de composição; o cache técnico é recomposto no próximo quadro estável. Sem redução da resolução ou arredondamento das coordenadas originais. Orçamento de 32 MiB para os pixels RGBA dos dois caches (não é medição da memória total de RAM/GPU); desenho direto quando faltar memória/contexto. No 3D continua existindo um único contexto WebGL, com grupos e recursos compartilhados.

## Pedestres

Agentes locais de regras com espera, travessia, chegada, reserva de espaço e passos de cessão para resolver encontros. Não é um modelo de linguagem nem comportamento humano calibrado. A mesma simulação fornece posições para planta, 3D e vídeo.

Pedestres usam faixas cadastradas, calçadas e passarelas. Caminhos informais sobre pista/ferrovia são recusados. Faixas com espera sobre trilhos são recusadas. Aproximação de trem considera pelo menos 50 m, a duração prevista da travessia e toda a composição; a faixa não é liberada antes da passagem completa. Veículos respeitam a ocupação da faixa, com retenção e proteção contra ultrapassagem junto à travessia. Semáforos associados exigem fase de pedestres suficiente. Faixas insuficientes permanecem em espera e geram aviso. Passarelas precisam alcançar área segura fora da pista/trilhos e adotam o gabarito configurado acima do maior nível cruzado; cotas reais ainda exigem conferência técnica.

Máximo de 80 pessoas simultâneas, 300 percursos e histórico numérico limitado. Semente reproduzível disponível nas opções dos pedestres. Auditorias detectam sobreposição entre pessoas, veículos e trens; conflito interrompe a exportação em vez de produzir um vídeo inseguro. Isso não constitui garantia universal de ausência de colisões em qualquer entrada.

## Fumaça ferroviária

Partículas reprodutíveis, aleatoriedade lateral limitada e componente longitudinal contrária ao trem. Marcha reversa usa a orientação real da locomotiva. Dez partículas por locomotiva, máximo de 240 simultâneas, sem novos contextos WebGL. Mesma fórmula no render 2D e WebGL; opção Fumaça dos trens para desativar. Faróis noturnos permanecem.

## Validação e limites

Validação direcionada autorizada pelo usuário: cálculo, edição/desfazer, dados de origem, sentido por intervalo, travessias, colisões, trem de 100 vagões, 2D, WebGL e MP4 decodificado. Resultados detalhados em suporte/documentacao/validacao_1_42_18/. Medições sintéticas não representam FPS ou memória de um projeto real. Windows/WebView2 nativo, carga prolongada e calibração de tráfego/pedestres não foram certificados nesta revisão. Preserva projetos, vídeos, KMZ, cache de GeoTIFF e rollback.
