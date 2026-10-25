# Rodovia Studio 1.42.18 — validação direcionada

Fontes de tráfego: eixos designados e seleção explícita com sentido; pavimento não gera esqueleto de circulação. KMZ não designado continua referência. Sentido por início/fim aplica-se somente ao intervalo projetado, altera as trajetórias e aciona recálculo após a edição. Ambiguidades e intervalos menores que 5 m exigem revisão; não há criação de retorno ou atalho para contornar uma inversão incompatível. Camadas e arquivos originais não são alterados.

Camadas gráficas: fundo e projeto técnico (incluindo hachuras e marcações) em dois caches auxiliares, com canvas principal de interação. Câmera, edição, desfazer e ladrilhos invalidam o conteúdo pertinente. Durante pan as marcações seguem o desenho direto do editor. Orçamento de 32 MiB em pixels RGBA, não memória total de RAM/GPU; fallback quando excedido. Um único contexto WebGL para o 3D, com recursos compartilhados.

Pedestres: controle local com espera, reservas, cessão de espaço, fases, retenção dos veículos e proteção contra ultrapassagem junto a travessias. Caminhos informais sobre pista/trilhos e espera sobre ferrovia são rejeitados. Aproximação ferroviária considera pelo menos 50 m e toda a composição; ensaio com 100 vagões confirmou espera e liberação posterior. Passarelas usam gabarito acima dos níveis cruzados e precisam alcançar área segura. Mesmo histórico fornece 2D/3D/vídeo; auditorias interrompem a exportação em caso de conflito detectado. Não é calibração de comportamento humano nem garantia universal de ausência de colisão.

Fumaça: relógio e semente reproduzíveis, componente oposta ao deslocamento e dispersão lateral limitada, inclusive marcha inversa. Mesma fórmula Python/WebGL, máximo de 240 partículas, opção para desativar.

80 testes distintos aprovados em 96 execuções, sem falhas/erros/ignorados. Incluem motor de sentido acionado pela interface, fontes autorizadas, escolha de linha sem camada Eixo, colisões entre corpos, fases, trem de 100 vagões, pare e siga, ultrapassagens, edição/desfazer, quadro completo com tolerância de rasterização de três níveis, duas exportações MP4 de 72 quadros (2D e WebGL), decodificação e repetição de quadro fora de ordem. 79 casos na execução principal e 17 verificações finais do cache/pan, com 16 repetições e um caso adicional.

DXF disponível de regressão: 31 eixos e seis fluxos revalidados, original preservado. Não é o projeto salvo atual do usuário.

Medição sintética, Chromium/Linux, 1366×900 e 100 hachuras: p50 estático 5,9→0,8 ms em DPI1 e 15,6→2,4 ms em DPI2. Pan p95 8,3→10,5 ms em DPI1 e 26,7→25,5 ms em DPI2; há variação/custo residual durante a navegação, portanto não se afirma ganho universal. Área gráfica idêntica: 644.280 px². Dados em medicoes.json; não são FPS de projeto real, teste Windows, carga prolongada ou memória total da GPU.

ZIP aplicado sobre 1.42.17, inicialização fora da raiz e encerramento controlado aprovados. Instalação movida e rollback para 1.42.17 restauraram o programa byte a byte. Sentinelas de KMZ, cache persistente de GeoTIFF e vídeos preservadas. Splash compilado com e sem WebView2 e conferido por Mono/Xvfb, incluindo retorno à pose inicial.

Validação direcionada solicitada pelo usuário; suíte integral, Windows/WebView2 nativo, calibração e uso intenso prolongado não executados nesta revisão. Nota provisória de prontidão: 7/10.

Pacote: atualizacoes/RodoviaStudio_1_42_18_atualizacao.zip
SHA-256: 23ec09bb099a5a38844faff935aad20209ecec5b2171496be40e0f5d29b44e44
