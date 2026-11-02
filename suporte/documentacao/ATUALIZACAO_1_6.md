# Rodovia Studio 1.6 — Fase D: vista da cabine

## Como usar
1. Gere a prévia. No editor, escolha a ferramenta **🚗 Cabine** e clique sobre uma trajetória (até 20 m dela). Esse ponto define o veículo (itinerário validado), o sentido e o início do trecho.
2. Na seção 5, abra **Vista da cabine**: marque **Gerar o vídeo pela vista da cabine** e informe a duração do trecho, a altura do olho, o campo de visão, a inclinação, a suavização, a velocidade (vazio = velocidade do tráfego) e se quer capô e painel.
3. Com **Câmera do vídeo** selecionada, **Gerar / atualizar prévia** mostra o quadro da cabine no instante escolhido. O editor continua na vista em planta para as marcações.
4. **Gerar novo vídeo** produz o MP4 da cabine com a duração escolhida. O `video.json` registra `camera: cabin`.

## Como funciona
- Projeção em perspectiva do plano do mapa por homografia: imagem aérea + camadas do projeto, com três níveis de detalhe conforme a distância, névoa no horizonte e céu em degradê.
- A sinalização horizontal é projetada como faixas de 15 cm até 220 m.
- Os outros veículos aparecem como volumes simples (carro 1,5 m, caminhão 3,6 m, ônibus 3,3 m de altura), com face visível, teto e sombra.
- O capô e o painel são sobrepostos; o cabeçalho e o rodapé do projeto são mantidos. O cabeçalho mostra km e velocidade.
- A direção é suavizada por filtro gaussiano ao longo da trajetória (padrão 1,2 s). A posição avança em velocidade constante. Se o trecho escolhido passar do fim da trajetória, o veículo para no fim e o `video.json` informa `cabin_reaches_path_end`.

## Limitação — terreno plano
Não há modelo digital de elevação: o terreno é um plano e a imagem aérea é “pintada” nele. Árvores, edificações, taludes e encostas aparecem achatados. OAE em desnível só têm diferença de altura quando há cota informada: ao passar por uma OAE marcada com nível, a câmera sobe esse valor, com rampas de 25 m, mas a OAE e o terreno continuam desenhados no plano. As OAE do DXF não têm cota, então não elevam a câmera. A nitidez do chão perto do carro é limitada pela resolução do mosaico (≈0,9 m/px no cache TH57 de 8192 px). A cena é ilustrativa.

## Medido
- TH57, 2560×1440, CPU deste ambiente: cerca de **1,2 s por quadro** na cabine. Um trecho de 20 s a 30 fps leva cerca de 12 min só de montagem.
- Testes: projeção de ponto conhecido (centro da tela e linha abaixo do horizonte por atan(h/d)), avanço = início + v·t, parada no fim do trecho, camadas céu/chão/painel/cabeçalho, suavização reduzindo a variação de direção em mais de 50%, elevação de 8 m só no trecho da OAE marcada, recusa de ponto longe da trajetória, e vídeo com a duração escolhida (3,5 s → 105 quadros).
- Quadros da cabine TH57 em `conferencia/v1_6_cabine_*.jpg`.

## Não testado / limites
- Velocidade de geração no seu computador. A NVENC só acelera a codificação; a montagem segue na CPU.
- Não há troca de faixa, frenagem ou interação com outros veículos: a câmera segue um itinerário fixo.
