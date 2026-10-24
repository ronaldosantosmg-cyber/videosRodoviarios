# Rodovia Studio 1.30 — abrir projeto, renomear, modelos, rotas de veículos por trecho, painéis recolhíveis, gerenciador de camadas e pincel de textura

## Abrir projeto salvo
- **Como abrir:** **Arquivo › Abrir projeto…**, **Ctrl+O**, o botão **Abrir…** da faixa de opções ou o comando **ABRIR**.
- **O que a janela mostra:**
  - um cartão por projeto, com a **miniatura da prévia** (quando existe);
  - DXF/KMZ carregados, vídeo gerado e data da última gravação;
  - na linha de baixo: origem → destino, data de criação e nomes dos arquivos enviados.
- **Procurar e ordenar:** busca por nome, origem, destino ou nome do arquivo. Ordena pela gravação, pela criação ou pelo nome.
- **Duplo clique (ou Enter) abre.** Alterações pendentes do projeto atual são salvas antes.
- **Na mesma janela:**
  - **Renomear…**
  - **Duplicar…** — cópia sem caches; o projeto aberto não muda.
  - **Salvar como modelo…**
  - **Excluir…** — vai para `_lixeira`.
  - **Novo projeto…** — pede o nome.

## Renomear projeto
- **Como renomear:** **Arquivo › Renomear projeto…**, o botão **Renomear** da faixa ou o comando **RENOMEAR**.
- **Onde o nome muda:** na lista de projetos, na configuração e no título da janela.
- **Nomes recusados:** os mesmos das caixas da 1.29 (vazio, só símbolos, nome já usado por outro projeto).

## Modelos de projeto
- **Salvar como modelo…** guarda as configurações do projeto:
  - vídeo, aparência, sinalização e texturas;
  - funções das camadas;
  - perfis e opções.
- **Marcações no modelo:** opcional (áreas, placas, fluxos, rotas, destaques…). Sem marcações, o modelo serve para qualquer trecho.
- **O que nunca entra no modelo:**
  - dados do trecho: nome, origem/destino, km, conferências, alinhamento, imagens locais;
  - arquivos DXF/KMZ.
- **Novo a partir de modelo…** cria um projeto com as configurações do modelo. Depois é só enviar o DXF/KMZ.
- **Aplicar ao projeto aberto:**
  - troca só as configurações;
  - marcações, km, arquivos e camadas do projeto ficam;
  - uma cópia da configuração anterior fica na pasta do projeto (`config_antes_modelo_<data>.json`).
- **Gerenciar:** renomear e excluir modelo (vai para `_lixeira`).
- **Onde ficam:** os modelos ficam na pasta de projetos, em `_modelos`. Modelos antigos são migrados ao abrir.

## Rotas de veículos (vários alinhamentos)
- **Criar:** **Fluxos › Rota de veículos** (comando **ROTA**/**RT**). O alinhamento pode ser desenhado por:
  - cliques;
  - uma linha do desenho;
  - seleção contínua.
  Enter confirma. Pode haver até 50 rotas.
- **Tipo de pista por rota:**
  - **pista simples:** um sentido de cada lado;
  - **pista dupla:** N faixas por sentido e canteiro central;
  - **sentido único:** N faixas no sentido do desenho.
- **Sentido:** o sentido em que a rota é desenhada fica à direita do alinhamento (mão de direção).
- **Trecho da rota** (comando **TRECHO**/**TR**): clique o início e o fim sobre a rota. Naquele trecho vale outro tipo, por exemplo simples → dupla com 2 faixas por sentido. Os trechos também aparecem numa tabela no painel de propriedades (início, fim, tipo, faixas, canteiro), com apagar e acrescentar.
- **Transições:** suaves (40 m, ajustável). Uma faixa que acaba converge para a faixa vizinha que continua, e uma que começa sai dela. Assim a rede de tráfego liga as duas.
- **Opções por rota:** velocidade (km/h), nível (viaduto) e “fora do pavimento” (deixa os veículos andarem onde o desenho não tem pavimento).
- **No editor:** as faixas aparecem já calculadas (verde = sentido do desenho, laranja = sentido oposto), pelo mesmo cálculo usado no vídeo. **Atualizar fluxos** faz os veículos usarem as rotas.
- **Sem pintura:** as faixas das rotas só conduzem veículos. Não geram pintura, setas, zebrados nem linhas de parada, e não cortam os outros trechos.

## Painéis com dados que expandem e recolhem
- **Grupos do painel de propriedades:**
  - Identificação;
  - Aparência e dimensões;
  - Vídeo e tráfego;
  - Outros;
  - Trechos da rota;
  - Grips.
- **Controles:** clique no título de um grupo, ou use **Expandir tudo** / **Recolher tudo**. A escolha fica lembrada.
- **Grips:** começam abertos quando há até 8 vértices.
- **Coluna esquerda:** **Exibir › Expandir painéis / Recolher painéis** abre ou fecha todas as seções e quadros.

## Gerenciador de camadas
- **Como abrir:** **Aparência › Gerenciador de camadas** ou o comando **CAMADAS**/**LA**.
- **A janela:**
  - é grande e redimensionável, e a tabela também aumenta;
  - tem filtro (aceita `*`, ex.: `SIN*`) e lista só visíveis, ocultas, congeladas ou com função;
  - mostra, por camada: função (editável), número de entidades, **Visível**, **Congelada** e **Ver**.
- **Ações sobre as camadas marcadas:**
  - Mostrar, Ocultar, Congelar, Descongelar;
  - **Isolar** (oculta as outras, menos o eixo);
  - **Congelar as demais (edição final)** — trava tudo menos as marcadas;
  - Mostrar e descongelar tudo;
  - **Desfazer**.
- **A tabela de camadas da coluna esquerda** também pode ser aumentada (arrastar a borda de baixo).

## Pincel de textura
- **Como abrir:** **Editar › Pincel de textura** ou o comando **PINCEL**/**PI**.
- **Origem:**
  - com uma área selecionada, ela é a origem;
  - sem seleção, o primeiro clique escolhe a origem: área de pista, região de textura ou área do desenho.
- **Destino:** cada clique seguinte aplica a mesma textura.
  - **Área de pista** recebe também o tipo e o material.
  - **Região de textura** recebe a superfície.
  - **Área do desenho** vira área com a textura. O DXF não muda.
- **Prioridade no clique:** a área com textura sob o cursor vale mais que linhas por cima (rota, fluxo).
- **Encerrar e desfazer:** **Esc** ou Enter encerra e mostra quantas aplicações foram feitas. **Ctrl+Z** desfaz uma aplicação por vez.

## Medido neste ambiente
- **Testes automáticos:** **257 passaram** (252 da 1.29 + 5 novos). Os novos testes cobrem:
  - geometria das faixas: simples, sentido único, trecho duplo com canteiro, transição sem degrau, faixa nova nascendo sobre a vizinha;
  - rede de tráfego:
    - sentido e lado das faixas;
    - velocidade da rota;
    - ligação entre as faixas;
    - **nenhuma pintura a mais**;
    - rota desativada;
    - opção fora do pavimento;
  - projetos: renomear, lista, miniatura 320 px;
  - modelos: só configurações / com marcações, nome repetido, novo a partir de, aplicar mantendo marcações e km, cópia de segurança, renomear, excluir;
  - esquema 25;
  - um teste de tela no Chromium:
    - Ctrl+O, procurar, renomear e abrir;
    - salvar modelo e criar projeto a partir dele;
    - rota com trecho duplo desenhada e editada no painel;
    - grupos recolhíveis lembrados;
    - gerenciador de camadas com edição final e desfazer;
    - pincel em área de pista e em área do desenho, encerrado com Esc.
- **Correção de um erro raro da 1.29:** clicar num item do menu suspenso depois que ele fechou gerava um erro no console. Encontrado pelo teste de tela.
- **Teste de tela da 1.29:** passou a esperar o projeto terminar de abrir antes de enviar arquivos. Antes, falhava às vezes por pressa do teste (cerca de metade das execuções aqui); no uso real, o envio acontece segundos depois de abrir.
- **Regressão TH57:** quadros 14, 40 e 96 s e vista do trevo **idênticos à 1.29**, pixel a pixel. Sem rotas, nada muda no vídeo.

## Não verificado / limitações
- **Windows:** não testado no seu computador.
- **Rotas × outros fluxos:**
  - as rotas se ligam entre si;
  - as pontas de outros fluxos podem se ligar às rotas;
  - a ponta de uma rota **não** corta um fluxo do desenho (isso mudaria a pintura dele). Para ligar uma rota a um fluxo existente, use **Forçar ligação**.
- **Pista simples desenhada fora do pavimento do DXF:** sem a opção “fora do pavimento”, os veículos só andam onde há pavimento.
- **Modelos:** guardam configurações, não imagens nem arquivos. Um modelo com marcações só faz sentido no mesmo trecho (coordenadas).
