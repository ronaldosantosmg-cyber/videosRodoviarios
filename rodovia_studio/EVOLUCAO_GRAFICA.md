# Edição CAD e visualização 3D

## Situação inspecionada

O editor usa Canvas 2D e coordenadas JavaScript Number (precisão dupla). Há
coordenadas digitadas, snap/orto, edição por grips e uma consulta de vértices
originais do desenho em `17_transformacoes_snap.js`. A visualização vetorial é
simplificada: a interface informa tolerância de 0,25 m. Os dados enviados ao
editor de fluxos também sofrem amostragem e arredondamento em `render.py`.
Essas representações não devem virar a fonte de geometria para uma edição CAD
que exija tolerâncias menores. A precisão do clique também depende de zoom,
DPI, seleção e transformação entre coordenadas de projeto e tela.

A 1.42.3 escondeu a barra original e ofereceu o catálogo num menu. Isso não
restabeleceu a experiência dos botões da 1.39. A 1.42.4 acrescenta a faixa visível
completa de ícones, ajuda ao passar o mouse e filtros por grupo. Os testes
conferem todos os identificadores originais como botões acessíveis.
A melhoria vale para qualquer projeto, sem usar nomes ou coordenadas do TH53.

## Arquitetura recomendada (ainda não implementada)

1. **Modelo geométrico independente da tela.** Fonte original de linhas, arcos,
   bulges e splines; cálculos em float64, unidades explícitas, operações
   reversíveis, coordenadas de projeto preservadas. Tolerância geométrica não
   deve ser confundida com número de casas decimais ou precisão geográfica.
2. **Edição 2D.** Canvas 2D ou SVG para apresentação, com seleção espacial e
   snapping na geometria original. Retas/arcos/splines exigem operações próprias
   e testes de interseção, tangência, perpendicularidade e transformação.
   SVG facilita vetores e eventos por objeto em cenas pequenas; grandes DXFs
   podem custar caro em elementos DOM. Trocar para SVG não recupera dados já
   simplificados nem garante precisão CAD.
3. **Visualização 3D.** Three.js ou Babylon.js sobre WebGL2, usando a mesma
   geometria/rede e estados de veículos do motor. Terreno, materiais, luz,
   sombras, câmeras e animação são etapas próprias. WebGL também usa Canvas;
   seu benefício é a GPU, não maior precisão numérica automática. Coordenadas
   UTM devem ser convertidas para uma origem local antes de buffers float32 da
   GPU. Modelo e salvamento continuam nas coordenadas originais float64.
4. **Renderização de apresentação.** Integração opcional com Unreal para um
   resultado próximo do Twinmotion, com sincronização/exportação explícita de
   cena, materiais, terreno e animação. Isso requer ferramentas e recursos
   adicionais e não transforma o editor atual em Twinmotion. WebGPU pode ser
   avaliado depois, conforme suporte real do navegador/WebView2 e GPU.

## Critérios antes da migração

- Validação de ida/volta projeto↔tela com coordenadas UTM, zooms e DPI diversos.
- Snap e seleção usam a geometria original; uma prévia simplificada é somente
  uma representação visual. Arredondamento só para exibição, não para salvar.
- Tolerância definida por operação, por unidades e pela qualidade do dado de
  origem. Não prometer precisão milimétrica geográfica sem fonte que a sustente.
- Terreno e cena 3D conservam escala, CRS, sentidos e identidade dos veículos;
  diagnósticos técnicos permanecem fora do vídeo final.
- Medir abertura, navegação e uso de memória com DXFs grandes, além de cenas
  sintéticas degeneradas e testes visuais. Preservar projetos, vídeos e caches.

Esta revisão não instala SVG, Three.js, Babylon.js, WebGPU ou Unreal. O desenho
atual e a exportação continuam usando os motores existentes.
