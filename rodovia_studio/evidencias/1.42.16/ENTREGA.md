# Correção funcional 1.42.16

Central visível **Corrigir fluxos…** na faixa superior e comando **CORRIGIRFLUXOS**. Localização do defeito, recuperação de partes válidas, recorte por início/fim, acesso às propriedades e revisão das camadas restritivas. A ação de seleção ativa a edição mesmo se já estiver ativa; localização/recorte reabilitam a apresentação das trajetórias.

A inferência de troca de pista pela mudança de eixo mais próximo não desativa mais a continuidade de um eixo CAD nativo ou seus conectores do mesmo eixo. Proibições explícitas e superfícies físicas continuam aplicadas. Para outros movimentos, a central permite suspender/restaurar explicitamente apenas a inferência automática de canteiro.

Afastamentos derivados são reduzidos em tentativas limitadas quando melhora a acomodação do corpo no pavimento. Não altera o DXF nem o pavimento e não funde dois sentidos ao centro. Barreiras lineares abertas agora integram os obstáculos físicos; furos de polígonos permanecem preservados. As verificações finais de movimento, colisão, interdição/pare e siga e semáforo continuam ativas.

Validação direcionada solicitada pelo usuário: 54 testes distintos aprovados em 63 execuções, sem falhas, erros ou ignorados. Inclui chamada real de recuperação pelo novo botão, preservação do DXF, corpo/afastamento, corte, recuperação, inferência de eixos, proibição explícita, barreira aberta, sinal vermelho, trem, pare e siga, seleção e continuidade da vista. 52 execuções iniciais + 11 verificações finais da central (nove repetições dirigidas e dois testes adicionais). Suíte integral e Windows/WebView2 nativo não executados nesta revisão.

DXF disponível de regressão: 31 eixos, seis fluxos aprovados e revalidados (cinco na revisão anterior), original preservado. Isso não representa reprodução do projeto salvo atual do usuário nem certificação normativa.

ZIP aplicado sobre 1.42.15 e inicializado fora da raiz; encerramento controlado aprovado. Após mover a instalação, rollback para 1.42.15 restaurou os arquivos byte a byte. Sentinelas de KMZ, cache persistente de GeoTIFF e vídeos preservadas. Splash compilado e verificado por Mono/Xvfb.

Nota provisória de prontidão para uso intenso: 7/10. Melhorias verificadas no fluxo de correção; faltam ensaio prolongado, mais projetos reais e Windows nativo. Não é garantia universal de funcionamento ou de ausência de colisões.

Pacote: atualizacoes/RodoviaStudio_1_42_16_atualizacao.zip
SHA-256: 4f114f4bc43e17098edb48792864de84b1d9cefbdbd45b5fe2b8bbb352bc877a
