# Rodovia Studio 2.11

**Estado: NÃO validada pelo gate nem em Windows/WebView2.** Executados aqui: testes puros e do motor (shapely) do arquivo test_v14243 (13 passaram; 1 teste de navegador não executável neste ambiente). Cumulativa sobre a 2.10.

- Fluxo: a ponte sobre vão sem pavimento (canteiro, OAE, obra, túnel) agora é aplicada logo ao formar o trecho, antes da recuperação de fluxo; antes a recuperação ainda via o vão como fora da pista e cortava (caso de ~500 m em OAE). Teste sintético: vão de 300 m atravessado em um único trajeto; frestas de hachura de até 2 m e linhas transversais não cortam.
- Camadas não operacionais deixam de criar função de pavimento/fluxo.
- Menus: sem ícone duplicado; layout original `.rsCascade` preservado.
- Imagem web: tile cinza “sem imagem” do Esri em zoom alto passa a usar o ladrilho-pai (não some a ~20 m).

Não feito: textura ao vivo ao selecionar layers; painel único por eixo.

- Ícones: botões passam a usar os ícones de linha estilo Windows/CAD (mesmo conjunto dos menus), com novos: aparar, estender, medir, linha, círculo, hachura. Emoji só quando não há equivalente. Não verificado no WebView2.
