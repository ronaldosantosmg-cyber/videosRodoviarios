# Entrega aprovada — Rodovia Studio 1.42.38

Pacote novo: atualizacoes/RodoviaStudio_1_42_38_atualizacao.zip (11877570 bytes).
SHA-256: `d655a7b174084a4c0a518ba08ffbcb363467342fa2f21fb1e7bab39b3c24c708`.

## Correção entregue

A falha na consulta de andamento deixava a tarefa ativa, encerrava o acompanhamento e fazia a fila emitir erros após dois minutos. Agora há reconexão de leitura da mesma tarefa, sem reenviar o cálculo. Retomar fica visível no rodapé compacto. A fila aguarda a aplicação do resultado recuperado; pedidos equivalentes continuam compartilhados. Duas consultas redundantes após a conclusão foram retiradas. Falhas reais continuam sendo informadas.

A geometria, os critérios de circulação e os cálculos não foram alterados. A interrupção inicial de comunicação no computador do usuário não foi reproduzida exatamente; a recuperação foi ensaiada com falha de conexão injetada, incluindo servidor real e confirmação de POST único.

## Validação desta revisão

971 casos aprovados; zero falhas, erros ou ignorados no resultado consolidado. A rodada completa está em entrega/; houve quatro erros de inicialização do Chromium (Page.goto, 60 segundos, antes do corpo do teste). Os dois módulos foram repetidos com menor concorrência em processos novos, mantendo os critérios: 12 casos passaram. Foram reutilizados 959 resultados válidos do mesmo produto; nenhum fonte ou teste mudou entre as duas rodadas. Consulte entrega-validada/resultado.json, pytest-resultados.xml, retomada.json e os hashes de origem.

- Compilação C# com e sem WebView2 e splash 1.42.38 conferidos em Mono/Xvfb, incluindo fabricante e animação.
- Testes funcionais e visuais de fila, retomada, cancelamento, histórico, painéis, nós, seções, materiais e imagens.
- MP4s 2D/3D produzidos e decodificados; os relatórios de cada cenário estão nas evidências. Não são validação de GPU Windows.
- ZIP final instalado em pasta isolada com espaço e acento: os cinco scripts corrigidos coincidiram por hash com o pacote. Rollback 38 → 37 conferido; configuração, KMZ, cache GeoTIFF e vídeo de teste preservados por hash. Procedimento e resultado: verificar_pacote.py e pacote-real.json.
- Encerramento controlado do servidor em outra pasta aprovado na suíte completa.

## Atualizar

Salve o trabalho e mantenha cópia do projeto. Coloque o ZIP em atualizacoes/ da instalação e use o atualizador do aplicativo. Confirme o encerramento controlado e reabra pelo iniciador. Não extraia sobre o programa aberto. Schema 31 mantido; rollback para 1.42.37 disponível pelo atualizador.

## Preferência e limites

Registrada em AGENTS.md a instrução do usuário: toda correção deve terminar em novo ZIP aprovado, sem sobrescrever históricos, com link HTTPS verificado e SHA-256.

Prontidão de referência: 7,8/10. Permanecem pendentes homologação nativa Windows/WebView2 em 8 GB, carga prolongada e reprodução com a configuração exata do projeto do usuário. Não inclui pesos de IA 3B; não há afirmação de ausência universal de travamentos, conformidade normativa ou ganho de desempenho sem medição. As durações dos testes não são benchmarks de abertura/pan/zoom no PC do usuário.

Publicação restrita à branch desenvolvimento/rodovia-studio-1.42. Main permanece em 4a4e47011ce44f6a33d4fc6f7bc31cac3ec472c3. Histórico de ZIPs preservado.
