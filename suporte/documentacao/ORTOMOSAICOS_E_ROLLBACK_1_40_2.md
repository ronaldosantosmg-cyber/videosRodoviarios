# Rodovia Studio 1.40.2 — Ortomosaicos e rollback

## Ortomosaico / ECW com borda branca

A remoção de fundo é baseada em conectividade com o perímetro. Pixels RGB próximos de branco só são descartados quando pertencem à mancha conectada às bordas da matriz. Brancos internos (telhados, concreto, sinalização, faixas) permanecem válidos.

Fluxo implementado em `app/orthomosaic.py`:
1. leitura RGB em overview;
2. máscara de candidatos a branco;
3. flood-fill a partir das quatro bordas;
4. `binary_fill_holes` na área válida;
5. vetorização da pegada;
6. `gdalwarp -cutline -crop_to_cutline -dstalpha`;
7. `gdal_translate -of COG` com DEFLATE e overviews.

### Equivalente GDAL rápido (colar conservador)

```bat
nearblack -of GTiff -white -near 8 -nb 0 -alg floodfill -setalpha ^
  -co TILED=YES -co COMPRESS=DEFLATE -co PREDICTOR=2 -co BIGTIFF=IF_SAFER ^
  -o ortofoto_alpha.tif entrada.ecw
```

Para recorte exato por pegada vetorial:

```bat
gdalwarp -overwrite -multi -wo NUM_THREADS=ALL_CPUS ^
  -cutline footprint.geojson -crop_to_cutline -dstalpha -r near ^
  -of GTiff -co TILED=YES -co BLOCKXSIZE=512 -co BLOCKYSIZE=512 ^
  -co COMPRESS=DEFLATE -co PREDICTOR=2 -co BIGTIFF=IF_SAFER -co NUM_THREADS=ALL_CPUS ^
  entrada.ecw recortado.tif

gdal_translate -of COG recortado.tif ortofoto_cog.tif ^
  -co COMPRESS=DEFLATE -co PREDICTOR=STANDARD -co BLOCKSIZE=512 ^
  -co BIGTIFF=IF_SAFER -co NUM_THREADS=ALL_CPUS -co OVERVIEWS=AUTO
```

## Restabelecer versão anterior

Toda atualização nova grava `rollback.json` dentro de `sistema/backups/antes_v...`. O manifesto registra:
- versão anterior e nova;
- arquivos que existiam e foram substituídos;
- arquivos novos adicionados pela atualização.

Ao restabelecer, o sistema:
1. cria snapshot de segurança da versão atual;
2. restaura os arquivos substituídos;
3. remove somente arquivos que foram criados pela atualização;
4. preserva `projetos/`, `videos/` e dados do usuário.

A função está disponível em **Arquivo › Atualizar › Restabelecer versão anterior**, comando `ROLLBACK`, ou `sistema\RESTAURAR VERSAO ANTERIOR.cmd`.
