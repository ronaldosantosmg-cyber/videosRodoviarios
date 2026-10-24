# Rodovia Studio 1.16 — texturas

Segunda etapa do plano de melhorias (funcionais).

## O que mudou
Em **Exportar vídeo**:
- **Texturas**: *Realistas* (padrão) ou *Anteriores* (iguais à 1.15).
- **Aparência dos taludes**: *Hachura de projeto* (padrão, como antes) ou *Terreno*.
- **Resolução do detalhe**: 0,2 m (padrão) ou 0,1 m por pixel.

### Texturas realistas
Todas ficam ancoradas no terreno, em metros, e não "nadam" com a câmera.
- **Pista projetada**: agregado fino do asfalto (grão de 4 a 16 cm), além do tom que já existia.
- **Pista existente**: mais desgastada.
  - Agregado e remendos escurecidos de grande escala.
  - Fissuras, que aparecem só de perto (menos de 0,25 m por pixel na tela) e somem suavemente ao afastar.
  - **Trilhas de roda** (±0,85 m do centro de cada faixa com tráfego), na camada de detalhe.
- **Acostamento**: levemente mais claro, com grão próprio.
- **OAE**: grão fino somado ao concreto.
- **Imagem detalhada × mosaico**: com imagem aérea real (Esri ou cache), a cor de baixa frequência de cada ladrilho detalhado é ajustada à do mosaico base. Assim não há salto de cor quando a câmera aproxima. Com fundo neutro, nada é ajustado.

### Taludes com aparência de terreno (opcional)
- **Corte**: solo exposto com grão de terra.
- **Aterro**: grama.
- Os dois mantêm um contorno fino na cor do tipo (vermelho e verde) e as linhas de crista/pé, para continuar identificáveis.
- A hachura de projeto continua como padrão.

### Detalhe a 0,1 m
- Os ladrilhos de detalhe passam a ter 102 m em vez de 205 m. As bordas do desenho do projeto ficam mais nítidas, o que é útil em vídeo 2560/4K e com a imagem local de alta resolução da próxima etapa.
- A imagem Esri continua no nível 19 (cerca de 0,3 m) e é apenas ampliada.

## Configuração
O esquema passou para a **versão 15**, com migração automática. Projetos antigos recebem as texturas realistas, a hachura de projeto e o detalhe de 0,2 m.

## Medido neste ambiente
- **Testes**: 157 automáticos passaram, 6 deles novos:
  - texturas só nas superfícies, sem mudar o tom geral;
  - trilhas de roda só na pista existente;
  - taludes naturais sem listras;
  - ajuste de cor da imagem detalhada;
  - detalhe a 0,1 m com bordas mais nítidas;
  - esquema v15.
- **Texturas "Anteriores"**: quadros do TH57 idênticos aos da 1.15, pixel a pixel, nos instantes 14, 40 e 96 s e na vista do trevo (1280×720).
- **Tempo** a 1920×1080 no TH57, com os ladrilhos de detalhe já em cache:

  | Situação | Anteriores | Realistas | Realistas + taludes naturais |
  |---|---|---|---|
  | Vista de 40 m | 263 ms | 306 ms | 360 ms |
  | Vista de 120 m | 295 ms | 317 ms | 343 ms |
  | Vista de 260 m | 320 ms | 385 ms | 439 ms |
  | Quadros do vídeo aos 40 e 96 s (média) | 591 ms | 573 ms | 601 ms |

- A primeira geração dos ladrilhos com trilhas de roda é mais lenta. Ela é feita uma vez e fica guardada em disco (`cache_detalhe`).

## Não verificado / limitações
- **Ajuste de cor com imagem Esri real**: não verificado, porque a internet está bloqueada neste ambiente. O teste usou imagens sintéticas.
- **Trilhas de roda**: só aparecem onde há trajetória de veículos na pista existente, e só na camada de detalhe (de perto).
- **Fissuras e remendos**: são um padrão procedural. Não representam o estado real do pavimento.
- **Água**: não mudou (continua a textura da 1.5).
