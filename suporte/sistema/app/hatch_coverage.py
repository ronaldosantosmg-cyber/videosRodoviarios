"""1.42.41: cobertura e conflitos entre hachuras (somente leitura; não altera a geometria usada no vídeo).

Recebe as entidades fechadas de ``geometry.analyze`` (dicts com role/points/holes) e informa:
- área por papel e hachuras degeneradas (área ~0, auto-interseção corrigida);
- sobreposições entre papéis diferentes, resolvidas por uma prioridade fixa (quem fica por cima);
- lacunas estreitas entre hachuras do mesmo papel (juntas) e lacunas largas (vazios reais);
- mapa raster de cobertura por papel para conferência visual.
"""
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from shapely.validation import make_valid

# Prioridade de sobreposição (maior número fica por cima). Obra nova sobre existente, OAE sobre pavimento, canteiro sobre tudo.
PRIORITY={'water':1,'domain':0,'cut':2,'fill':2,'earthwork':2,'existing_pavement':3,'pavement':4,'shoulder':5,'oae':6,'median':7,'barrier':8}
PAVED=('pavement','existing_pavement','shoulder','oae')
# Pares em que a sobreposição é esperada e não gera alerta.
EXPECTED_OVERLAP={frozenset(p) for p in [('pavement','existing_pavement'),('pavement','shoulder'),('existing_pavement','shoulder'),('oae','pavement'),('oae','existing_pavement'),('oae','shoulder'),('median','pavement'),('median','existing_pavement'),('domain','pavement'),('domain','existing_pavement'),('domain','shoulder'),('domain','oae'),('domain','median'),('domain','cut'),('domain','fill'),('domain','water'),('water','oae')]}
SOFT=('earthwork','cut','fill','water','domain')   # base natural: o que estiver por cima prevalece sem alerta
VOID_MAX_M=6.0   # vazios até 6 m entre hachuras de pavimento são reportados
JOINT_M=1.0      # lacuna <= 1 m entre hachuras do mesmo papel é tratada como junta
MIN_AREA=0.05

def _poly(e):
    pts=np.asarray(e['points'],float)
    if len(pts)<3:return None
    try:
        p=make_valid(Polygon(pts,[np.asarray(h,float) for h in e.get('holes',[]) if len(h)>=3]))
    except Exception:return None
    return None if p.is_empty else p

def _area_geoms(g):
    if g.is_empty:return []
    if g.geom_type in ('Polygon','MultiPolygon'):return list(g.geoms) if g.geom_type=='MultiPolygon' else [g]
    return [x for part in getattr(g,'geoms',[]) for x in _area_geoms(part)]

def analyze_coverage(entities,max_gap_report=40):
    by={}
    degenerate=[]
    for e in entities:
        if not e.get('closed') or e.get('role') in (None,'axis','edge_line','ignore'):continue
        p=_poly(e)
        if p is None or p.area<MIN_AREA:
            degenerate.append({'layer':e.get('layer'),'role':e.get('role')});continue
        by.setdefault(e['role'],[]).append(p)
    merged={r:unary_union(ps) for r,ps in by.items()}
    areas={r:round(float(g.area),1) for r,g in merged.items()}
    overlaps=[];roles=sorted(merged,key=lambda r:PRIORITY.get(r,0))
    for i,a in enumerate(roles):
        for b in roles[i+1:]:
            inter=merged[a].intersection(merged[b])
            m2=float(inter.area)
            if m2>1.0:
                low,high=a,b   # b tem prioridade maior
                overlaps.append({'under':low,'over':high,'area_m2':round(m2,1),'expected':frozenset((a,b)) in EXPECTED_OVERLAP or a in SOFT,
                                 'bounds':[round(float(v),1) for v in inter.bounds]})
    joints=[];voids=[]
    paved=unary_union([merged[r] for r in PAVED if r in merged]) if any(r in merged for r in PAVED) else None
    if paved is not None and not paved.is_empty:
        closed=paved.buffer(VOID_MAX_M/2,join_style=2).buffer(-VOID_MAX_M/2,join_style=2)
        gaps=closed.difference(paved)
        for g in _area_geoms(gaps):
            if g.area<0.02:continue
            w=2*g.area/max(g.length,1e-6)   # largura equivalente
            (joints if w<=JOINT_M else voids).append({'area_m2':round(float(g.area),2),'width_m':round(float(w),2),'at':[round(float(g.centroid.x),1),round(float(g.centroid.y),1)]})
    alerts=[]
    for o in overlaps:
        if not o['expected']:alerts.append({'code':'sobreposicao','text':f"{o['area_m2']} m² de {o['over']} sobre {o['under']}: prevalece {o['over']}.",'at':o['bounds']})
    if degenerate:alerts.append({'code':'degenerada','text':f'{len(degenerate)} hachura(s) degenerada(s) ignorada(s).'})
    if joints:alerts.append({'code':'juntas','text':f'{len(joints)} junta(s) estreita(s) entre hachuras de pavimento; o fluxo as fecha automaticamente.'})
    if voids:alerts.append({'code':'vazios','text':f'{len(voids)} vazio(s) largo(s) no pavimento: o fluxo os trata como impedimento.'})
    if not any(r in merged for r in PAVED):alerts.append({'code':'sem_pavimento','text':'Sem hachura de pavimento: o vídeo não apresentará veículos (sem erro).'})
    return {'areas_m2':areas,'overlaps':overlaps,'joints':joints[:max_gap_report],'voids':voids[:max_gap_report],'degenerate':len(degenerate),'alerts':alerts,
            'summary':{'roles':len(merged),'joints':len(joints),'voids':len(voids),'unexpected_overlaps':sum(1 for o in overlaps if not o['expected'])}}

def coverage_raster(entities,bounds,cell_m=2.0,max_cells=1_000_000):
    """Matriz uint8 com o código do papel de maior prioridade em cada célula (0 = sem hachura)."""
    x0,y0,x1,y1=bounds;nx=max(1,int(np.ceil((x1-x0)/cell_m)));ny=max(1,int(np.ceil((y1-y0)/cell_m)))
    while nx*ny>max_cells:cell_m*=1.5;nx=max(1,int(np.ceil((x1-x0)/cell_m)));ny=max(1,int(np.ceil((y1-y0)/cell_m)))
    from matplotlib.path import Path as MPath
    codes={r:i+1 for i,r in enumerate(sorted(PRIORITY,key=lambda r:PRIORITY[r]))}
    grid=np.zeros((ny,nx),np.uint8)
    xs=x0+(np.arange(nx)+.5)*cell_m;ys=y0+(np.arange(ny)+.5)*cell_m
    items=sorted((e for e in entities if e.get('closed') and e.get('role') in codes),key=lambda e:PRIORITY[e['role']])
    for e in items:
        pts=np.asarray(e['points'],float)
        if len(pts)<3:continue
        a,b,c,d=pts[:,0].min(),pts[:,1].min(),pts[:,0].max(),pts[:,1].max()
        i0=max(0,int((a-x0)/cell_m)-1);i1=min(nx,int((c-x0)/cell_m)+2);j0=max(0,int((b-y0)/cell_m)-1);j1=min(ny,int((d-y0)/cell_m)+2)
        if i1<=i0 or j1<=j0:continue
        X,Y=np.meshgrid(xs[i0:i1],ys[j0:j1]);P=np.c_[X.ravel(),Y.ravel()]
        inside=MPath(pts).contains_points(P)
        for h in e.get('holes',[]):
            if len(h)>=3:inside&=~MPath(np.asarray(h,float)).contains_points(P)
        sub=grid[j0:j1,i0:i1];sub[inside.reshape(sub.shape)]=codes[e['role']]
    return grid,codes,cell_m
