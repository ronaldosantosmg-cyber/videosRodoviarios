# Rodovia Studio 1.7 — tela cheia, geração mais rápida, elevação e ficha técnica

## Editor em tela cheia
- **⛶ Tela cheia** (ou tecla **F**) agora reorganiza o editor:
  - a imagem ocupa toda a altura da tela;
  - a barra de ferramentas fica no topo;
  - as marcações ficam num painel lateral com rolagem própria.
- **Painel de marcações** (tecla **L**) esconde ou mostra o painel lateral para usar a largura toda.
- Ao entrar e sair da tela cheia, a imagem é reajustada automaticamente. **Esc** também sai.

## Geração mais rápida em qualquer PC
1. **Processos de montagem** (seção 5) — em **Automático**, o aplicativo usa os núcleos livres e a memória disponível do computador:
   - reserva um núcleo para o processo principal e outro para o codificador quando ele roda na CPU;
   - estima cerca de 1 GB por processo e limita a 12;
   - vídeos com menos de 120 quadros usam um processo só.

   Como funciona: a cena é preparada uma vez e gravada como instantâneo, com as matrizes grandes compartilhadas pelo sistema. Cada processo monta uma parte intercalada dos quadros, e o principal os entrega em ordem a **um único** FFmpeg (NVENC ou CPU, como antes). As transições entre cenas e a chamada do cabeçalho seguem iguais.

   Se um processo auxiliar falhar (por exemplo, por falta de memória), a geração recomeça automaticamente em um processo só.
2. **Perfil de geração Rápido (rascunho)** — dispensa a superamostragem da imagem aérea; o resto da cena é igual. Serve para conferir enquadramento e tempos antes do vídeo final.
3. O `video.json` registra o número de processos, o motivo da escolha e o perfil usado.

## Elevação do terreno (Camadas, imagem local e intercâmbio → Elevação)
**Fontes:**
- **MDT local:** GeoTIFF de elevação, ou TIF/PNG de uma banda + arquivo de mundo + .prj/CRS. Valores “sem dado” são preenchidos pelo vizinho válido.
- **Web:** AWS Terrain Tiles (Terrarium, dados abertos SRTM/GMTED/ETOPO1, ~30 m no Brasil), com cache em `elevacao/` do projeto. A internet só é necessária na primeira geração.

**Por que a imagem não é deformada.** A ortofoto já está em planta (ortorretificada): cada pixel está no seu X/Y.
- Em planta, a elevação **não move a imagem**: entra como **relevo sombreado** (só brilho) e **curvas de nível** opcionais, com intervalo e opacidade configuráveis.
- Na **vista da cabine**, a imagem é aplicada sobre a superfície 3D pelas próprias coordenadas X/Y. Cada pixel ganha apenas altura.

**Pista nivelada (opcional, ligada por padrão).** Sem o greide de projeto, a superfície de rolamento usa o perfil do terreno sob o eixo suavizado em cerca de 150 m, com transição de 15 m para o terreno natural. Nas OAE, o tabuleiro segue em linha reta entre os encontros.

**Outros detalhes:**
- O exagero vertical é configurável.
- No editor, a **cota sob o cursor** aparece junto do km.

**Cabine com relevo.**
- Renderização por colunas, com visibilidade correta: morros escondem o que está atrás e o céu só aparece acima do relevo.
- Céu e névoa de distância.
- Faixas de sinalização e veículos com altura, ocultados pelo terreno quando necessário.
- O cabeçalho mostra a cota.

## Vídeo TH57 substituído pela ficha técnica
- O aplicativo não precisa mais do `referencia.mp4` (456 MB). Fica `assets/th57/referencia_ficha.json`, com:
  - dados do arquivo: 2560×1440, 30 fps, 202 s, 6060 quadros, H.264 High, yuv420p, ~18,1 Mbit/s, 0,164 bit por pixel e SHA-256 histórico;
  - métricas de imagem: nitidez (variância do Laplaciano), densidade de bordas, brilho, contraste, colorido, área e contraste da sinalização e textura do pavimento.
- **Ficha técnica de referência (TH57) e comparação** (seção 5):
  - **Comparar vídeo gerado com a referência** mede o vídeo do projeto pelo mesmo método e mostra a tabela lado a lado, com a diferença em %;
  - **Medir referência e remover o vídeo** mede o `referencia.mp4` no seu computador, grava a ficha completa e só então apaga o arquivo. Aparece enquanto o arquivo existir.
- O botão “Exportar referência TH57 idêntica” saiu. Sem o arquivo, a API responde que a referência agora é a ficha.

## Medido (ambiente Linux, 2 núcleos — não é o seu computador)
- TH57 1280×720, trecho de 20 s (600 quadros), codificação na CPU (libx264), mesmo cache. O tempo inclui montagem e codificação, sem a preparação:

  | Configuração | Tempo |
  |---|---|
  | 1 processo | 89,4 s |
  | 2 processos | 73,4 s (−18%) |
  | Perfil Rápido (1 processo) | 59,6 s (−33%) |

  Com 2 núcleos, o codificador disputa a CPU com a montagem. Com mais núcleos, ou com NVENC, o ganho dos processos tende a ser maior, mas não foi medido.
- Quadros enviados ao codificador: **idênticos** entre 1 e N processos, conferidos por hash de cada quadro, no TH57 (6 s, 180 quadros) e nos testes. Os MP4 podem diferir em bits porque o codificador x264 com várias threads não foi determinístico neste ambiente quando a CPU estava disputada.
- Cabine com MDT sintético (para conferir o renderizador, não um relevo real): cerca de 0,95 s/quadro em 1440p.
- Testes: **76 passaram**: os 62 da 1.6 e 14 novos (decodificação Terrarium, MDT web com ladrilhos simulados e cache, MDT local com sem-dado, sombreamento sem mover a imagem, curvas de nível, pista nivelada, cota pelo cursor, cabine com imagem aplicada no ponto projetado e morro ocultando o céu, plano de processos, quadros iguais em N processos aéreo e cabine, perfil rápido, ficha técnica, comparação e remoção da referência só após a ficha). O teste de interface também cobre a tela cheia (F/L).

## Não testado / limites
- A AWS Terrain Tiles não foi acessada daqui (rede bloqueada neste ambiente); o código foi testado com ladrilhos simulados. Confira se a rede da empresa libera `s3.amazonaws.com`. Sem acesso, use o MDT local.
- O relevo de ~30 m não mostra cortes e aterros do projeto. A pista nivelada é uma aproximação, não o greide.
- Com relevo, árvores e prédios continuam “pintados” no chão: não há modelo de superfície.
- A ficha técnica do TH57 vem parcial (só os dados do arquivo) até você clicar **Medir referência e remover o vídeo** no seu computador.
- O ganho dos processos paralelos no seu PC não foi medido. O consumo de memória por processo foi estimado, não medido em 1440p com mosaico de 8192 px.
