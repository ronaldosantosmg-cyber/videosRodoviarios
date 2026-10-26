"""Cache derivado de geometria, numérico/JSON, sem pickle nem mudança da fonte."""
import json,zlib,time,uuid
from pathlib import Path
import numpy as np

MAX_RAW=96*1024*1024
MAX_COMPRESSED=32*1024*1024


def _encode(value):
    if isinstance(value,np.ndarray):return {'__array__':value.tolist()}
    if isinstance(value,np.generic):return value.item()
    raise TypeError('Tipo não suportado pelo cache de geometria.')


def _decode(data):
    count=[0]
    def hook(row):
        if set(row)=={'__array__'}:
            a=np.asarray(row['__array__'],float);count[0]+=a.size
            if count[0]>4000000 or not np.isfinite(a).all():raise ValueError('Cache de geometria excede os limites numéricos.')
            return a
        return row
    def invalid_constant(value):raise ValueError('Número não finito no cache.')
    return json.loads(data,object_hook=hook,parse_constant=invalid_constant)


def cached_analyze(original,directory,settings,preview=None,hatch_preview=None):
    if preview is not None or hatch_preview is not None:return original(directory,settings,preview,hatch_preview)
    from .dependencies import revisions,digest
    d=Path(directory);folder=d/'_cache'/'geometry';started=time.monotonic()
    def cache_key():
        return revisions(d,settings)['geometry']
    key=cache_key();target=folder/(key+'.json.z')
    safe=not any(p.is_symlink() for p in (d/'_cache',folder,target))
    from .full_update import required,rebuilt
    force=required('geometry',str(target))
    if not force and safe and target.is_file() and target.stat().st_size<=MAX_COMPRESSED:
        try:
            decoder=zlib.decompressobj();raw=decoder.decompress(target.read_bytes(),MAX_RAW+1)
            if len(raw)>MAX_RAW or not decoder.eof or decoder.unconsumed_tail or decoder.unused_data:raise ValueError('Cache excede o limite de leitura.')
            result=_decode(raw)
            if not isinstance(result,list) or len(result)!=5 or not isinstance(result[4],dict):raise ValueError('Formato de cache inválido.')
            axis,distances=result[1:3]
            if not isinstance(axis,np.ndarray) or axis.ndim!=2 or axis.shape[1]!=2 or len(axis)<2 or not isinstance(distances,np.ndarray) or distances.shape!=(len(axis),) or distances[-1]<=0 or np.any(np.diff(distances)<0):raise ValueError('Eixo do cache inválido.')
            for rows in (result[0],result[3]):
                if not isinstance(rows,list) or len(rows)>100000:raise ValueError('Entidades inválidas no cache.')
                for row in rows:
                    points=row.get('points') if isinstance(row,dict) else None
                    if not isinstance(points,np.ndarray) or points.ndim!=2 or points.shape[1]!=2 or len(points)<1:raise ValueError('Coordenadas inválidas no cache.')
            from .pavement import tag_materials
            tag_materials(result[0],settings)
            result[4]['geometry_cache']={'hit':True,'seconds':time.monotonic()-started}
            return tuple(result)
        except (ValueError,TypeError,KeyError,zlib.error,OSError):pass
    result=original(directory,settings,preview,hatch_preview)
    if safe:
        temp=None
        try:
            raw=json.dumps(result,default=_encode,allow_nan=False,separators=(',',':')).encode()
            if len(raw)<=MAX_RAW and cache_key()==key:
                compressed=zlib.compress(raw,3)
                if len(compressed)<=MAX_COMPRESSED:
                    folder.mkdir(parents=True,exist_ok=True);temp=folder/('.'+uuid.uuid4().hex+'.tmp');temp.write_bytes(compressed);temp.replace(target);rebuilt('geometry',str(target))
                    for previous in sorted(folder.glob('*.json.z'),key=lambda p:p.stat().st_mtime,reverse=True)[2:]:
                        if not previous.is_symlink():previous.unlink(missing_ok=True)
        except (ValueError,TypeError,OSError):pass
        finally:
            if temp is not None:temp.unlink(missing_ok=True)
    result[4]['geometry_cache']={'hit':False,'seconds':time.monotonic()-started}
    return result
