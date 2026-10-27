# Validação dirigida — Rodovia Studio 1.42.35

27/10/2026. Base publicada 1.42.34, branch desenvolvimento/rodovia-studio-1.42. Main preservada.

## Evidências atuais

100 testes únicos aprovados, sem falhas ou ignorados na seleção final. Consolidação em pytest-direcionado.xml; origem, deduplicação e escopo em consolidacao_testes.json. Rodada de motor: 85 aprovados em 31,18 s. Rodada de interface/integrados: 15 aprovados em 321,91 s. Um caso de layout repetido após recolher a opção de reconstrução: aprovado em 35,42 s, sem somar duas vezes.

Cobertura dirigida: cadastro obrigatório de fonte nos dois modos; nós e desativação manual; recuperação de gravação após resposta perdida; falha e nova tentativa; rejeição de respostas atrasadas e limpeza de destaques; catálogo atual/declarações vazias; cancelamento e encerramento de auxiliares; espera do encoder com prazo e liberação da thread; dependências/cache; limites manuais de processos; atualização automática sem tarefa duplicada; reconstrução explícita; arrasto técnico; conservação de vista 3D; proteção de dados; MP4 paralelo e vídeo de nós no motor protegido, ambos decodificados.

O XML pytest-interrompido-antes-correcao.xml conserva duas falhas reais detectadas durante a implementação: a thread de escrita não encerrava após cancelamento/prazo. Corrigido com sinal de parada; testes correspondentes passaram na rodada final. Não há falha obrigatória conhecida deixada aberta nessa seleção. A suíte histórica completa não foi executada; a seleção e exclusões estão documentadas, não representam cobertura de todos os comandos do aplicativo.

## DXF e imagem

DXF DUPLICAÇÃO TH53 fornecido: 31 eixos geométricos, 7 itinerários revalidados, 6 veículos ativos e 2 desenhados no recorte em t=1 s; os 4 restantes estavam fora da vista. Nenhum corpo fora da superfície nesse instante. Camadas foram cadastradas explicitamente no ensaio; não houve autorização automática no produto. Fonte preservada. Prévia neutra HD inspecionada visualmente. O ensaio não usa o projeto salvo atual do usuário e não prova ausência universal de conflito.

## Medições

medicoes.json contém duas comparações pontuais com a 1.42.34 extraída do ZIP histórico. Cenário sintético: abrir → densidade → material reduziu leituras DXF de 3 para 1. Preparação da alteração de densidade: 1,0888 s antes e 0,0684 s depois. Alteração de material: 0,6650 s e 0,6811 s, sem ganho demonstrado de tempo nessa etapa, apesar de evitar leitura DXF. RSS de processo: 467,15 MiB e 446,76 MiB; não é memória global.

No navegador: abertura 14,0017→11,0901 s; reabertura 12,2838→5,4599 s; salvar nó 0,9472→0,1085 s. Pan/zoom têm tempos incluindo automação e espera, não são FPS. Vinte desenhos reutilizaram os caches nas duas versões. Heap JS 6.887.344→7.229.444 bytes: não houve redução nessa métrica. Uma execução por versão em host compartilhado, sem controle para atribuir todo ganho à mudança. Não extrapolar para Windows/8 GB.

## Distribuição e limites

92 módulos JavaScript/WebGL passaram na verificação de sintaxe. Iniciador C# compilado com e sem WebView2; splash conferido em Mono/Xvfb, com evidência própria. Isso não equivale a homologação Windows nativa. Verificacao_pacote.json, quando disponível ao lado, registra atualização 1.42.34→1.42.35, funcionamento fora da raiz, fechamento controlado, preservação de dados e rollback após mover a instalação.

Pendências: teste prolongado Windows/WebView2/8 GB e projeto salvo real do usuário; orçamento global CPU/GPU/IA é estimado, não quota física; demais extensões de interface ainda não migradas; modelo 3B e API real não homologados. Sem certificação normativa, laudo antivírus ou promessa de qualidade Twinmotion.

Prontidão estimada: 7,8/10 para uso intenso, fundamentada nos testes dirigidos e limitada pelas homologações pendentes. Não é certificação.
