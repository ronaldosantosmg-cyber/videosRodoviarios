# Revisões do Vídeos Rodoviários

Este arquivo registra entregas fechadas e utilizáveis do aplicativo. Cada revisão deve manter um ponto claro de retorno no histórico do Git.

## Regra obrigatória de aceite

Nenhuma revisão pode ser considerada fechada, marcada como release final ou apresentada como concluída se a avaliação global do aplicativo ficar abaixo de **8,0/10**.

Se uma alteração causar regressão que leve a avaliação para menos de 8,0, a revisão permanece com status **EM CORREÇÃO** até que os problemas sejam resolvidos e a nota volte para 8,0 ou mais.

A avaliação deve considerar, no mínimo:
- funcionamento do fluxo principal;
- usabilidade;
- estabilidade e ausência de regressões conhecidas;
- qualidade visual da prévia e do vídeo;
- desempenho do processamento/renderização;
- integridade de seleção, alinhamento, curvas, layers, CRS e tráfego;
- geração e abertura do pacote Windows quando aplicável.

Meta de qualidade das revisões:
- **mínimo obrigatório para fechar:** 8,0/10;
- **meta normal de entrega:** 9,0/10 ou superior;
- **meta final do produto:** 9,5/10.

## REV01 — Fluxo CAD e base integrada

Status: em consolidação.

Inclui a base já incorporada para:
- seleção geométrica mais precisa e confirmação por Enter/Esc;
- eixo/alinhamento selecionável;
- criação e edição de curvas circulares por PI, com raio digitado ou ajustado e restauração do PI seco;
- sinalização horizontal e setas de 4,00 m ligadas ao sentido de tráfego;
- classificação de canteiros/barreiras e travessias autorizadas;
- estados de layer herdados do DXF e controles de visibilidade/saída;
- imagem local com preparação ECW/GeoTIFF portátil;
- base de CRS com SIRGAS 2000, WGS84 e SAD69, incluindo UTM e inferência por KMZ.

Critério para fechar REV01:
- comandos acima acessíveis pelo fluxo principal da interface;
- prévia respeitando visibilidade e congelamento de saída;
- testes básicos de seleção, curva, CRS, layers e tráfego sem regressão conhecida;
- avaliação global confirmada em **8,0/10 ou superior**.

## Próximas revisões

### REV02 — Render rápido e retomável
- prévia rápida separada do render final;
- cancelamento;
- cache de geometrias, imagens, terreno e trajetórias;
- render por trechos/checkpoints;
- seleção automática de codec/GPU quando disponível;
- progresso por estágio.

### REV03 — Layers e limpeza visual
- painel simplificado de layers;
- Visível / Oculto / Não exportar;
- suporte consistente a HATCH;
- presets de visualização limpa;
- vídeo e exportações respeitando os estados definidos pelo usuário.

### REV04 — Tráfego e barreiras
- roteamento obedecendo canteiro, grama e barreiras físicas;
- retornos e cruzamentos somente em pontos autorizados;
- separação de interseções em nível e em desnível;
- fluxo derivado das setas e do alinhamento.

### REV05 — Georreferenciamento e DWG
- conflito de CRS detectado antes de processar;
- seleção manual quando necessário;
- backend portátil para DWG, se disponível/licenciável sem instalação administrativa;
- integração completa com ECW/GeoTIFF/KMZ.

### REV06 — Build final e validação
- executável portátil;
- CI estável;
- teste de abertura em Windows limpo;
- pacote com apoio, texturas, banco de dados e projetos salvos organizados.
