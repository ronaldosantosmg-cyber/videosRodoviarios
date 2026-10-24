# Rodovia Studio 1.15 — sinalização completa

Primeira etapa do plano de melhorias (funcionais): sinalização horizontal e vertical.

## O que mudou
Em **Configuração → Sinalização horizontal e vertical**:
- **Completa** (padrão) ou **Básica**. A Básica é igual à 1.14.
- **Largura da faixa** (padrão 3,5 m).
- **Sinalização do DXF**: substitui a gerada ou soma-se a ela.
- Liga e desliga separadamente: setas por faixa, zebrados automáticos, retenção/PARE e placas automáticas.

### Sinalização horizontal
- **Divisórias de faixa**: o programa mede a largura da pista nos dois lados da trajetória e divide pela largura da faixa. As divisórias são tracejadas (4 m pintados, 8 m sem pintura).
  - Nos tapers, alargamentos e junções a largura considerada fica limitada à típica do trecho, então não surgem faixas falsas.
  - Pista com veículos nos dois sentidos (sem canteiro): eixo amarelo duplo, com as faixas divididas por sentido.
- **☰ Faixas por trecho** (nova ferramenta): você desenha a área e informa o número de faixas. Ele vale no lugar do cálculo.
- **Setas por faixa**: as setas de fluxo passam a ser preenchidas (5 m), uma em cada faixa do mesmo sentido.
  - Antes de uma saída ou de um acesso, o tipo segue o itinerário dos veículos: reta e direita na faixa da direita, reta e esquerda na faixa da esquerda.
  - A ferramenta ↻ Girar seta funciona em qualquer uma delas e muda o sentido da via toda.
- **Retenção e PARE**: onde um acesso entra em nível numa via de maior prioridade, há linha de retenção (0,40 m) junto ao bordo da via principal, legenda PARE e placa R-1.
  - Isso não acontece em convergências tangenciais (faixa de aceleração).
  - Nas entradas de rotatória a retenção vira linha de dê a preferência, com a placa R-2.
- **Zebrados**:
  - **Automático**: no gore entre dois ramos com tráfego, antes do nariz. Para não sujar o vídeo, só é aceito quando o contorno encosta nas faixas dos dois ramos. A pintura de faixa dentro do zebrado é removida.
  - **▨ Zebrado** (nova ferramenta): desenho manual, com cor (branco ou amarelo), ângulo e espaçamento editáveis.
- **🚶 Faixa de pedestre** (nova ferramenta): clique num bordo e depois no outro. Barras de 0,40 m a cada 1 m, só sobre o pavimento.

### Sinalização vertical
- **🛑 Placa** (nova ferramenta). Tipos disponíveis:
  - R-1 PARE;
  - R-2 Dê a preferência;
  - R-19 Velocidade (com o número);
  - Advertência;
  - Obras;
  - Indicação (verde, com texto);
  - Serviço (azul).
- No vídeo, a placa aparece em pé sobre um poste, com tamanho legível. À noite continua visível, como placa refletiva.
- As placas automáticas (R-1 e R-2) vêm das retenções.

### Sinalização do DXF
- Há dois novos tipos de camada: **Sinalização horizontal** (polilinhas abertas viram linhas e polígonos/hachuras viram pintura preenchida) e **Sinalização vertical** (blocos, pontos, círculos e textos viram placas).
- O tipo da placa vem do nome do bloco: R-1/PARE, R-2/PREFER, R-19/VEL (o número vem do atributo), OBRA e A-… Os demais viram placas de indicação, com o texto.
- O perfil padrão reconhece nomes como `*SINALIZ*HORIZ*`, `*PINTURA*`, `*FAIXA*PEDEST*`, `*ZEBRAD*`, `*SINALIZ*VERT*` e `*PLACA*`.
- **Limitação**: os textos da camada de pintura (por exemplo, "PARE" escrito no CAD) não são desenhados, e o programa avisa. Converta-os em polilinha ou hachura no CAD.

### Edição
- Zebrados, faixas de pedestre, placas e faixas por trecho:
  - aparecem na lista de marcações, onde é possível editar, ver ou excluir cada item;
  - têm desfazer/refazer;
  - são salvos na configuração em coordenadas do projeto;
  - são exportados e reimportados em GeoJSON, KML/KMZ e DXF, nas camadas RS_FAIXA_PEDESTRE, RS_ZEBRADO, RS_PLACA e RS_FAIXAS_TRECHO.
- **🧽 Sem sinalização** também remove os zebrados, as retenções e as placas automáticas da área. As placas manuais ficam.
- O editor mostra a pintura preenchida e as placas como no vídeo.

## Configuração
O esquema passou para a **versão 14**, com migração automática. O DXF original não é alterado.

## Medido neste ambiente
- **Testes**: 151 automáticos passaram, 9 deles novos:
  - faixas pela largura e por trecho;
  - retenção, PARE e placa no T;
  - setas por itinerário e por faixa;
  - faixa de pedestre, zebrado e placas;
  - área sem sinalização;
  - desenho no quadro, de dia e à noite;
  - camadas de sinalização do DXF;
  - esquema v14 e exportação/reimportação;
  - gore na bifurcação;
  - ferramentas do editor no navegador.
- **Modo Básico**: quadros do TH57 idênticos aos da 1.14, pixel a pixel, nos instantes 14, 40 e 96 s e na vista do trevo (1280×720).
- **TH57 no modo Completo**:
  - 497 setas: 493 retas, 3 reta e direita, 1 reta e esquerda;
  - 6 pinturas preenchidas, 1 placa automática;
  - 21.575 segmentos de pintura de linha.
- **Tempo** no TH57 a 1920×1080, quadros de 40 e 96 s:
  - montagem dos quadros: 806 e 762 ms no Completo, contra 796 e 739 ms no Básico (+1% a +3%);
  - preparo da cena: 38 s no Completo, contra 35 s no Básico.

## Não verificado / limitações
- **Zebrados automáticos**: no TH57, poucos gores foram reconhecidos, porque a regra é conservadora para não pintar sobre faixas. Marque os demais com ▨ Zebrado.
- **Retenções automáticas**: só aparecem onde a geometria é clara. Algumas entradas do TH57 ficaram sem retenção (aproximação larga demais ou rotatória pouco circular). Use 🛑 Placa e 🧽 nos casos que precisarem de ajuste.
- **Placas**: a orientação da face não aparece na vista aérea. A placa é desenhada voltada para a câmera.
- **Cabine**: a vista da cabine ainda não mostra as placas verticais.
- **Normas**: as dimensões seguem valores usuais do Manual Brasileiro de Sinalização de Trânsito (CONTRAN). Não houve conferência normativa item a item.
