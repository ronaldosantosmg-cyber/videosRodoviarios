# Evidências — 1.42.23

Base: 1.42.22, commit 9ccb0673c33a4c8a97d154f0ca2431489db10a0a, desenvolvimento/rodovia-studio-1.42. Main preservada em 4a4e47011ce44f6a33d4fc6f7bc31cac3ec472c3.

## Contrato implementado

Modo Manual deixa confirmações de formulários pendentes; Automático agenda atualização completa após confirmação válida. Abertura/reabertura, Salvar projeto, Salvar como, Prévia e Vídeo sempre passam pelo recálculo completo. A gravação interna do pipeline não inicia outro cálculo. Resultados de tarefas usam load(resultsOnly), que não dispara a política de abertura.

full_update.py delimita o recálculo no contexto de uma tarefa. Geometria, faixas e superfície desconsideram resultados derivados anteriores na primeira utilização de cada chave; uma derivação já refeita pode ser compartilhada dentro da mesma tarefa. O contexto é limpo ao terminar ou falhar. Fontes, imagens e GeoTIFF persistente são preservados. Não há limpeza genérica de dados.

O modo é preferência do navegador, sem alteração no esquema dos projetos. Abrir projeto ainda sem geometria mantém sua identificação e pede os arquivos, sem produzir uma falha artificial de cálculo.

## Testes desta revisão

118 casos únicos aprovados, sem falhas ou ignorados na consolidação pytest-direcionado.xml. Os relatórios e logs correspondem às execuções desta revisão; testes anteriores foram reexecutados. O teste antigo de reutilização do botão Atualizar foi adaptado à nova exigência de recálculo completo. A reutilização continua testada nos cálculos parciais.

- Contexto completo força nova leitura da geometria e nova superfície, sem alterar os pixels no cenário comparado.
- Cada alinhamento é refeito uma vez por tarefa completa; contexto não vaza para outras tarefas.
- Manual salva e mantém pendência. Automático grava os valores confirmados e executa uma única atualização.
- Preferência resiste à reabertura do navegador; confirmação inválida não inicia cálculo.
- Salvar projeto em Manual atualiza. Salvar como calcula a cópia e preserva o DXF da origem.
- Reabrir calcula uma vez; recarga de resultados não cria ciclo. Recarga interna durante envio de arquivo adia o cálculo até liberar a operação.
- Confirmar formulário para gerar vídeo não agenda uma segunda tarefa automática.
- Cancelar refresh mantém fonte e prévia anterior. Concluir tarefa não grava nem fecha formulário ainda em edição.
- Falha de reconstrução 3D mantém a vista anterior. Reconstrução preserva luz, tempo e diagnóstico; exportação 3D passa por reconstrução prévia.
- MP4 2D e WebGL reais: 1280×720, 24 fps, 72 quadros conferidos. O vídeo 2D publica análise, editor e vetores atuais.
- Regressões de densidade, materiais, edição, fila, barreiras, semáforos, interdições, cache corrompido, concorrência de configuração e atualização/rollback.
- Compilação Python, sintaxe JavaScript/WebGL e iniciador/splash via Mono. O ZIP final também é exercitado fora da pasta raiz, com encerramento controlado e rollback após mover a instalação.

## Ensaio com DXF disponível

dxf_real.json registra uma execução completa de Scene e uma prévia neutra de 1280×720 com mosaico de 2048. Foram refeitas geometria e superfície: 31 eixos, 6 fluxos e 6 revalidados. SHA-256 original preservado. Tempo da execução: 39,96 s neste ambiente, uma amostra. Não é comparação de desempenho, projeto salvo atual do usuário ou teste de carga.

## Limites

Validação dirigida; suíte histórica completa, Windows/WebView2/OneDrive nativos e uso prolongado permanecem pendentes. Recalcular sempre aumenta o trabalho das operações obrigatórias. Não há garantia universal de tempo, estabilidade, conformidade normativa ou resolução de qualquer ligação de tráfego. Prontidão provisória: 7,5/10.
