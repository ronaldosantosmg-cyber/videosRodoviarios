# Rodovia Studio 1.13 — dia/noite e duas janelas

## Transição dia → noite
Em **Exportar vídeo → Dia e noite**:
- **Iluminação**: *Dia* (como antes), *Transição dia → noite* (escolha o instante e a duração do anoitecer) ou *Noite* (o vídeo todo).
- **Escuridão**: de 0,3 (entardecer) a 0,95 (noite fechada); o padrão é 0,78. A cena escurece com tom azulado.
- **Sinalização refletiva em destaque**: faixas, bordos e setas brilham como tinta refletiva iluminada, com um halo suave.
- **Veículos**: à noite os faróis acendem sozinhos, com feixe e lâmpadas, e as lanternas traseiras ficam vermelhas, mesmo com “Faróis acesos” desmarcado.
- O cabeçalho, o rodapé, os destaques e os textos continuam legíveis (não escurecem).
- Com *Dia*, o vídeo é igual ao da 1.12.

## Duas janelas sincronizadas
- **🗗 Duas janelas** (no cabeçalho) abre a **janela de visualização e resultados** e transforma a atual na **janela de configuração**. A janela de visualização tem o editor, as intervenções, o progresso e o vídeo, e pode ficar no outro monitor.
- **Sincronização**, feita pelo próprio navegador, sem servidor extra:
  - campos alterados na configuração chegam à visualização;
  - marcações feitas no editor chegam à configuração, que passa a salvá-las junto, sem sobrescrever;
  - um processamento (análise, prévia, vídeo) iniciado numa janela tem o progresso acompanhado na outra;
  - trocar de projeto numa janela troca na outra.
- **▣ Janela única** volta ao modo normal.
- Se o navegador bloquear a nova janela, permita pop-ups para 127.0.0.1.

## Configuração
O esquema passou para a **versão 12**, com migração automática.

## Medido neste ambiente
- **Testes**: 135 automáticos passaram (4 novos):
  - fator da transição;
  - cena escurecida, sinalização clara, lanternas acesas só à noite e quadro do modo Dia inalterado;
  - esquema v12;
  - duas janelas no navegador: marcação feita na visualização chega à configuração, campo da configuração chega à visualização sem apagar a marcação, processamento acompanhado nas duas e volta à janela única.
- **Tempo por quadro** no TH57 a 1920×1080: 673 ms de dia e 652 ms de noite (quadros da cena de detalhe), ou seja, sem custo perceptível.

## Não verificado / limitações
- **Vista da cabine**: ainda não escurece à noite. A noite vale para a vista aérea.
- **Iluminação pública**: postes e luzes não são simulados. A noite é um escurecimento da imagem com faróis, lanternas e sinalização em destaque.
- **Navegador**: as duas janelas precisam estar no mesmo navegador.
