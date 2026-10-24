# Rodovia Studio 1.42.2

Ajustes sobre a 1.42.1 conforme a revisão de uso:

- **Rodapé:** comando ativo, coordenadas, referência de km e legenda verde/vermelha/amarela ficam abaixo da tela gráfica. A linha de comando, quando expandida, também abre na parte inferior. O layout reserva altura para as informações, sem cortar a legenda.
- **Acesso rápido abaixo do menu:** Novo, Abrir, Salvar, Desfazer, Refazer, Propriedades, Selecionar, Enquadrar, Editar fluxos, Nova rota, Atualizar fluxos, Prévia e Gerar vídeo. Os botões utilizam as ações existentes e se distribuem em mais de uma linha nas telas menores.
- **Edição de fluxos:** o botão Editar fluxos ativa/desativa o modo persistente. As ferramentas de fluxo/rota também ativam o destaque durante o comando. Todos os fluxos, rotas, faixas calculadas e ligações são redesenhados em primeiro plano, com contorno de contraste e setas de sentido. Grips continuam visíveis.
- **Seleção:** no modo de edição de fluxos, rotas e trajetórias têm prioridade sobre as superfícies ao clicar. Fora desse modo, a seleção geral permanece disponível. Alt+clique/Tab continuam permitindo percorrer objetos sobrepostos.
- **Cores:** verde, vermelho e amarelo conservam os diagnósticos da 1.42.1. O destaque não reabilita rotas curtas nem modifica a simulação ou o vídeo final.
- Menus em cascata, opções da ferramenta e mini-barra da seleção continuam disponíveis. As opções de edição ficam abaixo da barra rápida; informações de estado ficam no rodapé.

Os testes desta revisão incluem posição e visibilidade do rodapé, ações dos botões, fluxo acima de superfícies, prioridade de seleção e telas de 1024, 1366 e 1920 px, além das regressões de atualização, rollback, dados persistentes e MP4.

Resultados atuais no pacote: suporte/documentacao/validacao_1_42_2/. A execução nativa de PowerShell e WebView2 no Windows não é testada nesta máquina Linux; o splash é validado em Mono/Xvfb e o C# compilado com e sem WebView2. A revisão não altera o iniciador 1.4 da 1.42.1; quem ainda usa um EXE anterior deve recompilá-lo pelo comando existente.
