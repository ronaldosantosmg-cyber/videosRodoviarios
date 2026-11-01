# GATE por risco

O padrão da 2.64 executa testes da alteração e das dependências diretas. A seleção inclui comportamento da janela, persistência, vídeo decodificado nos dois perfis, pavimento, estaqueamento PER, conservação de fluxo e aplicação/rollback. Não aprova a entrega apenas porque a tela abriu ou porque uma porcentagem de casos passou.

`python validar_entrega.py --gerar` usa o perfil curto quando a comparação com a 2.63 comprova o escopo conhecido de apresentação. Arquivos novos/alterados fora dessa lista e alterações no contrato antigo de modelos promovem o perfil ampliado. `--amplo` força a regressão maior. A classificação é conservadora, não substitui a revisão do diff nem prova cobertura universal de chamadas dinâmicas.

O subprocesso de testes tem limite de 180 s no perfil curto e 900 s no ampliado; exceder o prazo encerra os processos de teste e bloqueia a entrega. Não cancela uma tarefa do aplicativo do usuário. Todos os casos selecionados devem passar, sem ignorados. Os resultados podem ser reutilizados somente para produto de hash idêntico; alterações nos testes e controles de validação invalidam os casos dependentes.

Chromium headless não herda DISPLAY. O splash inicia seu próprio Xvfb e encerra-o ao terminar. Servidores de testes são encerrados e aguardados antes de abrir outro: isso evita filas artificiais e esperas de 150 s por infraestrutura inválida. Falhas de preparação devem ser investigadas, não contadas como aprovação parcial.

Evidências: `evidencias/<versão>/<tentativa>/perfil.json`, `resultado.json`, XML, log, capturas e conferência do MP4. O pacote só é produzido depois da aprovação. Os testes completos históricos e a homologação Windows permanecem trabalhos distintos e precisam ser descritos como tal.
