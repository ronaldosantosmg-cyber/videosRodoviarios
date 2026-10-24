# Verificação Rodovia Studio 1.42.3

164 testes aprovados; zero falhas, erros ou testes ignorados.
Verificados Python, JavaScript, interface Chromium, menus, controles rápidos,
zoom/pan/redesenho, inserção de vértices e desfazer, seleção prioritária de fluxos,
rotas curtas, entradas inválidas, sentido explícito e bloqueios de conectores,
frente/traseira por classe, curvas, trocas de faixa e vídeo MP4 1280×720/24fps
com 72 quadros integralmente decodificados. Capturas inspecionadas visualmente.

Compilação C# com e sem WEBVIEW2 aprovada. Splash Mono/Xvfb: versão 1.42.3,
fabricante Ronaldo Santos e animação conferidos. Avisos: depreciação de TestClient
na biblioteca instalada e código inalcançável preexistente na compilação sem
WEBVIEW2; nenhum falhou a verificação. Sem execução nativa Windows/WebView2 ou
PowerShell neste ambiente Linux.

Pacote testado em instalação temporária da versão 1.42.2, em caminho com espaços
e acentos. Aplicação do ZIP, inicialização fora da raiz, encerramento controlado,
mudança de pasta e rollback para 1.42.2 aprovados. Arquivos do programa original
restaurados byte a byte; arquivos sentinela KMZ, GeoTIFF e vídeo preservados.

SHA-256 do ZIP: `d74f28d9313b2011ff221837b77b5e4f9d6d10ad0a3adc208bbe46fed8b8bf24`.

A imagem enviada não substitui o projeto original: não foi possível reproduzir
exatamente aquele entroncamento sem DXF/KMZ/projeto. A auditoria é geométrica e
usa os sentidos e restrições disponíveis no projeto; não certifica conformidade
universal com o CONTRAN. Carretas usam corpo rígido conservador.

Após instalar, abra o projeto e use **Atualizar fluxos**. Revise os diagnósticos
verdes/vermelhos/amarelos antes de gerar o vídeo. Rotas derivadas incompatíveis
não recebem veículos; os dados originais não são apagados.
