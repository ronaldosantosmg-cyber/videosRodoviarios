# Rodovia Studio 1.42.4

Os comandos da 1.39 estavam no catálogo, mas a barra original ficava oculta.
Esta revisão restabelece os botões em uma faixa visível imediatamente abaixo dos menus, antes das
ações rápidas. Não é preciso abrir o menu Ferramentas para encontrá-los.

Grupos: Edição, Navegação, Estaqueamento e obras, Fluxos de tráfego, Áreas e
sinalização, Tráfego e acessos, Calibração e cabine. A vista padrão Todas exibe a barra compacta completa de ícones, conforme a referência
1.39. As outras abas permitem filtrar um grupo quando desejado. Edição oferece diretamente Mover, Girar, Copiar, Escala, Espelhar,
Paralela, Apagar, Medir distância e ferramentas de pontos/vértices. O botão Mostrar nomes foi eliminado. O nome e a ajuda da função aparecem ao passar
o mouse ou focar o botão pelo teclado. As opções da ferramenta ficam abaixo da barra. As abas permitem
navegação por setas, Home e End. Menus em cascata e contextuais são mantidos.

Os testes comparam a lista original do ZIP 1.39 e conferem que seus comandos
estão disponíveis como botões visíveis em seus grupos, além das ações rápidas,
edição e opções, teclado e layout em 1024, 1366 e 1920 pixels.

A revisão vale para qualquer projeto. Não altera o motor gráfico: o editor
continua em Canvas 2D. A evolução para precisão CAD e cena 3D exige separar
geometria original, tolerâncias e snapping da representação de tela; trocar o
Canvas por SVG/WebGL sozinho não garante mais precisão. Foi registrada uma
proposta técnica em EVOLUCAO_GRAFICA.md, no diretório rodovia_studio do repositório.
Nenhum motor Three.js/Babylon.js/Unreal está sendo anunciado como implementado.

Mantidos a auditoria de movimento da 1.42.3, dados originais, projetos/, videos/,
KMZ, cache de GeoTIFF, atualização automática, fechamento controlado e rollback.
O pacote é gerado apenas após os testes. Compilação C# e splash via Mono/Xvfb
não substituem a execução nativa Windows/WebView2, ainda não realizada aqui.

Referência 1.39 recebida e comparada byte a byte com a usada nos testes:
SHA-256 `a3cfbbf7b71dd11b391fc170cde108d609642f778ec0aa91bab46fe30a082bba`.

## Limite automático de fluxo por projeto

Seletor visível na barra: 20, 40, 60, 80, 100, 120, 140, 160, 180 e 200 m,
mais 50 m como padrão de compatibilidade. Fluxos estritamente menores que o
limite são desligados no cálculo; o comprimento original anterior aos cortes
por cruzamento é usado para não remover pequenas subdivisões de uma via longa.
O filtro também vale para fontes manuais, eixos e rotatórias curtos.
Ao mudar a seleção, a análise é refeita automaticamente após breve espera; uma
tarefa em andamento adia o recálculo e informa para usar Atualizar fluxos.

A geometria e a opção manual de habilitação são preservadas. Reduzir o limite
pode devolver à análise trajetórias antes excluídas por comprimento, sem reativar
aquelas desligadas manualmente e sem dispensar a análise cinemática. Configurações
legadas fora dos novos passos são identificadas e preservadas no carregamento.
As verificações de sentido e movimento continuam independentes do filtro.

## Revisão de robustez e operação

Fontes de vídeo incluídas localmente com licença. Zoom com normalização da roda,
proteção numérica e maior aproximação; desfazer/refazer invalida caches, descarta
estados sem mudança e limita memória do histórico. Progresso/duração inválidos
não quebram o registro. Configuração inválida do worker é catalogada como falha.

Catálogo local de uso/desempenho e melhorias fundamentadas nos logs, acessível
pela janela Registros. Prompt IA com configuração completa, snapshots por tarefa,
hashes e versões; pacote de registros com catálogo e snapshots. Inicialização e
etapas têm tempos registrados. Falhas de detecção NVENC são reutilizadas por até
60 segundos, sem alterar qualidade de vídeo.

Limpeza protegida contra links para outras pastas, preservação de logs recentes
e comparação SHA-256 antes de remover uma cópia de trabalho de vídeo. Veja
AUDITORIA_1_42_4.md para a nota de prontidão e os limites de validação.
