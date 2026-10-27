# Continuidade após a revisão 1.42.35

Atendido nesta revisão: cadastro explícito de fonte de tráfego nativa (papel Eixo ou seleção com sentido), preservando alinhamentos e trajetórias manuais do cadastro existente; bloqueio também no clássico; sugestões de nome não selecionam Eixo automaticamente. Limpeza dos destaques e estado gráfico ao trocar projetos, rejeição de respostas atrasadas de faixas/camadas/hachuras e catálogo CAD atual como fonte dos nomes. Camadas CAD declaradas vazias continuam preservadas e identificadas.

Causas de resíduo comprovadas no código: layerShow/layerPrev não isolados na troca e prévias de faixas sem guarda de contexto. Testes sintéticos cobrem ambos os caminhos. A ocorrência específica no projeto salvo do usuário ainda não foi reproduzida; não declarar que todo desenho residual possível foi eliminado.

Pendências de homologação: uso prolongado Windows/WebView2 e 8 GB, projeto salvo real do usuário, modelo/runtime 3B e API real. Limite de processos é estimativa, não quota global de memória. Migrar outras extensões de desenho para o registro comum apenas com regressões próprias; não reescrever a interface.

Manter branch de desenvolvimento, main protegida, fontes e dados persistentes preservados, testes atuais antes de qualquer pacote e ZIPs históricos intactos em atualizacoes/.
