"""Marcações do usuário (camadas do projeto, nunca gravadas no DXF), em coordenadas do CRS."""
import numpy as np
import shapely
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import unary_union
from .chainage import Stationing,fmt

MATCH_M=6.

def _xy(p):return (p.x,p.y) if hasattr(p,'x') else (p['x'],p['y'])

def zones_geometry(zones):
    """União dos cruzamentos sem conexão (ponto com raio ou área)."""
    shapes=[]
    for z in zones:
        if z.kind=='point':shapes.append(Point(*_xy(z.point)).buffer(z.radius_m))
        elif len(z.points)>=3:shapes.append(Polygon([_xy(p) for p in z.points]).buffer(0))
    return unary_union(shapes) if shapes else Polygon()

def deck_geometry(points):
    """Polígono do tabuleiro (válido, maior parte), eixo longitudinal, largura e guarda-corpos pelas bordas longitudinais."""
    from shapely import make_valid
    g=make_valid(Polygon(points))
    polys=[v for v in (list(g.geoms) if hasattr(g,'geoms') else [g]) if v.geom_type=='Polygon' and v.area>1]
    if not polys:raise ValueError('Polígono da OAE inválido (área nula).')
    g=max(polys,key=lambda v:v.area)
    rect=np.asarray(g.minimum_rotated_rectangle.exterior.coords)[:4]
    e1=rect[1]-rect[0];e2=rect[2]-rect[1]
    u=e1 if np.linalg.norm(e1)>=np.linalg.norm(e2) else e2;u=u/max(np.linalg.norm(u),1e-9);n=np.array([-u[1],u[0]])
    ring=np.asarray(g.exterior.coords);proj=(ring-np.asarray(g.centroid.coords[0]))@u
    c=np.asarray(g.centroid.coords[0]);lo,hi=proj.min(),proj.max()
    if hi-lo<1:raise ValueError('OAE com menos de 1 m de extensão.')
    centers=[];widths=[]
    for t in np.linspace(lo+.02*(hi-lo),hi-.02*(hi-lo),24):
        base=c+u*t;seg=LineString([base-n*500,base+n*500]).intersection(g)
        parts=[v for v in (getattr(seg,'geoms',None) or [seg]) if v.geom_type=='LineString' and v.length>.1]
        if not parts:continue
        v=max(parts,key=lambda v:v.length);a,b=np.asarray(v.coords)[[0,-1]];centers.append((a+b)/2);widths.append(v.length)
    if len(centers)<2:raise ValueError('Não foi possível obter o eixo da OAE desenhada.')
    line=np.asarray(centers)
    # Estende o eixo até as cabeceiras (bordas transversais).
    line[0]=line[0]-u*.02*(hi-lo);line[-1]=line[-1]+u*.02*(hi-lo)
    rails=[];cur=[]
    for a,b in zip(ring[:-1],ring[1:]):
        d=b-a;L=np.linalg.norm(d)
        if L<1e-6:continue
        if abs(float(np.dot(d/L,u)))>.7:
            if not cur:cur=[a]
            cur.append(b)
        elif cur:rails.append(np.array(cur));cur=[]
    if cur:rails.append(np.array(cur))
    if len(rails)>1 and np.allclose(rails[0][0],rails[-1][-1],rtol=0,atol=1e-6):rails=[np.vstack([rails[-1],rails[0][1:]])]+rails[1:-1]
    heads=[]
    for a,b in zip(ring[:-1],ring[1:]):
        d=b-a;L=np.linalg.norm(d)
        if L>1 and abs(float(np.dot(d/L,u)))<.5:heads.append(np.array([a,b]))
    return g,line,float(np.median(widths)),rails,heads

def oae_items(settings,stationing):
    """OAE marcada por dois pontos sobre o eixo (trecho do eixo entre as projeções) ou por vértices (polígono)."""
    out=[]
    for m in settings.oae_marks:
        if getattr(m,'polygon',None) and len(m.polygon)>=4:
            try:deck,line,width,rails,heads=deck_geometry([_xy(p) for p in m.polygon])
            except ValueError:continue
            ka0=float(stationing.km(line[0]));kb0=float(stationing.km(line[-1]))
            if kb0<ka0:line=line[::-1];ka0,kb0=kb0,ka0
            ka=m.km_start_override_m if m.km_start_override_m is not None else ka0
            kb=m.km_end_override_m if m.km_end_override_m is not None else kb0
            mid=np.array(LineString(line).interpolate(.5,normalized=True).coords[0])
            ch=sorted([stationing.chain(ka0),stationing.chain(kb0)])
            out.append({'id':m.id or 'oae','name':m.name,'line':line,'deck':deck,'level_m':m.level_m,'width_m':width,
                        'km_start_m':float(ka),'km_end_m':float(kb),'km_auto':[ka0,kb0],'mid':mid,'callout':m.callout,'chain':ch,
                        'rails':rails,'heads':heads,'direction':getattr(m,'direction','both'),'polygon':True})
            continue
        a=stationing.km(_xy(m.start));b=stationing.km(_xy(m.end))
        if b<a:a,b=b,a
        if b-a<1:continue
        line=stationing.substring(a,b)
        if line.length<1:continue
        ka=m.km_start_override_m if m.km_start_override_m is not None else a
        kb=m.km_end_override_m if m.km_end_override_m is not None else b
        deck=line.buffer(m.width_m/2,cap_style='flat',join_style='round')
        mid=np.array(line.interpolate(.5,normalized=True).coords[0])
        out.append({'id':m.id or 'oae','name':m.name,'line':np.asarray(line.coords),'deck':deck,'level_m':m.level_m,'width_m':m.width_m,
                    'km_start_m':float(ka),'km_end_m':float(kb),'km_auto':[float(a),float(b)],'mid':mid,'callout':m.callout,
                    'chain':[stationing.chain(a),stationing.chain(b)],'direction':getattr(m,'direction','both')})
    return out

def oae_direction_marks(items,stationing):
    """Sentido escolhido na OAE: [(tabuleiro, sinal no encadeamento do eixo)]. Crescente = sentido do km."""
    out=[]
    for o in items:
        d=o.get('direction','both')
        if d=='both':continue
        out.append((o['deck'],stationing.direction*(1 if d=='growing' else -1)))
    return out

def oae_pois(items):
    return [{'id':'oae-'+o['id'],'title':o['name'],'subtitle':f"OAE • km {fmt(o['km_start_m'])} a km {fmt(o['km_end_m'])}",'kind':'oae','x':float(o['mid'][0]),'y':float(o['mid'][1]),'km_m':None,'km_mode':'manual','anchor':None,'source':'oae_mark'} for o in items if o['callout']]

def validate_path(points,roads,obstacles,exclusions,allowed,vehicle=(4.6,1.9)):
    """Valida um fluxo desenhado. Retorna {'ok':bool,'reason':str,'at':[x,y]|None}."""
    from .traffic import sample,valid_centers
    p=np.asarray([_xy(v) for v in points],float)
    if len(p)<2:return {'ok':False,'reason':'Marque ao menos dois pontos.','at':None}
    q,ss=sample(p,.6)
    if ss[-1]<5:return {'ok':False,'reason':'Trajetória curta demais (mínimo 5 m).','at':None}
    xs,ys=q[:,0],q[:,1]
    def first(mask,reason):
        i=int(np.flatnonzero(mask)[0]);return {'ok':False,'reason':reason,'at':q[i].tolist()}
    if roads is None or roads.is_empty:return {'ok':False,'reason':'Não há pavimento no projeto: gere a prévia com as camadas de pavimento associadas.','at':None}
    out=~shapely.contains_xy(roads,xs,ys)
    if out.any():return first(out,'Fora do pavimento: a trajetória sai da superfície de pavimento/OAE do projeto.')
    if obstacles is not None and not obstacles.is_empty:
        hit=shapely.contains_xy(obstacles.buffer(.15),xs,ys)
        if hit.any():return first(hit,'Atravessa canteiro ou barreira.')
    if exclusions is not None and not exclusions.is_empty:
        hit=shapely.contains_xy(exclusions,xs,ys)
        if hit.any():return first(hit,'Passa por área de exclusão (limpeza).')
    ok=valid_centers(allowed,q,*vehicle)
    if not ok.all():return first(~ok,'O veículo não cabe nesse ponto: muito próximo da borda, do canteiro ou da barreira.')
    return {'ok':True,'reason':'Trajetória válida: dentro do pavimento e fora de canteiros, barreiras e exclusões.','at':None,'length_m':float(ss[-1])}

def assign(paths,overrides,marks):
    """Associa cada override/seta ao único trecho mais próximo (até MATCH_M).
    Evita que um clique numa pista afete a pista paralela do outro lado do canteiro."""
    from .traffic import tangent
    lines=[LineString(p) if len(p)>1 else Point(p[0]) for p in paths]
    out={i:{'reverse':False,'disable':False,'arrow':None,'override_ids':[]} for i in range(len(paths))}
    def nearest(xy,check=None):
        best=None
        for i,ln in enumerate(lines):
            d=ln.distance(Point(*xy))
            if d<=MATCH_M and (best is None or d<best[0]) and (check is None or check(i)):best=(d,i)
        return None if best is None else best[1]
    for o in overrides or []:
        if not o.enabled:continue
        i=nearest((o.x,o.y))
        if i is not None:
            if o.action=='speed':out[i]['speed_kmh']=getattr(o,'speed_kmh',None)
            else:out[i][o.action]=True
            out[i]['override_ids'].append(o.id)
    for m in marks or []:
        a=np.array(_xy(m.start));b=np.array(_xy(m.end));mid=(a+b)/2;v=(b-a)/max(np.linalg.norm(b-a),1e-9)
        def aligned(i):
            p=np.asarray(paths[i]);
            if len(p)<2:return False
            t=tangent(p);j=int(np.argmin(np.linalg.norm(p-mid,axis=1)));return abs(float(np.dot(t[j],v)))>=.5
        i=nearest(mid,aligned)
        if i is not None:
            p=np.asarray(paths[i]);t=tangent(p);j=int(np.argmin(np.linalg.norm(p-mid,axis=1)));out[i]['arrow']=bool(np.dot(t[j],v)>0)
    return out

def nearest_override(overrides,p,action):
    """Override habilitado mais próximo do segmento p (polilinha), até MATCH_M."""
    if not overrides:return None
    line=LineString(p) if len(p)>1 else Point(p[0])
    best=None
    for o in overrides:
        if not o.enabled or o.action!=action:continue
        d=line.distance(Point(o.x,o.y))
        if d<=MATCH_M and (best is None or d<best[0]):best=(d,o)
    return best[1] if best else None

def direction_for(marks,p,tangent):
    """Seta desenhada sobre o trecho: True se a seta segue a ordem dos vértices de p; None sem seta."""
    if not marks or len(p)<2:return None
    line=LineString(p);best=None
    for m in marks:
        a=np.array(_xy(m.start));b=np.array(_xy(m.end));mid=(a+b)/2
        d=line.distance(Point(*mid))
        if d>MATCH_M:continue
        # A seta deve estar alinhada com o trecho (não atravessá-lo).
        j=int(np.argmin(np.linalg.norm(p-mid,axis=1)));v=(b-a)/max(np.linalg.norm(b-a),1e-9)
        cos=float(np.dot(tangent[j],v))
        if abs(cos)<.5:continue
        if best is None or d<best[0]:best=(d,cos>0)
    return None if best is None else best[1]
