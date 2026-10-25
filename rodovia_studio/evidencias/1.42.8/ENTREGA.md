# Rodovia Studio 1.42.8

Entrega na branch de desenvolvimento; main preservada.

## Correções

- Destaque lateral acompanha o painel aberto e recolhe no segundo clique; selecionar fluxos abre suas propriedades.
- Ícones distintos por comando, grupos técnicos identificados e aba Cálculos funcional; botões da versão de referência continuam acessíveis.
- Painéis destacados amplos com rolagem, confirmação Salvar/Descartar/Continuar editando e Ctrl+S. Os campos/eventos originais são movidos, sem duplicação. Salvamentos e prévias automáticos aguardam a resolução da janela. Descartar restaura dados e indicadores gráficos, preservando alterações anteriores à abertura.
- Seleção direta de mapa, imagem local, composição nos detalhes e fundo neutro. Teste com GeoTIFF real gerou uma prévia com suas cores e conferiu SHA-256 intacto da fonte.
- Temporários JSON não repetem o nome/hash de destino: no comprimento relatado, caminho temporário reduzido de 289 para 223 caracteres, mantendo o definitivo em 252. A troca é atômica, com validação pelo descritor e três tentativas limitadas se o temporário desaparecer.

## Evidência

333 testes aprovados; zero falhas, erros ou ignorados. A suíte inclui 18 testes novos e os testes anteriores adaptados ao novo fluxo de confirmação. O ambiente de testes usa pasta temporária única, sem troca de diretório de dados durante a inicialização dos workers.

Python/JavaScript verificados, C# compilado com e sem WebView2. Splash executado em Mono/Xvfb com versão, fabricante e animação. Há avisos de depreciação do TestClient e do compilador/fallback GTK, sem falha de validação.

O pacote foi gerado somente após a aprovação pelo `validar_entrega.py`. O ensaio instalado aplicou a atualização sobre a 1.42.7, iniciou fora da raiz, verificou recursos locais e encerramento controlado, moveu a instalação e executou rollback. Todos os arquivos anteriores do programa voltaram byte a byte; sentinelas KMZ, GeoTIFF e vídeos permaneceram intactas. Registro completo em `verificacao_pacote.json`.

ZIP: `atualizacoes/RodoviaStudio_1_42_8_atualizacao.zip` — 9.887.932 bytes.
SHA-256: `41a4d812c832f1bfdf5f700d8c4097d3e1b030101e58a5c6261ba7d039a3e8cb`.
Fonte aprovada: `e14d6a7806f905d058ab5e4eba4381c49e5860bb97e1b04c9902bd25e2cb9a31`.

## Limites

Estimativa técnica mantida em **7/10 para uso intenso**. O limite clássico do caminho Windows foi simulado com o comprimento informado e operações reais de gravação/leitura; Windows e OneDrive nativos não foram executados. Continuam pendentes ensaios nativos Windows/WebView2/GPU, sessões prolongadas, projetos grandes variados e medições representativas de memória/4K. Não há certificação normativa de trânsito ou ferrovia. ECW/MrSID e ODA continuam componentes opcionais, não disponíveis neste ambiente de teste.

Main: `4a4e47011ce44f6a33d4fc6f7bc31cac3ec472c3`. ZIPs históricos preservados.
