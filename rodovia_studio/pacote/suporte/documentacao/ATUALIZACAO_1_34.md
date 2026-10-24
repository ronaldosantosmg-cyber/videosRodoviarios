# Rodovia Studio 1.34 — painéis por menu, visual do Windows (claro e escuro), progresso sempre visível, comandos contínuos e texturas artístico-realistas

## Painéis por menu (mais área para o desenho)
- **Barra de ícones à esquerda (tela ampla):** a coluna de seções virou uma barra de ícones. São 7 painéis:
  - Projeto, Configuração, Camadas, Vídeo e Manutenção;
  - Intervenções (antes ficava abaixo do editor);
  - Vista: prévia, instante da câmera, fundo de edição e sessões (antes eram as linhas acima do desenho).
- **Abrir e fechar:**
  - clique num ícone para abrir o painel;
  - clique de novo no ícone, ou em **×**, para fechar.
  - Fechar só tira o painel da frente: os campos, as tarefas e a edição continuam como estão.
- **📌 Fixar / desafixar:**
  - **Desafixado** (padrão): o painel abre **por cima do desenho**, e o desenho não muda de tamanho. Volta a se esconder quando você clica no desenho com a ferramenta Navegar. Com outra ferramenta ativa (ex.: Intervenção preenchendo X/Y), o painel fica aberto.
  - **Fixado:** o painel fica encaixado ao lado e o desenho se ajusta à largura que sobra.
  - A **barra da direita** (Propriedades, Marcações…) também ganhou 📌: desafixada, abre por cima do desenho.
- **Menus abrem o painel certo:** ex.: Vídeo › Configurar vídeo abre o painel Vídeo.
- **Área máxima (F10):** fecha o painel e recolhe a barra da direita.
- **Coluna antiga:** **Exibir › Área de trabalho › Coluna clássica** volta a mostrar todas as seções na coluna.

## Visual do Windows 11 — Claro, Escuro ou Igual ao Windows
- **Exibir › Tema:**
  - **Igual ao Windows** (padrão): segue o modo claro/escuro do Windows e muda junto quando o Windows muda.
  - **Claro** ou **Escuro**: fixa o tema escolhido.
  - O comando `TEMA` alterna entre os dois.
- **O que muda:**
  - fontes Segoe UI;
  - cores e botões do Windows 11 (campos com linha inferior, botão principal na cor de destaque);
  - faixa de opções, menus, barra de status, janelas e painéis com as mesmas cores.
  - No modo escuro, os menus, as janelas e a faixa de opções também ficam escuros (antes ficavam claros).
- **Tela de desenho:** continua escura nos dois temas, como num CAD.
- **Ao abrir:** o tema é aplicado antes de a página aparecer, sem piscar.

## Progresso sempre visível
- **Quadro de progresso:** aparece no canto inferior direito ao gerar vídeo, prévia, análise, exportação ou quadros PNG. Mostra:
  - o que está sendo feito;
  - a barra e a porcentagem;
  - a mensagem atual;
  - o tempo decorrido e o que falta (acima de 60 s, em minutos);
  - **Cancelar**.
  - Ao terminar, mostra “Concluído”, “Cancelado” ou “Falhou” por alguns segundos.
- **Downloads com progresso:** os arquivos baixados também aparecem no quadro, com tamanho baixado e total. Valem: registros (.zip), prompt para IA, vídeos guardados e exportações.
  - O arquivo vai para a pasta de downloads com o nome do servidor.
  - **Cancelar** interrompe o download.
- **“–”** esconde o quadro; o progresso continua no rodapé (barra maior que na 1.33).

## Comandos: Enter confirma, Esc cancela, o comando continua
- **Comandos sobre objetos** (MOVER, COPIAR, GIRAR, ESCALA, ESPELHAR, OFFSET, APAGAR):
  - ao concluir, o comando pede o **próximo objeto**: clique nele e o mesmo comando se repete;
  - **Enter** sem nada digitado, **Esc** ou um clique no vazio encerram, sem perguntar (nada fica pela metade);
  - digitar outro comando ou escolher outra ferramenta também encerra.
- **Ferramentas de desenho** (área de pista, hachura, faixas, acesso, alinhamento…):
  - **Enter** conclui o objeto e a ferramenta **continua pronta** para o próximo;
  - Enter de novo, sem pontos, encerra.
  - Esc continua pedindo confirmação quando há pontos marcados.
- **Arrastar:**
  - **Shift** (ou Orto ligado) prende o movimento na horizontal ou na vertical;
  - **Esc** durante o arraste devolve o objeto ao lugar, sem perguntar;
  - o rodapé mostra a distância e os deltas enquanto arrasta.

## Texturas “Artístico realista” (padrão dos projetos novos)
- **Camada a mais sobre as texturas realistas:**
  - **Grão fino em vez de manchas:** o asfalto e o concreto deixam de ter as “nuvens” de 2 a 5 m e ganham grão fino.
  - **Bordas da pista:** levemente mais escuras (pó/sombra, até ~0,6 m da borda); a grama junto ao pavimento fica um pouco mais seca.
  - **Cor do asfalto:** variação suave de tom em dezenas de metros.
  - **Detalhes de perto:** pedriscos claros do agregado.
  - **Grama:** em manchas de dois verdes, com folhagem fina de perto.
  - **Concreto:** placas de tom diferente e manchas.
  - **Talude de corte:** pedras e veios no solo.
- **Onde escolher:** **Exportar vídeo › Texturas** (Artístico realista, Realistas ou Anteriores). A amostra da textura no editor mostra o estilo escolhido.
- **Projetos existentes:** continuam com as texturas que tinham (formato do projeto 27, convertido automaticamente).

## Tela sem referências a versões anteriores nem ao TH57
- **Saíram da tela:**
  - o botão **Abrir exemplo TH57** (menu Arquivo, faixa de opções e seção 1);
  - a ficha técnica do vídeo de referência TH57 (seção 5).
- **Opções e textos renomeados:**
  - as opções “Como na 1.x” passaram a se chamar **Clássico**;
  - a opção de imagem “Cache TH57” passou a ser “Imagem guardada no pacote (trecho de exemplo)”;
  - os títulos da Ajuda não têm mais o número da versão;
  - a estrutura em Ajuda › Sobre mostra as extensões sem o número da versão.
- **O vídeo gerado:** não tinha nem passa a ter qualquer texto de versão ou do TH57.
- **O que não mudou:** os projetos e o exemplo continuam funcionando internamente (os testes usam o TH57).

## Medido neste ambiente
- **Testes automáticos:** **285** passaram (279 da 1.33 + 6 novos). Os novos testes cobrem:
  - esquema 27 e migração das texturas;
  - texturas artísticas (mudam só as superfícies, sem mudar o tom geral; borda mais escura; menos manchas grandes);
  - amostra de textura artística;
  - tela sem TH57 e sem número de versão;
  - módulos 39–42 e as variáveis dos dois temas;
  - um teste de tela no Chromium, que verifica:
    - os painéis (abrir por cima sem mudar o desenho, fechar, fixar reduzindo o desenho, × sem perder dados, menu abrindo o painel, clique no desenho fechando);
    - os temas (Windows escuro, claro guardado ao recarregar, volta ao Windows);
    - o quadro de progresso na análise e no download dos registros;
    - MOVER repetido em outro objeto, Esc e Enter encerrando, e COPIAR;
    - a ferramenta que continua após Enter;
    - o arraste com Shift e o Esc no arraste.
- **Testes de tela anteriores:** passaram a abrir a interface na “Coluna clássica”, em que foram escritos, já que os campos agora ficam em painéis. Mudaram também nestes pontos:
  - **dois testes** (alinhamento por cliques e área de pista) pressionam Enter duas vezes, porque a ferramenta continua após o primeiro Enter;
  - **um teste da 1.33** passou a verificar a visibilidade do painel com `checkVisibility`, porque o painel desafixado é posicionado por cima.
- **Vídeo TH57 (projetos existentes):** quadros 14, 40 e 96 s e vista do trevo **idênticos** à 1.33, pixel a pixel.
- **Texturas no TH57 (1280×720, caches prontos):**

  | | Realistas | Artístico realista |
  |---|---|---|
  | Tempo por quadro (14/40/96 s) | 0,17 / 0,40 / 0,35 s | 0,17 / 0,43 / 0,40 s |
  | Diferença média nos quadros do percurso | — | 0,02 (de 255) |
  | Diferença média na vista de perto (60 m) | — | 3,8 (de 255); a 260 m: 0,7 |

  Nos quadros do percurso (câmera alta), a pista ocupa poucos pixels e a diferença é pequena. O ganho aparece nas aproximações e na vista de perto.
- **Atualização simulada da 1.33 para a 1.34 (pelo atualizador da 1.33):** aplicada, com 57 arquivos novos ou alterados, e o esquema passou a 27.
- **Capturas no Chromium (1850 × 1000):** temas claro e escuro, painéis fechado/aberto/fixado, painel Vista, quadro de progresso, menu do botão direito no escuro e barra da direita desafixada.

## Não verificado / limitações
- **Windows:** não testado no seu computador, incluindo:
  - o tema “Igual ao Windows” no Edge/WebView2 do .exe;
  - os downloads com progresso no WebView2 (no Chromium, o arquivo foi salvo).
- **Painéis:** valem na **Tela ampla** e na janela única. No modo Compacto e em “Duas janelas”, a coluna continua como antes.
- **Arquivos muito grandes:** para mostrar o progresso, o arquivo baixado fica na memória do navegador até ser salvo. Para vídeos de vários GB, use “Abrir pasta” em Vídeos gerados.
- **Realismo das texturas:** a avaliação é visual. O que se mediu foi que mudam só as superfícies, que as bordas escurecem e que as manchas grandes diminuem.
