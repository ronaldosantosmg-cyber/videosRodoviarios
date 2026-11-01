# Rodovia Studio 1.42.28

## Veículos na apresentação e no vídeo

Corrigida a ocultação dos veículos em vistas com largura igual ou superior a 3 km. No DXF de referência havia sete veículos ativos em um enquadramento de aproximadamente 17 km, mas o desenho descartava todos por essa condição. Em escalas amplas os veículos continuam pequenos: não foram aumentados artificialmente.

Abra **Tráfego ou Vídeo → Diagnosticar veículos**. A janela distingue itinerários, veículos simulados e veículos desenhados; informa o que ainda não foi medido. O diagnóstico lê somente resultados da revisão atual. Se necessário, Atualizar diagnóstico das rotas prepara esses resultados.

**Ativar veículos e gerar prévia de tráfego** habilita a apresentação global e seleciona a câmera **Tráfego — veículos em evidência**, com 350 m de largura. Esse modo usa um veículo real persistente ou enquadra uma via com veículos reais. Não apaga câmeras cadastradas, não aumenta a demanda, não altera seções, não reativa rotas desligadas e não ignora barreiras, colisões, interdições ou sinais. Volte ao modo de câmera anterior para restaurar a composição de obras/pontos-chave.

Conferida a correspondência entre o centro de desenho e a análise dos eixos dianteiro/traseiro; esse cálculo já era compartilhado e foi preservado. A aceitação gráfica usa o corpo real; não acrescenta margem gráfica além das dimensões validadas. O cache dessa aceitação passa a distinguir posições e rumos, em vez de reutilizar uma decisão para toda uma aresta.

A exportação registra uma conferência de visibilidade em três instantes, com aviso de enquadramento amplo, ausência de itinerários ou veículos. Essas amostras não certificam cada quadro. O modo de tráfego recusa a exportação sem itinerário/veículo disponível, com orientação; não fabrica circulação para concluir o vídeo. O projeto salvo atual do usuário não estava disponível: o diagnóstico permite identificar causas adicionais sem declarar que qualquer projeto esteja corrigido.

## Hachuras e fechamento

Corrigida uma validação adicional da janela: origem e destino opcionais em projetos antigos impediam salvar qualquer alteração, inclusive de hachura. A janela agora segue os requisitos do motor; o nome continua obrigatório. Projeto novo mantém a conferência de identificação já existente.

Salvar e fechar confirma os dados e fecha. Fechar com alterações permite Salvar, Descartar ou Continuar editando. Erro de gravação mantém o rascunho visível para corrigir e tentar novamente. Não preenche metadados silenciosamente nem exige descartar para sair de uma edição válida.

## API online de apoio

1. Abra Ajuda → IA de apoio — API online (ou Projeto → IA de apoio).
2. Clique Conectar API online, escolha o serviço e consulte os links oficiais para obter a chave e identificar modelos.
3. Informe modelo e chave no próprio aplicativo. Clique Usar conexão nesta sessão. O aplicativo não inclui chave, conta ou créditos do provedor.
4. Escolha a etapa, descreva a necessidade e prepare o mini prompt.
5. Confira o contexto e marque a autorização de envio. Somente então consulte a IA.
6. Revise a proposta nas ferramentas do motor. Texturas podem ser revisadas e confirmadas; fluxos usam a proposta geométrica validada já existente, com revalidação e desfazer.

Serviços oferecidos: OpenAI, Groq e OpenRouter. Os identificadores e a disponibilidade dos modelos dependem do serviço e da conta. Use um modelo compatível com chat e JSON. Links de chaves/modelos são oficiais e abrem no navegador. Cobrança e limites são definidos pelo provedor.

A chave é mantida apenas na memória da sessão, não em projetos, logs, perfis, exportações ou localStorage. Ao fechar o aplicativo, configure novamente. Desconectar desativa a API durante a sessão. A validade da chave e do modelo é conferida na primeira consulta, sem envio automático ao configurar.

## Contrato, não treinamento de pesos

A API recebe instruções e contrato JSON. Isso não é fine-tuning de um modelo. OpenAI recebe também o esquema de resposta; outros provedores usam modo JSON com validação pelo aplicativo. Campos/ações desconhecidos, contexto obsoleto e camadas fora do pedido são recusados. Nenhum código recebido é executado. As propostas não são aplicadas automaticamente.

O contexto mostrado pode conter nomes de camadas e coordenadas do empreendimento; confira antes de autorizar. Credenciais e caminhos reconhecíveis são reduzidos, não há promessa de anonimização completa. A política de retenção do serviço deve ser considerada pelo usuário.

## Modelo local

O adaptador 3B continua opcional, sem pesos neste ZIP. Download e inferência do GGUF real ainda dependem do acesso e homologação da fonte. A atualização pode ser usada com regras locais e/ou API online sem instalar modelo 3B. Não há alegação de inferência local validada em 8 GB.

## Atualização e limites

Use o pacote completo pelo atualizador. Preservados projetos/, videos/, DXF/KMZ, imagens originais, cache GeoTIFF, histórico, snapshots, encerramento controlado e rollback. Main não alterada.

Testes funcionais e visuais desta revisão constam de evidencias/1.42.28. Respostas online foram testadas com transporte simulado; não havia chave de conta para consultar um provedor real. Isso valida contrato, revisão e aplicação confirmada, não a disponibilidade, cobrança ou acerto de um modelo online específico. Sem alegação de conformidade normativa, teste universal de carga ou GUI Windows completa.
