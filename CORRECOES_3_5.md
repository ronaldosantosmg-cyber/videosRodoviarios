# Rodovia Studio 3.5.1 — estado do editor e progresso

Base: atualização RodoviaStudio_3_5_atualizacao.zip fornecida pelo proprietário.

- O projeto só anuncia o editor como pronto quando o resultado está atual.
- Abrir um projeto não solicita automaticamente um editor obsoleto por existir uma prévia antiga; conflito durante a leitura informa a necessidade de recalcular sem registrar uma exceção interna.
- Atualização e construção 3D mostram a operação ocupada como orientação, mantendo o bloqueio de concorrência.
- A preparação informa montagem das rotas e detalhes após recuperar a geometria do cache.
- A barra de uma tarefa não retrocede quando a simulação começa. A simulação distingue aquecimento e instante útil e informa a semeadura inicial.
- O batimento de etapas sem total conhecido mantém a porcentagem da etapa e informa o tempo decorrido, sem inventar avanço até 92%.

O log enviado registra uma execução antiga com mais de 3h40 na prévia, seguida de prévias concluídas em 79,11 s e 67,88 s. A recuperação de cache ficou cerca de 12 s nos 22%; depois, no render, a simulação reiniciou sua indicação em 22%. O log termina no início da simulação e não comprova conclusão do vídeo.

Esta correção não demonstra a eliminação de todo gargalo. O trecho, a configuração e a máquina do usuário são necessários para reproduzir o desempenho integral. Os diagnósticos preservados de simulações anteriores não equivalem à simulação do projeto atualizado.
