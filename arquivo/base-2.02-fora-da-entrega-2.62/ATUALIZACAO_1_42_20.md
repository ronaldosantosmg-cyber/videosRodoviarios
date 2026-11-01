# Rodovia Studio 1.42.20

Inclui as correções de densidade, OAE, gravação, importação e KMZ da revisão 1.42.19 e acrescenta a montagem direta das faixas pelo eixo central.

## Montar fluxo utilizável a partir do eixo

1. Abra **Corrigir fluxos → Montar seção típica de fluxo** ou o ícone de seção na faixa Fluxos de tráfego.
2. Escolha um eixo do DXF ou uma rota cadastrada. Eixos abaixo do limite do projeto não são listados.
3. Defina pista simples/duplicada, com/sem terceira faixa, início/fim por distância, km ou coordenadas. Confira o km de origem e a ordem do eixo, especialmente em eixos auxiliares.
4. Na montagem rápida, informe quantidade de faixas por lado, largura e acostamentos. Clique **Montar faixas da seção**. As linhas individuais permitem ajustar cada largura e ligar/desligar **Veículos** por faixa; acostamentos não recebem circulação.
5. Use **Aplicar e calcular**. Para vários intervalos, use **Adicionar seção**; para modificar um intervalo já cadastrado, use **Editar** na lista.

A opção **Usar a seção como pista de circulação** torna as larguras declaradas uma fonte explícita de geometria operacional. A circulação não depende de a hachura de pavimento coincidir com o eixo e não é bloqueada por linhas de bordo/referências. Não é uma liberação indiscriminada: barreiras/canteiros físicos, interdições, semáforos, proteção entre veículos e análise cinemática continuam ativos. Auto-interseções ou curvas fisicamente incompatíveis ainda exigem correção.

O eixo do DXF é preservado. Uma associação por geometria/camada/nível substitui a geração nativa daquele eixo sem duplicar faixas nem alterar seus comandos de sentido. Remover a derivação pelo histórico desfaz a associação. Desligar o alinhamento mantém sua circulação desligada.

Na configuração nova, circula-se somente nos intervalos cadastrados. Faixas derivadas abaixo do limite de processamento são omitidas do motor e da prévia, sem apagar o eixo. Pista simples usa sentidos opostos; duplicada usa as faixas de cada lado do canteiro. A terceira faixa pode ser configurada no lado necessário pelas quantidades independentes.

## Densidade

A caixa fica editável mesmo quando há demanda explícita. Ao digitar uma densidade, o programa retira a demanda explícita e passa ao modo de densidade. O botão **Usar densidade** continua disponível. Gravação em janela e processamento usam a mesma configuração. Gere a prévia ou reconstrua o 3D após mudar os valores. Densidade não cria veículos em faixas desligadas ou sem itinerário seguro.

## Materiais e maquete artística

- Corrigida a prioridade de interpretação de hachuras: ACOSTAMENTO_EXISTENTE continua acostamento, OAE_EXISTENTE continua OAE e CORTE_EXISTENTE continua corte. A palavra EXISTENTE não transforma outros elementos em pavimento.
- Corrigida a falha de concreto OAE que interrompia o vídeo. Foram exercitados pavimentos, acostamentos, canteiro, corte/aterro, OAE e ferrovia juntos em MP4 e cena 3D.
- No painel **Vídeo**, use **Aplicar maquete artística natural**: materiais artísticos, solo/vegetação nos taludes, texturas detalhadas e grama. As hachuras técnicas do projeto são preservadas; a opção de materiais naturais evita sobrepor padrões de desenho na maquete. Ao editar explicitamente a representação de pavimento, o modo natural é desmarcado para respeitar a nova escolha.
- Texturas das feições de engenharia são ancoradas em metros e processadas em faixas de memória limitadas; não mudam com o pan/zoom. No WebGL há mapas próprios para concreto, pavimento existente, solo e lastro, compartilhados por material. OAE é desenhada acima da superfície do pavimento na apresentação em planta 3D.

Esta é uma apresentação procedural e ilustrativa. Não equivale a uma maquete fotogramétrica ou a um núcleo CAD/3D completo; cotas de OAE e gabaritos ainda exigem conferência técnica.

## Atualização e limites

Salve o ZIP em `atualizacoes/` e use **Arquivo → Atualizar o Rodovia Studio**. Projetos, vídeos, KMZ e cache GeoTIFF são preservados. Snapshot, fechamento controlado e rollback do programa são conferidos na entrega. Versões antigas não implementam os controles novos de seção; use a revisão atual para operar projetos configurados com esses controles.

Validação direcionada autorizada pelo usuário, com testes funcionais/visuais e vídeos decodificados antes de empacotar. Evidências em `suporte/documentacao/validacao_1_42_20/`. O desenho disponível foi usado em regressão; o projeto salvo atual do usuário não foi fornecido.

Reconhecimento semântico de imagem continua condicionado a pesos locais adequados e avaliação real, ainda não incluídos. Reconstrução de fluxo permanece limitada e segura; não garante solucionar qualquer ligação. Windows/WebView2/OneDrive e carga prolongada não foram validados nativamente. Nota provisória para uso intenso: **7/10**. Main preservada.
