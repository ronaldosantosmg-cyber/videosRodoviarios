# Evidências da revisão 1.42.30

238 casos únicos com último ensaio aprovado, sem ignorados. Retentativas não contam como novos casos. A consolidação usa o início das suítes; os relatórios brutos preservam falhas corrigidas. A suíte histórica completa não foi executada.

## Conferido

- Ultrapassagem opcional pelo próprio pesado: passagem e retorno completos em simulação com chegadas/velocidades controladas, 30 cm laterais, sem sobreposição dos corpos, com setas; recusa com largura insuficiente, barreira, velocidade igual, opção desligada, modo somente rotas ou reserva de colisões desligada. Quadro conferido no renderizador real em 14230_pesado_ultrapassa_acostamento.png. Identificação ENSAIO; não é autorização normativa.
- Entrada longitudinal de 5 m, modo de conferência com um veículo por itinerário por vez e reinserção após a saída, independente dos controles de semáforos/colisões e prevenção de travessia do canteiro.
- Distribuição padrão 80/20 e percentuais explícitos; conservação de demanda, VDM agregado por entradas/sentidos, ausência de duplicação da densidade ao adicionar ramal e cabeça de fila ponderada que não favorece sempre o primeiro índice.
- Entroncamento Y real calculado, curva tangente dentro da superfície permitida, proibição de ligação entre níveis diferentes e referência física dos trechos recuados para incorporação/seguimento.
- Confirmação individual de corredor sem hachura; barreira ainda impede continuidade. Exclusão selecionada e confirmada da circulação, com preservação da geometria e desfazer.
- Chromium real: salvar, descartar e aplicar/calcular; o cálculo recebeu VDM e controles efetivamente salvos. Modal testado em janela de 760 px; exclusão não ocorreu antes da confirmação.
- Frota Engenharia: dimensões matemáticas e de desenho 2×6 m, 0,5×2 m, 3×18 m e 3×30 m. Envelope de 30 m conferido na cena 2D, no JSON 3D e no MP4. Frota real no WebGL; o ensaio de 30 m força essa categoria somente por fixture.
- Captura WebGL com controles desativados identificada como ENSAIO, incluindo os pixels da faixa no PNG. Captura acessada pelo menu de contexto real. Saída protegida mantém a apresentação normal.
- OAE: Z do DXF preservado; Z=0 não cria barreira. Cota CAD absoluta não é tratada como desnível relativo confirmado. OAE com desnível confirmado libera a passagem sobre a ferrovia, inclusive na reserva espacial; em nível zero, a reserva continua retendo. O controle entre veículos pode ser desligado sem retirar as proteções de pessoas, obras e trens.
- Regressões dirigidas: semáforos/ferrovia, pare e siga, pedestres, colisões, seções, materiais, sondagem de pesados, interface, política de atualização, assistência, execução revisada, snapshot autenticado e MP4 com um/dois processos.
- MP4 de envelope de 30 m: 72/72 quadros decodificados, 1280×720, 24 fps, H.264. Ensaio de sondagem: 288/288 quadros. Sem erros de decodificação nos ensaios; não é prova de cada veículo em cada quadro nem teste prolongado.
- DXF TH53: SHA-256 original preservado, 31 eixos, 6 itinerários revalidados, 7 veículos ativos e 1 desenhado no enquadramento de 350 m. Preparação e quadro em 59,84 s neste ambiente. Não é comparação controlada de desempenho nem o projeto salvo atual do usuário.
- Iniciador compilado e splash conferido em Mono/Xvfb. Isso não equivale a GUI Windows/WebView2 nativa. Auditoria estática de fonte/ZIP não substitui antivírus.
- Atualização, encerramento controlado, instalação movida e rollback: consultar verificacao_pacote.json após a conferência do ZIP. Dados e fontes preservados no ensaio.

## Limites materiais

O veículo de 30 m é envelope rígido conservador, não composição articulada homologada. Não há reconhecimento universal de regulamentação, calibração DNIT/HCM/CONTRAN, garantia de contagens exatas 80/20 em vídeos curtos ou correção automática de qualquer geometria impossível. Cotas ausentes não são inventadas. A apresentação não foi substituída por outro motor.

Estimativa de prontidão para uso intenso: **7,5/10**. Pendentes uso prolongado no PC Windows de 8 GB, GUI Windows completa, calibração por empreendimento, dinâmica articulada e validação do projeto salvo atual do usuário. A main permaneceu intacta.
