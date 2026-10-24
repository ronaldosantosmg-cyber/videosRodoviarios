# Rodovia Studio 1.40 — Desktop Workspace

## Objetivo de produto
A interface passa a seguir um modelo **viewport-first** semelhante a softwares desktop de engenharia/CAD: o projeto é o elemento principal; ferramentas e informações aparecem somente quando necessárias e nunca devem cobrir o desenho durante a operação normal.

## Princípios de UX
1. **Projeto primeiro:** a área gráfica recebe todo o espaço não utilizado por um painel ativo.
2. **Sem sobreposição operacional:** painéis laterais e linha de comando entram no fluxo da janela e redimensionam o viewport.
3. **Divulgação progressiva:** recursos avançados ficam recolhidos até serem acionados.
4. **Uma ação, um comando:** parâmetros como resolução, qualidade e modo não devem gerar comandos duplicados no cromo.
5. **Contexto antes de quantidade:** ferramentas específicas devem aparecer de acordo com seleção/atividade.
6. **Estado previsível:** abertura, fechamento e foco seguem regras únicas e são persistidos apenas quando útil.
7. **Operação por teclado:** atalhos não interceptam digitação em inputs, selects, textareas ou campos editáveis.

## Arquitetura de frontend
O controlador da 1.40 foi isolado em `app/js/50_desktop_workspace.js` e expõe somente uma API pública controlada em `window.RodoviaDesktopWorkspace`.

Responsabilidades do módulo:
- estado de layout e persistência;
- abertura/fechamento da linha de comando;
- modo Projeto;
- recolhimento da faixa de opções;
- integração com os painéis existentes sem alterar o motor;
- redimensionamento coordenado do viewport;
- atalhos de teclado e acessibilidade.

O módulo usa `requestAnimationFrame` para agrupar redimensionamentos e `ResizeObserver` para manter o canvas sincronizado com mudanças reais de tamanho.

## Alterações de interface
- Área do projeto ocupa a maior área útil da janela.
- Painel esquerdo começa fechado e abre encaixado.
- Painel direito começa recolhido e abre encaixado.
- Painéis flutuantes/sobrepostos deixam de ser o comportamento normal.
- Linha de comando vira gaveta inferior fechada por padrão e **não usa `position: fixed`**.
- `Ctrl+Espaço`: abre/fecha a linha de comando.
- `Ctrl+B`: abre/fecha o painel esquerdo.
- `Ctrl+Alt+B`: abre/fecha o painel direito.
- `F11`: ativa/desativa o modo Projeto.
- Faixa de opções inicia recolhida.
- Cabeçalho reduzido e comandos repetidos removidos do cromo principal.
- Painéis têm largura mínima/máxima e limite proporcional à janela.
- Foco por teclado recebe indicação visual consistente.
- `prefers-reduced-motion` é respeitado.

## Regras de manutenção
- Nenhum módulo de interface da 1.40 deve executar cálculo de geometria, DXF/DWG, tráfego ou renderização.
- Novos painéis devem ser encaixados por padrão.
- Novos comandos devem reutilizar uma ação canônica existente antes de criar um novo botão.
- Estados de UI não devem ficar espalhados em variáveis globais.
- IDs existentes usados pelo motor são preservados para reduzir regressão.
- Alterações de layout devem disparar um único ciclo coordenado de resize.

## Compatibilidade
Nenhum motor de análise, DXF/DWG, hachuras, elevação, tráfego ou renderização foi alterado nesta etapa. A mudança é de organização da interface e preserva os elementos necessários às rotinas existentes.

## Testes da 1.40
O conjunto específico de regressão verifica:
- existência da API do workspace;
- presença de `ResizeObserver`;
- gaveta de comando encaixada, sem `fixed`/`absolute`;
- painéis forçados ao fluxo do layout;
- proteções de atalhos em campos editáveis;
- atributos básicos de acessibilidade;
- isolamento do workspace em relação ao motor de engenharia.

## Próxima consolidação
A segunda fase da 1.40 deve revisar o catálogo completo de comandos e consolidar a interface em quatro áreas canônicas: **Projeto, Layers, Propriedades e Vídeo**, eliminando duplicidades remanescentes do ribbon/menu/contexto sem remover capacidade funcional.
