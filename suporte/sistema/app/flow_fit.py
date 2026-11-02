"""Ajuste lateral derivado: reduzir afastamento sem inventar superfície ou ligações."""
import numpy as np
from shapely.geometry import LineString,Polygon


TRANSVERSE_MIN_DEG=60.


def crosses_transversally(line,axes,min_deg=TRANSVERSE_MIN_DEG):
    """True se a linha cruza algum eixo com ângulo >= min_deg (transversal ao sentido do eixo)."""
    for a in axes or ():
        try:q=np.asarray(a['points'] if isinstance(a,dict) else a,float)
        except (KeyError,TypeError,ValueError):continue
        if q.ndim!=2 or len(q)<2:continue
        axis=LineString(q);hit=line.intersection(axis)
        if hit.is_empty:continue
        pts=[g for g in (hit.geoms if hasattr(hit,'geoms') else [hit]) if g.geom_type=='Point']
        for pt in pts:
            d=axis.project(pt);d0,d1=max(0.,d-1.),min(axis.length,d+1.)
            if d1-d0<1e-6:continue
            ta=np.subtract(axis.interpolate(d1).coords[0],axis.interpolate(d0).coords[0])
            ld=line.project(pt);l0,l1=max(0.,ld-1.),min(line.length,ld+1.)
            if l1-l0<1e-6:continue
            tl=np.subtract(line.interpolate(l1).coords[0],line.interpolate(l0).coords[0])
            c=abs(float(ta@tl))/max(float(np.linalg.norm(ta)*np.linalg.norm(tl)),1e-12)
            if np.degrees(np.arccos(min(1.,c)))>=min_deg:return True
    return False


def physical_obstacles(items,axes=None):
    """Obstáculos físicos. Linhas ABERTAS transversais ao eixo só valem se forem canteiro; as demais são ignoradas."""
    result=[]
    for e in items:
        if e.get('role') not in ('barrier','median'):continue
        p=np.asarray(e.get('points',[]),float)
        if p.ndim!=2 or p.shape[1]!=2 or not np.isfinite(p).all():continue
        if e.get('closed') and len(p)>=3:
            polygon=Polygon(p,holes=e.get('holes',[])).buffer(0)
            if not polygon.is_empty:result.append(polygon)
        elif e.get('role')=='barrier' and len(p)>=2:
            line=LineString(p)
            if line.length>1e-6 and not crosses_transversally(line,axes):result.append(line.buffer(.2))
    return result


def fit_offset(q,normal,offset,allowed,both=False):
    from .traffic import valid_centers
    lane=q+normal*offset;valid=valid_centers(allowed,lane)
    initial=int(valid.sum());best=initial;chosen=float(offset)
    # Não sobrepor sentidos opostos; 1,8 m + 0,5 m livres entre dois carros.
    lower=1.2 if both else 0.
    if offset<=lower or valid.all():return lane,valid,None
    for value in np.linspace(offset,lower,6)[1:]:
        candidate=q+normal*value;mask=valid_centers(allowed,candidate)
        count=int(mask.sum())
        if count>best:
            lane,valid,best,chosen=candidate,mask,count,float(value)
        if mask.all():break
    report=None if chosen==offset else {'original_m':round(float(offset),3),'applied_m':round(chosen,3),'valid_before':initial,'valid_after':best,'samples':len(q),'strategy':'reduzir_afastamento_dentro_da_pista'}
    return lane,valid,report


SEAM_CLOSE_M=.4


def close_seams(merged,close_m=SEAM_CLOSE_M):
    """Junta de hachura: fresta estreita (< 2*close_m) entre polígonos de pavimento vizinhos deixa de ser vazio.
    Só preenche frestas finas; canteiros, ilhas e vazios largos continuam vazios. Nunca remove área."""
    if merged is None or merged.is_empty:return merged
    closed=merged.buffer(close_m,join_style='mitre',mitre_limit=2.).buffer(-close_m,join_style='mitre',mitre_limit=2.)
    gaps=closed.difference(merged)
    if gaps.is_empty:return merged
    pieces=[g for g in (gaps.geoms if hasattr(gaps,'geoms') else [gaps]) if g.geom_type=='Polygon' and g.area>1e-6 and 2*g.area/max(g.length,1e-9)<=close_m]
    if not pieces:return merged
    from shapely.ops import unary_union
    return unary_union([merged,*pieces])


def edge_guide(lines,axes=None,half=.08,boundary=None,tol=1.2,report=None):
    """Linhas de bordo de sinalização como guia lateral: o corpo do veículo não as atravessa. Linhas transversais ao eixo são ignoradas.
    1.42.43: com ``boundary`` (contorno do pavimento), só valem como guia as linhas que seguem esse contorno; uma linha interna à pista
    (contorno de hachura falso, divisão desenhada na layer de bordo) não vira parede e não interrompe o fluxo."""
    out=[]
    # 3.4: o contorno alargado é o mesmo para todas as linhas: calcula UMA vez (antes 927 buffers de ~30 ms = 30 s no trecho TH53)
    zona=boundary.buffer(tol) if boundary is not None and not boundary.is_empty else None
    if zona is not None:
        from shapely import prepare as _prep
        try:_prep(zona)
        except Exception:pass
    for p in lines or ():
        q=np.asarray(p,float)
        if q.ndim!=2 or q.shape[1]!=2 or len(q)<2 or not np.isfinite(q).all():continue
        ln=LineString(q)
        if ln.length<2. or crosses_transversally(ln,axes):continue
        if zona is not None:
            near=ln.intersection(zona).length/max(ln.length,1e-9)
            if near<.5:
                if report is not None:report['ignored']=report.get('ignored',0)+1
                continue
        out.append(ln.buffer(half,cap_style='flat'))
    if not out:return None
    from shapely.ops import unary_union
    return unary_union(out)
