# Rodovia Studio 1.4 — Fase B: camadas, imagem local e intercâmbio

Nova seção **Camadas, imagem local e intercâmbio** (coluna da esquerda).

## Camadas DXF adicionais
- **Adicionar camada** envia outro DXF, que é guardado em `camadas/` dentro do projeto. O DXF principal não muda.
- Cada camada tem: ligar/desligar, ordem (▲▼), cor, opacidade, espessura em metros, preenchimento de polígonos, CRS próprio (é reprojetado para o do projeto), deslocamento dx;dy próprio e associação de cada layer a uma classe (pavimento, via existente, OAE, canteiro, barreira, corte, aterro, domínio, eixo), a “Desenho (estilo da camada)” ou a “Ignorar”.
- Layers associadas a uma classe passam a valer como geometria do projeto: o pavimento entra no grafo de tráfego, por exemplo.
- **Excluir camada** remove a entrada e o arquivo dela do projeto.

## Imagem georreferenciada local
- Aceita GeoTIFF (tags GeoTIFF: ModelPixelScale/ModelTiepoint ou ModelTransformation, EPSG pela GeoKey, PixelIsPoint tratado) ou JPG/PNG/TIF com arquivo de mundo (.tfw/.jgw/.pgw/.wld) e .prj — ou com o CRS informado.
- A imagem é reprojetada para o CRS do projeto em faixas, ponto a ponto pelo pyproj (não por grade aproximada), recortada à área do projeto e guardada no cache `imagery/`. Imagens muito mais detalhadas que o mosaico são reduzidas antes, por média de área.
- Nova fonte de fundo **Imagem local**. O cabeçalho mostra “Imagem local: nome · X m/px”.
- Arquivo sem georreferência, ou sem CRS, é rejeitado com mensagem clara e não é guardado.

## Exportação
**Gerar exportação** cria em `exportacao/` do projeto (todos para download no navegador):
- `modelo_EPSGxxxx.geojson` (CRS do projeto) e `modelo_wgs84.geojson`;
- `modelo.kml` e `modelo.kmz` para Google Earth, com pastas por tipo, estilos e km na descrição;
- `marcacoes.dxf` (ezdxf, R2010) com uma layer por tipo: RS_EIXO, RS_MARCO_KM, RS_INICIO_KM, RS_TRAJETORIA, RS_FLUXO_INCLUIDO, RS_SENTIDO, RS_FLUXO_OVERRIDE, RS_EXCLUSAO, RS_OAE, RS_SEM_CONEXAO, RS_INTERVENCAO, RS_OBRA, RS_CHAMADA e RS_PAR_CONTROLE. As propriedades vão em XDATA “RODOVIA”;
- `obras.csv` com obras, intervenções e OAE, km inicial/final e X/Y.

O conteúdo inclui eixos, marcos de km a cada 100 m, trajetórias orientadas no sentido do tráfego, exclusões, OAE, obras, chamadas, cruzamentos sem conexão, setas e pares de controle, cada um com km.

**Baixar pacote do projeto (.zip)** junta configuração, DXF, KMZ, camadas, imagem local e um `manifest.json` com SHA-256 de cada arquivo. **Abrir pacote** cria um projeto novo em outro computador, confere os hashes e recusa caminhos fora do projeto.

**Importar marcações** lê GeoJSON, KML/KMZ (exportados pelo aplicativo, inclusive se editados em SIG ou no Google Earth) ou CSV de obras, substituindo os tipos de marcação presentes no arquivo.

**Sequência PNG**: escolha início, fim e “1 a cada N quadros”. Os quadros vão para `quadros_png/<data>/`. Com **camadas RGBA**, cada quadro também sai sobre fundo transparente (pavimento, sinalização, veículos, símbolos e textos), obtido compondo o quadro sobre preto e sobre branco. Cabeçalho e rodapé ficam opacos.

## Medido
- TH57 1280×720 sem camadas e sem imagem local: quadros idênticos à 1.2 (mesma medição da 1.3).
- Testes: reimportação de GeoJSON (CRS do projeto, tolerância 1e-6 m), GeoJSON WGS84, KML e KMZ (tolerância 2 mm) com geometria e km preservados; DXF relido pelo ezdxf com todas as layers e XDATA; CSV relido com km e X/Y; pacote com SHA-256, adulteração e caminho malicioso recusados; GeoTIFF (PixelIsArea e PixelIsPoint), PNG + .pgw + .prj e imagem em graus (EPSG:4326) posicionados no ponto conhecido; rejeição sem georreferência; camadas com classe, estilo, offset, CRS próprio, desligar e excluir; sequência PNG com camadas RGBA pela API.

## Não testado / limites
- KML não foi aberto no Google Earth, e o DXF não foi aberto no AutoCAD/Civil 3D. A validação foi a releitura pelo aplicativo e pelo ezdxf.
- GeoTIFF com compressão JPEG/WebP interna precisa ser convertido para LZW, Deflate ou sem compressão. A rotação no arquivo de mundo entra no cálculo, mas não foi testada. Mosaicos em vários arquivos não são aceitos: envie um arquivo único.
- A sequência PNG não reproduz a transição de 0,8 s entre cenas do MP4, e as camadas RGBA não incluem imagem aérea nem textura da água.
- Quadros PNG em 1440p ocupam alguns MB cada: escolha um trecho.
