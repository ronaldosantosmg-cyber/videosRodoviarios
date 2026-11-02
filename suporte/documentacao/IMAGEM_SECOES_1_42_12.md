# Imagem aérea, seções e circulação — 1.42.12

## Contornos e máscaras da imagem

Carregue uma imagem local georreferenciada. Em **Áreas e sinalização**, passa a aparecer **Contornos e máscaras da imagem aérea**. A função fica oculta sem imagem local válida. Na janela, escolha a imagem local ou a fonte on-line do projeto. O processamento ocorre localmente; a fotografia não é enviada a um serviço de IA. Para a opção on-line, o programa obtém os ladrilhos da fonte selecionada e preserva a captura utilizada.

Enquadre uma área de interesse e use **Analisar área visível**. Sem DXF aberto, usa a extensão georreferenciada da imagem. A área deve ter até 10 km por lado, em CRS projetado em metros. Áreas muito grandes têm resolução insuficiente para objetos pequenos: aproxime e analise por partes. São aceitas análises de 512 a 2048 pixels, 2 a 32 grupos e limite de 500 sugestões por execução. O limite de complexidade evita travar edição ou renderização.

A implementação é **segmentação assistida por cor/textura**, com amostras do usuário e referências CAD classificadas. Não contém um modelo semântico treinado capaz de reconhecer autonomamente e com precisão comprovada as nove classes. Cor verde pode ser vegetação ou outro objeto; azul pode ser água, sombra ou cobertura; telhas e solo exposto podem se confundir. Ferrovia, OAE, transmissão e sinalização precisam de referência/amostra e conferência. Não são inferidas cotas, alturas reais, bitola ou cadastro de concessionárias a partir de pixels.

Use **Marcar amostra na imagem** para indicar uma classe conhecida. Os resultados são separados em edificações, hidrologia, ferrovia, OAE, vegetação densa, taludes, transmissão, rodovias, sinalização e “A classificar”. O número de semelhança agrupa aparências próximas; não é uma classe técnica. **Usar classe nos semelhantes** propaga a classificação como rascunho e exige nova revisão. **Revisar grupo** é uma confirmação explícita de revisão em lote.

Cada objeto permite nome, classe, material, material das paredes, altura/cota de apresentação, cor branca/amarela da sinalização e opções individuais. Aplique e selecione um contorno para mover, editar vértices ou usar Desfazer. Alturas são ilustrativas até conferência. Em cada grupo há controles distintos para **Editar/ver** e **Apresentar**; o primeiro controla a edição e o segundo as texturas/volumes na apresentação.

Nada é aprovado automaticamente. Marque a classificação como revisada e aplique. Os contornos tracejados são técnicos, ficam abaixo dos vetores do projeto e não são enviados ao MP4 nem à captura 3D. Somente máscaras revisadas e habilitadas entram na apresentação. As máscaras técnicas recortam o contexto para preservar sua prioridade. Edificações têm cobertura e paredes separadas em 3D; não são reconstruções fotogramétricas. Os objetos derivados da imagem não habilitam circulação nem substituem eixos, OAEs ou ferrovias técnicas existentes.

A captura e sua referência são preservadas em `projetos/<id>/contexto_imagem/fontes/`, com hash, CRS, extensão, fonte e data. Não são descartadas pela limpeza de caches temporários. Alterar a imagem ou sua transformação invalida as sugestões e máscaras anteriores até nova análise; a geometria cadastrada permanece guardada na configuração. Cache derivado de bordas de nodata não invalida a imagem original.

## Seções tipo

Selecione uma **rota de veículos/alinhamento** e use **Seções tipo e pare e siga** nas propriedades ou na barra **Fluxos de tráfego**. Monte pista simples/duplicada com ou sem terceira faixa; informe quantos elementos existem à esquerda e à direita do eixo. Para cada elemento, escolha pista, acostamento ou faixa de segurança e sua largura. A ordem é do eixo para fora. Somente pista gera veículos. Um veículo mais largo que a faixa não é admitido.

Os limites podem ser distâncias no alinhamento, coordenadas projetadas sobre ele ou quilômetros relativos ao km inicial informado para esse alinhamento. Esses quilômetros não são automaticamente as estacas oficiais de um eixo auxiliar. Coordenadas a mais de 30 m do alinhamento são recusadas. Seções não podem se sobrepor ou ultrapassar a extensão do eixo. **Adicionar seção**, **Editar** e **Remover** preparam o rascunho; **Aplicar e calcular** salva e envia ao motor. Se um cálculo estiver em andamento, aguarda sua conclusão; os dados salvos permanecem disponíveis para recalcular.

As novas seções prevalecem dentro de seus intervalos; fora deles, valem os tipos/trechos anteriores. Transições e setas usam as mesmas faixas calculadas para a circulação. Regras de sentido, ligações, interdições, mínimo de comprimento, movimento, pavimento e ultrapassagem continuam sendo verificadas. Uma seção desenhada não certifica a capacidade ou a segurança de uma via real.

## Corpos, ultrapassagem e alerta

Os corpos matemáticos são retângulos orientados, com frente, traseira e comprimentos distintos por classe. Larguras: 3 m para caminhão/ônibus/carreta; 1,8 m para carro/picape/van; 0,8 m para moto. A distância lateral livre total entre dois veículos é de **0,50 m**, conforme correção do usuário; o cálculo divide essa reserva em 0,25 m de cada lado dos corpos. No mesmo fluxo, a distância longitudinal mínima é de **2 m**. Essas dimensões são parâmetros ilustrativos solicitados, não uma classificação legal de veículos.

O motor verifica corpos e o espaço percorrido antes de gravar os estados. Em corredores estreitos, restringe admissões conflitantes e mantém fila. Não resolve colisão apagando um veículo nem autoriza contramão. A verificação final bloqueia a geração se uma reserva lateral calculada falhar. O relatório inclui retenções, folgas e intervenções; não é certificação de ausência universal de acidentes ou de conformidade CONTRAN.

Ultrapassagens continuam limitadas a faixas adjacentes do mesmo alinhamento/sentido, janelas permitidas, espaço, geometria e pavimento. As setas piscam durante a manobra em 2D/3D/MP4. Paradas ligadas a interdição, pare e siga ou risco de sobreposição exibem pisca-alerta. Cruzamentos complexos precisam das prioridades/semáforos correspondentes; segurança geométrica não equivale a calibração de tráfego.

## Pare e siga

Na mesma janela, indique início/fim, faixa operacional e liberação padrão de **10 s**. Exige pista simples, uma faixa por sentido, espaço de transição e 25 m de aproximação em cada ponta. Os dois sentidos passam pela faixa operacional validada. A janela de 10 s é uma liberação de entrada de comboio, seguida de um intervalo fechado até o último veículo desocupar completamente. Só então começa o sentido contrário; não há inversão forçada a cada 10 s.

Pode ser associado a uma interdição existente. O desvio precisa ficar fora da área fechada e dentro da pista disponível; se não houver caminho válido, o motor mantém o bloqueio. O pare e siga fica ativo enquanto seu cadastro estiver habilitado; horários da interdição não removem sua geometria compartilhada. Desative/remova o cadastro para retirar o desvio. Ao remover/desativar seu alinhamento, o cadastro dependente é desativado. Semáforos e passagem ferroviária também podem reter o comboio.

## Gravação e limites de validação

As janelas trabalham com rascunhos, oferecem salvar/descartar/continuar e mantêm erros visíveis. Falha de gravação restaura o estado anterior do modelo. Os dados entram na configuração e no histórico de Desfazer. Projetos, vídeos, fontes DXF/KMZ e cache persistente de GeoTIFF são preservados. Instale o ZIP pela pasta `atualizacoes/` e use a atualização do aplicativo.

Uma tarefa automática pendente de gravação não fecha uma janela reaberta nesse intervalo. A análise/prévia automática é adiada enquanto houver diálogo aberto; comandos explícitos continuam resolvendo salvar/descartar antes de processar. Uma prévia adiada permanece marcada como desatualizada.

Campos novos são opcionais para leitura por revisões anteriores; uma revisão antiga não executa as funções novas. Preserve o histórico do projeto antes de editar novamente numa versão antiga. Prontidão provisória para uso intenso: **7/10**; ainda depende de validação Windows/OneDrive/WebView2, projetos reais salvos, imagens com referência conferida e sessões prolongadas. Não há medição de acurácia semântica em base rotulada.
