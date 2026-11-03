# Rodovia Studio 3.9

Atualização do aplicativo existente. Instale o ZIP pelo atualizador e reinicie o Studio antes de abrir o projeto.

## Correção de projetos antigos

Configurações com `traffic_classic=true` ou `traffic_model=anterior` são migradas para o motor simulado, com prevenção de colisões e respeito à sinalização. Rotas, demanda e semente são preservadas. Isso corrige a falha «A regra de ouro exige o modelo de tráfego simulado para exportar veículos». Tráfego desativado continua desativado. As verificações finais permanecem obrigatórias.

## Motor e exportação

- Cache persistente identificado pela configuração física, rede, duração e versão do código. Mudanças apenas visuais compatíveis reutilizam a simulação. Alterações físicas invalidam o cache.
- Checkpoints a cada bloco de 5 segundos permitem retomar a física após cancelamento. O MP4 reinicia sua codificação.
- Simulação e montagem avançam por blocos, com fila limitada a dois checkpoints. Histórico de veículos em disco e dois blocos decodificados em memória.
- Arquivos persistentes usam JSON/NPZ com hashes e validação, sem desserialização pickle do cache. Entradas inválidas são descartadas e recalculadas.
- A auditoria completa do tráfego e a conferência do MP4 precedem a publicação. Uma falha preserva o vídeo final anterior.

A câmera Tráfego depende de movimentos futuros: no primeiro processamento ela ainda exige a simulação completa. Não há extensão automática de uma simulação para outra duração. Os limites da fila e do histórico não representam um limite de memória para todo o aplicativo.

Taludes, zebrados DXF, janelas sobrepostas e iluminação das versões anteriores permanecem no aplicativo. A ajuda explica reutilização, cancelamento e migração.

Consulte [validação e limitações](VALIDACAO_3_9.md). Não foi medido o projeto que levou 40 minutos; o ganho depende do empreendimento, máquina e etapa de processamento.
