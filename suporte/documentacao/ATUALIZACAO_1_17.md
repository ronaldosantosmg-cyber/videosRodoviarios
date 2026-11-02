# Rodovia Studio 1.17 — imagem georreferenciada local de alta resolução

Terceira etapa do plano (funcionais): usar a ortofoto ou o levantamento de drone da concessionária no lugar da Esri onde houver cobertura.

## Formatos
| Formato | Como é lido | Observação |
|---|---|---|
| GeoTIFF / COG em blocos, sem compressão ou Deflate | Por blocos, só a parte necessária, usando as visões reduzidas | Indicado para arquivos grandes |
| GeoTIFF LZW/JPEG, JPG, PNG | Leitura completa | Limite de 700 milhões de pixels |
| JPEG2000 (.jp2) | Leitura completa | Georreferência pela caixa GeoJP2, pelo GMLJP2 ou pelo .j2w |
| ECW, MrSID (.sid), .img | Convertidos uma vez para GeoTIFF em blocos (Deflate, com visões) pelo GDAL do QGIS ou OSGeo4W instalado no computador | Formatos proprietários: o Python do aplicativo não os lê diretamente |

## Como usar
Na seção **Camadas, imagem local e intercâmbio → Imagem georreferenciada local**:
1. Selecione juntos a imagem, o arquivo de mundo e o .prj (ou informe o CRS).
2. Em **Ao enviar**, escolha:
   - **Substituir a imagem principal** (como antes);
   - **Acrescentar ao mosaico** (a primeira imagem tem prioridade onde elas se sobrepõem).
3. Para ECW ou MrSID: envie o arquivo e clique em **Converter ECW/MrSID com o QGIS**.
   - O programa procura o QGIS em `C:\Program Files\QGIS*\bin`, `C:\OSGeo4W\bin` ou no PATH. Também é possível indicar a pasta pela variável `RODOVIA_GDAL_BIN`.
   - Sem QGIS, converta no próprio QGIS (Raster → Conversão → Converter, com TILED=YES e COMPRESS=DEFLATE) e envie o GeoTIFF.
4. A lista mostra cada imagem com tamanho, resolução e CRS, com os botões **Ver** e **Retirar**.
5. Ajustes:
   - usar na aproximação do vídeo;
   - mostrar no editor;
   - brilho, contraste e saturação;
   - bordas pretas/brancas como "sem dados".

## Onde a imagem aparece
- **Aproximação do vídeo** (camada de detalhe, 0,2 m ou 0,1 m por pixel): a imagem local tem prioridade. Onde ela não cobre, vale a Esri (se o fundo for Esri), com transição suave na borda. O ladrilho fica guardado em disco.
- **Mosaico base**: com "Imagem local" como fonte de fundo. Uma imagem pequena em JPG/PNG/TIF continua no caminho anterior, com resultado igual. Mosaico, JPEG2000 e arquivos com mais de 300 MB são lidos por blocos.
- **Editor**: ladrilhos Web Mercator gerados pelo servidor local e guardados em disco. É possível aproximar até o zoom da resolução da imagem (por exemplo, nível 21 a 5 cm), como no Google Earth, e ajustar fluxos e sentidos sem distorção.

## Configuração
O esquema passou para a **versão 16**, com migração automática. As imagens novas ficam na pasta `imagem_local` do projeto. O arquivo original nunca é alterado.

## Medido neste ambiente
- **Testes**: 165 automáticos passaram, 8 deles novos. Dois testes da 1.11 passaram a indicar explicitamente que o fundo é Esri.
- **Georreferência**: em imagem sintética de 5 cm, o ponto de controle caiu a menos de 1,5 pixel (menos de 8 cm) no mosaico e no JPEG2000 com .j2w ou GeoJP2; no ladrilho do editor o ponto aparece no ladrilho certo.
- **Desempenho** com um GeoTIFF sintético de 12.000 × 12.000 px (0,05 m, 569 MB, com visões):
  - ladrilho de detalhe de 1024 px: 0,16 a 0,21 s, tanto a 0,2 m quanto a 0,1 m;
  - mosaico base de 4096 px: 4,4 s.
- **TH57 sem imagem local**: quadros idênticos aos da 1.16, pixel a pixel, nos instantes 14, 40 e 96 s e na vista do trevo.

## Não verificado / limitações
- **ECW e MrSID reais**: a conversão foi testada com um gdal_translate simulado. Não foi testada com o QGIS e o plugin ECW no Windows da empresa. A licença do SDK ECW de leitura é a distribuída com o QGIS/OSGeo4W.
- **Arquivos reais**: não houve teste com ortofotos reais da NOVA 381. A precisão real depende da georreferência do arquivo.
- **Arquivos grandes com LZW/JPEG**: GeoTIFF com essas compressões e JPEG2000 grandes são lidos inteiros e consomem memória. Para arquivos grandes, prefira GeoTIFF em blocos com Deflate, ou COG.
- **Esri com imagem local**: a transição não foi verificada com ladrilhos Esri reais, porque não há internet neste ambiente.
