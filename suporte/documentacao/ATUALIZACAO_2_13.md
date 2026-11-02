# Rodovia Studio 2.13

**Estado: NÃO validada pelo gate completo nem em Windows/WebView2.** Cumulativa sobre a 2.12. Motor e testes do `test_v14243` executados aqui (17 passaram; 1 teste de navegador não executável).

## Marcadores de corte com motivo
- O motor classifica cada ponto de corte: **Impedimento real** (canteiro/barreira a menos de 1 m; quadrado vermelho), **Vão sem pavimento** (sem pavimento a mais de 3 m; losango âmbar) e **Veículo não cabe na pista** (círculo laranja). Forma e cor diferem.
- Ao clicar no marcador, a janela mostra o motivo, a explicação e a correção sugerida, além das ações já existentes (Localizar, Analisar com IA, Editar trecho).

## Vão sem pavimento no editor
- Os vãos atravessados pelo fluxo (ponte de vão) aparecem como faixa âmbar hachurada translúcida; só no estudo técnico, não entram no vídeo.

Próximos (não feitos): fase/fila/pedestre do semáforo na tela, demanda por ramal na seta, prioridade de entrada/rotatória, velocidade em curva e ultrapassagem por geometria, prévia animada no editor, textura ao vivo.
