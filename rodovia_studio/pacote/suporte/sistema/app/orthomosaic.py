"""Processamento seguro de ortomosaicos/ortofotos com colar branco externo.

Regra central: pixels claros só viram transparência quando pertencem à mancha
conectada ao perímetro da imagem. Objetos claros internos permanecem válidos.

Fluxo:
1) lê uma visão reduzida RGB;
2) encontra candidatos próximos de branco;
3) propaga somente a partir das bordas (flood-fill);
4) inverte a máscara e preenche buracos internos (binary_fill_holes);
5) vetoriza a pegada válida;
6) usa gdalwarp -cutline -crop_to_cutline -dstalpha;
7) opcionalmente converte o resultado para COG com compressão lossless.
"""
from __future__ import annotations

import json, shutil, subprocess, tempfile
from pathlib import Path


def _imports():
    try:
        import numpy as np
        import rasterio
        from rasterio.enums import Resampling
        from rasterio.features import shapes
        from scipy import ndimage
        from shapely.geometry import shape, mapping
        from shapely.ops import unary_union
    except Exception as exc:
        raise RuntimeError(
            'Processamento de ortomosaico requer numpy, rasterio, scipy e shapely. '
            'Instale essas dependências no Python do Rodovia Studio.'
        ) from exc
    return np, rasterio, Resampling, shapes, ndimage, shape, mapping, unary_union


def _gdal_tool(name: str) -> str:
    exe=shutil.which(name)
    if exe:return exe
    # Windows costuma expor .exe explicitamente.
    exe=shutil.which(name+'.exe')
    if exe:return exe
    raise RuntimeError(f'{name} não foi encontrado no PATH/GDAL. Instale/ative o GDAL do Rodovia Studio.')



def _valid_mask_from_rgb(rgb, white_threshold=248, close_iterations=1, connectivity=1):
    """Núcleo testável: mantém branco interno e remove só branco ligado à borda."""
    np,_,_,_,ndimage,_,_,_=_imports()
    white=np.all(rgb >= int(white_threshold), axis=0)
    seed=np.zeros_like(white,dtype=bool)
    seed[0,:]=white[0,:];seed[-1,:]=white[-1,:];seed[:,0]=white[:,0];seed[:,-1]=white[:,-1]
    structure=ndimage.generate_binary_structure(2,connectivity)
    external_white=ndimage.binary_propagation(seed,structure=structure,mask=white)
    valid=ndimage.binary_fill_holes(~external_white)
    if close_iterations:
        valid=ndimage.binary_closing(valid,structure=structure,iterations=int(close_iterations))
        valid=ndimage.binary_fill_holes(valid)
    return valid,external_white

def detect_valid_footprint(src, *, white_threshold=248, max_overview=4096,
                           close_iterations=1, connectivity=1):
    """Retorna (geom, metadados) da área válida sem furar brancos internos.

    `white_threshold=248` considera candidato a colar somente pixel cujo R,G,B
    sejam >= 248. A máscara candidata NÃO é aplicada globalmente: apenas os
    candidatos conectados às bordas são descartados.
    """
    np,rasterio,Resampling,shapes,ndimage,shape,mapping,unary_union=_imports()
    src=Path(src)
    with rasterio.open(src) as ds:
        if ds.count < 3:
            raise ValueError('A detecção de colar branco exige pelo menos 3 bandas RGB.')
        scale=min(1.0, float(max_overview)/max(ds.width,ds.height))
        ow=max(1,int(round(ds.width*scale))); oh=max(1,int(round(ds.height*scale)))
        rgb=ds.read([1,2,3], out_shape=(3,oh,ow), resampling=Resampling.nearest)
        # uint16/float: normalize pela faixa do dtype apenas quando necessário.
        if rgb.dtype != np.uint8:
            arr=rgb.astype('float32')
            finite=arr[np.isfinite(arr)]
            if not finite.size:raise ValueError('Raster sem valores RGB finitos.')
            hi=float(np.percentile(finite,99.95)); lo=float(np.percentile(finite,0.05))
            rgb=np.clip((arr-lo)/max(hi-lo,1e-9)*255,0,255).astype('uint8')

        # Somente a mancha clara alcançável desde o perímetro é considerada colar.
        valid,external_white=_valid_mask_from_rgb(rgb,white_threshold,close_iterations,connectivity)

        if not valid.any():raise ValueError('Nenhuma área útil foi detectada; reduza a tolerância ao branco.')
        # Transform da visão reduzida preservando o georreferenciamento.
        from affine import Affine
        transform=ds.transform * Affine.scale(ds.width/ow, ds.height/oh)
        geoms=[shape(g) for g,v in shapes(valid.astype('uint8'), mask=valid, transform=transform) if int(v)==1]
        if not geoms:raise ValueError('Não foi possível vetorizar a área útil.')
        geom=unary_union(geoms)
        if not geom.is_valid:geom=geom.buffer(0)
        # simplificação subpixel reduz milhares de vértices sem alterar a pegada visível
        px=max(abs(transform.a),abs(transform.e))
        if px>0:geom=geom.simplify(px*0.35,preserve_topology=True)
        meta={
            'source':str(src),'source_size':[ds.width,ds.height],
            'overview_size':[ow,oh],'white_threshold':int(white_threshold),
            'external_white_pixels':int(external_white.sum()),
            'valid_pixels':int(valid.sum()),'crs':ds.crs.to_string() if ds.crs else None,
            'bounds':list(map(float,geom.bounds)),
        }
        return mapping(geom),meta


def write_cutline(src, cutline, *, white_threshold=248, max_overview=4096,
                  close_iterations=1):
    """Detecta e grava a pegada válida em GeoJSON no CRS do raster."""
    geom,meta=detect_valid_footprint(src,white_threshold=white_threshold,
        max_overview=max_overview,close_iterations=close_iterations)
    crs=meta.get('crs')
    fc={'type':'FeatureCollection','features':[{'type':'Feature','properties':{'kind':'valid_footprint'},'geometry':geom}]}
    # GeoJSON moderno não depende do membro crs; gdalwarp recebe -cutline_srs quando disponível.
    Path(cutline).write_text(json.dumps(fc,ensure_ascii=False),encoding='utf-8')
    return meta


def gdal_nearblack_command(src, dst, *, threshold=8):
    """Comando conservador: flood-fill de branco a partir do perímetro + alpha.

    `-nb 0` faz a busca parar no primeiro pixel não candidato, reduzindo o risco
    de avançar sobre objetos internos. Para casos críticos prefira `process_orthomosaic`,
    que gera a pegada vetorial explicitamente.
    """
    return [_gdal_tool('nearblack'),'-of','GTiff','-white','-near',str(int(threshold)),
            '-nb','0','-alg','floodfill','-setalpha','-co','TILED=YES',
            '-co','COMPRESS=DEFLATE','-co','PREDICTOR=2','-co','BIGTIFF=IF_SAFER',
            '-o',str(dst),str(src)]


def process_orthomosaic(src, dst, *, white_threshold=248, max_overview=4096,
                        close_iterations=1, cog=True, keep_cutline=False, workdir=None,
                        status=lambda *_:None):
    """Gera GeoTIFF/COG RGBA recortado à pegada válida, preservando brancos internos."""
    np,rasterio,*_= _imports()
    src=Path(src);dst=Path(dst)
    if not src.exists():raise FileNotFoundError(src)
    own=workdir is None
    if own:
        try:
            from .imagery_cache import session_temp
            td=Path(tempfile.mkdtemp(prefix='ortho_',dir=session_temp()))
        except Exception:
            td=Path(tempfile.mkdtemp(prefix='rodovia_ortho_'))
    else:td=Path(workdir)
    td.mkdir(parents=True,exist_ok=True)
    cut=td/'footprint.geojson';tmp=td/'cropped.tif'
    try:
        status(.05,'Detectando somente o colar branco conectado ao perímetro')
        meta=write_cutline(src,cut,white_threshold=white_threshold,max_overview=max_overview,
                           close_iterations=close_iterations)
        crs=meta.get('crs')
        warp=[_gdal_tool('gdalwarp'),'-overwrite','-multi','-wo','NUM_THREADS=ALL_CPUS',
              '-cutline',str(cut),'-crop_to_cutline','-dstalpha','-r','near',
              '-of','GTiff','-co','TILED=YES','-co','BLOCKXSIZE=512','-co','BLOCKYSIZE=512',
              '-co','COMPRESS=DEFLATE','-co','PREDICTOR=2','-co','BIGTIFF=IF_SAFER',
              '-co','NUM_THREADS=ALL_CPUS']
        if crs:warp += ['-cutline_srs',crs]
        warp += [str(src),str(tmp)]
        status(.45,'Recortando pela pegada válida e criando canal Alpha')
        subprocess.run(warp,check=True)
        if cog:
            status(.78,'Gerando Cloud Optimized GeoTIFF')
            cmd=[_gdal_tool('gdal_translate'),'-of','COG',str(tmp),str(dst),
                 '-co','COMPRESS=DEFLATE','-co','PREDICTOR=STANDARD','-co','BLOCKSIZE=512',
                 '-co','BIGTIFF=IF_SAFER','-co','NUM_THREADS=ALL_CPUS','-co','OVERVIEWS=AUTO']
            subprocess.run(cmd,check=True)
        else:
            dst.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(tmp),str(dst))
        status(1.0,'Ortomosaico processado sem furar elementos brancos internos')
        meta.update({'output':str(dst),'cutline':str(cut) if keep_cutline else None,'cog':bool(cog)})
        if keep_cutline:
            target=dst.with_suffix('.footprint.geojson');shutil.copy2(cut,target);meta['cutline']=str(target)
        return meta
    finally:
        if own:shutil.rmtree(td,ignore_errors=True)
