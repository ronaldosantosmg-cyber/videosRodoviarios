# Rodovia Studio 1.29 — correção do erro ao salvar, arquivos DXF + KMZ, aparência de taludes/água/sinalização, faixa de opções do Windows e nomes válidos

## Erros corrigidos
- **“Input should be 'partial' or 'total'” (interdição com modo “deny”)**
  - **Causa:** o painel de propriedades oferecia, para o campo “modo”, as opções de todos os tipos juntas. Assim, a interdição recebia “Proibida”, que é o valor da travessia, e a configuração deixava de ser salva.
  - **Agora:** cada tipo mostra só as suas opções, lidas do próprio esquema do projeto (`/api/esquema`):
    - interdição: Parcial e Total;
    - travessia: Permitida e Proibida;
    - acesso: Entrada e saída, Só entrada, Só saída.
  - **Se ainda houver um valor inválido na memória:** ele volta para o padrão antes de salvar, com aviso de qual objeto foi corrigido.
  - **Se o servidor recusar algo:** a mensagem diz o objeto e o campo em português, em vez do texto técnico.
- **Cor (#rrggbb) do pórtico e do destaque:** aparecia como uma lista “Branco/Amarelo”, o que gerava o mesmo tipo de erro. Agora é um campo de cor (digitar #rrggbb ou escolher na paleta), com validação.
- **DXF e KMZ — “só aparece um lido”**
  - **Causa:** ao escolher o DXF e depois o KMZ no mesmo campo, o navegador troca a primeira escolha pela segunda, e só um era enviado.
  - **Agora:**
    - cada arquivo é **enviado na hora** em que é escolhido;
    - há botões separados **Escolher DXF…** e **Escolher KMZ/KML…**, e também dá para **arrastar** os arquivos para a caixa;
    - a tabela mostra o nome original, o tamanho e a data de cada um, com **Retirar**;
    - **KML** solto é aceito (vira KMZ);
    - DWG e arquivos que não são DXF são recusados com explicação.

## Nomes válidos em todas as caixas
- **Regra:** vazio, só espaços ou só símbolos (ex.: “---”) não são aceitos. O nome precisa ter pelo menos uma letra ou número. Os caracteres < e > e os caracteres de controle são retirados. Limite de 80 caracteres.
- **Onde vale:** no painel de propriedades, em ATRIB, nos campos das ferramentas (pórtico, destaque, trecho de avanço, cidade) e nas caixas de diálogo.
- **Caixas de diálogo próprias:** Salvar como, Salvar perfil de camadas e Salvar sessão não usam mais a janela do navegador. Têm aviso na hora e o botão OK desligado enquanto o nome for inválido. Sessões e perfis também recusam \ / : * ? " < > |.
- **No servidor:** nomes vazios ou só com símbolos que chegarem de projetos antigos ou de importações são trocados por um nome válido ao abrir.

## Trocar textura: taludes, canteiro, água e sinalização (além do pavimento)
- **Botão direito sobre uma área do desenho:**
  - talude de corte/aterro, canteiro ou concreto → **textura própria só naquela região** (grão, tom, manchas, sulcos e brilho), ou em todo o projeto; a cor do tipo também pode ser escolhida;
  - água → aparência da água;
  - sinalização → aparência da tinta.
- **Regiões com textura (“texture_areas”):** mudam só a textura da superfície escolhida dentro do contorno. O tipo e a geometria do desenho não mudam. Têm grips e propriedades como os demais objetos.
- **Taludes:** a textura aparece com a aparência **natural (terreno)**, que pode ser ligada no próprio diálogo. Com **hachura (técnica)**, valem a cor e a hachura.
- **Água:** cor, textura de ondulação, opacidade, animação e nomes dos rios.
- **Sinalização horizontal:** cor da tinta branca e da amarela, **desgaste** (manchas fixas no terreno, sem “piscar” no vídeo) e opacidade. Amostra ao vivo no diálogo.
- **Acesso:** aba **Aparência** da faixa de opções, menu do botão direito (sem seleção) › Aparência, ou o botão direito sobre a área.

## Mais cara de aplicativo do Windows
- **Faixa de opções** no lugar da barra de menus. **Arquivo** fica em azul, com o menu; as abas são:

  | Aba | Grupos |
  |---|---|
  | Início | Projeto, Arquivos, Prévia, Seleção |
  | Inserir | todas as ferramentas, por grupo |
  | Editar | Modificar, Propriedades, Histórico |
  | Aparência | Superfícies, Camadas |
  | Fluxos | Tráfego, Câmera |
  | Vídeo | Gerar, Suporte |
  | Exibir | Janela, Desenho |
  | Ajuda | Ajuda |

  Duplo clique numa aba (ou Ctrl+F1) recolhe a faixa.
- **Tela ampla, sem rolar a página inteira:**
  - a faixa e o título ficam fixos;
  - o painel da esquerda e o editor rolam cada um por si;
  - o editor ocupa a altura toda, com o **painel de propriedades à direita da tela de desenho** (como no CAD).
- **Título:** a barra de título fica fina; a barra de navegação das seções é escondida (a faixa a substitui); a janela mostra “<projeto> — Rodovia Studio”.
- **Caixas de diálogo no estilo Windows 11:** claras, com o botão principal em azul. Vale para confirmação, nome, textura, aparência e Sobre.

## Medido neste ambiente
- **Testes automáticos:** **252 passaram** (246 da 1.28 + 6 novos). Os novos testes cobrem:
  - opções por tipo;
  - nomes;
  - envio de DXF + KML e retirada;
  - região de textura (só onde a superfície é do tipo escolhido; mais escura com brilho −0,25);
  - sinalização (cor vermelha aparece; desgaste e opacidade reduzem a tinta; valores neutros dão um quadro idêntico);
  - um teste de tela no Chromium com:
    - interdição só com Parcial/Total;
    - correção automática antes de salvar;
    - nome vazio e “---” recusados;
    - DXF e KML escolhidos separadamente, ambos carregados;
    - aparência de sinalização, água e taludes pela faixa;
    - região de talude a partir de uma área do desenho;
    - faixa de opções e Sobre.
- **Testes de tela anteriores:** ajustados ao novo layout (faixa de opções; caixas de diálogo próprias no lugar da janela do navegador).
- **Regressão TH57:** idêntica à 1.28. Com valores neutros, nada muda na imagem.
- **Opções da ferramenta:** ficam flutuando sobre a tela de desenho, para que a área de desenho não mude de tamanho ao trocar de ferramenta (antes isso deslocava os cliques).

## Não verificado / limitações
- **Windows:** não testado no seu computador.
- **Textura por região:** não se aplica à água. A água tem só ajustes gerais (cor, ondulação, opacidade, animação).
- **Sinalização:** os ajustes valem para toda a sinalização do projeto, não por faixa.
- **Tema:** a faixa de opções e os diálogos são claros e o restante continua escuro. Um tema totalmente claro ainda não existe.
