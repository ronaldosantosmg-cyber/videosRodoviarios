# Validação 1.42.33

35 testes dirigidos executados nesta revisão, todos aprovados, sem ignorados. Suíte histórica completa não executada. Leitura de camadas/blocos, cache limitado, troca de regras, análise do worker com uma leitura, cancelamento, atualização completa, salvar/reabrir/copiar, painéis com confirmação, preservação da vista 3D e falhas controladas. MP4 real decodificado: 72 quadros, 1280×720, 24 fps.

O DXF de referência foi novamente processado: 31 eixos, 9538 entidades convertidas no ensaio de abertura; seis itinerários revalidados, veículos visíveis na prévia real. Fonte original preservada. Geometria/hachuras/prévias e conteúdo dos fluxos do editor iguais entre antes/depois, removendo somente a revisão do motor e os contadores de cache da comparação do editor.

Um par de medições sequenciais mostrou 76,8 → 20,1 s para análise e preparação leve de fluxos; duas leituras → uma. Caches derivados inicialmente vazios em diretórios distintos. Host compartilhado, sem isolamento de carga e sem limpeza do cache de páginas do SO. Não extrapolar para todos os projetos ou para Windows. Pico RSS dos processos individuais registrado em comparacao_abertura.json; não representa a memória de todo o aplicativo/navegador.

Compilação C# com e sem WebView2 e splash Mono/Xvfb aprovados. Não é teste nativo Windows. Nota de prontidão mantida em 7,5/10: faltam homologação prolongada Windows/8 GB, projeto salvo atual do usuário e calibração mais ampla. Não há certificação normativa ou equivalência Twinmotion.

Editor gráfico dedicado de nós (inserir/mover/apagar em planta) permanece pendente. Há classificação de extremos A/B, direção/giro e ferramenta de ligação de ramal no motor existente. Nenhum modelo IA novo foi instalado nesta revisão.
