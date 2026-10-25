# Entrega 1.42.11 — ícones InfraRail

Integra o pacote de 32 símbolos SVG fornecido pelo usuário. O original está em `pacote/suporte/sistema/app/icons/infrarail-sprite.svg`, preservado byte a byte: SHA-256 `a54a83c01a61d34d60706f0d761e7d2226f36ba86dc9ebefd81989a72745e9dc`.

## Interface

- Corte por início/fim, junção, nova rota, direção, ferrovia, semáforo, OAE, edificações e vegetação usam símbolos correspondentes na barra técnica abaixo dos menus.
- Recuperação e direção única/dupla recebem ícones nas propriedades; nomes acessíveis e textos são preservados.
- Catálogo mostra símbolos de materiais/redes, gás, postes, hidrologia, erosão, cortina, fibra, radar e torre.
- Iluminação alterna os ícones de dia/noite; diálogo ferroviário distingue carga e passageiros por silhueta. O ícone não identifica um modelo físico específico de locomotiva.
- Sem dependências de rede, botões novos sem ação ou captura de mouse pelos SVGs. Os símbolos adicionais permanecem disponíveis no sprite para funções correspondentes futuras. As funções existentes e o agrupamento são preservados.

## Evidências

Os testes específicos verificam a integridade e o conteúdo passivo do arquivo; renderização dos 32 símbolos no Chromium com a página real; tamanho de desenho dos símbolos referenciados; clique nos comandos de corte, junção, ferrovia, semáforo e OAE; ajuda por hover; ícones de recuperação/direção e preservação do texto acessível; recriação do catálogo após busca; alternância dia/noite no WebGL real.

Imagens: `14211_01_icones_barra_tecnica.png`, `14211_02_pacote_32_simbolos.png` e `14211_03_catalogo_com_simbolos.png`. O painel com 32 amostras na segunda imagem é exclusivamente de teste, não um menu extra do produto.

## Prontidão

**7/10, estimativa provisória para uso intenso**, mantida da revisão anterior: esta revisão melhora a iconografia e sua integração; não substitui validação nativa Windows/OneDrive/WebView2, conversores DWG/ECW do usuário, projetos reais salvos e sessões prolongadas. A suíte Linux não certifica conformidade normativa ou ausência universal de erros.

Para instalar: copiar o ZIP para `atualizacoes/` e usar a atualização pelo Rodovia Studio. Pacotes históricos, projetos e vídeos são preservados. Código publicado apenas na branch de desenvolvimento; `main` preservada.

## Resultado final

409 testes aprovados; zero falhas, erros ou ignorados. Sintaxe Python/JavaScript e dependências verificadas; iniciador C# compilado com e sem WebView2; splash validado em Mono/Xvfb. Execução completa em Linux: 823,87 s. Avisos conhecidos Starlette/httpx, C# CS0162 e fallback de cores GTK não impediram a aprovação.

O ZIP foi aplicado sobre a 1.42.10 em pasta com espaços e acentos, iniciado fora da raiz e encerrado pela API de controle. A página instalada contém os 32 símbolos e o módulo local. Após mover a instalação, rollback restaurou todos os arquivos anteriores byte a byte, preservando sentinelas KMZ, GeoTIFF e vídeo. Estes ensaios não equivalem à execução nativa Windows.

- ZIP: `RodoviaStudio_1_42_11_atualizacao.zip`; 12260089 bytes.
- SHA-256: `db066d5dbb1d351f25bbc35625ce66df49e9718e3b4ea140f720a733d8c8ae38`.
- Fonte validada: `ebf44bacb1cafe6d3b07943ed5a6026dd44b3d4a15b7bbeaee54226369fd73ff`.
