# Revisão 1.42.19 — resultado conferido

109 testes distintos aprovados em 131 execuções finais, sem falhas, erros ou ignorados. Validação direcionada solicitada pelo usuário; suíte completa não executada. XML consolidado: pytest-direcionado.xml.

O log fornecido foi lido e tratado como dado de diagnóstico, sem incluir seus caminhos pessoais no pacote. Correções: concreto OAE (KeyError), acesso à densidade quando existe demanda explícita, recebimento da revisão após importação, coleta atual das gravações em fila, mesclagem segura de campos não concorrentes, recálculo automático aguardando painéis/importações, KMZ incremental até 256 MiB e redimensionamento fora do ResizeObserver.

Resultados: densidade 1 → 6 veículos; densidade 6 → 35 veículos no mesmo cenário sintético. Sem colisões detectadas nesses cenários. MP4 com OAE: H.264, 1280×720, 24 fps, 72/72 quadros decodificados. Quadro inicial de construção e quadro final inspecionados; pista e tabuleiro visíveis no final. Capturas da interface e da central de reparo conferidas.

DXF disponível: 31 eixos, seis fluxos revalidados, maior 286,29 m; fonte original preservada por hash. Não foi fornecido o projeto salvo atual nem o KMZ exato de 146,9 MB; o teste de grande XML usa aproximadamente 147 MiB sintéticos. Não se afirma reprodução exata de todas as condições do PC.

Iniciador C# compilado com/sem referências WebView2; splash testado em Mono/Xvfb. ZIP aplicado sobre 1.42.18; inicialização fora da raiz em 1,47 s; fechamento controlado aprovado; instalação movida e rollback byte a byte para 1.42.18 aprovado. Sentinelas de KMZ, GeoTIFF e vídeo preservadas. Detalhes: verificacao_pacote.json.

ZIP: atualizacoes/RodoviaStudio_1_42_19_atualizacao.zip — 5.963.518 bytes.
SHA-256: 04671107c81950a75e729eb2ea703c64713bc0e4739bfa950690f12574c58625.

Continuidades: reconstrução contínua optativa e limitada, mantendo rejeição segura e alternativa de exclusão; curvas paramétricas para seleção/medição, sem núcleo CAD completo. Adaptador ONNX integrado, porém sem pesos treinados: reconhecimento semântico autônomo continua pendente e indisponível na interface até instalação/avaliação de modelo adequado. Testes do adaptador não são teste de acurácia.

Nota provisória para uso intenso: 7/10. Sem validação nativa Windows/WebView2/OneDrive, carga prolongada, calibração DNIT/CONTRAN ou avaliação semântica real. Canal estável não promovido; main preservada.
