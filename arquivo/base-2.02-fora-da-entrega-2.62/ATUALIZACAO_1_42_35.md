# Rodovia Studio 1.42.35 — estabilidade e atualização incremental

## Uso

1. Preserve uma cópia do projeto e coloque o ZIP na pasta atualizacoes/ da instalação. Use a atualização do próprio Rodovia Studio; o fechamento controlado, snapshot e rollback existentes permanecem.
2. Em Projeto → Camadas, associe explicitamente a camada ao papel Eixo, ou cadastre/selecione um alinhamento em Tráfego. O nome EIXO sozinho apenas sugere uma fonte; não habilita veículos. Eixos já explicitamente associados e rotas manuais cadastradas são preservados. Desligamentos manuais continuam valendo, inclusive no modo clássico.
3. Atualização Manual/Automático permanece. Abrir, Salvar projeto, prévia e vídeo conferem o modelo, reutilizando derivações válidas. Diagnóstico → Reconstruir integralmente refaz os resultados derivados sem apagar fontes.
4. Ao confirmar nós, aguarde a conferência de gravação. Se a resposta se perder, o aplicativo consulta a configuração persistida antes de confirmar. Se não puder confirmar, mantém as edições e orienta a nova tentativa. Não feche o aplicativo à força durante uma gravação sem antes tentar a recuperação normal.

## Alterações

- Índice/cache dos símbolos de nós, evitando buscas repetidas nos segmentos durante redesenhos.
- Limpeza do destaque e das referências gráficas do projeto anterior; rejeição de prévias de faixas e destaques que chegam atrasados.
- Catálogo CAD atual como fonte dos nomes de camadas; camadas declaradas vazias identificadas sem apagar o original.
- Fonte explícita exigida para tráfego nativo, inclusive clássico. Rotas manuais e alinhamentos usam seus cadastros existentes, sem banco paralelo.
- Requisições com prazo e conciliação de gravação em caso de resultado incerto.
- Cancelamento observável durante espera por quadros; prazo para processo auxiliar sem dados e encerramento limitado.
- Sinal de vida de tarefas separado do progresso; supervisão de cancelamento.
- Reutilização de geometria em mudanças de simulação e aparência; reconstrução integral explícita.
- Limite estimado de processos também no modo manual.
- Registro comum de etapas de desenho aplicado a nós/arrasto e ferrovia/semáforos, mantendo compatibilidade com as demais extensões.
- Formulários de modelagem desabilitam seus campos durante confirmação e restauram controles em caso de erro.
- Contexto de fonte, alinhamento, sentido e nível disponível no diagnóstico de fluxo e nas evidências da IA assistida. As propostas continuam tipadas, revisáveis e limitadas às ações existentes.

## Limites

Não é certificação normativa nem homologação nativa Windows/8 GB. O limite de memória é uma estimativa de planejamento, não quota global do sistema operacional. A causa exata de todo travamento no projeto salvo do usuário não foi reproduzida. Não há pacote de pesos/runtime 3B homologado nem execução irrestrita de correções de uma IA. Não houve substituição do motor gráfico ou reescrita geral da interface. Ver evidências desta revisão para testes realmente executados e pendências.
