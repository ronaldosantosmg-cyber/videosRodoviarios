# Rodovia Studio 1.18 — faixas por sentido, menos setas, camada 0, km em planta, passarela e acessos

Esta versão atende aos pedidos recebidos durante a etapa funcional. O desempenho fica para a 1.19.

## Faixas por sentido e acostamento
- **Faixas por sentido na pista principal** (Configuração → sinalização): o padrão é **2**.
  - As faixas têm a largura informada (3,5 m) a partir do bordo interno, junto ao canteiro.
  - O restante da pista é **acostamento**, separado por uma linha contínua de bordo da faixa.
  - Também há as opções 1, 3, 4 ou "pela largura" (comportamento da 1.15 a 1.17).
- **➕ 3ª faixa (início/fim)**: nova ferramenta. Clique sobre a pista no início e depois no fim da faixa adicional. Entre os dois km vale o número de faixas por sentido informado (padrão 3). Fica na lista de marcações, com edição, desfazer e exportação (RS_FAIXA_ADICIONAL).
- Uma trajetória paralela dentro de uma pista principal já pintada (por exemplo, a pista existente ao lado da nova) não gera um segundo conjunto de faixas.

## Setas sem excesso
- No máximo uma seta a cada **25 m** no mesmo sentido. A distância é ajustável; 0 reproduz a 1.17.
- A seta é repetida em cada faixa **só antes de saídas e acessos**. Também há as opções "todas" e "nunca".
- As setas dos anéis de rotatória têm prioridade e não são removidas.

## Leitura de camadas protegida
- **Camada única**: quando o DXF tem tudo na layer 0 (ou 60% ou mais numa camada só, misturando cores e tipos), ela é separada por **cor e tipo de entidade**.
  - Exemplos: "0 · cor 1 · LWPOLYLINE" (eixo), "0 · cor 8 · HATCH" (pavimento), "0 · cor 2 · LINE" (barreira), "0 · cor 7 · LINE" (sinalização).
  - Cada grupo recebe o seu tipo na lista e pode ser conferido com "Ver".
  - Opções: automático, separar todas, não separar.
  - Projetos que já tinham camadas mapeadas continuam sem separação, para não perder o mapeamento.
- **Avisos de mapeamento suspeito**:
  - pavimento, acostamento, canteiro ou OAE sem áreas fechadas;
  - eixo com mais de 40 entidades;
  - sinalização horizontal com áreas maiores que 500 m², que são ignoradas na pintura.

## Km em planta
- Nas ferramentas **Início do km** e **Fim do km**, digite o km do ponto antes de clicar.
- O km digitado no fim liga o ajuste proporcional. Assim o km inicial e o final ficam presos aos pontos marcados.

## Vão da passarela
- **↔ Vão da passarela**: clique sobre a passarela e arraste. O comprimento (10 a 160 m) e o ângulo em relação à pista (±85°) acompanham o mouse. Com Shift, só o comprimento muda.
- O editor desenha o vão de todas as passarelas.

## Acesso rodoviário com taper
- **🛣 Acesso com taper**: clique o primeiro ponto junto ao bordo da pista e siga pelo eixo do acesso.
- O programa gera:
  - o pavimento do acesso (largura padrão de 7 m);
  - o **taper de entrada**, de desaceleração, antes da ligação (padrão 60 m);
  - o **taper de saída**, de aceleração, depois da ligação (padrão 60 m).
- O lado e o sentido seguem a mão de direção da pista do lado do acesso.
- Os tapers viram pavimento do projeto, com bordos, sinalização e **fluxos de veículos**. A ponta do acesso passa a ser origem e destino de itinerários.
- Opções: entrada e saída, só entrada ou só saída, além das larguras e dos comprimentos.
- Exportação e reimportação na camada RS_ACESSO.
- Se o primeiro ponto estiver a mais de 40 m do bordo, aparece um aviso e nada é gerado.

## Configuração
O esquema passou para a **versão 17**, com migração automática. O DXF original não é alterado.

## Medido neste ambiente
- **Testes**: 172 automáticos passaram, 7 deles novos. Os testes da 1.15 passaram a declarar as opções que reproduzem a 1.15 (faixas pela largura e todas as setas).
- **Opções que reproduzem a 1.17** (faixas "pela largura", setas repetidas em todas as faixas, distância 0): quadros do TH57 idênticos aos da 1.17, pixel a pixel, nos instantes 14, 40 e 96 s e na vista do trevo.
- **TH57 no padrão novo**:
  - setas: de 497 para 259 (255 retas, 3 reta e direita, 1 reta e esquerda);
  - as pistas principais conferidas aparecem com 2 faixas por sentido e acostamento (quadros revisados nas vistas do trevo e dos km 0,8, 2,5 e 4,2 do eixo).

## Não verificado / limitações
- **3ª faixa entre dois pontos**: vale para a pista mais próxima dos pontos marcados. Em pistas muito próximas uma da outra, confira o resultado na prévia.
- **Tapers**: seguem o bordo do pavimento do DXF com largura linear. Não há projeto geométrico normativo (raios, comprimentos por velocidade).
- **Acessos**: em alça ou rotatória não foram testados.
- **Separação da camada 0**: testada com DXF sintético. Desenhos reais com blocos aninhados e cores "por bloco" podem gerar mais grupos.
