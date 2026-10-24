# Rodovia Studio 1.40 — Desktop Workspace

## Objetivo
A interface passa a priorizar a área do projeto e adota comportamento de aplicativo Windows/CAD: os painéis ficam ocultos quando não são necessários e, quando abertos, ficam encaixados e redimensionam a área gráfica em vez de sobrepor o desenho.

## Alterações
- Área do projeto ocupa a maior área útil da janela.
- Painel esquerdo começa fechado; ao abrir, entra encaixado e redimensiona o viewport.
- Painel direito começa recolhido; ao abrir, entra encaixado e redimensiona o viewport.
- Modos de painel flutuante/sobreposto deixam de ser o comportamento normal da 1.40.
- Linha de comando passa a uma gaveta inferior fechada por padrão.
- `Ctrl+Espaço`: abre/fecha a linha de comando.
- `Ctrl+B`: abre/fecha o painel esquerdo.
- `Ctrl+Alt+B`: abre/fecha o painel direito.
- `F11`: modo Projeto, escondendo o cromo não essencial e maximizando o desenho.
- Faixa de opções inicia recolhida para liberar altura.
- Cabeçalho reduzido: ações raras e repetidas ficam nos menus, em vez de competir com o projeto.
- Largura dos painéis limitada proporcionalmente à janela para evitar sobreposição e perda excessiva da área gráfica.

## Compatibilidade
Nenhum motor de análise, DXF/DWG, hachuras, elevação, tráfego ou renderização foi alterado nesta etapa. A mudança é de organização da interface e preserva os mesmos elementos e IDs para manter as rotinas existentes.

## Validação
- Sintaxe JavaScript validada com `node --check`.
- Testes 1.36, 1.37, 1.38, 1.39 e 1.40: 21 testes aprovados.
- Testes estruturais da interface: 6 aprovados, 1 ignorado.
- Os testes visuais Playwright não foram executados neste ambiente por ausência do binário Chromium; não houve falha funcional do Rodovia Studio nesses testes.
