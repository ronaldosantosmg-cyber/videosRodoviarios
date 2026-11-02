# Rodovia Studio 2.06

**Estado: NÃO validada pelo gate completo (`validar_entrega.py`), nem em Windows/WebView2. Gerada por decisão do usuário (gate dispensado). Nada foi publicado em `main`.** Cumulativa sobre a 2.05. Microsimulador fora do fluxo.

## Novo
- **Vista estável:** localizar item, mostrar camada ou editar não altera o zoom quando o ponto já está visível; fora da tela, apenas desloca. Zoom só quando solicitado.
- **APARAR (TRIM)** — comandos `APARAR`, `TR`, `TRIM` e botão ✂ em Editar › Modificar: remove o trecho de fluxo/acesso/linha entre as interseções vizinhas ao clique, usando os demais objetos como arestas; divide em duas partes se o corte for no meio. Ctrl+Z desfaz. Linha simples de 2 pontos: só corta ponta.
- **Pincel:** Shift+clique troca a origem sem sair da ferramenta.
- Formulários com *Aplicar* (opt-in) e “Cancelamento solicitado” (já na 2.05 parcial), mapeamento do percurso em `auditorias`.

## Verificado
Apenas a lógica do APARAR em Node (4 testes) e sintaxe JS. **Não verificado:** comportamento no navegador, testes de regressão e gate.

## Instalação
Feche o app, rode `ATUALIZAR RODOVIA STUDIO.cmd`. Projetos, vídeos, DXF/KMZ e cache GeoTIFF não são tocados. Rollback: `RESTAURAR VERSAO ANTERIOR.cmd`.
