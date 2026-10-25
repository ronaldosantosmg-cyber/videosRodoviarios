"""Ajuste lateral derivado: reduzir afastamento sem inventar superfície ou ligações."""
import numpy as np
from shapely.geometry import LineString,Polygon


def physical_obstacles(items):
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
            if line.length>1e-6:result.append(line.buffer(.2))
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
