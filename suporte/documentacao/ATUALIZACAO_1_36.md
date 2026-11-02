# Rodovia Studio 1.36 — estilo Twinmotion (parte 1): câmera por pontos-chave, clima, sombras pelo sol e antes/depois

Começamos pelas funções mais simples de implementar no motor atual (vista aérea). Todas ficam **desligadas por
padrão**: projetos novos e antigos geram o mesmo vídeo de antes até você ligar cada uma.

## Câmera por pontos-chave
- **Como marcar:** no painel **Vídeo**, quadro **Câmera, clima, sol e antes/depois** (ou **Vídeo › Ambiente › Ponto-chave da câmera**, comando `PC`):
  - enquadre o desenho como quer ver no vídeo e clique **Adicionar a vista atual**;
  - repita para as próximas vistas.
  - Com 2 ou mais pontos, o **Voo da câmera** passa sozinho para “Pontos-chave marcados”.
- **No vídeo:**
  - a câmera **para** em cada vista o tempo escolhido (padrão 3 s) e **voa suavemente** até a próxima;
  - nos deslocamentos longos, a câmera se afasta um pouco no meio do caminho (como um drone);
  - a duração do vídeo é repartida proporcionalmente entre paradas e voos;
  - o **título** de cada vista aparece no cabeçalho.
  - Neste modo, o projeto aparece todo desde o início (sem a construção progressiva).
- **Lista de vistas:**
  - título, tempo parado e largura;
  - ⌖ vai até a vista, ⟲ troca pela vista atual, ↑↓ mudam a ordem, 🗑 exclui;
  - Ctrl+Z desfaz.
- **No editor:** as vistas aparecem numeradas, com a moldura aproximada (16:9) e o caminho tracejado.

## Clima
- **Nublado:** cores mais apagadas e um pouco mais escuras, com leve tom frio.
- **Chuva:**
  - nublado mais forte;
  - **gotas animadas**: diferentes a cada quadro e sempre iguais no mesmo quadro (o vídeo é reproduzível);
  - **pista molhada**: mais escura, com poças claras (reflexo do céu), só sobre o pavimento.
- **Neblina:** véu cinza-claro, um pouco mais denso no alto da tela, e leve desfoque.
- **Intensidade:** de 10 % a 100 %.
- O cabeçalho e o rodapé do vídeo não mudam.

## Sombras pela hora do sol
- **O que faz:** as sombras dos **veículos** e das **OAE** seguem a posição do sol, calculada para o Brasil (~20° S):
  - às 7 h: longas, para oeste;
  - ao meio-dia: curtas, para o sul;
  - às 17 h: longas, para leste.
- **Desligado:** sombra fixa como antes (sol a noroeste).

## Comparação antes/depois
- **O que faz:** nos últimos segundos do vídeo (padrão 8 s), uma **divisória** atravessa a tela da esquerda para a direita:
  - à esquerda, o projeto (**DEPOIS**);
  - à direita, só a imagem aérea (**ANTES**).
  - Os rótulos e a alça da divisória são desenhados na tela.
- **Onde acontece:** no fim do vídeo. Com os pontos-chave, a comparação acontece sobre a última vista que você marcar.

## Medido neste ambiente
- **Testes automáticos:** **301** passaram (294 da 1.35 + 7 novos). Os novos testes cobrem:
  - posição do sol e sombras (manhã longa a oeste, meio-dia curta ao sul);
  - padrão idêntico com tudo desligado;
  - clima (nublado menos saturado e mais escuro, neblina com menos contraste, chuva determinística e animada, cabeçalho intacto);
  - sombra pelo sol;
  - antes/depois (janela de tempo e divisória na tela);
  - câmera por pontos-chave (posições, zoom de voo, título; com 1 ponto, o voo normal continua);
  - um teste de tela (adicionar vistas, título, parada, ordem, desfazer, ir para, clima, sol e antes/depois gravados).
- **Vídeo TH57 (projeto existente):** quadros 14, 40 e 96 s e vista do trevo **idênticos** à 1.35, pixel a pixel.
- **Tempo por quadro (TH57 1280×720, caches prontos, média dos quadros 40, 60 e 80 s):** limpo 0,30 s · nublado 0,33 s · chuva 0,37 s · neblina 0,34 s · sol às 7 h 0,32 s.
- **Atualização simulada da 1.35 para a 1.36 (pelo atualizador da 1.35):** aplicada, com 16 arquivos novos ou alterados.
- **Conferência visual (TH57):**
  - chuva, de longe e de perto (pista molhada e gotas);
  - neblina;
  - sol às 7 h;
  - divisória antes/depois;
  - voo com 3 pontos-chave (títulos “Trevo de acesso” e “Passarela”).

## Não verificado / limitações
- **Windows:** não testado no seu computador.
- **Antes/depois:** acontece no fim do vídeo (sobre a vista final). Ainda não dá para colocá-lo no meio do vídeo nem numa vista específica.
- **Moldura no editor:** a moldura das vistas é aproximada. O vídeo pode girar a imagem para acompanhar o traçado.
- **Sombras:** valem para veículos e OAE; pórticos, defensas e árvores ainda não têm sombra.

## Próximas partes (estilo Twinmotion)
- **1.37:** biblioteca de árvores e vegetação (aplicada com o pincel), pedestres e mais tipos de veículo (ônibus, caminhão, moto).
- **1.38:** vista inclinada sobre o terreno (MDT).
- **Depois:** modo 3D.
