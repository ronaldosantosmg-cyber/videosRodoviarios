# Validação da migração Studio 3.5.1

Data: 02/11/2026. Ambiente: Linux, Python 3.12; dependências da versão Studio, incluindo Pillow 13.0.0.

- 5 testes de integração passaram: prévia subpixel, pacote íntegro sem dados de projetos, editor obsoleto não anunciado como pronto, bloqueio da atualização durante tarefa e cancelamento antes da semeadura.
- 22 regressões selecionadas passaram (sinalização/fantasmas, preparo DXF, materiais/surgimento, rastro de carreta). Dois testes não pertencem a este recorte: endpoint completo de preparo DXF e relatório de simulação de 120 segundos.
- Chromium: projeto com editor antigo abriu sem solicitar editor.json; atualização e 3D aguardaram tarefa ativa; nenhum erro JavaScript não tratado no cenário exercitado.
- Sintaxe: 452 arquivos Python e 116 módulos JavaScript conferidos pelo portão original.
- Pacote 3.5.1: validado, aplicado em instalação sintética, servidor importado, estrutura sem pendências e rollback confirmado.
- Componentes: instalação e restauração verificadas.
- Servidor real: API, página inicial, JavaScript e sete texturas acessíveis/íntegras.
- pip check: sem dependências quebradas.

O portão foi executado com --sem-suite. A suíte integral não foi aprovada por esta entrega. Windows/WebView2, GPU física, vídeo completo e desempenho no desenho real do usuário não foram testados. Os workflows foram adaptados para executar o Studio; a execução remota deve ser acompanhada em GitHub Actions.

Os arquivos de proveniencia registram separadamente os hashes originais 3.5 e os arquivos corrigidos na 3.5.1. O ZIP público é gerado do código atual e não inclui o banco nem resultados antigos de testes do anexo.
