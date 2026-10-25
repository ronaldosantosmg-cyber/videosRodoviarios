# Fluxos contínuos — 1.42.13

Depois de atualizar, use **Calcular e atualizar fluxos**. A mudança do motor invalida os resultados derivados antigos; DXF, projetos, imagens, KMZ e vídeos originais são preservados.

O motor passa a usar todos os eixos habilitados do DXF, inclusive os secundários. O traçado automático complementa as vias sem eixo, evitando duplicar trajetórias paralelas ao eixo cadastrado. A trajetória derivada preserva o alinhamento; a suavização de um itinerário inteiramente nativo fica limitada a 0,50 m de desvio.

Fragmentos alinhados da mesma camada, nível e configuração de sentido podem ser unidos na derivação quando o encontro é inequívoco, o desvio angular não ultrapassa 10°, a distância não ultrapassa 0,25 m e a ligação cabe no pavimento. O DXF original não é movido nem regravado. Não se juntam ramificações ambíguas, camadas/níveis incompatíveis, eixos desligados ou uma lacuna fora do pavimento. A junção é suspensa se há cortes/edições vinculados a identidades salvas; vínculos anteriores de desativação são preservados.

Um pequeno trecho interno criado nos encontros continua pertencendo ao eixo longo. O limite de 50 m (ou aquele escolhido no projeto) vale para o eixo/itinerário; esse pedaço interno não cria uma mini-rota nem um ponto independente de nascimento de veículos. Encontros quase coincidentes não eliminam 1–3 m do próprio eixo. Minirrotas automáticas independentes continuam excluídas. Excedentes externos ao pavimento podem ser aparados; uma lacuna interna não vira entrada/saída artificial nem é atravessada por atalho.

**Linhas de bordo são sinalização, não barreiras físicas.** Selecione o fluxo e confira o motivo nas propriedades e o ponto vermelho. “Corpo fora do pavimento” exige conferir a hachura/classificação da pista ou reposicionar a faixa. Canteiros, obstáculos, exclusões, cortes, sentidos proibidos e curvas inviáveis continuam bloqueando. Não foi criado um comando para ignorar todos os erros.

Para uma escolha manual explícita, use **Rota de veículos → Selecionar uma linha / Seleção contínua**, confira o sentido/faixas e confirme. **Recuperar fluxo principal** continua disponível para revalidar os restos de um eixo defeituoso, sem unir através das partes excluídas. Ajuste os vértices de curvas reprovadas ou a superfície de pavimento e recalcule. O diagnóstico identifica separadamente corpo fora da pista, esterçamento, mudança brusca, auto-interseção e ziguezague.

Revisão com testes direcionados funcionais e visuais, no fluxo simplificado solicitado. Os resultados exatos e os limites de validação estão nas evidências. Não constitui certificação CONTRAN nem comprovação de ausência universal de falhas; não houve execução nativa Windows/OneDrive/WebView2. A reorganização da tela e as outras funções previstas para a próxima revisão permanecem separadas desta correção.
