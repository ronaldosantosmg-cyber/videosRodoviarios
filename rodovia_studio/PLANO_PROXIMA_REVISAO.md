# Próxima revisão — área gráfica, apresentação e pedestres

Solicitado em 25/10/2026. Implementar somente depois de finalizar e validar a revisão em andamento. Este documento é um plano; não descreve recursos já entregues.

## Área útil e comandos

- Reunir controles de prévia, apresentação, imagens e limite de fluxo com os grupos técnicos da faixa superior, mantendo ajuda por hover e acesso por teclado.
- Reduzir a faixa lateral e permitir recolhimento. Abrir os respectivos painéis com espaço suficiente, cabeçalho, rolagem interna e salvar/descartar/cancelar quando houver alterações.
- Usar grupos contextuais e transbordamento acessível, evitando várias fileiras permanentes. Preservar identificação do comando, atalhos, estado e desfazer. Informações de estado permanecem no rodapé.
- Medir a área gráfica efetiva em 1024, 1366 e 1920 px e comparar com a revisão anterior; nenhuma função pode desaparecer sem um acesso equivalente.

## Composição gráfica por camadas

Separar os dados e as invalidações primeiro; escolher quantidade de superfícies após medir desempenho. Três canvas completos em alta densidade podem aumentar bastante o consumo de memória e não são automaticamente mais rápidos. Não criar três contextos WebGL independentes.

Inspeção da revisão em andamento: `app/js/05_desenho.js:draw()` limpa a superfície e recompõe fundo e desenho a cada chamada. Já há recorte visível da imagem, cache de ladrilhos e transformação comum em `app/js/02_vista_imagem_web.js`; preservar e evoluir essas proteções, sem duplicar caches. O visualizador WebGL já usa `requestAnimationFrame` para reprodução. A primeira melhoria deve medir e separar as invalidações de `draw()`, preservando as chamadas e os eventos existentes por uma camada de compatibilidade.

1. Fundo aéreo: mosaico em blocos, cache com limite de memória e resolução adequada ao zoom. Reutilizar texturas/blocos durante pan; carregar detalhe adicional ao estabilizar a vista, sem reprocessar a imagem inteira. Resolução máxima permanente não é viável para todo GeoTIFF.
2. Projeto técnico: geometria original e máscaras em cache, atualização somente por mudança de câmera, configuração, seleção ou dados pertinentes. Câmera, CRS e transformação compartilhados com o fundo e com a seleção; nenhum arredondamento das coordenadas originais.
3. Dinâmica: veículos, pedestres, indicadores e efeitos no relógio da simulação. Cálculos em tarefas independentes da interface; progresso e resultados técnicos em camada apropriada. Hachuras estáticas pertencem ao cache técnico, não precisam ser redesenhadas por quadro.

No 2D, avaliar canvas sobrepostos com apenas a camada superior recebendo os eventos e superfícies auxiliares para cache. No 3D, preferir um único renderizador WebGL com grupos, texturas e passes compartilhados. OffscreenCanvas/worker são opcionais, com fallback. A exportação deve compor as mesmas camadas na mesma ordem e excluir os contornos técnicos do vídeo.

Medir tempo de quadro p50/p95, latência de seleção/zoom, memória, pico de GPU, abertura e exportação antes/depois, incluindo DPI 1/2, imagens grandes, perda de contexto e troca repetida de projetos. Exigir equivalência dos cálculos, máscaras, seleção, desfazer e apresentação. Só aprovar otimização com ganho medido e sem regressão funcional.

## Fumaça ferroviária

Partículas limitadas por composição, com semente reprodutível e tempo da simulação. Velocidade da fumaça sempre com componente contrária ao movimento do trem e dispersão lateral aleatória limitada, sem lançamento para a frente. Definir comportamento parado e em marcha a ré. Preservar faróis noturnos, oclusão e desempenho; verificar planta, 3D e vídeo, não apenas a prévia.

## Pedestres

Agentes com estados de espera, autorização, travessia e chegada; destinos e intervalos aleatórios com semente reproduzível. Priorizar rede caminhável, faixas, passarelas e travessias semaforizadas; não gerar destinos no leito de circulação nem travessias informais automáticas.

Usar reservas de espaço/tempo entre pedestres, corpos veiculares e trens, antecipação de colisões e espera em local seguro. Distância de 50 m impede iniciar travessia desprotegida na presença de veículo ou locomotiva. Uma faixa de pedestres não dispensa checagem de segurança: a prioridade deve efetivamente deter os veículos. Em região semaforizada, considerar vermelho para o fluxo veicular conflitante e autorização dos pedestres; não interpretar vermelho de um movimento como parada de todos os demais. Nunca liberar pedestres diante de trem em passagem em nível. Passarela com separação vertical validada não interfere no tráfego abaixo.

Testar fases, amarelo/limpeza, filas, veículo já dentro da travessia, aproximação ferroviária, níveis Z, grupos densos, duas pessoas em conflito, cancelamento, pausa/retomada e exportação. Nenhuma promessa de ausência universal de colisões ou conformidade normativa sem evidência e calibração apropriadas.

## Ordem e critérios de aprovação

1. Concluir a revisão atual, incluindo a correção para **0,50 m de distância lateral livre total entre dois veículos**.
2. Ajustar a organização da tela, testar todos os comandos e registrar comparação visual.
3. Instrumentar e implementar as camadas, validar desempenho e equivalência visual/geométrica.
4. Implementar fumaça e pedestres com testes próprios, integração aos controladores e vídeo real.
5. Executar a bateria funcional e visual completa, instalação e rollback. Somente então gerar pacote em `atualizacoes/`, preservando projetos, vídeos, originais e cache persistente.

Trabalhar na branch de desenvolvimento; não alterar `main` sem autorização.
