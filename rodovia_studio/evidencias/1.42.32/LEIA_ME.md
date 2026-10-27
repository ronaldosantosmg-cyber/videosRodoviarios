# Evidências da revisão 1.42.32

73 casos únicos com último ensaio aprovado, sem ignorados. A consolidação considera o início do último ensaio de cada caso; retentativas não contam como novos casos. Relatórios brutos preservados, incluindo os problemas de preparação do rascunho e as adaptações de navegação dos testes legados. A suíte histórica completa não foi executada.

## Conferido

- Rodapés de vídeo com ações visíveis e atingíveis por clique em 1366×620 e 760×480, mesmo após rolar o conteúdo até o fim.
- Edição de densidade e fumaça descartada sem mudar a configuração salva; estado anterior da janela restaurado.
- Gerenciador de camadas: rascunho não é gravado depois de 1,1 s; salvar confirma via API; descartar restaura a configuração e fecha. Filtro não cria edição pendente. Esc, X e Cancelar usam o controle de decisão; não existe X legado dentro do corpo.
- Falha de gravação simulada: janela e rascunho preservados, servidor sem alteração, botões novamente habilitados e descarte funcionando.
- Matriz de Projeto, Configuração/hachuras e Materiais/apresentação em tela baixa, com ações disponíveis no rodapé.
- Regressões de propriedades: salvar/descartar, texto sem Enter, fechamento mesmo após falha de atualização de propriedades e preservação da seleção/enquadramento. Testes legados do limite de fluxo foram adaptados para navegar por Projeto → Parâmetros de apresentação, em vez de tentar operar o seletor oculto.
- Cálculo solicitado com janela aberta resolve a edição e usa os dados confirmados; continuar editando cancela essa solicitação. Salvamento de janela em modo automático inicia uma única atualização no ensaio.
- Hachura com origem/destino legados vazios salva sem obrigar descarte; validação de nome inválido preserva a janela e permite corrigir/salvar.
- IA: testes dirigidos de regras locais, perfis, JSON, revisão, dados obsoletos e cancelamento; integração de API online simulada até revisão/aplicação confirmada. Não foram usadas credenciais nem provedores reais.
- Percurso orientado por nós nos motores existentes 2D/3D e MP4: 72/72 quadros H.264 decodificados em 1280×720, 24 fps, fonte DXF preservada.
- 102 módulos Python de app/ comparados byte a byte com a revisão 1.42.31, sem mudanças: motor_preservado.json. Alterações de produção restritas a interface e identificação da revisão.
- DXF TH53 disponível: 31 eixos, 6 itinerários revalidados, 7 veículos ativos e 1 desenhado no enquadramento de 350 m. Preparação e quadro em 44,12 s, sem comparação controlada de desempenho. Não é o projeto salvo atual do usuário.
- Iniciador compilado com/sem WebView2 e splash conferido em Mono/Xvfb, sem validação Windows nativa. Auditoria estática de fonte/ZIP não é antivírus.
- Instalação, encerramento controlado, movimentação da pasta e rollback são conferidos com o ZIP final; consultar verificacao_pacote.json. Preservados KMZ, GeoTIFF, vídeos, perfis e relatórios de IA no ensaio.

## Limites

Esta revisão não entrega pesos/runtime 3B, não treina IA e não amplia seus executores. O estado local consultado refere-se ao ambiente de validação, não ao PC do usuário. Os testes online usam transporte simulado. O relatório MODO_IA_1_42_32.md separa implementação, adaptação preparada e pendência.

Não há garantia universal de que todo diálogo/cálculo esteja sem falhas. A correção cobre os caminhos ensaiados. Permanecem pendentes uso prolongado em Windows/WebView2 e 8 GB, inferência 3B real, provedor online real, correção universal de redes, reconhecimento semântico homologado e dinâmica articulada.

Prontidão estimada para uso intenso: **7,5/10**. Melhorou a conclusão das edições; a nota não sobe para 9 sem as validações técnicas e de plataforma pendentes. Main preservada.
