# Rodovia Studio 1.11 — editor nítido para fluxos, detalhe em alta resolução, OAE por vértices e marca GeoRas

## Marca GeoRas
- O símbolo da GeoRas virou o **ícone do aplicativo**: atalho da Área de Trabalho (`rodovia.ico`), aba do navegador e cabeçalho.
- O logotipo completo aparece no cabeçalho como “Desenvolvido por GeoRas”.
- Arquivos em `assets/marca` (original, logotipo recortado e ícone 512 px). O Windows pode manter o ícone antigo do atalho em cache até a próxima entrada no sistema.

## Prioridade: editor para conferir o sentido das vias e ajustar os fluxos
- **Fluxos e sinalização sem prévia**: “Analisar arquivos” agora também calcula a rede de tráfego. O editor desenha, como vetores nítidos em qualquer zoom:
  - as **trajetórias com setas de sentido** (camada “Trajetórias e sentidos”);
  - a **pintura de faixas** (“Sinalização do vídeo”);
  - as **setas do vídeo** (“Setas de fluxo do vídeo”).

  É a mesma geometria que vai para o vídeo, sobre a imagem web, como no Google Earth com o KMZ carregado.
- **⟳ Atualizar fluxos**: depois de inverter, desativar ou incluir fluxos, ou de mudar o sentido de uma OAE, recalcula tudo em segundos, sem renderizar a prévia.
- **Imagem web direta**: se o aplicativo não conseguir baixar os ladrilhos (proxy ou bloqueio da empresa), o navegador busca direto no Esri. A imagem aparece quando o navegador tem acesso à internet.
- **Correção**: com o editor parcialmente fora da tela, o primeiro clique podia cair alguns metros ao lado do ponto (a página rolava antes de ler a posição). Corrigido.

## Vídeo: imagem e texturas em alta resolução
Quando a câmera se aproxima (abaixo de 90% do pixel do mosaico; no TH57, 0,87 m), o quadro passa a usar **ladrilhos de detalhe**, com transição suave:
- **Desenho do projeto a 0,2 m por pixel** (pavimento, acostamento, canteiro com grama, barreira, OAE, taludes e camadas extras). Bordas, hachuras e canteiros ficam nítidos (veja `conferencia/v1_11_texturas_antes_depois_TH57.jpg`). As hachuras mantêm o passo em metros e a continuidade entre ladrilhos.
- **Imagem aérea Esri no nível 19** (~0,3 m no TH57), reprojetada para o CRS do projeto:
  - baixada em paralelo antes da montagem e guardada em `projetos\_ladrilhos`, a mesma pasta do editor;
  - onde o Esri não tem imagem nesse nível, usa o nível anterior;
  - sem internet, desiste na hora e o vídeo usa o mosaico base, mantendo as texturas nítidas.
- Os ladrilhos ficam em cache por projeto (`cache_detalhe`) e funcionam com vários processos de montagem.
- **Opções** (Exportar vídeo → Sinalização, setas e anotações): “Imagem detalhada” (Automática/Desligada) e “Texturas do projeto em alta resolução”.

## OAE por vértices, com sentido
- **Nova ferramenta 🌉 OAE (vértices)**:
  - clique 4 ou mais vértices do tabuleiro; polígonos irregulares são aceitos, como uma ponte esconsa;
  - Enter conclui;
  - ajuste com **Editar vértices** (arrastar; clique na aresta insere; Shift+clique remove);
  - tem desfazer/refazer.
- **O que o programa calcula a partir do polígono**:
  - o eixo longitudinal (pela maior dimensão);
  - a largura média;
  - os km de início e fim;
  - os guarda-corpos (nas bordas longitudinais) e as juntas (nas cabeceiras).
- **Sentido**: dois sentidos, crescente ou decrescente. Nas trajetórias que passam pelo tabuleiro, os veículos seguem esse sentido. O editor mostra uma seta azul sobre a OAE.
- A OAE de 2 pontos continua funcionando.
- **Exportação e reimportação**: a OAE por vértices sai como polígono em GeoJSON/KML/KMZ/DXF e volta com o sentido.

## Configuração
O esquema passou para a **versão 10**, com migração automática. Com “Imagem detalhada: Desligada” e as texturas desligadas, os quadros TH57 de 14, 40 e 96 s e a vista do trevo são **idênticos aos da 1.10**, pixel a pixel.

## Medido neste ambiente
- **Testes**: 118 automáticos passaram (11 novos, incluindo o editor no navegador com a OAE por vértices, as camadas e a imagem direta).
- **Georreferenciamento da imagem detalhada**: com ladrilhos simulados, um ponto marcado na posição Web Mercator caiu a menos de 1,5 px (0,3 m) do lugar certo no ladrilho do projeto.
- **TH57 a 2560×1440, quadros da câmera do vídeo** (sem imagem detalhada, que não pôde ser baixada aqui): 713 ms por quadro sem detalhe e 1.102 ms com as texturas em 0,2 m, ou seja **+55%**.
- **Editor**: redesenho em ~15 ms com as camadas de sinalização do TH57 (19 mil traços, 154 setas).
- **Análise do TH57**: fica mais longa porque agora calcula a rede de tráfego para o editor. Ainda é muito mais rápida que gerar a prévia.

## Não verificado
- **Imagem Esri de nível 19 do TH57**: não pôde ser baixada aqui (acesso bloqueado). Os testes usam ladrilhos simulados. No seu PC, a primeira montagem com aproximação baixa os ladrilhos e as próximas usam o cache.
- **Cores entre a imagem detalhada e o mosaico**: podem diferir um pouco, por datas diferentes da imagem Esri por nível. A transição é suave, mas pode haver mudança de tom perceptível.
- **Busca direta da imagem pelo navegador**: depende da política da rede da empresa.

## Próximas etapas
- **1.12, tráfego**: sem colisão traseira, travessia do canteiro só em retornos ou locais indicados, engarrafamento, bloqueio parcial de faixas e rotas alternativas.
- **1.13**: dia/noite com faróis e as duas janelas sincronizadas.
