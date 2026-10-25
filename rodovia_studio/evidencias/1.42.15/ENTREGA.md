# Revisão 1.42.15 — validação direcionada

Correção prioritária para perda da vista após comandos de rotas: preservar centro e escala em CRS, conservar a prévia já carregada quando ficar desatualizada e manter a imagem anterior diante de falha temporária, sem atravessar sessões de projetos diferentes. Corrigida exceção ao apresentar fluxos sem cache vetorial.

52 verificações aprovadas, zero falhas/erros/ignorados: 47 na execução principal, três de WebGL/exportação MP4, duas verificações finais de isolamento e entrada inválida (uma repetição dirigida). O relatório consolidado conserva as três execuções. A suíte integral não foi executada; procedimento direcionado solicitado pelo usuário. Sem certificação de Windows/WebView2 nativo, conformidade normativa ou carga prolongada.

DXF de regressão: 31 eixos, cinco fluxos aprovados novamente pela análise de movimento, original preservado. O DXF disponível não é uma reprodução do projeto salvo atual do usuário.

Área gráfica em Chromium Linux: 1366×900 passou de 1236×479 para 1239×579 pixels (+21,2% de área). Caches auxiliares limitados a 32 MiB, fallback sem duplicação de transparência, equivalência de pixels e invalidação por câmera/dados verificadas. Medição sintética de 15.000 segmentos: p50 de pintura CPU de 8 ms direto e 0,9 ms em cache; não é medição de FPS de projeto real nem de memória GPU.

Aplicação do ZIP sobre 1.42.14, inicialização fora da raiz, encerramento controlado, movimentação da instalação e rollback para 1.42.14 aprovados. Arquivos do programa restaurados byte a byte; sentinelas de KMZ, GeoTIFF persistente e vídeos preservadas. Splash compilado e testado por Mono/Xvfb, com versão, fabricante e animação. Drivers opcionais ECW/MrSID e DWG/ODA ausentes neste ambiente.

Pendentes: fumaça ferroviária e motor de pedestres seguro em 2D/3D/vídeo. Protótipo incompleto preservado fora do pacote em desenvolvimento/pedestres_em_validacao/. A entrega não ativa esse protótipo.

Nota provisória de prontidão para uso intenso: 7/10. As regressões dirigidas melhoraram a confiança; faltam validação Windows nativa, projetos reais adicionais e ensaio prolongado de carga para justificar nota 9 ou superior.

Pacote: atualizacoes/RodoviaStudio_1_42_15_atualizacao.zip
SHA-256: 48de8a4cd701c0076476c21ae47b00c7ced4c5899c13c7839cb768ce4d4642c3
