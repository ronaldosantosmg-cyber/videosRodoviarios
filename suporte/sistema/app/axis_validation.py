"""1.42.41: validação de continuidade dos eixos antes da simulação (somente leitura).

Para cada eixo: cobertura dentro do pavimento reconhecido (amostrada a cada 5 m), maior trecho fora do pavimento
(estacas), autointerseção, extremidades livres e lacunas das seções cadastradas. Não altera eixo, sentido nem rotas.
"""
from .falhas import registrar as _falha
import math
import numpy as np
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
from shapely.prepared import prep

PAVED=('pavement','existing_pavement','shoulder','oae')
STEP_M=5.0

def _paved(entities):
    ps=[]
    from shapely.geometry import Polygon
    from shapely.validation import make_valid
    for e in entities:
        if e.get('role') in PAVED and e.get('closed') and len(e['points'])>=3:
            try:ps.append(make_valid(Polygon(e['points'],[h for h in e.get('holes',[]) if len(h)>=3])))
            except Exception as _e:_falha(__name__,_e)
    return unary_union(ps).buffer(0) if ps else None

def validate_axes(axes,entities,route_alignments=(),min_cover=0.85,end_tol_m=1.0):
    paved=_paved(entities);pp=prep(paved) if paved is not None and not paved.is_empty else None
    rows=[];ends=[]
    lines=[]
    for i,a in enumerate(axes):
        p=np.asarray(a['points'],float)
        lines.append(LineString(p) if len(p)>=2 else None)
    for i,a in enumerate(axes):
        line=lines[i]
        if line is None or line.length<=0:continue
        L=float(line.length);n=max(2,int(L//STEP_M)+1);st=np.linspace(0,L,n)
        row={'index':i,'name':a.get('layer') or f'Eixo {i+1}','length_m':round(L,1),'alerts':[]}
        if pp is not None:
            inside=np.array([pp.covers(line.interpolate(s)) for s in st])
            row['coverage']=round(float(inside.mean()),3)
            runs=[];start=None
            for k,ok in enumerate(inside):
                if not ok and start is None:start=k
                if (ok or k==len(inside)-1) and start is not None:
                    end=k if not ok else k-1;runs.append((st[start],st[end]));start=None
            if runs:
                worst=max(runs,key=lambda r:r[1]-r[0]);row['longest_off_m']=round(worst[1]-worst[0]+STEP_M,1);row['longest_off_at_m']=[round(worst[0],1),round(worst[1],1)]
            if row['coverage']<min_cover:
                row['alerts'].append({'code':'fora_do_pavimento','text':f"Só {row['coverage']*100:.0f}% do eixo está sobre pavimento reconhecido"+(f"; maior trecho fora: {row['longest_off_m']} m (estaca {row['longest_off_at_m'][0]} a {row['longest_off_at_m'][1]} m)." if runs else '.')})
        else:row['coverage']=None;row['alerts'].append({'code':'sem_pavimento','text':'Sem pavimento reconhecido para conferir o eixo.'})
        if not line.is_simple:row['alerts'].append({'code':'autointersecao','text':'O eixo cruza a si mesmo; confira o traçado.'})
        for k,pt in enumerate((line.coords[0],line.coords[-1])):
            free=True
            for j,other in enumerate(lines):
                if j==i or other is None:continue
                if other.distance(Point(pt))<=end_tol_m:free=False;break
            ends.append((i,k,free))
        rows.append(row)
    for i,k,free in ends:
        if free:
            r=next((x for x in rows if x['index']==i),None)
            if r is not None:r.setdefault('free_ends',[]).append('início' if k==0 else 'fim')
    for r in rows:
        if r.get('free_ends'):r['info']=f"Extremidade livre ({', '.join(r['free_ends'])}): esperado nas pontas da via; confira se houver ligação prevista."
    gaps=[]
    try:
        from .road_sections import continuity_report
        for route in route_alignments:
            rep=continuity_report(route)
            if rep and rep['gaps']:gaps.append(rep)
    except Exception as _e:_falha(__name__,_e)
    alerts=[{'axis':r['name'],**a} for r in rows for a in r['alerts']]
    for g in gaps:alerts.append({'axis':g['name'],'code':'lacuna_de_secao','text':f"{len(g['gaps'])} intervalo(s) sem seção cadastrada: "+', '.join(f"{x['start_m']:.0f}–{x['end_m']:.0f} m" for x in g['gaps'][:5])+'.'})
    return {'axes':rows,'section_gaps':gaps,'alerts':alerts,'summary':{'axes':len(rows),'with_alerts':sum(1 for r in rows if r['alerts']),'section_gaps':len(gaps)}}
