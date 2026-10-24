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


## 1.40.1 — Professional Shell
- Navegação principal reduzida a quatro hubs: Projeto, Layers, Propriedades e Vídeo.
- Faixa de opções reorganizada em Projeto, Modelar, Propriedades, Vídeo, Exibir e Ajuda.
- Ações repetidas foram removidas da faixa; os comandos continuam disponíveis no contexto, menus ou linha de comando.
- Os painéis secundários continuam acessíveis por “Mais”, sem competir permanentemente com o viewport.
- Nenhum motor de DXF/DWG, geometria, tráfego, elevação ou renderização foi alterado.
