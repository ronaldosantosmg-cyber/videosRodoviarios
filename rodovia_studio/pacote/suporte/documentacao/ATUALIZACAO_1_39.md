# Rodovia Studio 1.39 — bordas da imagem local no 255 e tráfego sem ziguezague

## O que mudou
- **Onde:** Camadas, imagem local e intercâmbio › Imagem georreferenciada local › **Bordas pretas/brancas**.
- **Nova regra (padrão):** ficam transparentes só os pixels de **branco puro (255)** ou **preto puro (0)** que estão **ligados à beira da imagem**:
  - a imagem começa no primeiro pixel abaixo de 255 (ou acima de 0); um pixel 254 já é imagem;
  - branco puro **no meio** da imagem (telhado, pintura, nuvem) continua visível, porque não está ligado à beira.
- **Antes (até a 1.38):** qualquer pixel ≥ 253 ou ≤ 3, em qualquer lugar da imagem, ficava transparente. Isso comia a borda da imagem real e furava telhados e pinturas brancas.
- **Opções do campo:**
  - **Transparentes só no branco 255 / preto 0 da beira** (nova, padrão);
  - **Anterior** (≥ 253 e ≤ 3 em toda a imagem);
  - **Manter** (nada fica transparente).
- **Vale para todas as imagens do mosaico.**
- **Imagens de 16 bits:** o limite é o máximo do arquivo (65535) e o 0, lidos antes do ajuste de cor.
- **Como acha a beira:** uma vez por imagem, o programa lê a imagem reduzida e marca as regiões 255/0 que tocam a beira. O resultado fica guardado num arquivo oculto ao lado da imagem (`.<imagem>.borda_….npz`), que os processos paralelos reaproveitam. Ao trocar a imagem, é refeito.

## Tráfego: trechos curtos fora das rotas (sem ziguezague)
- **Regra:** trechos com **menos de 50 m** (medidos no trecho inteiro, antes dos cortes nos encontros) são **ignorados nas rotas** dos veículos. São os ramos curtos que o programa acha nos encontros e cruzamentos e que faziam o veículo desviar e voltar.
- **Atalho:** quem chegava ao trecho curto passa a ligar direto ao trecho seguinte por uma curva suave, desde que caiba na pista e as pontas estejam a até 30 m. Se não couber, aquela passagem deixa de existir.
  - O atalho não troca de pista pelo canteiro (respeita a regra de travessia).
- **O que não muda:**
  - a pintura e a sinalização;
  - as ligações mostradas no editor (Fluxos);
  - as pontas de entrada e saída dos veículos: tirar um trecho curto não cria um ponto de nascer ou sumir veículo no meio da via.
- **Exceções (nunca ignorados):** o eixo principal do DXF, os trechos desenhados por você, as faixas de rota e o anel das rotatórias.
- **Onde ajustar:** painel Vídeo › Tráfego › **Ignorar trechos curtos nas rotas (m)**. Padrão 50; 0 usa todos os trechos como antes.
- **Segurança:** se, sem os curtos, não sobrar nenhuma rota completa, o programa mantém os curtos e avisa.

## Projetos existentes
- **Bordas da imagem:** os projetos com “Transparentes” passam para a nova regra (formato do projeto 30), porque esta é a correção pedida. Para voltar ao comportamento de antes, escolha **Anterior**.
- **Tráfego:** os projetos existentes também passam a ignorar os trechos curtos, como pedido. Para voltar, use 0 no campo.

## Medido neste ambiente
- **Testes automáticos:** **315** passaram (311 da 1.38 + 4 novos; o teste do padrão das bordas, da 1.17, foi ajustado). Os novos testes cobrem:
  - colar branco 255 e colar preto 0 transparentes;
  - telhado 255 e pintura 253 no meio continuam visíveis;
  - faixa 254 colada ao colar continua visível;
  - opção Anterior (fura como antes) e Manter;
  - 16 bits;
  - migração dos projetos (também nas imagens do mosaico);
  - tráfego: um caminho com um ramo curto de 23 m que desvia e volta. Com 0, o veículo desvia 4,6 m para o lado e volta; com 50, segue reto (variação < 0,05 m), pelo atalho. Ligações e pintura iguais.
- **Teste da 1.17 ajustado:** o teste do padrão do campo (agora “borda”) foi ajustado; o teste do colar preto do mosaico passou sem mudança.
- **Tempo:** marcar a beira de um GeoTIFF de 12000 × 8000 px **sem visões reduzidas** levou 5,7 s (uma vez; depois vem do arquivo guardado). Com visões reduzidas (o normal após a conversão), é bem menos.
- **TH57 (tráfego):** 152 trechos curtos ignorados. Os 50 itinerários de veículos são **os mesmos** com 0 e com 50 m (nenhum passava por trecho curto no TH57).
- **Vídeo TH57 (projeto existente, sem imagem local):** quadros 14, 40 e 96 s e vista do trevo **idênticos** à 1.38, pixel a pixel.
- **Atualização simulada da 1.38 para a 1.39:** aplicada pelo atualizador da 1.38, com 16 arquivos novos ou alterados; versão 1.39.0, esquema 30.

## Não verificado / limitações
- **Ziguezague no seu projeto:** não testado com o seu desenho. No TH57 as rotas já não passavam por trechos curtos. Se o ziguezague continuar, me diga onde (km ou print): pode vir de outra causa, como trocas de faixa ou um trecho maior que 50 m.
- **Sua imagem real:** não testado com a sua ortofoto. Se a borda for JPEG (valores 254/253 por compressão), alguns pontos isolados podem não ser 255 exato. O acabamento da borda tende a apagar pontos soltos, mas uma franja com ruído de compressão pode aparecer. Nesse caso, me mande um recorte que eu ajusto.
- **Imagem com transparência própria (alfa):** usa a transparência do arquivo; esta regra não se aplica.

## Próximas partes (estilo Twinmotion)
- **1.40:** vista inclinada sobre o terreno (MDT).
- **Depois:** modo 3D.
