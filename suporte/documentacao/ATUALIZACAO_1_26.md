# Rodovia Studio 1.26 — pórticos, chamadas, camadas ocultas/congeladas, alinhamento por linha, menu de contexto, sessões e registros

## O que mudou
### Pórticos
- Ferramenta **Pórtico** (barra *Áreas e sinalização*, comando **PT**). Para criar:
  1. Clique no primeiro apoio e depois no segundo, do outro lado da pista.
  2. No painel de propriedades, use **Enviar imagem…** com a arte da placa (PNG ou JPG).
- **No vídeo** (vista de cima) aparecem:
  - os pilares (dois no pórtico; um no semipórtico e na bandeira);
  - a viga treliçada e a sombra no chão, proporcional à altura;
  - uma faixa com a cor média da placa;
  - a **caixa de chamada com a imagem**, o nome, o tipo e o km.
- **Atributos editáveis:** tipo, largura da viga, altura, cor, descrição, mostrar no vídeo, caixa de chamada, tamanho do texto e janela de tempo (aparece a partir de / até).
- Os pórticos aceitam MOVER, COPIAR, GIRAR, ESCALA, ESPELHAR, grips e desfazer, como os demais objetos.
- A imagem enviada é guardada em `imagens\` do projeto, já normalizada em PNG.

### Caixas de chamada
- **Posição automática sem sobreposição:** a caixa procura uma posição livre ao redor do marcador e, se não houver, o espaço livre mais próximo no quadro.
- **Novos atributos do destaque:**
  - estilo (cartão completo, compacto ou etiqueta);
  - tamanho do texto;
  - imagem;
  - linha de chamada reta ou em cotovelo;
  - janela de tempo, com entrada e saída suaves.
- **Posicionar caixa** (clique no lugar) e **Caixa automática** no painel de propriedades.
- O desenho agora é feito só na área da caixa, e não no quadro inteiro, o que deixa a montagem mais rápida.
- Projetos anteriores abrem com **“Caixas de chamada: como na 1.25”**, para manter o resultado. A opção fica no *Perfil de vídeo*.

### Camadas: ocultar e congelar (como no CAD)
- Na lista de camadas há dois botões por camada. Também dá para usar o menu de contexto ou os comandos **OC/OCULTAR**, **CG/CONGELAR**, **ISOLAR**, **MOSTRAR** e **DESCONGELAR**.
- **Ocultar (👁):** a camada some na hora no editor e também do vídeo. O DXF não é alterado. Não é permitido ocultar a camada do eixo.
- **Congelar (❄):** a camada continua visível no editor, mas travada (sem snap e sem seleção de linha). No vídeo ela **aparece pronta desde o início**, sem a construção progressiva.
- Depois de ocultar ou congelar, clique “Analisar arquivos” para recalcular fluxos e sinalização.

### Leitura das hachuras do DXF
- **Entidades:** lê também **MPOLYGON** (AutoCAD Map/Civil). Coleções de geometria aninhadas não perdem mais partes.
- **Contagem:** o programa conta ilhas e laços de cada assinatura de hachura.
- **Padrões reconhecidos:**

  | Padrão | Leitura |
  |---|---|
  | AR-CONC, AR-HBONE, AR-B816 | concreto |
  | AR-SAND | asfalto |
  | GRAVEL | acostamento |
  | GRASS | canteiro |
  | SWAMP | água |
  | EARTH | corte |
  | ANSI37 | pista existente |

- **Cada sugestão traz a confiança e o motivo:**
  - alta: pelo nome da camada ou pelo perfil;
  - média: pelo padrão.
- **Hachuras sólidas sem nome reconhecível** recebem uma indicação pela cor (“talvez canteiro”). Essa indicação **nunca é aplicada sozinha**.
- **Botão “Ver”:** cada assinatura de hachura tem o seu, que a destaca no editor.

### Alinhamento
- A ferramenta Alinhamento (AL) tem três modos:
  - **Cliques:** como antes.
  - **Selecionar uma linha do desenho:** a polilinha inteira, com os vértices exatos.
  - **Seleção contínua:** cada clique acrescenta a linha seguinte, e as linhas conectadas sem bifurcação entram sozinhas.
- **Teclas:** Enter confirma; Esc cancela (com confirmação); Backspace desfaz o último trecho ou ponto.
- O alinhamento por linha não é suavizado: segue o desenho exatamente.

### Comandos, atributos e menu de contexto
- **Botão direito na tela** abre um menu no estilo do Windows, de acordo com o contexto. Ele tem:
  - para a seleção: propriedades, mover, copiar, girar, escala, espelhar, paralela, copiar propriedades, apagar;
  - para a camada sob o cursor: ocultar, congelar, isolar, usar a linha como alinhamento;
  - **Inserir** (pórtico, destaque, alinhamento, placa), desfazer/refazer, repetir o último comando, enquadrar, centralizar, regenerar a prévia ou a tela, sessão e ajuda.
- **Ajuda no menu:** cada item mostra uma linha de ajuda no rodapé. O menu funciona com o teclado (setas, Enter, Esc) e abre também com a tecla Menu ou Shift+F10.
- **ATRIB (AT):** com vários objetos selecionados, mostra os **atributos em comum** e altera todos de uma vez. Campos diferentes aparecem como “(vários)” e não mudam.
- **PINTAR (MA):** copia o estilo (cor, tamanho, tipo e similares) do objeto selecionado para os objetos que você clicar.
- **Propriedades em português, com ajuda em cada campo.** Os campos numéricos opcionais aceitam vazio.
- **Reflexo na apresentação:** a opção “Atualizar a prévia desta vista ao alterar” gera de novo a prévia do enquadramento atual depois de cada alteração.
- **Linha de comando:**
  - lista de comandos com sugestão ao digitar;
  - histórico com ↑/↓;
  - Enter vazio repete o último comando;
  - **?** ou **AJUDA** mostra todos os comandos;
  - novos: REGEN, RP (regenerar prévia), SS (salvar sessão), LOG, IA.

### Tela
- **Tela ampla** (padrão, em *Tela ampla* no topo): usa toda a largura, com um **divisor arrastável** entre o painel e o editor (duplo clique volta ao padrão). A área do editor fica limitada à altura da janela.
- **Compacto:** menos espaçamento.
- **PAN e ZOOM:**
  - os redesenhos durante o gesto são agrupados por quadro;
  - se o desenho completo levar mais de 16 ms, o gesto mostra a imagem da tela transformada e o quadro é redesenhado completo, em alta qualidade, 0,14 s depois de parar.
  - O desenho em repouso não perde qualidade.

### Sessões de trabalho e prévia
- **Sessões:** salvar, restaurar e apagar (linha “Sessão” no editor, ou comando SS).
  - Uma sessão guarda a vista, a ferramenta, o fundo, as camadas visíveis, os painéis abertos, a seleção e as opções de snap/orto.
  - As marcações do projeto não são afetadas.
- **Sessão automática “(última)”:** é atualizada enquanto você trabalha. Com **Retomar ao abrir** marcado, o projeto abre onde você parou.
- **⟳ Regenerar prévia** (botão e comando RP) e **Regenerar tela** (REGEN).

### Registros (logs) e prompt para IA
- **Registro de execução:** cada tarefa (análise, prévia, vídeo, exportação) grava início, cada etapa com o tempo e o fim, em `logs\execucao.jsonl` do projeto.
- **Registro de erros:** grava as falhas de tarefa com o rastreamento, os erros inesperados do servidor e os erros e avisos da tela (`logs\erros.jsonl`). Mensagens repetidas são limitadas.
- **Seção “Registros e suporte”:** ver os registros, **exportar o prompt para IA** (.md), copiar o prompt, baixar tudo (.zip) e limpar.
- **O prompt traz:**
  - a versão e o ambiente;
  - os arquivos de entrada com SHA-256;
  - o resultado da análise;
  - a configuração completa;
  - as tarefas, as etapas e os erros;
  - o passo a passo para reproduzir o vídeo.

## Medido neste ambiente
- **Testes:** **236 testes automáticos passaram** (228 da 1.25 + 8 novos). Os novos cobrem:
  - pórticos no quadro (viga, imagem e janela de tempo);
  - caixas sem sobreposição;
  - layout anterior idêntico;
  - ocultar e congelar (análise, vídeo e assinatura de cache);
  - hachuras (MPOLYGON com ilha, padrões, cor só como indicação);
  - seleção de linha e encadeamento (para na bifurcação);
  - imagens, sessões e registros pela API (incluindo falha com rastreamento e o prompt);
  - um teste de tela no Chromium: pórtico com imagem, ATRIB, menu de contexto com ajuda e Esc, ocultar e congelar, alinhamento por linha, lista e histórico de comandos, sessão, divisor, agrupamento do zoom e registros.
- **Regressão TH57** (quadros 14, 40 e 96 s e vista do trevo):
  - padrão: **idêntico pixel a pixel à 1.24/1.25**;
  - motor “anterior”: idêntico à 1.23.
- **Teste de interface existente:** a tela ampla mantém a proporção 16:9 do editor limitada à altura da janela, e o teste de interface anterior continua passando.

## Não verificado / limitações
- **Windows:** nada foi testado no seu computador (Windows/Edge). A fluidez do PAN/ZOOM depende do computador e do tamanho do desenho.
- **Pórtico em planta:** o pórtico é desenhado em vista de cima. Na **vista da cabine (3D)** ele ainda não aparece.
- **Seleção contínua:** segue linhas cujas pontas coincidem (até 5 cm). Em bifurcações, ela para e você escolhe o próximo trecho clicando.
- **Indicação pela cor:** é só heurística. Confira sempre a lista de hachuras antes de gerar.
- **Prompt para IA:** inclui a configuração completa e os nomes/SHA-256 dos arquivos, mas **não** o DXF. Revise o conteúdo antes de compartilhar fora da empresa.
