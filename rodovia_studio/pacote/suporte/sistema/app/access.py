"""1.18: acesso rodoviário desenhado no editor, com taper de entrada (desaceleração) e de saída (aceleração).

O operador marca o eixo do acesso a partir do bordo da pista. O programa gera o pavimento do acesso e os
tapers ao longo do bordo da pista principal, como áreas de 'pavimento' do projeto. Assim, sinalização,
bordos e fluxos de veículos saem pelo mesmo cálculo das demais pistas. O DXF não é alterado.
"""
import numpy as np
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union,nearest_points

def _xy(p):return (p.x,p.y) if hasattr(p,'x') else (p['x'],p['y'])

def _geoms(g):
    if g is None or g.is_empty:return []
    return [x for x in (list(g.geoms) if hasattr(g,'geoms') else [g]) if x.geom_type=='Polygon' and not x.is_empty]

def build(a,paved,axis):
    """Polígonos (acesso + tapers) de um acesso; levanta ValueError com motivo claro."""
    pts=np.array([_xy(p) for p in a.points],float)
    if len(pts)<2:raise ValueError(f'Acesso “{a.name}”: marque pelo menos dois pontos.')
    if paved is None or paved.is_empty:raise ValueError(f'Acesso “{a.name}”: o projeto não tem pavimento para ligar o acesso.')
    p0=Point(*pts[0]);edge=paved.boundary
    q=np.array(nearest_points(edge,p0)[0].coords[0])
    if np.linalg.norm(q-pts[0])>40:raise ValueError(f'Acesso “{a.name}”: o primeiro ponto deve ficar junto ao bordo da pista (está a {np.linalg.norm(q-pts[0]):.0f} m).')
    # Direção da pista no ponto de ligação (pelo eixo principal) e lado do acesso.
    ax=np.asarray(axis,float);k=int(np.argmin(np.linalg.norm(ax-q,axis=1)))
    t=ax[min(len(ax)-1,k+1)]-ax[max(0,k-1)];t/=max(np.linalg.norm(t),1e-9)
    out=pts[min(1,len(pts)-1)]-q;n_out=out-t*float(out@t);n_out/=max(np.linalg.norm(n_out),1e-9)
    right=float(t[0]*n_out[1]-t[1]*n_out[0])<0   # acesso à direita do sentido do eixo
    d=t if right else -t                # mão de direção: tráfego da pista do lado do acesso
    lw=float(a.lane_width_m);parts=[]
    # Pavimento do acesso: começa um pouco dentro da pista para fundir com ela.
    line=np.vstack([q-n_out*.5,pts[1:]]) if np.linalg.norm(pts[0]-q)<lw else np.vstack([q-n_out*.5,pts])
    parts.append(LineString(line).buffer(a.width_m/2,cap_style=2,join_style=2))
    def taper(sign,L):
        """sign=-1: antes da ligação (entrada/desaceleração); +1: depois (saída/aceleração)."""
        ss=np.linspace(0,L,max(3,int(L/4)+1));inner=[];outer=[]
        for s in ss:
            e=np.array(nearest_points(edge,Point(*(q+d*sign*s)))[0].coords[0])
            w=lw*(1-s/L)+.0;inner.append(e-n_out*.3);outer.append(e+n_out*max(w,.05))
        return Polygon(np.vstack([inner,outer[::-1]])).buffer(0)
    if a.mode in ('both','in') and a.taper_in_m>0:parts.append(taper(-1,float(a.taper_in_m)))
    if a.mode in ('both','out') and a.taper_out_m>0:parts.append(taper(1,float(a.taper_out_m)))
    # Concordância (raios) entre o acesso e os tapers.
    g=unary_union(parts).buffer(1.5,join_style=1).buffer(-1.5,join_style=1)
    return _geoms(g)

def items(settings,entities,axis,warnings):
    acc=[a for a in getattr(settings,'accesses',[]) or [] if a.enabled]
    if not acc:return []
    roads=[Polygon(e['points'],holes=e.get('holes',[])).buffer(0) for e in entities if e['closed'] and e['role'] in ('pavement','existing_pavement') and len(e['points'])>=3]
    paved=unary_union(roads) if roads else None;out=[]
    for a in acc:
        try:polys=build(a,paved,axis)
        except ValueError as e:warnings.append(str(e));continue
        for g in polys:
            out.append({'layer':'ACESSO · '+a.name,'role':'pavement','closed':True,'points':np.asarray(g.exterior.coords),'holes':[np.asarray(h.coords) for h in g.interiors],'access':a.id or a.name})
    return out
