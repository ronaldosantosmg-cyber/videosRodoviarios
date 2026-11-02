# Rodovia Studio 3.6 — janelas sobrepostas e trabalho repetido removido

Base: Studio 3.5 / correção 3.5.1. Mantém o esquema de projetos 31.

## Janelas e comandos

Os painéis laterais, as opções de ferramenta, a faixa expandida e a linha de comando ficam sobre a área de projeto. Abrir e fechar esses elementos não reserva novas colunas ou linhas para reduzir o canvas. Aplicar continua salvando sem fechar; Salvar e fechar confirma; Cancelar/Fechar continuam respeitando a decisão sobre alterações pendentes. Descartar restaura o estado da janela. O cabeçalho da janela pode ser arrastado e o pan com botão do meio continua disponível.

Corrigida também a largura da linha de comando, cujo botão Fechar podia ficar fora da tela. Testados nove painéis em 1920×1080, 1366×768, 1024×768 e 760×620, mantendo o retângulo do canvas (tolerância inferior a um pixel) e os controles originais.

## Processamento

- Abrir ou salvar verifica a revisão dos resultados e reutiliza a prévia/editor atuais. Não inicia outra tarefa se os mesmos resultados continuam válidos. Reconstruir integralmente continua forçando recálculo.
- Corrigido o controle de instante: o limite do slider é aplicado antes do valor, e valores fracionários não são arredondados ao abrir. O modelo limita o instante à duração. Antes isso podia alterar a configuração apenas ao abrir o projeto, invalidando a prévia e provocando recálculo desnecessário.
- Dados do editor da mesma revisão são reutilizados; alterações de sentido, geometria, fontes ou código relevante invalidam a reutilização. Reconstrução explícita não usa esse atalho.
- O estudo de ultrapassagem usa um índice espacial, em vez de procurar em todos os percursos para cada percurso. Uma via distante não é tratada como faixa contrária ao lado da câmera. Isso é estudo ilustrativo, não autorização de ultrapassagem nem alteração das restrições físicas de tráfego.
- Busca de líder usa busca binária na ocupação já ordenada, preservando distâncias e desempate por identidade.
- Poses sem mudança de faixa usam cache limitado a 4096 entradas. A varredura de corpos usa cálculo vetorizado dos cantos e mantém a reserva física.
- JSON volumoso do editor é compacto, preservando verificação e troca atômica do arquivo.
- Codificação CPU e montagem compartilham o orçamento de núcleos. O FFmpeg deixa de disputar até 12 threads com os processos de montagem. Em máquinas com ao menos quatro núcleos, o planejamento mantém margem para a interface; isso não é garantia de utilização máxima de CPU.
- Conexão com ponta incompleta é recusada e diagnosticada, sem KeyError nem ligação inventada.

## Medições executadas nesta revisão

Linux/Python 3.12. Comparação com 3.5.1, três execuções, rodovia **sintética** de 1500 m, 33 veículos gerados, 6 s úteis mais aquecimento:

| Operação | Antes | Depois |
| --- | ---: | ---: |
| Simulação, mediana | 2,027 s | 0,926 s |
| Estudo de 180 percursos sem faixa contrária próxima | 0,474 s | 0,0074 s |

Todos os arrays de estado de todos os quadros das simulações comparadas foram iguais. Os tempos do profiler não foram usados como benchmark. Esses números não medem o computador do usuário nem demonstram a duração de um empreendimento completo.

## Pesquisa técnica aplicada

Foram consultadas fontes primárias na web:

- [MDN — posicionamento CSS](https://developer.mozilla.org/en-US/docs/Web/CSS/position): posicionamento fixo fora do fluxo normal para não deslocar o projeto.
- [MDN — diálogo não modal](https://developer.mozilla.org/en-US/docs/Web/API/HTMLDialogElement/show): mantém a interação com o restante da página quando apropriado.
- [Python 3.12 — cProfile](https://docs.python.org/3.12/library/profile.html): localizar chamadas e tempo acumulado; medir tempos separadamente do profiler.
- [Shapely — STRtree](https://shapely.readthedocs.io/en/stable/strtree.html): consultar vizinhos espaciais em vez de comparar toda a rede.
- [NumPy — desempenho em múltiplos núcleos](https://numpy.org/devdocs/user/basics.performant_code.html): evitar concorrência excessiva entre pools e bibliotecas numéricas.

## Atualizar e limites

Coloque RodoviaStudio_3_6_atualizacao.zip em atualizacoes e use o atualizador com as tarefas encerradas. O pacote depende de Python 3.12 e preserva projetos/vídeos; não é um executável portátil compilado. Cálculos afetados pela mudança de código precisam ser atualizados uma vez.

Consulte VALIDACAO_3_6.md e PENDENCIAS_3_6.md no repositório para o escopo dos testes e as falhas históricas que continuam abertas. A versão não é declarada isenta de falhas nem homologada para qualquer projeto, GPU ou Windows/WebView2.
