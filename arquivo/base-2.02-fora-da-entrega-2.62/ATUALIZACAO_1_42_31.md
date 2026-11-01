# Rodovia Studio 1.42.31 — nós integrados ao motor existente

## Como configurar

Abra **Tráfego → Regras e operação dos fluxos → Eixos, nós e giro das rotatórias**. Se a lista estiver vazia, selecione um eixo do desenho e configure suas faixas pelos comandos existentes. A classificação é explícita; não se inventa a função pelo nome da camada.

1. Classifique o alinhamento: Principal, Acesso, Retorno, Dispositivo ou Rotatória. Automático existente preserva o comportamento anterior.
2. A corresponde ao início geométrico do cadastro e B ao fim. Defina Entrada, Saída, Conexão ou Fim de percurso. Entrada → saída/fim orienta o percurso; A=saída e B=entrada produz sentido decrescente. Conexão não cria uma origem externa.
3. Confira a seção, suas faixas e larguras. Um par orientado define um percurso em um sentido; para manter ambos, use a seção bidirecional com orientação automática ou cadastre os percursos correspondentes. Faixas explicitamente desligadas não são reativadas.
4. Acesso circula sobre o eixo. Retorno/dispositivo/rotatória circulam à direita do sentido efetivo. Configurações de acesso com várias faixas simultâneas exigem conferência: não se apaga sua seção para fazer caber a regra.
5. Para rotatória com eixo fechado completo, escolha Horário ou Anti-horário. Nó, sentido e giro contraditórios são recusados com orientação. Marcações manuais de sentido que contradizem um percurso orientado pelos nós geram aviso e não o invertem; retire a orientação por nós para voltar ao controle manual existente.
6. Se for uma chegada sem origem desenhada, indique Entrada e configure veículos/h **ou** VDM externo. Essa demanda soma à principal. VDM externo usa a fração horária configurada no projeto. Sem quantidade, um ramal externo não recebe uma demanda inventada.
7. Use Aplicar e calcular. Salvar/descartar/contexto do projeto continuam no contrato de janelas existente.

## Distribuição e contagem

- Em uma derivação classificada, acessos compartilham 5%; retornos/dispositivos/rotatórias compartilham 20%; a continuação recebe o restante (75% quando ambos grupos estão presentes).
- Cada categoria é dividida por ramal, e depois por suas saídas/faixas válidas. Mais faixas não multiplicam a parcela de um ramal.
- Na mera continuidade ou incorporação não se cria um novo lote de veículos. Conexões já validadas e a identidade do veículo são reutilizadas.
- Percentuais manuais de ligações continuam prevalecendo. Revise-os se quiser adotar os padrões 5/20 em conexões com valores antigos.
- O relatório da simulação inclui balanço de entradas, saídas e veículos ativos, além das transferências concluídas entre arestas/eixos. A contagem inclui o aquecimento quando ativo; percentuais não garantem contagens exatas em um vídeo curto.
- Entradas externas podem elevar o volume a jusante acima de 100% da referência inicial. Isso não autoriza sobreposição; a capacidade e a fila continuam limitando a admissão.

## Interdição total

A seleção de alternativa antes da entrada continua no motor existente. Na rede classificada, veículos já admitidos também podem trocar o futuro do itinerário enquanto estiverem em uma aproximação física compartilhada, antes da bifurcação. O percurso alternativo precisa estar calculado, válido e sem bloqueio total ativo. Mantêm-se identidade, posição e direção; não há transporte instantâneo até o nó. A nova rota ainda passa pelas reservas, semáforos, pedestres, obras e trens.

Sem alternativa válida, o veículo aguarda. Quem já ultrapassou a bifurcação não é movido para trás. Com o fim da interdição, novas escolhas voltam ao padrão; veículos desviados completam o trajeto escolhido. Essa busca não reconstrói qualquer desvio nem garante passagem de toda a demanda quando falta capacidade.

## Compatibilidade e preservação

Os campos novos são opcionais no mesmo RouteAlignment, consumidos por build_lanes, TrafficNetwork, TrafficSim, Scene e scene3d. Não há outro motor nem nova dependência de execução. As seções, setas e veículos usam as mesmas faixas derivadas. A chave do cache inclui o contrato de orientação novo; resultados antigos são invalidados, não misturados.

As identidades anteriores das faixas são mantidas como referências para cortes e desligamentos ao adotar os nós, evitando reativação de uma faixa manualmente desligada. Fontes DXF, projetos, vídeos, imagens, cache GeoTIFF e mecanismos de atualização/rollback são preservados. Não se altera main.

## Limites

As conexões continuam sujeitas à geometria, superfície, barreiras, níveis e zonas sem conexão. Um contato em planta entre níveis diferentes não vira ligação. Rampas com transição de nível e redes impossíveis exigem cadastro/edição compatíveis com os recursos existentes; não há reconstrução universal ou certificação normativa. Não foi implementado nesta revisão um novo editor gráfico independente de nós ou classificação automática de todas as camadas. A seleção das extremidades aqui usa A/B e os contatos existentes.

A origem dos fluxos vermelhos/amarelos do projeto salvo do usuário ainda precisa ser reproduzida nesse projeto. Um aviso não é autorização para liberar um impedimento físico.
