# Revisão 1.42.12 provisória

Empacotamento antecipado expressamente autorizado pelo usuário em 25/10/2026: “como a validação ja fez 90% dos testes, empacote a revisçao e devolva”. A autorização dispensa aguardar a repetição integral para este pacote; não transforma validação parcial em aprovação completa.

A bateria anterior executou 439 casos: 438 aprovados e uma falha ao acessar o campo de capacidade após salvar e reabrir a janela. A investigação identificou uma corrida: tarefa automática aguardava gravação e depois fechava uma janela reaberta. Foi implementado adiamento de tarefas automáticas diante de diálogo aberto, inclusive após aguardar a gravação. Os 13 testes relacionados a popups/capacidade passaram após essa correção. A bateria completa posterior foi interrompida para devolver esta revisão; não se afirma aprovação de todos os seus 440 casos. Consulte os contadores e logs incluídos.

A distância lateral livre solicitada é de 0,50 m no total entre dois veículos; o afastamento longitudinal permanece 2 m. As mudanças de organização da tela, camadas gráficas, fumaça e pedestres ficaram para a próxima revisão e não estão implementadas neste pacote.

Instale pela pasta `atualizacoes/` usando o atualizador do Rodovia Studio. A integridade do pacote e a instalação/rollback serão verificadas separadamente. Projetos, vídeos, originais e cache persistente devem permanecer preservados. Este pacote não recebe promoção automática do canal estável. `main` permanece protegida.

Prontidão estimada para uso intenso: **7/10 provisória**, sem aprovação integral desta revisão. Não houve execução nativa Windows/OneDrive/WebView2 nem certificação normativa. A análise de imagens é assistida por semelhança, amostras e CAD; não é reconhecimento semântico autônomo com acurácia medida.
