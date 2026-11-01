# Rodovia Studio 1.42.36 — circulação, sentidos e nós

## Como usar

1. Atualize pelo próprio aplicativo com o ZIP em atualizacoes/. Preserve uma cópia completa do projeto antes de atualizar. Projetos salvos nesta revisão usam um formato novo: para voltar à 1.42.35, use a cópia anterior, pois a versão antiga não interpreta os vínculos novos de sentido.
2. Em Tráfego, use Sentidos e nós para conferir o sentido de cada eixo e alinhamento. Reverter sentido troca a circulação; o desenho e o estaqueamento permanecem. Nós de entrada/saída acompanham a reversão de alinhamentos. Ligações precisam ser conferidas novamente.
3. Se aparecer Conferir sentido antigo, escolha explicitamente os sentidos: versões antigas usavam índices de lista. A atualização não transfere essas decisões para outra geometria nem reativa desligamentos automaticamente. Eixos associados a uma seção são controlados no alinhamento correspondente.
4. Escolher eixo e Configurar faixas continuam disponíveis mesmo sem itinerários. Subtrechos curtos são mostrados na conferência especial de registros antigos; não geram itinerários independentes abaixo do limite.
5. Use Testar circulação para obter uma prévia de até 10 s e compatibilidade por classe de veículo. Localizar mostra o ponto da recusa; Editar seção e Corrigir trechos usam as ferramentas existentes. O teste não altera a configuração nem substitui o vídeo final.
6. Depois das correções e conferências, use a geração normal de vídeo. Diagnósticos ficam desatualizados quando a fonte/configuração muda e precisam ser refeitos.

## Preservado

Inserir, selecionar, editar, mover e apagar nós; extremos de entrada/saída/fim; setas e seções; rotatórias e distribuição entre ramais; cortes e desligamentos manuais; snapshot, fechamento controlado e rollback. A reversão não libera barreiras/canteiros, semáforos, interdições, conflitos de veículos/pessoas ou travessias ferroviárias.

## OAE com Z=0

Os contornos não criam barreira nem desnível. O caminho legado de direção da OAE foi ajustado para não alterar o fluxo por uma OAE com Z=0; sentidos explicitamente cadastrados têm prioridade. Cotas absolutas CAD não são autorização automática de passagem em níveis diferentes. Desnível relativo confirmado e obstáculos físicos reais continuam nas regras existentes.

## Diagnóstico e estabilidade

Sentidos nativos passam a usar a impressão da geometria/camada, não a posição da linha na lista. Fontes editadas cuja identidade mudou exigem revisão; não há associação automática por simples proximidade. Chaves de origem têm identificadores estáveis e aliases compatíveis com registros anteriores quando a fonte corresponde. Resultados de ajuste DXF/imagem são rejeitados após troca de contexto/entrada. Retomar acompanhamento consulta a tarefa existente após falha de conexão, sem disparar outro cálculo.

A compatibilidade de frota usa a mesma verificação de admissão da simulação. No desenho normal, aproveita auditorias já realizadas; no teste dedicado, confere explicitamente as classes. Longos são corpos rígidos conservadores. A conferência de frota tem orçamento de até 300 itinerários e informa quando a análise é parcial. O clássico continua identificado como ensaio e não certifica segurança.

Não é reconstrução automática universal de ligações, homologação normativa ou validação Windows/8 GB. Ver evidências para a seleção de testes realmente executada. Pesos/runtime 3B e API real permanecem não homologados. Fontes e dados persistentes são preservados.
