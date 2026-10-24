# Rodovia Studio 1.20 — veículos em linha reta, sentido pelo eixo, áreas de pista e apresentação técnica

## O que mudou

### 1. Veículos sem zigue-zague
- **Causa encontrada no TH57**: nas emendas entre trechos da rede, a trajetória voltava alguns centímetros a 1,5 m para trás antes de seguir. Eram 338 pontos de recuo nas 50 trajetórias. O veículo "tremia" e girava por um instante. Havia ainda degraus herdados do esqueleto da pista.
- **Correção**:
  - os recuos nas emendas são retirados;
  - a trajetória é suavizada (cerca de 3 m) só onde o veículo continua inteiro dentro da pista;
  - nas pontas e nas curvas apertadas, o traçado original é mantido.
- Configuração: **Exportar vídeo → Trajetória dos veículos**. "Como na 1.19" reproduz o comportamento anterior.

### 2. Sentido pelo eixo quando não há seta
- Nos trechos paralelos ao eixo e sem seta marcada, vale a mão de direção pelo eixo do projeto: à direita do eixo, km crescente; à esquerda, km decrescente.
- Continuam com prioridade:
  - setas desenhadas e giradas;
  - sentido da OAE;
  - rotatórias e ilhas;
  - "Sentidos de circulação" por eixo.
- Trechos sobre o próprio eixo (pista simples) mantêm o cálculo anterior.
- Configuração: **Sentido sem seta marcada**. "Como na 1.19" reproduz o anterior.

### 3. Hachura de pista nova, pista existente e acostamento por área
- **▦ Área de pista (desenhar)**: escolha o tipo (pista nova, pista existente ou acostamento) e clique os vértices. Enter conclui.
- **⬚ Área de pista (selecionar)**: escolha o tipo e clique dentro de uma área fechada do desenho (pavimento, canteiro, camada extra…). Ela passa a ser do tipo escolhido.
- A área recebe a cor e a hachura do tipo e **prevalece sobre a classificação do DXF** naquele local. O resto da superfície continua como estava; o total de pavimento não muda.
- Na lista há: nome, tipo, ativa, Editar vértices, Ver e Excluir, com desfazer/refazer.
- A área também é exportada e importada (GeoJSON/KML) como `area_pista`.

### 4. Acostamento por início, fim e largura
- **⇥ Acostamento (início/fim)**: informe a largura (0,5 a 6 m) e clique o início e o fim junto ao bordo da pista. O programa cria a faixa ao longo do bordo, por dentro da pista.
- Se os pontos não estiverem junto ao mesmo bordo (até 15 m), aparece um aviso claro e nada é gerado.
- Na lista há: largura, km de início e fim, ativo e Excluir.
- O acostamento também é exportado e importado como `acostamento`.

### 5. Perfil "Apresentação técnica" (conferência com a SKILL enviada)
O botão **Aplicar perfil "Apresentação técnica"** (seção 5) aplica estes valores, todos ajustáveis depois:

| Item | Valor |
|---|---|
| Resolução e taxa | 2560×1440, 24 quadros/s |
| Duração | 96 s |
| Pista nova | preenchimento escuro com hachura dourada suave |
| Pista existente | preenchimento e hachura cinza-azulados |
| Acostamento | tom e hachura próprios |
| Hachuras | fixas nas coordenadas do projeto |
| Voo | contínuo até o fim do segmento, sem paradas nas obras, com breve permanência no ponto final |
| Setas de fluxo e veículos | desligados |
| Indicador de progresso | "Revelação do projeto NN%" no rodapé, igual à fração revelada do segmento |

Além disso, valem para todos os perfis:
- **Conferência DXF × KMZ**: a análise mede o desvio entre o eixo do DXF e a linha do KMZ em 25 pontos distribuídos (mediana, 95% e máximo). Com mediana acima de 10 m, aparece um aviso.
- **Mosaico Esri**:
  - até 3 tentativas por bloco, com espera crescente;
  - blocos brancos ou pretos uniformes e mensagens "sem dados" são detectados e avisados.
  - Nas fontes web, esses ladrilhos são descartados.
- **Conferência do MP4**: depois de gravar, o vídeo é **decodificado por inteiro**. São conferidos o número de quadros, a resolução, o codec, a pixel format, a taxa e o faststart. Se algo não confere, o arquivo não é entregue e aparece o motivo. O resultado fica em `video.json` (`validation`).

**Da SKILL, ainda não feito (fase de desempenho)**:
- renderização em blocos independentes de cerca de 8 s, com validação e reprocessamento de cada bloco;
- revelação que trata pistas paralelas e curvas próximas pela distância ao longo do percurso, e não pela estaca mais próxima.

## Configuração
- O esquema passou para a **versão 19**.
- Projetos anteriores recebem a trajetória suavizada e o sentido pelo eixo; as opções "Como na 1.19" voltam ao anterior.
- O perfil técnico, o voo contínuo e o indicador de progresso começam desligados.

## Medido neste ambiente
- **Testes**: 13 testes novos:
  - trajetória sem recuos e sem zigue-zague;
  - curva fechada dentro da pista;
  - rede sem recuos;
  - sentido pelo eixo em pista dupla;
  - área de pista prevalecendo sobre o DXF;
  - acostamento por início/fim/largura, com aviso;
  - exportação e importação;
  - hachura ancorada nas coordenadas;
  - quadros do perfil técnico: hachura, voo contínuo e indicador;
  - conferência DXF × KMZ;
  - blocos vazios;
  - conferência do MP4, inclusive de um arquivo truncado;
  - esquema 19;
  - editor no navegador: desenhar, selecionar, acostamento, desfazer e perfil.
  - Ao todo, 196 testes automáticos passaram (183 da 1.19 + 13 novos). Dois testes da 1.19 passaram a aceitar esquema 18 ou mais novo.
- **TH57, trajetórias**:

| Medida | 1.19 | 1.20 |
|---|---|---|
| Pontos de recuo | 338 | 0 |
| Inversões de curvatura a cada 100 m | 1,1 | 0,0 |
| Desvio lateral de alta frequência (médio) | 0,20 m | 0,11 m |
| Itinerários | 50 | 50 |

- **TH57, simulação de 202 s**:

| Medida | 1.19 | 1.20 |
|---|---|---|
| Veículos | 993 | 1.014 |
| Colisões traseiras | 0 | 0 |
| Menor distância entre veículos | 4,45 m | 4,66 m |

- **TH57, sentido pelo eixo**: muda o sentido de 1 trecho curto (13 m) na pista da direita. Antes ele seguia o sentido da outra pista, porque o eixo dessa pista tinha uma falha ali.
- **TH57, compatibilidade**: com "Como na 1.19" nas duas opções, os quadros de 14, 40 e 96 s e a vista do trevo ficaram idênticos à 1.19, pixel a pixel.

## Não verificado / limitações
- O zigue-zague que você viu pode ter outras causas em projetos diferentes do TH57. Confira no seu vídeo e me diga onde ainda acontecer (km e sentido).
- **Área selecionada**: usa o contorno externo da área fechada (simplificado a 0,25 m). Ilhas internas dessa área passam a fazer parte dela. Para excluí-las, desenhe a área à mão.
- **Sentido pelo eixo**: pressupõe tráfego pela direita e o eixo entre as pistas, ou sobre a pista simples. Se o eixo do projeto estiver sobre uma das pistas de uma rodovia duplicada, confira os sentidos no editor.
- **Hachura técnica**: as cores seguem a descrição da SKILL. A reprodução visual não certifica conformidade normativa.
- **Conferência do MP4**: aumenta o tempo final (decodificação completa). Aqui, 20 s de vídeo 2560×1440 a 24 q/s levaram 6,3 s para conferir (2 núcleos, com testes rodando ao mesmo tempo). Por proporção, um vídeo de 96 s levaria cerca de 30 s, mas isso não foi medido num vídeo real do TH57.
