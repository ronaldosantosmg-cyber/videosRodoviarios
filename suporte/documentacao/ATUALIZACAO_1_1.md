# Atualização 1.1 — velocidade e NVIDIA

O modo Automático executa um teste real de três quadros com o encoder h264_nvenc na resolução e taxa escolhidas. A presença da marca NVIDIA ou do nome do encoder não é tomada como prova de funcionamento. Em caso de falha no teste, usa libx264. Se o NVENC falhar durante a gravação, a renderização é reiniciada pela CPU, preservando o número de quadros e as configurações de cena.

O progresso informa o encoder ativo, quadros processados, taxa em quadros por segundo e estimativa de tempo restante. O resultado registra o encoder em video.json.

## Otimizações

- Fontes, cabeçalho e rodapé reutilizados.
- Consulta das posições de sinalização e trajetórias reutilizada.
- Composição do traçado limitada à área visível do mapa; a câmera e o desenho são preservados.
- Cache persistente da superfície e estaqueamento: arquivos, camadas, unidades, CRS, eixo ou exclusões alterados invalidam o cache automaticamente.
- A geometria preparada pode ser reutilizada entre prévia e exportação. A leitura dos arquivos, imagem aérea e preparação de trajetórias ainda ocorrem. A primeira preparação continua necessária.
- Perfil CPU veryfast como padrão; o perfil original fast permanece disponível.

## Medição executada

CPU deste ambiente Linux, TH57 real em 2560×1440, montagem de 60 quadros de um trecho em movimento, após aquecimento:

- Versão anterior: 16.69 s, 3.60 quadros/s.
- Versão otimizada: 13.23 s, 4.54 quadros/s.
- Ganho de taxa: 26.1%; redução de tempo da etapa medida: 20.7%.
- Quadros completos em 14, 37, 66 e 106 s comparados: idênticos pixel a pixel antes da compressão.

Este teste mede montagem de quadros, não a exportação completa nem a placa NVIDIA do usuário. Não há promessa de ganho fixo no Alienware. O cache não foi contabilizado como ganho numérico nesse teste.

## Validação

10 testes automatizados passaram: fluxo anterior da API e renderização, teste de encoder, resposta negativa/timeout, cache e invalidação e falha de GPU durante gravação com reinício completo na CPU. O teste de falha em execução utiliza encoder inválido para provocar uma falha real no FFmpeg e comprovar a recuperação. Os testes positivos de seleção NVENC são simulados; não há GPU NVIDIA disponível neste ambiente.

O FFmpeg do ambiente Linux retornou indisponibilidade de NVENC e a CPU foi selecionada. O wheel Windows usado pelo aplicativo contém o encoder h264_nvenc; o funcionamento físico será confirmado pelo teste na máquina de destino. O iniciador e atualizador Windows não foram executados aqui.

NVENC usa CQ 19, VBR, preset p4 e tune hq; CPU usa CRF 16. Essas escalas são diferentes e não implicam equivalência de qualidade. Ambos mantêm H.264 High, yuv420p, 30 fps quando selecionado, keyint 250 e limite de 18 Mbit/s. A composição preservada não implica MP4 binariamente idêntico após codificação diferente.

## Uso

Feche o aplicativo antes de atualizar. Abra ATUALIZAR.cmd do pacote pequeno e selecione a pasta existente do Rodovia Studio. Seus projetos, dependências, cache de imagem e vídeo aprovado são preservados. Um backup dos arquivos substituídos é criado. Reabra INICIAR.cmd e atualize o navegador com Ctrl+F5. Deixe Aceleração em Automática.

O cache geométrico ocupa cerca de 400 MB por variante para mosaico de 8192 pixels; são mantidas até duas variantes. Pode apagar a pasta cache_geometria do projeto com o aplicativo fechado; ela será reconstruída na próxima geração. Falta de permissão de gravação do cache permite continuar sem o reaproveitamento.
