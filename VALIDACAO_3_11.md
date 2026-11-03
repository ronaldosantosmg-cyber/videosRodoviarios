# Validação — Studio 3.11

## Reprodução com os insumos fornecidos

DXF e configuração originais preservados em área de diagnóstico, sem inclusão dos arquivos do usuário no repositório ou pacote.

- Antes: reproduzido o mesmo comboio do log, com semente 1729, densidade 1, velocidade 70 km/h, frota variada e duração 220 s. A posição, itinerário e falha aos 174 s coincidem.
- Depois: todos os 220 s simulados, 1.102 amostras auditadas, zero violações, zero colisões longitudinais/laterais e 55 saídas.
- Pipeline com cache e histórico em disco também concluiu todos os 220 s, com auditoria final aprovada.
- Trecho de 172 a 175 s montado em 2.880×1.620 e reduzido para 1.920×1.080, 30 FPS, qualidade alta. MP4 H.264/yuv420p com faststart; 90/90 quadros integralmente decodificados, sem erro. Quadro em 174 s inspecionado.

As imagens de satélite e os arquivos de imagem do Windows não foram fornecidos. O trecho de teste usa fundo neutro e hidrografia online desativada; os parâmetros físicos e a geometria foram preservados. O vídeo completo de 6.600 quadros ainda não foi codificado nesta validação.

## Medições locais

Linux/Python 3.12. Física isolada completa: 14,71 s. Pipeline completo com checkpoints/cache: 45,55 s; primeiro bloco disponível em 2,84 s. Tempos medidos neste ambiente, sem imagens nem montagem do vídeo. Não representam o tempo total no computador do usuário.

## Regressões

Ajuda e catálogo conferidos no Chromium. Pacote aprovado por sintaxe, manifesto, aplicação, importação, reversão, componentes e servidor real. O portão usa `--sem-suite`, com os testes dirigidos executados separadamente.

**110 testes dirigidos aprovados**, incluindo exportação Full HD de 3 s pelo caminho principal do perfil Final, com 72 quadros decodificados.

Testes incluem reserva física, folga projetada à frente/atrás, frenagem pelo líder do destino durante a troca, mínimo de parada fora das exceções, preservação das filas de semáforo, retomada/cache, exportação, controles terminais e validação das resoluções públicas/internas. As pendências históricas de PENDENCIAS_3_6.md não são encerradas por esta revisão.
