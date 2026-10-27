# Evidências da revisão 1.42.31

210 casos únicos com último ensaio aprovado, sem ignorados. Consolidação pelo início da última suíte de cada caso, sem contar retentativas como casos novos. Os relatórios brutos preservam as falhas encontradas e suas correções; retentativas não contam como novos casos. A suíte histórica completa não foi executada.

## Conferido nesta revisão

- A/B como extremidades geométricas do alinhamento, entrada/saída/conexão/fim, orientação crescente/decrescente e seção simples/duplicada com preservação de faixas desligadas.
- Acesso sobre o eixo; retorno/dispositivo à direita de seu sentido. Giro horário/anti-horário de eixo fechado de rotatória, com coordenadas CAD grandes e rejeição de contradições, aberturas ou degenerações.
- Repartição total por categoria 5/20/75 em nó com os dois grupos; divisão por ramal e depois por faixa, sem multiplicação de demanda ao aumentar a quantidade de faixas.
- Entroncamento Y classificado real; demanda externa de 400 veículos/h somada a 1.000 veículos/h principais, sem descontá-la da demanda principal. Os 1.400 veículos/h são demanda, não garantia de vazão efetiva.
- Identidade conservada na incorporação e balanço entradas = saídas + veículos ativos, incluindo aquecimento quando presente.
- Interdição total programada: troca de itinerário na aproximação física compartilhada, antes da bifurcação, sem novo veículo ou salto de posição; nenhuma invasão do bloqueio nos quadros amostrados. Sem alternativa, o veículo aguarda.
- Desligamento manual anterior preservado ao classificar acesso sobre o eixo, por referências às identidades derivadas anteriores.
- Marcação antiga contrária ao sentido dos nós gera aviso e não inverte o percurso. Caminho de marcações legado preservado.
- Chromium real em janela de 760 px: aplicar/calcular, campos chegando à configuração e ao cálculo, seção duplicada preservada, reabertura do cadastro com os valores salvos. Sem novo motor ou nova dependência.
- Percurso decrescente por nós nos motores existentes 2D/3D e MP4; 72/72 quadros H.264 decodificados em 1280×720, 24 fps. Fontes DXF preservadas.
- Comparação identificada com o ZIP 1.42.30: mesma geometria de itinerários, mesmas posições de veículos nos instantes amostrados, mesma imagem renderizada e mesmo número de veículos gerados no cenário legado. Conferir compatibilidade.json. Não prova equivalência universal.
- Medições pontuais de preparação, simulação, quadro e memória máxima em processos Linux separados, com outras tarefas ativas. Os valores estão nos JSONs de compatibilidade. Não fundamentam promessa de ganho, ensaio Windows ou uso prolongado de 8 GB.
- DXF TH53 disponível: 31 eixos, 6 itinerários revalidados, 7 veículos ativos e 1 desenhado no enquadramento de 350 m; fonte preservada. Preparação e quadro em 38,76 s. Não é o projeto salvo atual do usuário.
- Iniciador compilado com/sem WebView2 e splash conferido em Mono/Xvfb; não é validação de GUI Windows nativa. Auditoria estática não é antivírus.
- Instalação final, encerramento controlado, movimentação da pasta e rollback devem ser conferidos no verificacao_pacote.json do ZIP final, preservando KMZ, GeoTIFF, vídeos, perfis e relatórios de IA.

Um ensaio agregado de reabertura excedeu a espera de 60 s; a repetição isolada passou em 45,98 s, sem alteração adicional do produto. O relatório bruto da falha foi preservado. A causa temporal não foi comprovada e a latência deve continuar sendo acompanhada. As quatro falhas anteriores de trajetórias legadas independentes foram corrigidas no acesso às arestas da demanda externa e passaram novamente.

## Limites materiais

Nós aqui são papéis das extremidades dos alinhamentos e contatos geométricos já existentes; não foi criado outro editor independente de rede. Atribuição de funções é explícita, sem classificação universal de camadas. Rampas em níveis diferentes precisam de cadastro e geometria compatíveis com os recursos existentes; não se inventa ligação de um cruzamento em planta. O desvio depende de itinerário alternativo já válido e capacidade disponível. Veículos que passaram da bifurcação não voltam para trás.

A causa dos fluxos vermelhos/amarelos do projeto salvo atual do usuário não foi reproduzida a partir desse projeto; a validação usa cenários identificados e o DXF disponível. Os percentuais não garantem contagem exata em vídeos curtos nem certificação CONTRAN/DNIT/HCM. Veículo de 30 m continua sendo envelope rígido conservador. Não há garantia universal de ausência de falhas.

Prontidão estimada para uso intenso: **7,5/10**. Pendentes ensaio prolongado no PC Windows de 8 GB, GUI Windows completa, calibração por empreendimento, dinâmica articulada e validação do projeto salvo do usuário. Main preservada.
