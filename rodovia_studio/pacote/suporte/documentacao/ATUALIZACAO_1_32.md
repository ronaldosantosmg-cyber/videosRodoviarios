# Rodovia Studio 1.32 — pasta principal limpa, vídeos guardados sem substituir, limpar memória, qualidade Alta/Máxima e janelas reorganizadas

## Pasta principal só com o arquivo principal
- **Pasta principal:** só o arquivo que abre o programa — `Rodovia Studio.exe` ou, enquanto não houver o .exe, `ABRIR RODOVIA STUDIO.cmd` — e as pastas `projetos`, `videos`, `atualizacoes` e `sistema`.
- **Pasta `sistema` (antes “suporte”):**
  - o programa (`sistema\programa`, antes `suporte\sistema`);
  - documentação, backups e logs;
  - os auxiliares `ATUALIZAR RODOVIA STUDIO.cmd`, `COMPILAR INICIADOR.cmd` e `LEIA-ME.txt`;
  - uma reserva do `ABRIR RODOVIA STUDIO.cmd`.
- **Reorganização automática:** acontece ao atualizar e não apaga nada. Só pastas inteiras são movidas.
  - **ATUALIZAR antigo:** o `ATUALIZAR RODOVIA STUDIO.cmd` antigo da pasta principal pode estar em execução durante a atualização. Por isso ele só é arrumado na próxima abertura do programa (vai para `sistema\backups\legado_<data>`).
  - **Rodovia Studio.exe antigo (iniciador 1.1):** ele procurava `suporte\sistema`, por isso é guardado em `sistema\backups`. Na primeira abertura pelo `ABRIR RODOVIA STUDIO.cmd`, o programa recompila o .exe sozinho (iniciador 1.2). Depois disso, o .cmd sai da pasta principal e fica de reserva em `sistema`.
  - **Atalho:** o atalho “Rodovia Studio” da Área de Trabalho é corrigido se apontar para um arquivo que não existe mais.
- **Iniciador 1.2:**
  - reconhece a organização nova e a anterior;
  - ganhou “Abrir pasta de vídeos” no ícone perto do relógio;
  - relê as pastas depois de atualizar.
- **Atualizar pelo aplicativo:** **Arquivo › Atualizar o Rodovia Studio** mostra a versão instalada e os ZIPs encontrados (pasta `atualizacoes`, pasta principal, Downloads).
  - **Aberto pelo `ABRIR RODOVIA STUDIO.cmd`:** o programa fecha, aplica a atualização numa janela própria e abre de novo.
  - **Aberto pelo .exe:** a atualização continua pelo ícone perto do relógio (o .exe controla o programa).

## Vídeos guardados, um por geração
- **Onde ficam:** cada vídeo gerado vira um arquivo novo em `videos\<nome do projeto>\`, por exemplo `Trecho BR-381_2026-10-22_14h05_v03.mp4`.
- **Ficha:** cada vídeo tem uma ficha `.json` com data, versão do programa, resolução, qualidade, codificador, tempo de geração e a configuração usada. **O vídeo anterior não é substituído.**
- **Nome da pasta:** a pasta do projeto é reconhecida pelo identificador. Renomear o projeto continua na mesma pasta, e dois projetos com o mesmo nome não se misturam.
- **Vídeos gerados:** em **Arquivo › Vídeos gerados** (ou aba Vídeo, comando `VIDEOS`) dá para:
  - ver a lista (data, resolução, qualidade, duração, tamanho);
  - **assistir** na própria janela;
  - **baixar**;
  - **apagar** (vai para a lixeira da pasta de vídeos);
  - **abrir a pasta** no Explorer.
- **Último vídeo:** continua também dentro do projeto (`video.mp4`), como antes. Se essa cópia for limpa, a tela passa a mostrar o vídeo da pasta `videos`.

## Limpar memória (resíduos)
- **Como abrir:** **Arquivo › Limpar memória** (ou aba Vídeo, comando `LIMPAR`).
- **O que mostra:** o tamanho de cada tipo de resíduo; apaga o que você marcar:
  - caches regeneráveis (ladrilhos de imagem, geometria, detalhe, hidrografia, mosaicos locais);
  - arquivos temporários (vídeos interrompidos, envios incompletos, quadros de montagem);
  - registros antigos (mais de 30 dias) e logs de vídeo;
  - cópias antigas da configuração (ficam as 3 mais recentes por projeto);
  - lixeira (projetos, modelos e vídeos retirados);
  - atualizações antigas (ficam os 2 backups e o ZIP mais recentes);
  - opcional, desmarcado: a cópia de trabalho do último vídeo dentro do projeto, quando ela já está na pasta `videos`.
- **O que nunca é apagado:** projetos, DXF/KMZ, imagens enviadas, marcações e os vídeos da pasta `videos`.
- **Com tarefa em andamento:** a limpeza é recusada.

## Qualidade do vídeo
- **Novo campo “Qualidade do vídeo” (Configuração):**
  - **Padrão:** igual às versões anteriores (vídeo idêntico).
  - **Alta:**
    - imagem de fundo mais nítida: máscara de nitidez com limiar, só na imagem aérea (o desenho do projeto e os textos não ganham halo; o ruído fraco não é realçado);
    - ampliação dos ladrilhos com Lanczos;
    - veículos sem serrilhado;
    - menos compressão: CRF 14 / NVENC CQ 16 com AQ espacial, até 35 Mbit/s.
  - **Máxima:**
    - além do que a Alta faz, cada quadro é montado **1,5× maior e reduzido** (superamostragem: bordas, linhas e textos lisos);
    - detalhe a **0,1 m** e imagem Esri **nível 20** onde existir (senão, nível 19 automaticamente);
    - CRF 12 / NVENC CQ 14, até 60 Mbit/s.
- **Qual vale para cada projeto:** projetos **novos** começam em **Alta**. Os **existentes ficam em Padrão** (o vídeo não muda sozinho); para melhorar, escolha Alta ou Máxima na configuração.
- **Resolução 4K (3840 × 2160):** nova opção. A superamostragem da Máxima vale até 2560; em 4K a Máxima usa os demais ganhos.

## Janelas reorganizadas (padrão do Windows)
- **Estrutura igual em todas as janelas:** barra de título com **×**, conteúdo com rolagem e **rodapé fixo**.
  - No rodapé, as ações gerais ficam à esquerda (ex.: Novo projeto, Restaurar padrão, Abrir pasta); a ação principal (em azul) e Fechar/Cancelar ficam à direita.
- **Ações sobre o item escolhido:** ficam numa barra logo abaixo da lista (Renomear, Duplicar, Excluir…), em vez de misturadas no rodapé.
- **Gerenciador de camadas:** filtro, “Mostrar” e “Marcar todas” numa linha; ações em grupos de botões (Mostrar/Ocultar · Congelar/Descongelar · Isolar/Congelar as demais).
- **Janelas antigas no mesmo padrão claro:** Registros (abas Execução/Erros), Comandos, Limpar trabalho, Regras do perfil e Detalhes da execução.
- **Botões e campos:** tamanho uniforme e mais compacto; botões de excluir em vermelho; os atalhos não aparecem mais no texto dos botões (“OK”, “Cancelar”), só na dica.
- **Correções visuais encontradas na revisão:**
  - **Controles indevidos à mostra:** nas janelas **Água** e **Sinalização** apareciam também os controles de textura de taludes (o atributo “oculto” era vencido pelo estilo). O mesmo acontecia com o botão “Atualizar agora”.
  - **Campos de cor:** apareciam como barras escuras; agora mostram a cor.
  - **Vídeos gerados:** a coluna de ações saía da janela. Tamanhos pequenos aparecem em KB.
  - **Escolha de arquivos repetida:** o campo antigo único e o botão “Enviar arquivos” repetiam os botões Escolher DXF/KMZ (que já enviam na hora) e saíram da tela.
  - **Opções da ferramenta:** ganharam um quadro próprio sobre a tela.
  - **Mini-barra:** some ao trocar de ferramenta.

## Medido neste ambiente
- **Testes automáticos:** **274 passaram** (263 da 1.31 + 11 novos). Os novos testes cobrem:
  - organização 1.31 → 1.32 com o .exe antigo;
  - entrega pelo atualizador da 1.31 real ao da 1.32;
  - arrumação da raiz com e sem .exe;
  - arquivo de vídeos (numeração, nomes, pastas por identificador, lixeira, último vídeo);
  - geração pelo processo de tarefas sem substituir;
  - API de vídeos, pastas e limpeza;
  - categorias de limpeza preservando os arquivos do projeto;
  - qualidade (migração, parâmetros do codificador, nitidez, nível 20 e queda para 19, superamostragem gerando 1280×720);
  - um teste de tela.
  - Testes do atualizador, do iniciador e de esquema ajustados à nova organização e versão.
- **Vídeo TH57 em Padrão:** quadros 14, 40 e 96 s e vista do trevo **idênticos à 1.31**, pixel a pixel.
- **Quadros TH57 (1280×720, caches prontos, sem internet para a imagem Esri):**

  | Qualidade | Tempo por quadro | Nitidez (var. do laplaciano) | Gradiente médio |
  |---|---|---|---|
  | Padrão | 0,38 s | 1383 | 104 |
  | Alta | 0,44 s | 2017 (+46%) | 121 (+16%) |
  | Máxima | 1,02 s | 1672 (+21%) | 121 (+16%) |

  A Máxima mede menos “nitidez” que a Alta porque a superamostragem alisa as bordas de propósito (serrilhado menor).
- **Codificação (60 quadros 1280×720 com movimento, x264):**

  | Qualidade | PSNR | Taxa |
  |---|---|---|
  | Padrão | 37,6 dB | 196 kB/s |
  | Alta | 39,1 dB | 271 kB/s |
  | Máxima | 39,6 dB | 312 kB/s |

- **Janelas:** todas capturadas antes e depois no Chromium (15 janelas, opções de ferramenta e painel de propriedades).

## Não verificado / limitações
- **Windows:** não testado no seu computador, incluindo:
  - os scripts `.cmd`/PowerShell novos;
  - a recompilação automática do .exe;
  - a correção do atalho;
  - a atualização pelo aplicativo;
  - o “Abrir pasta” no Explorer.
- **Atualização a partir do .exe antigo (ícone perto do relógio):** depois de aplicar a 1.32, o .exe antigo não encontra mais as pastas e mostra um erro uma vez. Abra pelo **ABRIR RODOVIA STUDIO** da pasta principal: o .exe é recriado sozinho.
- **Imagem Esri nível 20:** não verificada aqui (sem acesso à Esri neste ambiente). Onde não houver nível 20, o programa usa o 19.
- **A nitidez da imagem aérea tem limite:** depende da resolução da imagem de origem (Esri ≈ 0,3 m no nível 19). A imagem local de alta resolução (GeoTIFF/ECW) continua sendo a melhor opção quando existir.
- **Tempo de geração na Máxima:** cerca de 2,5× o da Alta.
