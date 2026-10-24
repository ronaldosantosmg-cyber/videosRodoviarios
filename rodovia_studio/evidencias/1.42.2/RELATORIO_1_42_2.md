# Rodovia Studio 1.42.2 — resultados

121 testes aprovados, nenhum falhou ou foi ignorado. 46 testes executaram Chromium. Compilação C# com e sem WebView2 aprovada e splash verificado em Mono/Xvfb. Fontes Python, sintaxe JavaScript e dependências verificados.

## Mudanças verificadas

- Comando ativo, coordenadas, referência e legenda na parte inferior, inteiramente visíveis.
- Botões rápidos abaixo do menu com ações reais, Desfazer/Refazer preservados e Propriedades alternável.
- Barras sem sobreposição do canvas em 1024, 1366 e 1920 px.
- Todas as rotas/fluxos em primeiro plano durante a edição, cores de diagnóstico e contorno de contraste. Verificação de pixels confirma o fluxo visível acima da superfície.
- Clique de fluxo tem prioridade sobre a área subjacente no modo Editar fluxos. Grips das rotas continuam acessíveis.
- Regressões de menus em cascata, contexto, API, rotas menores que 50 m, números inválidos, GeoTIFF persistente, KMZ, vídeo, snapshot e rollback aprovadas.
- Instalação do ZIP final sobre a 1.42.1, inicialização por outro diretório, encerramento controlado e rollback após mover a instalação: aprovados. Todos os arquivos originais do programa voltaram byte a byte, e os dados foram preservados.

## Artefato

SHA-256: `ab7f36ecbd7bd065af8423e6812eebd890f4af4f8605c088b304bf756193886d`.

- [Tela com botões e rodapé](1422_01_acesso_rapido_rodape.png)
- [Fluxos acima das superfícies](1422_03_fluxos_sobre_superficies.png)
- [Seleção prioritária de fluxo](1422_05_selecao_fluxo_prioritaria.png)
- [Resultados JUnit](pytest-resultados.xml)
- [Instalação e rollback do pacote](verificacao_pacote.json)

Validação em Linux/Python 3.12/Chromium/Mono, com trechos sintéticos e fixtures. Execução nativa de PowerShell/WebView2 no Windows não foi realizada. A revisão não altera o iniciador 1.4 já fornecido na 1.42.1. Não há certificação de um empreendimento completo ou dos drivers do usuário.
