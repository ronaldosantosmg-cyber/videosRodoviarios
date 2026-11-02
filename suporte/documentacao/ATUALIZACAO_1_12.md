# Rodovia Studio 1.12 — sinalização limpa em todo o modelo, setas em todas as faixas e tráfego sem colisão

## Sinalização: sem sujeiras em todo o modelo
Na 1.10 a limpeza removia as sobras, mas a pintura ainda vinha das trajetórias calculadas do pavimento, que fazem zigue-zague em rotatórias, alças e alargamentos. Agora, no modo **Limpa** (padrão):
- **Linhas de bordo** seguem o **contorno real do pavimento** em todo o modelo: pistas, acostamentos, canteiros, rotatórias, ilhas, alças e OAE. Ficam a 0,35 m da borda, contínuas. Pequenas frestas entre hachuras vizinhas são fechadas antes, para nenhuma linha atravessar a pista.
- **Eixos e divisórias de faixa** só nas vias principais e marginais (trechos de 60 m ou mais), e nunca dentro das junções: convergências, divergências e rotatórias, com 22 m de folga.
- **Rotatórias**: a trajetória do anel vira arco de círculo, sem o zigue-zague do esqueleto do desenho.
- **Ramos curtos sem saída** do esqueleto (menos de 14 m) deixam de virar trajetória.
- Resultado no TH57 conferido em 8 vistas ao longo de todo o traçado e no trevo (`conferencia/v1_12_*`).

## Setas: todas as faixas mostram o sentido (o erro marcado na imagem)
- Além das setas a cada km e nos conflitos, **toda faixa direcional** recebe seta: ramos, alças, aproximações divididas por ilha e anéis de rotatória. Faixas de 8 a 90 m recebem uma seta; as mais longas, uma a cada 60 m.
- Os trechos de desenho que não formam itinerário de veículo também mostram o sentido.
- **Mão de direção nas ilhas divisórias**: a circulação deixa a ilha à esquerda do motorista (sentido anti-horário, como nas rotatórias). Corrige as aproximações em que a faixa da esquerda aparecia subindo.
- **Projetos com muitas ilhas**: aplicar “⟳ Atualizar fluxos” e conferir no editor.

## Tráfego simulado (padrão)
- **Sem colisão traseira**: cada veículo mantém distância segura do veículo da frente. O modelo de seguimento é o IDM, com distância mínima de 2,5 m e 1,4 s de intervalo. Vale também para quem vem de outro itinerário pelo mesmo trecho.
- **Convergências**:
  - quem vem da via principal tem prioridade, e o ramo cede passagem;
  - entre vias iguais, passa quem chega antes;
  - a entrada na rede só acontece com espaço livre.
- **Engarrafamento**: “Densidade do tráfego”, de 1 (normal) até 8. Acima de 3 forma fila.
- **Interdições de faixa** (ferramenta 🚧 no editor):
  - **Parcial**: os veículos reduzem a velocidade (padrão 15–20 km/h) e aumentam a distância, e a fila se forma antes.
  - **Total**: os veículos param antes da área e, se houver itinerário alternativo com a mesma entrada, os novos veículos seguem por ele (rota alternativa).
  - **Período**: início e fim em segundos do vídeo.
  - **No vídeo**: área zebrada laranja e branca, cones na borda e o nome.
  - **Edição**: desfazer/refazer e edição de vértices. Exporta e reimporta em GeoJSON/KML/DXF.
- **Canteiro central** (“Travessia do canteiro”):
  - **Só em retornos** (padrão): a travessia só é permitida em retornos em desnível (pela OAE), rotatórias e retornos em nível (abertura no canteiro).
  - **Só desnível/rotatória**: as aberturas não contam.
  - **Livre**: comportamento anterior.
  - **Ferramentas ↶ Travessia permitida e ⛔ Travessia proibida**: o operador indica os locais. Trechos fora da regra ficam sem veículos, com aviso.
- **Desempenho**: a simulação é calculada uma vez antes da montagem, com passo de 0,2 s e 90 s de aquecimento, e cada quadro só interpola as posições. Funciona igual com qualquer número de processos. No TH57 leva cerca de 0,5 s com densidade 1 e 2,5 s com densidade 4.
- **Movimento anterior**: a opção “Movimento dos veículos: Anterior” mantém o da 1.11.

## Configuração
O esquema passou para a **versão 11**, com migração automática.

## Medido neste ambiente
- **TH57, 202 s**:
  - densidade 1: 1.051 veículos, **0 colisões traseiras**, menor distância entre para-choques de 4,9 m;
  - densidade 4 com interdição parcial: 3.764 veículos, 0 colisões, menor distância de 3,6 m.
- **Testes** (131 automáticos passaram):
  - **colisões e velocidade**: sem colisões com densidade 1 e 5 em dois desenhos; a velocidade média cai com o engarrafamento;
  - **interdições**: a parcial reduz a velocidade; a total não deixa nenhum veículo dentro da área no período ativo, forma fila parada antes e libera depois;
  - **canteiro**: uma abertura é retorno em nível; “só desnível/rotatória” bloqueia; a travessia permitida libera e a proibida bloqueia;
  - **ilha e setas**: a ilha deixa o tráfego à direita; toda faixa com 8 m ou mais tem seta;
  - **pintura**: as linhas de bordo ficam a menos de 0,9 m do contorno, e nenhum eixo é pintado dentro das junções.

## Não verificado / limitações
- **Faixas**: uma trajetória por sentido em cada pista, sem troca de faixa. Em pistas de 2 faixas os veículos andam em fila na mesma faixa.
- **Cruzamentos em nível**: nos pontos onde duas vias se cruzam sem convergir, não há controle de conflito, e os veículos podem se sobrepor por instantes.
- **Rota alternativa**: só existe quando a rede tem outro itinerário com a mesma entrada. Desvios desenhados pelo operador entram como “Incluir fluxo”.
- **Tráfego**: é ilustrativo, não um modelo de tráfego calibrado.
- **Vídeo completo do TH57**: não foi gerado aqui; foram conferidos quadros e a simulação.
