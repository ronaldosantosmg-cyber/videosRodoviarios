"""Inventário das camadas originais, independente do cálculo de eixos/tráfego."""
import json
from collections import Counter
from pathlib import Path
import ezdxf
from .geometry import walk,guess,NO_GEOMETRY
from .store import write_json


def catalog(directory):
    d=Path(directory);source=d/'input.dxf'
    if not source.exists():return {'layers':[],'warnings':[],'source':'none'}
    stat=source.stat();key=[stat.st_size,stat.st_mtime_ns,2];cache=d/'camadas_fonte.json'
    try:
        saved=json.loads(cache.read_text(encoding='utf-8'))
        if saved.get('revision')==key:return saved
    except (OSError,ValueError):pass
    doc=ezdxf.readfile(source);counts=Counter();usable=Counter();types=Counter();stats={};warnings=[]
    for entity in walk(doc.modelspace()):
        layer=entity.dxf.layer;counts[layer]+=1;types[entity.dxftype()]+=1
        kind=entity.dxftype()
        row=stats.setdefault(layer,{'types':Counter(),'linear_count':0,'hatch_count':0,'closed_count':0})
        row['types'][kind]+=1
        if kind in ('LINE','LWPOLYLINE','POLYLINE','ARC','SPLINE'):row['linear_count']+=1
        if kind=='HATCH':row['hatch_count']+=1
        closed=kind in ('HATCH','CIRCLE','SOLID','3DFACE') or bool(getattr(entity,'closed',False)) or bool(getattr(entity,'is_closed',False))
        if closed:row['closed_count']+=1
        if kind not in NO_GEOMETRY:usable[layer]+=1
    names={entry.dxf.name for entry in doc.layers}|set(counts)
    if any(getattr(block.block.dxf,'flags',0)&4 for block in doc.blocks):warnings.append('Há referências externas (XREF). Arquivos externos precisam estar incorporados no DXF para participar da geometria.')
    if any(k.startswith(('AECC_','AEC_')) or k=='ACAD_PROXY_ENTITY' for k in types):warnings.append('Há objetos especiais/proxy. Exporte uma cópia com EXPORTTOAUTOCAD no Civil 3D para converter sua geometria; os nomes das camadas foram preservados.')
    if counts and set(counts)=={'0'} and len(names)>1:warnings.append('As entidades do espaço de modelo estão na camada 0; as demais camadas existem na tabela, mas precisam receber geometria no arquivo de origem. Nenhum nome foi inventado.')
    out={'revision':key,'source':'input.dxf','layers':[{'name':name,'count':counts[name],'geometry_count':usable[name],'suggested_role':guess(name),'declared':True,**{k:(dict(v) if isinstance(v,Counter) else v) for k,v in stats.get(name,{}).items()}} for name in sorted(names)],'warnings':warnings}
    write_json(cache,out);return out
