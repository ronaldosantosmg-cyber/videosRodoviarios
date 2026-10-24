# Entrega 1.42.7 — primeiras melhorias das etapas 3 e 4

- 315 testes aprovados; zero falhas, erros ou ignorados. Inclui 20 novos testes de persistência, concorrência, dependências e interface.
- Python e JavaScript verificados. C# compilado com e sem WebView2. Splash executado em Mono/Xvfb, conferindo versão, fabricante e animação.
- ZIP gerado exclusivamente após a aprovação pelo `validar_entrega.py`.
- ZIP instalado a partir da versão 1.42.6, iniciado fora da pasta raiz e encerrado pelo controle do aplicativo.
- Após mover a instalação, rollback recuperou todos os arquivos anteriores do programa byte a byte. Sentinelas KMZ, GeoTIFF e vídeos foram preservadas. O registro completo está em `verificacao_pacote.json`.

Pacote: `atualizacoes/RodoviaStudio_1_42_7_atualizacao.zip` — 9.151.214 bytes.

SHA-256: `03ee5e519f214a790bcd50e1c5b1b09dda0fe8f71f7e81cfac3cb442a751decd`.

Implementação incremental: persistência comum com revisão/histórico/recuperação, importação transacional dos arquivos principais, coordenação das gravações e recargas da interface, revisões de dependências e proveniência dos resultados. As extensões antigas continuam presentes e não se declara concluída toda a refatoração.

Estimativa técnica de prontidão para uso intenso: **7/10**. A melhora corresponde à proteção comprovada contra perda de edições e resultados desatualizados, não a uma certificação de produção. Para sustentar 9 ou mais ainda faltam ensaios nativos Windows/WebView2/GPU, sessões prolongadas com falhas/interrupções, projetos grandes variados e medição comparativa de memória, tempos e exportações 4K representativas. O WebGL deste ambiente usa renderização por software. Não foi realizada certificação normativa de trânsito/ferrovia.

DXF, KMZ, GeoTIFF, FFmpeg, edição, simulação e módulos WebGL locais foram verificados na instalação. ECW/MrSID e conversor DWG/ODA são componentes opcionais e não estão disponíveis neste ambiente, conforme o relatório de capacidades; não se afirma que todos os drivers foram instalados.

Main preservada no SHA `4a4e47011ce44f6a33d4fc6f7bc31cac3ec472c3`. ZIPs históricos preservados.
