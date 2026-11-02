# Rodovia Studio 1.35 — obras do PER e cronograma (Excel / MS Project), marcadores corrigidos, seleção precisa, menus do Windows e tela simplificada

## Obras do PER e cronograma
- **Painel “Obras”:** novo ícone à esquerda e grupo **Início › Obras do PER**. Lista as obras, cada uma do km inicial ao final, com tipo, lado e datas.
  - **Duplo clique** (ou ✎) abre as propriedades da obra:
    - nome, tipo, lado e km inicial/final;
    - início, término e % concluído;
    - cor, ano e tabela do PER;
    - mostrar ou não.
  - **⌖** mostra a obra no desenho; **🗑** exclui (Ctrl+Z desfaz).
- **26 tipos de obra:**
  - duplicação, faixa adicional (3ª faixa), via marginal, iluminação;
  - passarela, OAE, alargamento de OAE, interseção/dispositivo, retorno, acesso;
  - correção de traçado, acostamento, pavimento (restauração), drenagem, contenção/talude, sinalização, defensa/barreira;
  - ciclovia, calçada, praça de pedágio, posto/base operacional, cerca;
  - passagem de fauna, baia de ônibus, travessia de pedestres e “outra obra”.
  - As intervenções pontuais (seção 4) aceitam os mesmos tipos.
- **Marcar no desenho:** ferramenta “Obra do PER” (botão **Marcar no desenho**, comando `OBRA`).
  - Clique o **início** e o **fim** sobre o eixo; a janela vem com o km preenchido e pede nome, tipo, lado e datas.
  - **Enter** confirma, **Esc** cancela.
  - A ferramenta continua para a próxima obra.
  - Se o painel estiver desafixado, ele sai da frente do desenho.
- **Importar (botão “Importar Excel / cronograma…”, comando `CRONOGRAMA`):**
  - **Excel (.xlsx) ou CSV:** colunas **Obra**, **Km inicial**, **Km final**; opcionais Tipo, Lado, Início, Término, % concluído, Ano PER e Tabela PER.
    - O cabeçalho é encontrado nas 15 primeiras linhas.
    - Aceita km como 325+850, 325,850 ou “km 325+850 a 326+200” numa coluna só.
    - Aceita datas do Excel ou dd/mm/aaaa, e % como 45, 45% ou 0,45.
    - Há um **Modelo Excel** para baixar (com a aba “Tipos aceitos”).
  - **Cronograma do MS Project salvo como XML:**
    - lê as tarefas (nome, início, término, % concluída);
    - o km vem do **nome da tarefa** (“Duplicação km 325+850 a 326+200”) ou de um **campo personalizado** com “km” no nome;
    - tarefas sem km aparecem para você digitar o km (ao digitar, a tarefa entra).
    - O arquivo .mpp não é lido: no Project, use Salvar como › XML.
  - **Tipo da obra:** reconhecido pelo texto (duplica…, marginal, ilumina…, viaduto, alargamento de ponte, 3ª faixa…).
  - **Conferência antes de gravar:**
    - uma janela mostra todas as linhas com caixas de marcar;
    - escolha **Acrescentar**, **Substituir** ou **Só atualizar datas e %** das obras de mesmo nome (para atualizar o cronograma sem perder ajustes).
- **Exportar Excel:** a lista atual vira uma planilha .xlsx (abre no Excel).
- **No vídeo:**
  - cada obra aparece como **faixa colorida** (cor do tipo) do km inicial ao final, num lado ou nos dois, além da caixa de chamada;
  - opção “Só a caixa de chamada”: o comportamento anterior.
- **Linha do tempo pelo cronograma** (painel Obras):
  - o vídeo percorre as datas, do primeiro início ao último término, ou nas datas que você escolher;
  - obra **prevista**: tracejada (pode ocultar);
  - obra **em execução**: cresce do km inicial ao final conforme o prazo decorrido, com um marcador na frente;
  - obra **concluída**: cheia.
  - Um quadro no canto mostra o **mês/ano** e quantas obras estão em execução, concluídas e previstas.
- **No editor:** as obras aparecem como faixas coloridas sobre o eixo, com sigla e nome.
- **Projetos existentes:** continuam com “Só a caixa de chamada” e a linha do tempo desligada (vídeo igual; formato do projeto 28).

## Marcadores (destaques)
- **Correção:** no painel de propriedades, digitar o nome e depois trocar a categoria (ou outra lista) **apagava o nome digitado**. Agora:
  - os campos alterados são gravados juntos;
  - um Ctrl+Z desfaz os dois;
  - sair de um campo grava o valor, como no Windows; Esc continua desfazendo a digitação.
- **18 categorias novas:**
  - redes: água/esgoto, gasoduto/oleoduto, fibra/telefonia, linha de transmissão/torre;
  - árvore/vegetação, cerca/muro, placa/outdoor;
  - desapropriação, ocupação na faixa;
  - escola, hospital/posto de saúde, comércio/indústria;
  - curso d’água/nascente, talude/risco geotécnico, patrimônio/área protegida;
  - ponto de ônibus, travessia de pedestres, ponto crítico de acidentes.
  - As 7 anteriores mantêm nome, cor e letra.

## Seleção mais precisa
- **Realce antes do clique:** o objeto sob o mouse fica realçado em amarelo, com o nome numa etiqueta.
- **Prioridade:** ponto > linha > borda de área > interior de área (a área menor primeiro). Antes, o interior de uma área podia “ganhar” de um ponto dentro dela.
- **Objetos sobrepostos:** clique de novo no mesmo lugar para alternar entre eles (como no CAD). A mensagem diz “2 objetos neste ponto (1 de 2)”.
- **Escala do Windows:** as tolerâncias de clique, grips, alça de giro e ligações acompanham a escala (125 %, 150 %). Antes ficavam menores na tela com escala, o que deixava o clique impreciso. Os grips ficaram do mesmo tamanho na tela em qualquer escala.

## Menus e janelas no padrão do Windows
- **Ícones:** ícones de linha (monocromáticos, na cor de destaque) no menu do botão direito, na mini-barra da seleção e na faixa de opções, no lugar dos emojis.
- **Menu do botão direito:**
  - itens de 32 px, atalhos à direita e a ajuda do item como dica;
  - **submenus abrem ao lado** (antes o menu inteiro era trocado).
- **Janelas novas:** as janelas da obra e da importação seguem o padrão das janelas da 1.32 (título com ×, rodapé com OK/Cancelar). Na janela da obra, Enter confirma e Esc cancela.

## Tela simplificada (modo painéis)
- **Ferramentas numa linha:** “Navegação” fica à mostra; os outros grupos viram **botões com lista suspensa** (como os grupos do Office). O botão mostra a ferramenta ativa.
- **Cabeçalho:** Duas janelas, Tela ampla, Compacto, Dicas nos campos e Como usar saíram (estão em **Exibir › Janela** e **Ajuda**). Fica a situação do ambiente.
- **Painéis sem repetições:**
  - **Projeto:** sem Novo/Salvar/Salvar como/Excluir (estão na faixa de opções e em Arquivo).
  - **Vista:** sem Ajustar/Regenerar/Atualizar fluxos/Tela cheia/Barra lateral/Área máxima (estão em Início, Fluxos e Exibir).
  - **Manutenção:** saiu da barra de ícones; use Arquivo › Limpar memória, mais completo.
- **Ordem da barra lateral esquerda:** Projeto, Configuração, Camadas, **Obras**, Vídeo, Intervenções, Vista.
- **Coluna clássica:** **Exibir › Área de trabalho › Coluna clássica** mostra tudo como antes.

## Medido neste ambiente
- **Testes automáticos:** **294** passaram (285 da 1.34 + 9 novos). Os novos testes cobrem:
  - tipos de obra e km no texto;
  - modelo Excel ida e volta (ler → exportar → ler);
  - CSV com % e km numa coluna;
  - cronograma MS Project XML (km no nome, em campo personalizado e tarefa sem km);
  - situação por data;
  - esquema 28 e categorias;
  - vídeo (só caixa igual ao anterior, faixa visível, datas da linha do tempo);
  - API de obras;
  - um teste de tela no Chromium com escala de 150 %, que verifica:
    - nome que não some e um Ctrl+Z para os dois;
    - ponto antes da área e alternância de sobrepostos;
    - realce;
    - submenu ao lado com ícones;
    - ferramentas em grupos e cabeçalho simplificado;
    - importação do Excel e do XML (com km digitado e Ctrl+Z);
    - obra marcada no desenho, editada pela lista e excluída;
    - gravação.
  - Dois testes da 1.34 foram ajustados: o de esquema passou a aceitar 27 ou mais novo, e o de tela passou a contar 7 ou mais ícones (entrou Obras, saiu Manutenção) e a achar o painel Vídeo pelo campo, não pela posição.
- **Vídeo TH57 (projeto existente):** quadros 14, 40 e 96 s e vista do trevo **idênticos** à 1.34, pixel a pixel.
- **Vídeo com obras (TH57, 1280×720):** conferido visualmente com 4 obras (duplicação, via marginal à direita, iluminação, passarela), com e sem linha do tempo, nos instantes 20, 60 e 110 s e na vista geral.
- **Atualização simulada da 1.34 para a 1.35:** aplicada pelo atualizador da 1.34, com 30 arquivos novos ou alterados, e o esquema passou a 28.

## Não verificado / limitações
- **Windows:** não testado no seu computador.
- **Cronograma real:** a leitura do MS Project XML foi testada com um XML montado aqui, não com o seu cronograma. Mande o XML (ou a planilha) se alguma tarefa não for reconhecida. Os campos personalizados com “km” no nome funcionam quando o Project grava o apelido (Alias) do campo.
- **Obras no editor:** a faixa no editor não é selecionável por clique. Use a lista (⌖ mostra; duplo clique edita).
- **Linha do tempo:** usa as datas do cronograma, distribuídas igualmente ao longo do vídeo, sem pausa por mês.
- **Tela simplificada:** vale na Tela ampla com janela única (como os painéis). No modo Compacto e em Duas janelas, a tela continua como antes.
