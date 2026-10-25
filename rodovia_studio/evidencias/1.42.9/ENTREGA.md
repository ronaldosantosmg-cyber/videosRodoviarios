# Entrega 1.42.9

Correções: confirmação de dados dos popups antes do cálculo, sincronização após conversão de imagens, inventário original de camadas independente da análise, preservação de classificação nos grupos de cor, atualização do gerenciador de camadas, orientações de recuperação de rotas e recuperação do mouse após interrupção de arraste.

Validação completa: 350 testes aprovados; zero falhas, erros e ignorados. Splash animado conferido em Mono/Xvfb; iniciador C# compilado com e sem WebView2. A compilação mantém um aviso CS0162 de código inalcançável; não é erro de compilação. Diagnóstico rápido separado: 14 testes; não autoriza gerar pacote.

ZIP gerado somente após a validação. Aplicação sobre 1.42.8, inicialização fora da raiz, encerramento controlado, mudança de pasta e rollback para 1.42.8 passaram. Os arquivos anteriores do programa retornaram byte a byte; sentinelas de KMZ, GeoTIFF persistente e vídeo permaneceram intactas. Detalhes em verificacao_pacote.json.

O DXF fornecido apresentou 295 camadas, 283 com entidades, incluindo eixos nomeados; o inventário não equivale à simulação completa do empreendimento. A conversão foi validada por reutilização de GeoTIFF válido no cache; não houve execução de conversor ECW nativo Windows.

Windows/WebView2, OneDrive e conversão DWG do computador do usuário continuam sem validação nativa. A nota de campo 2/10 informada para a 1.42.7 não é substituída por uma nota alta baseada apenas nos testes Linux. A revisão ainda requer validação de campo para atribuir nova nota de prontidão para uso intenso.

SHA-256 do ZIP: 2418b9c18104e5b7fbc60db0b9f9b74f6d245283edf0bd586b2d00ee52bd37f9

Main preservada: 4a4e47011ce44f6a33d4fc6f7bc31cac3ec472c3. Branch: desenvolvimento/rodovia-studio-1.42.
