# Rodovia Studio 1.33 — mais área para o desenho: barra lateral em abas e janelas flutuantes, área máxima, progresso no rodapé e vídeo/registros nos menus

## Barra da direita em abas (recolher / expandir)
- **Abas no lugar da coluna longa:** Propriedades ☰, Marcações do projeto 📌, Ajuste DXF × imagem ⌖, Conexões de tráfego ⤳ e Avisos da análise ⚠.
  - Só uma aba aparece por vez. Os avisos amarelos saíram do fim da coluna e foram para a aba ⚠, que mostra quantos são.
  - Os campos são os mesmos de antes (só mudaram de lugar).
- **Recolher / expandir:**
  - Clicar na aba aberta (ou em ⯈) recolhe a barra numa faixa estreita de ícones, e o desenho ganha a largura. Clicar num ícone expande de novo.
  - Também por **Exibir › Barra lateral**, pelo botão **Barra lateral** do editor e por **Ctrl+Shift+L**.
- **Ao editar, a barra volta sozinha:**
  - Ao selecionar um objeto, a aba **Propriedades** abre, mesmo com a barra recolhida.
  - Ao desmarcar, a barra volta como estava.
- **Janelas flutuantes (popout):**
  - **⧉** destaca a aba aberta numa janela própria, que se arrasta pelo título e se redimensiona pelo canto.
  - **⇲** ou **×** devolve a janela para a barra.
  - A posição, o tamanho e quais abas estavam destacadas são lembrados ao reabrir o programa.

## Área máxima (F10)
- **O que faz:** esconde a coluna da esquerda (projeto, configuração…) e recolhe a barra da direita. O editor ocupa a largura toda.
- **Como ligar:** F10, botão **Área máxima** do editor, **Exibir › Área de trabalho** ou comando `AREA`.
- **Editar continua possível:**
  - selecionar um objeto mostra as propriedades;
  - abrir uma seção pela faixa de opções (ex.: **Vídeo › Configurar vídeo**) traz a coluna da esquerda de volta até o próximo clique no desenho.

## Progresso no rodapé; tempos em minutos
- **A seção “Progresso e resultado” saiu da coluna.** No lado direito da barra de status (rodapé) ficam:
  - a mensagem (clique para lê-la inteira, com acesso aos registros);
  - uma barra de progresso pequena;
  - a porcentagem, o tempo decorrido e o que falta;
  - o botão **Cancelar**.
  - A barra, o tempo e o Cancelar só aparecem durante uma tarefa.
- **Tempos acima de 60 s aparecem em minutos** (e horas acima de 60 min):
  - nas mensagens do servidor (vídeo: “falta ~2 min 05 s”; simulação de tráfego; durações nos registros);
  - no tempo de processamento;
  - no instante da prévia, no percurso do avanço e na duração dos vídeos gerados.
  - Exemplos: `45 s`, `2 min 05 s`, `1 h 02 min`.

## Gerar vídeo e registros nos menus
- **Gerar vídeo:** o botão saiu da seção 5 da coluna e fica no menu superior (faixa de opções):
  - **Início › Vídeo:** Gerar vídeo e Vídeos gerados;
  - **aba Vídeo:** Gerar vídeo, Configurar vídeo (abre a seção 5) e Cancelar;
  - comando `VIDEO`.
  - Ao terminar um vídeo, a lista de **Vídeos gerados** abre sozinha.
- **Registros:** a seção “Registros e suporte” saiu da coluna e foi para os menus:
  - **aba Vídeo › Suporte:** Ver registros, Exportar prompt para IA, Baixar registros (.zip) e Detalhes do erro;
  - **menu Arquivo:** Registros e suporte, Prompt para IA, Baixar registros (.zip) e Detalhes do último erro.

## Medido neste ambiente
- **Testes automáticos:** **279** passaram (274 da 1.32 + 5 novos). Os novos testes cobrem:
  - os tempos em Python e em JS (iguais, inclusive a conversão das mensagens);
  - o uso dos tempos no servidor;
  - a estrutura da tela;
  - um teste de tela no Chromium, que verifica:
    - as abas com os mesmos campos;
    - recolher (a tela de desenho fica mais de 200 px mais larga);
    - a reabertura sozinha ao selecionar e o recolhimento ao desmarcar;
    - a janela flutuante e o encaixe;
    - a área máxima com F10 e a coluna voltando ao abrir uma seção;
    - o progresso, o tempo e o Cancelar no rodapé;
    - a mensagem em minutos;
    - os itens da faixa de opções.
- **Vídeo TH57:** quadros 14, 40 e 96 s e vista do trevo **idênticos** à 1.32, pixel a pixel. Só o texto da mensagem de progresso mudou.
- **Atualização simulada da 1.32 para a 1.33 (pelo atualizador da 1.32):** aplicada, com 23 arquivos novos ou alterados. A pasta principal continuou organizada.
- **Capturas no Chromium (1850 × 1000):** tela normal, barra recolhida, seleção reabrindo, área máxima, janela flutuante, rodapé durante a tarefa e aba Vídeo.

## Não verificado / limitações
- **Windows:** não testado no seu computador (Edge/WebView2 do .exe).
- **Área máxima:** vale na **Tela ampla**. No modo Compacto (coluna única) a página já usa a largura toda.
- **Janela flutuante:** fica dentro da janela do programa (não é uma janela separada do Windows). Não pode ser levada para outro monitor.
