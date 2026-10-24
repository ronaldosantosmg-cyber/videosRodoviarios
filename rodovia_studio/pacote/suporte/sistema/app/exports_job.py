"""Tarefas de exportação (processo separado, como a renderização)."""
import json,time
from pathlib import Path
import numpy as np
from PIL import Image
from . import exporters
from .store import replace

def _scene_light(d,s,status):
    # Exportação vetorial: dispensa imagem aérea e hidrografia.
    from .render import Scene
    return Scene(d,s.model_copy(update={'imagery':'neutral','hydrography':False}),status)

def run_export(d,s,status):
    d=Path(d);out=d/'exportacao';out.mkdir(exist_ok=True)
    sc=_scene_light(d,s,status);status(.6,'Montando feições')
    segs=[{**r,'points':r['points']} for r in sc.network.raw_info]
    feats=exporters.features(s,sc.stationing,sc.axes,segs,sc.oae)
    files={'modelo_'+s.crs.replace(':','')+'.geojson':exporters.geojson(feats,s.crs),'modelo_wgs84.geojson':exporters.geojson(feats,s.crs,True),'modelo.kml':exporters.kml(feats,s.crs,s.name),'obras.csv':exporters.works_csv(feats)}
    for name,text in files.items():
        tmp=out/(name+'.tmp');tmp.write_text(text,encoding='utf-8');replace(tmp,out/name)
    tmp=out/'modelo.kmz.tmp';tmp.write_bytes(exporters.kmz(feats,s.crs,s.name));replace(tmp,out/'modelo.kmz')
    tmp=out/'marcacoes.tmp.dxf';exporters.dxf(feats,tmp);replace(tmp,out/'marcacoes.dxf')
    (out/'exportacao.json').write_text(json.dumps({'features':len(feats),'files':sorted(list(files)+['modelo.kmz','marcacoes.dxf']),'crs':s.crs},ensure_ascii=False,indent=2),encoding='utf-8')
    status(1,'Exportação concluída')

def run_frames(d,s,status,cancel):
    """Sequência PNG do vídeo; com rgba_layers, também camadas do projeto com fundo transparente."""
    from .render import Scene
    d=Path(d);pe=s.png_export;sc=Scene(d,s,status)
    stamp=time.strftime('%Y%m%d_%H%M%S');out=d/'quadros_png'/stamp;out.mkdir(parents=True);rgba=out/'camadas_rgba'
    if pe.rgba_layers:rgba.mkdir()
    fps=s.fps;total=round(s.duration_s*fps);first=round(pe.start_s*fps);last=min(total-1,round(pe.end_s*fps))
    if last<first:raise ValueError('Intervalo de quadros vazio.')
    wanted=list(range(first,last+1,pe.every_n_frames));done=0
    sc.shown_poi=None;sc.poi_since=-100
    # A chamada do cabeçalho depende dos quadros anteriores: percorre desde o início, salvando só os pedidos.
    want=set(wanted)
    for k in range(0,last+1):
        if cancel():raise InterruptedError('Exportação cancelada.')
        t=k/fps
        if k in want:
            im,_=sc.frame(t);Image.fromarray(im).save(out/f'quadro_{k:06d}.png',compress_level=3)
            if pe.rgba_layers:
                layer=sc.layer_rgba(t);Image.fromarray(layer,'RGBA').save(rgba/f'camada_{k:06d}.png',compress_level=3)
            done+=1;status(.25+.74*done/len(wanted),f'Quadro {k+1} · {done}/{len(wanted)} salvos')
        else:sc.advance_state(t)
    (out/'sequencia.json').write_text(json.dumps({'fps':fps,'first_frame':first,'last_frame':last,'every_n_frames':pe.every_n_frames,'count':len(wanted),'width':sc.W,'height':sc.H,'rgba_layers':pe.rgba_layers,
        'note':'camadas_rgba: pavimento, sinalização, veículos, símbolos e textos sobre fundo transparente; sem imagem aérea e sem textura de água.'},ensure_ascii=False,indent=2),encoding='utf-8')
    return out
