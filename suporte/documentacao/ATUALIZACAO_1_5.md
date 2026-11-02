# Rodovia Studio 1.5 — Fase C: qualidade visual

Na seção 5, a opção **Qualidade visual** tem dois modos. **Aprimorada** é o padrão. **Anterior (1.4)** reproduz o desenho anterior pixel a pixel e é o mais rápido.

## Hidrografia em duas camadas
- **Textura da água** e **Nomes dos rios** ligam e desligam de forma independente, cada uma com sua opacidade.
- A textura aprimorada tem variação de tom, transição suave nos primeiros ~6 m a partir da margem mapeada, água mais escura longe da margem e brilho discreto fixo no terreno.
- **Ondulação animada sutil** é opcional e vem desligada.
- Continua sem inventar margens: a textura só vale dentro dos polígonos existentes. Sem polígonos, fica apenas a linha cartográfica fina.
- A legenda “Água” só aparece quando a textura está ligada.

## Pavimento
- Textura de asfalto procedural ancorada nas coordenadas do projeto, com escala em metros (ladrilho periódico de 20,48 m a 4 cm por texel).
- Pirâmide pré-filtrada: de perto o grão continua visível; de longe ele é suavizado em vez de cintilar.
- Variação de grão e tom: o projetado tem mais grão; a via existente é mais clara e lisa e mantém a distinção; o acostamento tem textura própria.
- Bordas vetoriais nítidas da superfície de rolamento (contorno da união das áreas, sem costura entre hachuras vizinhas), respeitando a construção progressiva. A sinalização horizontal continua vetorial.

## OAE
- Textura de concreto e juntas de dilatação a cada 30 m, perpendiculares ao eixo.
- Guarda-corpos nos bordos longitudinais.
- Sombra projetada no terreno, deslocada conforme o nível: nas OAE marcadas, o nível informado; nas OAE do DXF, que não têm cota, 5 m.
- Os detalhes aparecem quando a OAE já foi revelada.

## Veículos
- Vista superior com sombra suave, vidros e teto.
- Tipos: carro, caminhão (cabine e baú) e ônibus. A atribuição é determinística: caminhões e ônibus só em trajetórias principais/marginais, e só onde o veículo maior cabe no pavimento; caso contrário vira carro.
- Dez cores de carro e paletas próprias para ônibus e caminhão.
- **Faróis acesos** (opção global): lanternas e feixe discreto à frente, em camada aditiva suave.
- A validação “o veículo cabe no pavimento” agora é memorizada por posição na trajetória, com o mesmo resultado.

## Medido (TH57, CPU deste ambiente Linux, 2 núcleos)
Validação visual em 2560×1440, quadros em 14, 40 e 96 s, com o estado da chamada do cabeçalho reconstituído desde o início. As imagens estão em `conferencia/v1_5_*`.
- **Anterior (1.4)** × 1.2: idênticos pixel a pixel nos três instantes.
- **Aprimorada** × 1.2: diferenças em 17,3% (14 s), 1,3% (40 s) e 1,3% (96 s) dos pixels. Na vista aérea de 750 m, a mudança é pequena. Ela aparece nas cenas de detalhe, nas bordas, nos veículos e nas OAE.
- Tempo de montagem, 60 quadros em movimento após aquecimento, ambos com cache geométrico: **Anterior 529 ms/quadro**, **Aprimorada 756 ms/quadro**, ou seja, **+43%**. A codificação do vídeo não entra nessa medida. Por isso a opção Anterior foi mantida.
- O 1º quadro do modo aprimorado levou 974 ms, contra 756 ms dos seguintes (inclui a criação das texturas).

## Não testado / limites
- O impacto no tempo do seu Alienware não foi medido. A proporção pode ser diferente.
- A ondulação animada pesa mais quando há muita água na tela e não foi medida no TH57.
- A textura de asfalto não substitui a imagem aérea: o mosaico continua com a resolução da fonte escolhida.
