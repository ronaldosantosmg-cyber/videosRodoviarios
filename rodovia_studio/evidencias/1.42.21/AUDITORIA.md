# Auditoria da revisão 1.42.21

Base conferida: 1.42.20, commit fa5a0d3a1e1381a6c41052d0e62ce8780b36cdda, branch desenvolvimento/rodovia-studio-1.42. A main não integra esta alteração.

## Levantamento e dependências

| Área | Entrada e dependência | Situação encontrada e tratamento |
|---|---|---|
| Configuração | 01_estado_configuracao, project_state, dependencies | Salvar persiste configuração; automações adicionais em 56 e 73 iniciavam análise. Retiradas essas automações, sem remover seus comandos manuais. |
| Prévia | 19, 27, start/poll em 07 | Temporizadores regeneravam após alterações e abertura de propriedades. O agendamento agora marca pendência; Atualizar inicia trabalho explicitamente. |
| Janelas | 59_paineis_destacados | Concluir janela podia agendar análise. Agora conclui gravação/descarte e comunica pendência, mantendo o controlador existente. |
| Tarefas | start, poll, pipeline3D/capture | Fila local por projeto/contexto/configuração, reutilização da mesma promessa para pedidos equivalentes; execução sequencial e descarte de contexto antigo. Backend mantém validação de revisões. |
| Progresso | progress/message originais, quadro 41, captura 54 | Um estado Map e uma apresentação no rodapé; poll publica eventos, sem uma segunda consulta periódica. O temporizador antigo de porcentagem/ETA em 38 foi retirado; poll não escreve diretamente na barra. Captura e downloads usam o mesmo controlador. |
| Menus e ferramentas | 45, 53, extensões 54/57/62/63/65/66 | Catálogo antigo é montado para registrar extensões dinâmicas; 75 reorganiza suas instâncias, preservando handlers. Cinco abas e oito menus. Não foram removidos workers ou rotas. |
| Geometria | geometry.analyze → render/Scene/editor/vectors | Cache JSON comprimido, validado, com fallback ao leitor e chave de entradas/configuração/código. Fonte técnica preservada. |
| Tráfego | geometria → topologia/seções → simulação | Densidade/velocidade invalidam simulação e resultados, sem invalidar editor/geometria. Seção/sentido invalidam topologia. Proteções permanecem. |
| Aparência | materiais/imagens → apresentação → prévia/vídeo | Controles existentes reunidos em Cena. Material padrão é reatribuído no cache sem substituir mapeamentos explícitos. Mudanças de aparência não invalidam editor. |
| Tela 2D | 68_camadas_graficas + 05_desenho | Dois caches auxiliares e canvas principal preservados; chave por camada. Reuso por translação no pan em superfícies menores; superfícies grandes mantêm desenho direto. Liberação do pan reconstrói a vista exata. |
| Imagem | 02_vista_imagem_web + tiles locais/online | Fonte original e exportação preservadas. Tiles locais separados por projeto/fonte, fallback de nível e rejeição de resposta de outro contexto. |
| WebGL | viewer.mjs, scene3d, capture3d | Motor existente preservado e testado separadamente. Não recebe automaticamente a estratégia dos caches 2D. |
| Atualização | atualizador, launcher | Sem substituição nesta revisão; ensaios de snapshot, encerramento, mudança de pasta e rollback exigidos na entrega. |

As cópias dos cinco scripts alterados em desenvolvimento/automacoes_arquivadas_1_42_21 são registro do comportamento anterior. Os módulos ativos permanecem no aplicativo; não se presumiu obsolescência por ausência de referências estáticas.

## Comparação e limites

medicoes.json compara 1.42.20 extraída do ZIP histórico com a implementação nova no mesmo cenário sintético. Os relatórios XML correspondem a execuções desta revisão, incluindo testes anteriores reexecutados; não constituem execução de toda a suíte histórica.

Incrementalidade ainda é conservadora por categoria: alterar uma geometria pode reconstruir toda a geometria dependente. O cache não transforma a simulação em atualização parcial por veículo, nem garante aceleração em todo hardware. RAM total/GPU e uso prolongado no Windows não foram medidos. A imagem não ganha resolução inexistente na fonte. Reconhecimento semântico autônomo, núcleo CAD completo e reconstrução universal de ligações permanecem fora desta revisão.

O painel contextual e as janelas extensas reutilizam os controladores existentes. As opções avançadas continuam disponíveis; não há uma implementação nova paralela para cada comando. A seção típica continua sendo fonte explícita de faixas, sem liberar barreiras ou sinal vermelho.
