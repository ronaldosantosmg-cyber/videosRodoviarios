# Rodovia Studio 1.19 — comandos, imagens locais, fontes web, limpeza e atualizador

## O que mudou

### 1. Comandos do editor
- **Enter** conclui o comando em andamento (área, fluxo, acesso…) e volta para **Navegar**. Assim você pode começar outro comando em outro lugar. **Esc** cancela o comando.
- **Mudar o ponto de início**:
  - **Placa**: arraste uma placa existente.
  - **Vão da passarela**: arraste o centro para mudar a passarela de lugar. Arrastar a ponta continua mudando o vão e o ângulo.
  - **Linha de chamada**: arraste a âncora (ponta) ou o marcador da obra (início).
- Nova ferramenta **Mover ponto**: move qualquer ponto marcado, como placa, intervenção, âncora, destaque, cidade, faixa de pedestre, início/fim da 3ª faixa, vértices de acesso, travessia ou OAE de 2 pontos.
- Tudo entra no desfazer/refazer.

### 2. Imagens locais: prioridade e ajuste por grips
- Na lista de imagens:
  - **▲/▼** mudam a prioridade. A imagem de cima prevalece onde as imagens se sobrepõem.
  - Onde nenhuma imagem local cobre, vale a imagem web (Esri ou a fonte escolhida).
- O botão **Ajustar** abre a ferramenta **Ajustar imagem local**, com o contorno da imagem e grips:
  - arrastar **dentro** da imagem desloca;
  - arrastar um **canto** gira e escala em torno do centro (Shift: só gira; Ctrl: só escala);
  - as setas do teclado deslocam 5 cm (com Shift, 50 cm);
  - há **desfazer**, **refazer** e **posição original**.
- O ajuste fica gravado na configuração do projeto, no CRS do projeto (deslocamento em metros, rotação em graus, escala). Vale para:
  - o editor;
  - o mosaico do vídeo;
  - a aproximação do vídeo.
- **O arquivo da imagem não é alterado.**

### 3. Prévia com zoom forte (~10 m)
- **No editor**: a prévia passou a desenhar só o recorte visível. Antes, o navegador recebia uma imagem de dezenas de milhares de pixels de largura.
- **No vídeo e na prévia**: abaixo de 3,5 cm por pixel de tela (vistas de cerca de 45 m ou menos em 1280 px), a cena usa ladrilhos de detalhe de **5 cm**. Abaixo de 2 cm por pixel, entra um **grão fino** nas texturas, para que pista e concreto não virem um borrão.
- **Detalhar vista atual** passou a aceitar vistas a partir de **5 m** (antes, 20 m).

### 4. Menus profissionais
- A barra de ferramentas agora tem:
  - **grupos com título**: Navegação, Estaqueamento e obras, Fluxos, Áreas e sinalização, Tráfego e acessos, Calibração e cabine;
  - **ícones vetoriais** em todas as ferramentas;
  - dica completa ao passar o mouse.
- O botão **Mostrar nomes** exibe o nome ao lado de cada ícone. A escolha fica lembrada.
- As seções ganharam ícones nos títulos.

### 5. Limpar o trabalho e retirar projeto
- **Limpar trabalho…** (seção 1) remove os grupos escolhidos:
  - obras: intervenções, PER, destaques, interdições e cabine;
  - sinalização: placas, faixas de pedestre, zebrados e áreas sem sinalização;
  - geometria: acessos, 3ª faixa, faixas por trecho, OAE e exclusões;
  - fluxos: fluxos, sentidos, inversões, sem conexão e travessias;
  - cidades.
- Ficam sempre as **características do segmento**: DXF/KMZ, CRS, km inicial e final, estaqueamento, camadas, alinhamento, imagens local e web, elevação e parâmetros do vídeo.
- Antes de limpar, o programa salva `config_antes_limpeza_<data>.json`. **Desfazer limpeza** restaura essa configuração.
- Opcionalmente, apaga também o vídeo, a prévia e o cache de aproximação.
- **Retirar projeto** tira o projeto da lista e move a pasta para `projetos\_lixeira`. O programa não apaga nada definitivamente.
- **Exemplo TH57**: abra o exemplo e use **Limpar trabalho** para ficar só com o segmento.

### 6. Outras fontes de imagem web (no lugar da Esri atual)
Em **Configuração → Fonte da imagem web**:
- **Esri World Imagery (atual)**: como antes. É o padrão.
- **Esri Wayback**: arquivo histórico da própria Esri, georreferenciado.
  1. Clique **Carregar datas da Wayback**.
  2. Escolha a data.
  3. Clique **Aplicar fonte**.
  - Serve quando a imagem atual de um trecho está pior (nuvens, distorção) do que uma versão anterior. Compare no editor antes de gerar o vídeo.
- **Serviço XYZ** (`https://…/{z}/{x}/{y}.jpg`; aceita `{-y}`) ou **WMS** (camadas e endereço), por exemplo uma ortofoto oficial do estado ou do município.
  - Use apenas serviços que você tem direito de usar. A atribuição informada aparece no editor e no vídeo.

A fonte escolhida vale para o editor, o mosaico do vídeo (montado por ladrilhos, reprojetados para o CRS do projeto) e a aproximação. Cada fonte tem cache próprio em `_ladrilhos`. A imagem local continua por cima de qualquer fonte web.

### 7. Atualização automática (arquivo faltando)
- **Causa** (pelo `suporte\logs\atualizacao.log` do seu computador): o atualizador extraía o ZIP dentro de `suporte\backups\tmp_…`, na pasta do OneDrive. O caminho de uma imagem de conferência passava de 260 caracteres, o limite do Windows, e o arquivo "não existia".
- **Correções**:
  1. **Pacote 1.19**:
     - a pasta interna do ZIP passou a ser curta (`RS119`);
     - as imagens de conferência das versões anteriores não vão mais no pacote (continuam na sua pasta `documentacao`).
     - Assim, o caminho mais longo, extraído pelo atualizador **1.18 já instalado**, fica em cerca de 220 caracteres. Calculado para a sua pasta.
  2. **Novo atualizador**:
     - extrai em uma pasta temporária curta do sistema;
     - usa caminhos longos do Windows (`\\?\`) na extração e na cópia.

## Configuração
- O esquema passou para a **versão 18**.
- A migração é automática: as fontes web começam como "Esri atual" e as imagens locais, sem ajuste.

## Medido neste ambiente
- **Testes**: 183 testes automáticos passaram (172 da 1.18 + 11 novos). O teste da 1.18 do vão da passarela passou a arrastar a ponta do vão, porque agora o centro move a passarela. Os novos cobrem:
  - ajuste da imagem: deslocamento, rotação, escala e cantos;
  - chave do cache sem ajuste igual à da 1.18;
  - API de prioridade e ajuste;
  - URLs e cache das fontes web;
  - lista da Wayback, com e sem internet (simulada);
  - mosaico por ladrilhos georreferenciado;
  - chave do detalhe;
  - limpeza, desfazer e lixeira;
  - esquema 18;
  - caminho longo do atualizador;
  - editor no navegador: Enter, placa arrastada, Mover, grips da imagem, desfazer, ícones e recorte da prévia.
- **Precisão** (dados sintéticos):
  - imagem a 5 cm deslocada 2 m / 1 m, girada 2° e escalada 1,01: o ponto de controle caiu a menos de 1,5 pixel (menos de 8 cm) da posição esperada;
  - mosaico de fundo montado por ladrilhos XYZ simulados: o ponto de controle ficou a menos de 3 pixels (1,5 m em pixels de 0,5 m).
- **TH57 com a configuração padrão**: quadros de 14, 40 e 96 s e a vista do trevo idênticos, pixel a pixel, aos do pacote 1.18. As mudanças de zoom forte só atuam abaixo de 3,5 cm por pixel.
- **Vistas próximas do TH57** (1280 px, cache de detalhe já gerado): 90 m em 4,8 s (inclui preparação), 30 m em 1,9 s, 10 m e 5 m em 0,3 s.

## Não verificado / limitações
- **Prévia a ~10 m no seu computador**: o desaparecimento **não foi reproduzido** aqui. No Chromium deste ambiente, o desenho antigo funcionou. A correção do recorte visível segue o limite conhecido de canvas com aceleração por GPU, mas só a sua conferência confirma.
- **Imagem a 10 m**: sobre áreas uniformes (por exemplo, o tabuleiro de concreto), a vista de 10 m mostra textura e bordas, não detalhes novos. A nitidez real depende da imagem: a Esri chega a cerca de 30 cm, e uma ortofoto ou drone local, a poucos centímetros.
- **Wayback, XYZ e WMS reais não foram baixados** (sem internet neste ambiente). O endereço dos ladrilhos da Wayback segue a documentação pública da Esri (`wayback.maptiles.arcgis.com …/tile/{versão}/{z}/{y}/{x}`). Não confirmei serviços de ortofoto de MG (por exemplo, IDE-Sisema) nem o direito de uso de cada um.
- **Atualizador**: não foi executado no Windows. A extração pelo atualizador 1.18 instalado foi avaliada pelo cálculo do comprimento dos caminhos, não por execução.
- **Ajuste por grips**: é uma transformação de semelhança (deslocar, girar, escalar). Não corrige distorções locais (ortorretificação).
