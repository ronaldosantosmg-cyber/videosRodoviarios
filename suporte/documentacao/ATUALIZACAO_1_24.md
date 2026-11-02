# Rodovia Studio 1.24 — leitor ECW interno, comandos tipo CAD completos, texturas editáveis, leitura automática dos hatches e vídeo mais rápido

## O que mudou — edição e comandos
- **Enter finaliza e aceita** em todas as funções: desenho (fecha a área/linha), campos das opções da ferramenta (aceita e volta para a tela), propriedades, formulários de pontos de interesse, linha de comando. Enter vazio repete/encerra o comando, como no CAD.
- **Esc pede confirmação** quando há um comando em andamento: aparece uma caixa “Cancelar o comando?” com o que será perdido (por exemplo, “2 pontos”). *Continuar* mantém o desenho; *Cancelar* (ou Enter) sai. Sem comando ativo, Esc só desfaz a seleção.
- **Seleção múltipla**:
  - Shift+clique acrescenta/retira um objeto;
  - **Ctrl+arrastar** desenha uma janela: da esquerda para a direita (**janela**, azul) pega o que está inteiro dentro; da direita para a esquerda (**crossing**, verde tracejado) pega o que toca;
  - SELTUDO seleciona tudo; Delete apaga todos os selecionados (com desfazer).
- **Novos comandos** (digite na linha de comando; aceitam clique ou coordenadas X,Y e @dx,dy):
  - **COPIAR (CO)**: ponto base e segundo ponto;
  - **GIRAR (RO)**: ponto base e ângulo em graus (anti-horário) ou clique da direção;
  - **ESCALA (SC)**: ponto base e fator;
  - **ESPELHAR (MI)**: dois pontos da linha de simetria (cria cópias, os originais ficam);
  - **OFFSET (OF)**: distância e clique do lado — cria a paralela de linha, polilinha ou área;
  - **MOVER (M)** agora move vários objetos; **U**/**REFAZER** desfazem/refazem;
  - **TELACHEIA (TC)** e **PAINEL (PN)**.
- **Snap exato**: o snap passa a usar os **vértices e pontos médios originais do DXF** (sem a simplificação de 0,25 m do desenho da tela), carregados por área visível quando a vista tem menos de 1,2 km. A dica mostra “(exato)”. Fora disso, continua valendo o snap aproximado.
- **Atalhos com a tela em foco**: **Ctrl+Shift+F** (tela cheia) e **Ctrl+Shift+L** (painel). F e L sozinhos continuam funcionando fora da tela; dentro dela as letras vão para a linha de comando.
- **Informação na tela** (pode desligar em “Info na tela”): perto do cursor mostra o comando ativo, número de pontos, distância e azimute desde o último ponto, área parcial do desenho e km/afastamento do eixo. O painel de propriedades mostra comprimento, área, perímetro e faixa de km do objeto, e o resumo da seleção múltipla.
- **Menus**: barra de atalhos para as seções no topo do painel; cada seção recolhe/expande clicando no título (lembrado no navegador); botões Recolher tudo/Expandir tudo.

## O que mudou — fluxos
- Clicar numa trajetória (sem objeto selecionado) **seleciona o fluxo**, destaca-o e abre o painel com **inverter sentido**, **desligar/religar** e comprimento.
- **Atualização automática dos fluxos** (caixa “Atualizar fluxos sozinho”): depois de uma alteração, recalcula em 1,2 s; desligada, mostra o aviso para atualizar manualmente.

## O que mudou — texturas editáveis
- Em *Perfil de vídeo → Texturas*, cada superfície (pista nova, pista existente, concreto, acostamento, canteiro, trilhas de roda, talude de corte e de aterro) tem controles de **grão, tom, remendos, fissuras e brilho**, com **amostra ao vivo**. Com tudo no padrão, o resultado é idêntico ao anterior.

## O que mudou — leitura automática dos hatches do DXF
- Na análise, cada hachura do DXF é identificada por **camada | padrão | cor** e listada em *Hachuras do DXF* com área, quantidade e **sugestão automática** (pista nova, existente, acostamento, canteiro, zebrado, ignorar) e material (flexível/rígido) pelo nome da camada e do padrão (por exemplo CONC, CCP, AR-CONC → rígido; ASFALT, CBUQ, TSD → flexível).
- Você pode trocar o papel de cada tipo; “Usar todas as sugestões” aceita tudo. Projetos antigos mantêm a leitura anterior (sugestões desligadas na migração), até você ligar.

## O que mudou — geração do vídeo
- **Motor de montagem “otimizado”** (padrão; “anterior” fica disponível em Perfil de vídeo): menos cópias de imagem por quadro, fundo calculado só quando o detalhe não cobre a tela, redução direta em vez de suavização dupla e gravação mais rápida dos ladrilhos em cache.
- A conferência do MP4 ao final (1.20) continua.

## O que mudou — leitor ECW interno
- **Instalar leitor ECW interno (uma vez)**: botão em *Camadas, imagem local e intercâmbio → Imagem georreferenciada local*. O aplicativo instala no próprio Python portátil, sem administrador e sem QGIS:
  - **GDAL para Python** (rodas binárias de Christoph Gohlke para Windows, pelo índice *Geospatial Wheels Index*);
  - **plugin ECW do GDAL** (pacote `gdal-ecw`, com as DLLs do ERDAS ECW/JP2 SDK distribuídas pelo GISInternals).
- **Sem internet ou com bloqueio**: copie os arquivos `.whl` para `suporte\sistema\pacotes_ecw` e clique em Instalar de novo. A instalação usa só essa pasta. São estes os arquivos:
  - GDAL para Python 3.12, Windows 64 bits (`GDAL-3.11.x-cp312-cp312-win_amd64.whl`);
  - `gdal_ecw-3.11.x-py3-none-win_amd64.whl`.
- **Conversão automática**: ao enviar um `.ecw` (ou `.jp2`/`.sid`), a conversão para GeoTIFF em blocos começa sozinha, dentro do aplicativo:
  - compressão Deflate e visões reduzidas;
  - canal alfa preservado.
  - Sem o leitor interno, continua valendo o caminho pelo QGIS/OSGeo4W, se houver.
- **Georreferência garantida**: antes de aceitar o resultado, o programa confere que tamanho, origem, tamanho do pixel, sistema de coordenadas e os **quatro cantos** são idênticos ao original. Se algo mudar, o arquivo é descartado e o motivo aparece.
  - Além das etiquetas do GeoTIFF, grava **.tfw** e **.prj** ao lado, como dupla garantia.
  - A conferência fica registrada em `imagem_local\<nome>_conferencia.json`.

## Sobre "imagens atuais"
| Fonte | Atualidade | Resolução | Situação no Rodovia Studio |
|---|---|---|---|
| Drone ou aerolevantamento da concessionária (ECW, GeoTIFF, JP2) | A data do voo | 2 a 10 cm | Melhor opção para obra. Agora o ECW é lido dentro do aplicativo (1.24) |
| Esri atual / Esri Wayback | Varia por região; pode ter anos | ~30–60 cm | Já disponível (1.19) |
| Satélite comercial (Pléiades Neo, Vantor/Maxar, Planet SkySat) | Programável (dias) | 30–50 cm | Contratada à parte; entra como GeoTIFF/JP2 pela imagem local |
| Serviços XYZ/WMS de órgãos públicos | Varia | Varia | Já disponível (1.19), se o serviço for autorizado |

Nenhum serviço gratuito traz imagem de alta resolução recente garantida para trechos em obra. Por isso o caminho escolhido foi ler bem a imagem que a própria concessionária já contrata (ECW).

## Medido neste ambiente
- **Testes**: **222 testes automáticos passaram** (210 da 1.23 + 12 novos).
- Teste do editor no Chromium: menus; Esc com confirmação (Continuar/Cancelar); Enter nas opções; janela com Ctrl+arrastar; COPIAR, GIRAR 90°, ESCALA 2, ESPELHAR conferidos na coordenada exata; Delete múltiplo; OFFSET de 1 m de uma área; seleção e inversão de fluxo; textura gravada no projeto.
- Snap exato: o endpoint devolve os vértices exatos do DXF (conferidos a 0,1 mm).
- Hachuras: assinatura, sugestões, papéis escolhidos e migração.
- **Regressão TH57** (quadros 14, 40, 96 s e vista do trevo, 1280 px): com o motor **anterior**, **idêntico pixel a pixel à 1.23**. Com o otimizado, diferença média de 1,6 níveis de cinza (máx. 54, em bordas finas) por causa da redução direta; visualmente equivalente na comparação lado a lado.
- **Velocidade de montagem** (TH57, 1920 px, 20 quadros, ladrilhos já em cache, CPU deste ambiente, 2 medições de cada): anterior 594–694 ms/quadro; otimizado 443–524 ms/quadro — cerca de **20–25 % mais rápido**. A medida varia bastante neste ambiente; não inclui a codificação do MP4.
- Testes do ECW usam um GDAL simulado com a mesma interface:
  - conversão que mantém a georreferência e grava .tfw/.prj, com o ponto de controle a menos de 1,5 pixel no mosaico;
  - recusa quando a origem muda 0,5 m, quando o sistema de coordenadas muda ou quando falta georreferência;
  - preservação do canal alfa;
  - instalação online, sem internet e com erro;
  - estado do leitor sem GDAL;
  - envio pela API e conversão pelo leitor interno sem QGIS.

## Não verificado / limitações
- **Velocidade no seu computador** não foi medida; o ganho depende do processador e de quanto do quadro é coberto pela imagem de detalhe.
- **Renderização em blocos de 8 s com conferência por bloco** não foi feita nesta versão.
- O snap exato só é carregado com a vista menor que 1,2 km (para não pesar); a área pedida é limitada a 4 km².
- As sugestões de hachura dependem dos nomes de camada/padrão do seu DXF; confira a lista antes de gerar.
- **Nada foi executado com um ECW real nem no Windows**. Este ambiente não tem GDAL nem acesso aos pacotes para Windows. Falta conferir no seu computador:
  - a instalação;
  - o carregamento do plugin ECW;
  - a conversão de um arquivo da NOVA 381.
- **Visual C++**: se o Windows não tiver o Microsoft Visual C++ 2015-2022 (x64), o plugin pode não carregar ("Can't load requested DLL"). A instalação desse componente exige a TI.
- **Licença do SDK ECW** (Hexagon/Intergraph):
  - o uso permitido é **somente leitura (decodificação) em aplicativo de computador**: não grava ECW e não pode ser usado em servidor;
  - o pacote `gdal-ecw` não informa na página qual versão da licença acompanha as DLLs atuais;
  - **confirme com o jurídico ou a TI da concessionária** antes de usar em produção.
- **Bloqueios**: proxy ou bloqueio a github.com/pypi.org impedem a instalação online. Use a pasta `pacotes_ecw`.
- **Versões**: o GDAL instalado fica fixo na série 3.11, a mesma do plugin `gdal-ecw` 3.11.3 (publicado em janeiro de 2026).
