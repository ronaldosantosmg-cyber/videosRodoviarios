"""1.20: áreas de pavimento marcadas no editor (pista nova, pista existente, acostamento) e acostamentos por
início/fim/largura. Viram entidades do projeto, com a hachura/cor do tipo, e "vencem" a classificação do DXF
dentro da área marcada (a área é retirada das outras superfícies). O DXF não é alterado.
"""
import numpy as np
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import unary_union,substring,linemerge

SURF_ROLES=('pavement','existing_pavement','shoulder')
LABEL={'pavement':'pista nova','existing_pavement':'pista existente','shoulder':'acostamento'}

TEX_CODE0=32   # 1.27: códigos de superfície 32.. = áreas com textura própria

def tex_of(a):
    t=getattr(a,'texture',None)
    if t is None:return None
    d=t.model_dump() if hasattr(t,'model_dump') else dict(t)
    return None if (d.get('grao',1),d.get('tom',1),d.get('remendos',1),d.get('fissuras',1),d.get('brilho',0))==(1,1,1,1,0) else d

def _xy(p):return (p.x,p.y) if hasattr(p,'x') else (p['x'],p['y'])

def _polys(g):
    if g is None or g.is_empty:return []
    return [x for x in (list(g.geoms) if hasattr(g,'geoms') else [g]) if x.geom_type=='Polygon' and x.area>.05]

def _entity_poly(e):
    try:return Polygon(e['points'],holes=e.get('holes',[])).buffer(0)
    except Exception:return None

def shoulder_band(m,paved):
    """Faixa de largura m.width_m ao longo do bordo da pista entre os pontos de início e fim."""
    if paved is None or paved.is_empty:raise ValueError(f'Acostamento “{m.name}”: o projeto não tem pavimento.')
    a=Point(*_xy(m.start));b=Point(*_xy(m.end))
    rings=[]
    for p in _polys(paved):rings+=[LineString(p.exterior.coords)]+[LineString(r.coords) for r in p.interiors]
    best=None
    for r in rings:
        da=r.distance(a);db=r.distance(b)
        if max(da,db)<=15 and (best is None or da+db<best[0]):best=(da+db,r)
    if best is None:raise ValueError(f'Acostamento “{m.name}”: início e fim devem ficar junto ao mesmo bordo da pista (até 15 m).')
    r=best[1];sa=r.project(a);sb=r.project(b);L=r.length
    lo,hi=sorted((sa,sb))
    # Anel fechado: usa o trecho mais curto entre os dois pontos.
    if r.is_ring and hi-lo>L/2:
        seg=linemerge([substring(r,hi,L),substring(r,0,lo)])
    else:seg=substring(r,lo,hi)
    if seg.is_empty or seg.length<1:raise ValueError(f'Acostamento “{m.name}”: início e fim muito próximos.')
    band=seg.buffer(float(m.width_m),cap_style=2,join_style=2).intersection(paved)
    return _polys(band)

def items(settings,entities,warnings):
    """Acrescenta as superfícies marcadas e retira essas áreas das outras superfícies do projeto."""
    areas=[a for a in getattr(settings,'pavement_areas',[]) or [] if a.enabled and len(a.points)>=3]
    shoulders=[m for m in getattr(settings,'shoulder_marks',[]) or [] if m.enabled]
    if not areas and not shoulders:return entities
    surf=[e for e in entities if e['closed'] and e['role'] in SURF_ROLES and len(e['points'])>=3]
    paved=unary_union([g for g in (_entity_poly(e) for e in surf) if g is not None]) if surf else None
    marks=[]  # (role, polígonos, nome, id)
    for a in areas:
        g=Polygon([_xy(p) for p in a.points]).buffer(0)
        if g.is_empty or g.area<.5:warnings.append(f'Área “{a.name}”: contorno inválido ou pequeno demais.');continue
        marks.append((a.kind,_polys(g),a.name,a.id or a.name,getattr(a,'material','auto'),tex_of(a)))
    for m in shoulders:
        try:marks.append(('shoulder',shoulder_band(m,paved),m.name,m.id or m.name,'auto',None))
        except ValueError as e:warnings.append(str(e))
    if not marks:return entities
    cut=unary_union([p for _,ps,_,_,_,_ in marks for p in ps])
    out=[];sid={id(e) for e in surf}
    for e in entities:
        if id(e) in sid:
            g=_entity_poly(e)
            if g is not None and g.intersects(cut):
                rest=_polys(g.difference(cut))
                for p in rest:out.append({**e,'points':np.asarray(p.exterior.coords),'holes':[np.asarray(h.coords) for h in p.interiors]})
                continue
        out.append(e)
    # A marcação mais recente prevalece sobre as anteriores na sobreposição.
    later=None
    from .pavement import default_material
    code=TEX_CODE0;codes={}
    for role,ps,name,mid,mat,tex in marks:
        if tex is not None and code<TEX_CODE0+200:codes[mid]=code;code+=1
    for role,ps,name,mid,mat,tex in reversed(marks):
        for p in ps:
            q=p.difference(later) if later is not None else p
            for x in _polys(q):
                ent={'layer':f'{LABEL[role].upper()} · {name}','role':role,'closed':True,'points':np.asarray(x.exterior.coords),'holes':[np.asarray(h.coords) for h in x.interiors],'mark':mid,'material':mat if mat!='auto' else default_material(settings,role)}
                if mid in codes:ent['tex_code']=codes[mid];ent['tex_base']=3 if ent['material']=='rigido' else {'pavement':1,'existing_pavement':2,'shoulder':4}[role];ent['tex_p']=tex
                out.append(ent)
        u=unary_union(ps) if ps else None
        later=u if later is None else (later.union(u) if u is not None else later)
    return out
