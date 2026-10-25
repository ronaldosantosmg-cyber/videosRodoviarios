# 1.42.12 — entrega provisória autorizada

O usuário autorizou expressamente o empacotamento antes da repetição integral dos testes em 25/10/2026. O pacote é provisório e não recebe promoção automática do canal estável. `main` permanece preservada.

## Alterações

- Corrida de popups: tarefas automáticas adiam o disparo quando uma janela é aberta durante a espera pela gravação; prévias adiadas continuam desatualizadas. Ações explícitas mantêm salvar/descartar.
- Distância lateral livre de **0,50 m total entre dois veículos**, conforme correção do usuário, e afastamento longitudinal de 2 m. Corpos orientados e reservas de movimento; larguras ilustrativas por classe.
- Seções por lado/faixa e intervalos por coordenadas, distância ou km; pare e siga com 10 s de admissão por sentido e espera até a cauda do último veículo sair.
- Indicadores de ultrapassagem e pisca-alerta no 2D/3D/vídeo.
- Contornos de imagem assistidos por cor/textura, amostras e CAD; revisão explícita, grupos e objetos editáveis, captura persistente e máscaras/volumes abaixo do projeto. Contornos técnicos não entram no vídeo. Não há modelo semântico treinado nem acurácia medida para as nove classes.
- Diagnóstico por área em `validar_correcao.py`, com durações e evidências separadas; nunca autoriza pacote por si só.

A reorganização maior da tela, a composição por camadas, a fumaça ferroviária e o comportamento dos pedestres estão apenas no plano da próxima revisão.

## Validação efetivamente realizada

A bateria anterior executou 439 casos: **438 aprovados e uma falha**. Após investigar e corrigir a corrida relacionada, **13 testes direcionados passaram**, sem erros, falhas ou ignorados. A nova bateria de 440 casos foi interrompida por autorização do usuário após **198 aprovações**, sem falhas registradas até aquele ponto. Esses números não representam 440 aprovações da fonte final.

Integridade, hashes e sintaxe Python/JavaScript do pacote verificados. Iniciador C# compilado com e sem WebView2; splash com versão/fabricante/animação conferido em Mono/Xvfb.

ZIP aplicado sobre a 1.42.11 em pasta com espaços e acentos; inicialização fora da raiz e encerramento controlado aprovados. Após mover a instalação, rollback restaurou todos os arquivos anteriores byte a byte e preservou sentinelas KMZ, GeoTIFF e vídeo. Relatório: `verificacao_pacote.json`. Não houve execução nativa Windows/OneDrive/WebView2 nem ensaio prolongado de uso intenso.

Prontidão: **7/10 provisória**, sem aprovação integral desta revisão. A autorização de antecipação não certifica conformidade normativa ou ausência universal de falhas.

## Pacote

- Arquivo: `atualizacoes/RodoviaStudio_1_42_12_atualizacao.zip`.
- Tamanho: **3.904.375 bytes**. Evidências históricas repetidas não foram incluídas; funções anteriores são preservadas.
- SHA-256: `da1c7b8da22a3293e2975b9706ae1b78b3718107442a5a12de8f1f0cbd3e5099`.
- Fonte: `5ce584886144a30243e447242480ea939cd60bb3f312c0996391e74043b0474a`.
- Instalação: copiar o ZIP para `atualizacoes/` da instalação e usar a atualização pelo Rodovia Studio.
