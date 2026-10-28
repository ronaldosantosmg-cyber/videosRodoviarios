# Continuação: formulários, menus e informações do rodapé

Base 1.42.36, branch desenvolvimento/rodovia-studio-1.42. Não é pacote instalável nem nova versão homologada. Main, projetos, fontes, vídeos, cache persistente e contratos do motor preservados.

## Implementado

- Confirmação compartilhada de fechamento: continuar, descartar ou salvar; uma pergunta por janela, erro visível e tentativa repetível. Aplicada aos diálogos de modelagem, catálogo de materiais, perfil do assistente e conexão de API.
- Salvamento de perfil não aplica a classificação ao projeto nem dispara atualização automática. Aplicar textura/eixo continua uma confirmação separada. Trava de gravações duplicadas e campos durante gravação; conexão não fecha enquanto grava. Descartar conexão não envia a chave.
- Expansão de ferramentas com grupos ocupando a largura disponível e mantendo atalhos/ícones principais; corrigida regra antiga que forçava nowrap. Grupos expansíveis depois das ações principais, sem empurrar botões para uma coluna estreita.
- Ícones próprios para correção, orientação de cálculos, imagens, IA e diagnóstico de veículos, mantendo handlers existentes e ajuda por título/nome acessível.
- Legenda 2D usa a mesma função de estado e a mesma paleta do desenho: trajeto válido (verde), impedimento (vermelho), conferir/pendente (amarelo) e desligado ou abaixo do limite (cinza). Contagens de trechos, não veículos. Artefato antigo ou edição pendente não pode parecer aprovação atual. Cor da rota não é estado do semáforo nem certifica compatibilidade de toda a frota.
- Rodapé em UMA linha, altura de 30 px, sem segunda/terceira linha introduzida. A mudança é informativa: percentual do avanço recebido, estado final separado, tempo explicitamente decorrido. Só mostra Concluído após estado final; 100% ainda em execução é apresentado como 99%.
- Conversão por GDAL CLI sem medição do estágio de overviews passa a indicar percentual indisponível e barra indeterminada. Conversão ECW com callback mantém avanço informado. Não há estimativa restante inventada a partir do percentual. Estimativa já fornecida pela renderização é rotulada como estimativa.
- Tempo calculado desde a criação da tarefa quando o servidor informa data válida, incluindo fila; alternativa é desde o acompanhamento nesta sessão. Textos longos recebem elipse/hover sem aumentar altura da tela. A regra existente que oculta alguns textos em telas muito estreitas foi preservada, com informação completa no hover do progresso.
- Caso de máscara irregular semelhante ao formato da captura: ensaio sintético com branco externo, ilha colorida e branco interno. Corrigido RGBA no commit anterior; esse ensaio verifica preservação da ilha e do branco interno. A captura não substitui a ortofoto georreferenciada original para reproduzir o caso real.

## Evidência atual

resultado.json consolida cada caso por classe+nome, usando a execução mais recente e sem somar repetições. Relatórios intermediários conservados. Uma falha inicial era um seletor amplo do teste que encontrou também inputs de diálogos ocultos; corrigido para o dono do rascunho. A inspeção visual identificou o conflito CSS, corrigido e retestado com medida de largura do grupo. A proposta de duas linhas para telas menores foi retirada conforme correção do usuário; teste específico confirma barra <=32 px, controles na mesma linha e altura do canvas inalterada ao iniciar progresso, em 1440, 1024 e 760 px.

Capturas finais de expansão e rodapé foram inspecionadas. Testes de API online usam provedor simulado; não houve envio para um serviço real nem inferência real 3B. Sintaxe de todos os JS conferida pelo executor de validar_entrega.py. Não foi executado o gate histórico completo nem exportado um novo MP4. Não houve pacote, teste nativo Windows ou atualização/rollback nesta etapa.

## Pendências

Consolidação de seções/sentidos/nós em editores principais; migração completa de todos os formulários e catálogo único de comandos; materiais/layers e qualidade em vídeo; ensaios no projeto real e Windows/8 GB; regressões finais de exportação/atualização/rollback antes do próximo ZIP. Prontidão global mantida em 7,8/10, sem aumento de nota por mudanças de interface.

## Vista, prévia e sessões

Controles existentes reorganizados em navegação, prévia/instante, fundo/camadas, sessões e opções avançadas. Preservados IDs, handlers e alternância para layout clássico. Corrigidas regras antigas que escondiam sessões e navegação dentro do painel; as falhas intermediárias desses testes estão nos relatórios e foram corrigidas, sem exclusão dos casos.

Descartar restaura transparências e preferências efetivas, inclusive armazenamento local. Selecionar uma sessão não altera o projeto. Escape em uma janela filha não fecha a aba principal. Respostas de listagem/restauração de sessões de outro contexto são descartadas. Testes cobrem salvar/restaurar sessão, abertura sem cálculo, descarte, controles visíveis em janela pequena e preservação de identidade ao alternar layouts. Não se trata de revisão completa de todos os caminhos assíncronos do aplicativo.
