# Recuperar fluxo principal

Selecione uma trajetória no estudo de fluxos e abra as propriedades. Use **Recuperar fluxo principal…**, confirme a gravação dos dados pendentes e aguarde o recálculo.

O motor mantém o eixo original e aplica a recuperação à sua origem geométrica correspondente, incluindo as partes resultantes dos cortes de contato. Localiza falhas de movimento/corpo e auto-interseções, exclui intervalos com margem e revalida integralmente cada parte restante. Trechos abaixo do limite do projeto não recebem veículos. Uma desativação manual não é reativada. Sentidos explícitos e restrições físicas permanecem. Não há criação de atalhos entre intervalos excluídos.

No estudo técnico, partes recuperadas aparecem em verde, excluídas em vermelho e o estado geral parcial em amarelo. Esse realce não é exportado no vídeo. O desenho permanece intacto; veículos usam somente os trechos aprovados. Pode haver interrupções na circulação onde existem lacunas. Isto não garante uma rota contínua do início ao fim.

As propriedades mostram os comprimentos calculados, que podem somar faixas/sentidos. Para retornar ao comportamento anterior use **Remover recuperação** ou **Desfazer**. Se nenhuma parte passar, o motor mantém o bloqueio e pede ajuste manual. A ação não certifica conformidade normativa nem corrige a superfície de pavimento mapeada incorretamente. Confira a classificação das camadas, a largura e a posição do eixo quando o motivo for corpo fora da pista.

A configuração de recuperação foi adicionada como campo separado, preservando a leitura pela versão anterior durante rollback.
