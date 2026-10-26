# Revisão 1.42.20 — conferência da entrega

98 testes distintos aprovados, sem falhas, erros ou ignorados na validação direcionada consolidada. Suíte completa não executada. Inclui cenários de segurança, edição, aplicação da seção por coordenadas/km, seleção por faixa, densidade pela interface, gravação/importação, cache de materiais, imagem, WebGL, perda/recuperação de contexto e vídeos reais.

Seções simples/duplicadas, com/sem terceira faixa, geraram respectivamente 2, 4, 3 e 5 faixas contínuas nos cenários, sem depender da hachura DXF como superfície operacional. Diagnósticos verdes, sentidos opostos por lado e omissão de trechos abaixo do limite conferidos. Desativação por faixa mantém a posição da outra faixa; acostamentos não recebem veículos; barreiras reais e desligamentos manuais permanecem respeitados. Associação ao eixo não altera seus comandos de sentido e pode ser removida pelo histórico.

Densidade fica editável com demanda preenchida; digitar a densidade retira a demanda explícita e o valor chega à configuração do servidor. Teste comparativo: densidade 1 → 6 veículos, densidade 6 → 35, sem colisões detectadas nesses cenários.

Materiais de pavimento projetado/existente, acostamentos, canteiro, taludes, OAE e ferrovia exercitados juntos em vídeo H.264 1280×720, 24 fps, 72/72 quadros decodificados. Seção típica gerou veículos no 3D sem colisões detectadas. Capturas reais de montagem da seção, perfil artístico e vídeo inspecionadas. Configuração de hachura técnica permanece salva e o cache distingue a apresentação natural.

DXF disponível: 31 eixos, seis fluxos revalidados, maior 286,29 m; original preservado por SHA-256. Não foi fornecido o projeto salvo atual do usuário; estes resultados não são reprodução exata do PC.

Iniciador C# compilado com/sem WebView2; splash verificado em Mono/Xvfb. Atualização direta 1.42.18 → 1.42.20 aprovada, inicialização fora da raiz em 1,289 s, fechamento controlado e rollback byte a byte após mover a instalação aprovados. Sentinelas de KMZ, GeoTIFF e vídeo preservadas. Não houve resíduos arquivados na instalação limpa de teste. Dados não foram limpos ou removidos por categoria genérica.

ZIP: atualizacoes/RodoviaStudio_1_42_20_atualizacao.zip — 5.363.962 bytes.
SHA-256: 56e691f14557ecf1ec3782cfb73e3c2376082ba95a1c1d7a98d3bf2098b76727.

Nota provisória para uso intenso: 7/10. Sem validação nativa Windows/WebView2/OneDrive, carga prolongada ou calibração DNIT/CONTRAN. Materiais são procedurais/ilustrativos e cotas de OAE exigem conferência; não é maquete fotogramétrica nem núcleo CAD completo. Reconhecimento semântico ainda depende de pesos e avaliação reais. O motor continua recusando reconstruções inseguras; não promete liberar qualquer traçado. Versões antigas não interpretam os controles novos de seção. Canal estável não promovido; main preservada.
