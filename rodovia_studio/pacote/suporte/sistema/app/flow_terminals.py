"""Recuo somente nos portais externos; conexões internas mantêm suas estações."""
import numpy as np
from shapely.geometry import LineString,Point
from shapely.ops import substring


def terminal_offsets(points,pavement,inset):
    p=np.asarray(points,float);line=LineString(p);length=line.length
    if pavement.is_empty or inset<0:return 0.,0.
    start=p[1]-p[0];end=p[-1]-p[-2]
    start/=max(float(np.linalg.norm(start)),1e-9);end/=max(float(np.linalg.norm(end)),1e-9)
    extension=max(30.,float(inset)+1)
    extended=LineString(np.vstack([p[0]-start*extension,p,p[-1]+end*extension]))
    hit=extended.intersection(pavement)
    def lines(g):
        if g.geom_type=='LineString':return [g]
        return [r for child in getattr(g,'geoms',[]) for r in lines(child)]
    intervals=[(extended.project(Point(g.coords[0])),extended.project(Point(g.coords[-1]))) for g in lines(hit) if g.length>.01]
    intervals=[(min(a,b),max(a,b)) for a,b in intervals]
    intervals=[(a,b) for a,b in intervals if b>extension and a<extension+length]
    if not intervals:return 0.,0.
    first=min(a for a,b in intervals);last=max(b for a,b in intervals)
    a=max(0.,first-extension+inset) if first>.01 else float(inset)
    b=max(0.,extension+length-last+inset) if last<extended.length-.01 else float(inset)
    return a,b


def inset_path(path,pavement,inset):
    from .traffic import sample,tangent
    p=path['p'];length=float(path['length']);a,b=terminal_offsets(p,pavement,inset)
    if a+b>=length-1:return None
    if a+b<1e-6:return {**path,'terminal_inset_applied':True,'terminal_offsets_m':[a,b]}
    clipped=np.asarray(substring(LineString(p),a,length-b).coords);q,d=sample(clipped)
    total=(path.get('links') or [(None,0.,length)])[-1][2] or length;ratio=length/total
    links=[];offsets=[]
    for (identity,start,end),offset in zip(path.get('links',[]),path.get('link_offsets',[])):
        lo=max(a,start*ratio);hi=min(length-b,end*ratio)
        if hi-lo<1e-6:continue
        links.append((identity,lo-a,hi-a));offsets.append(float(offset)+(lo-start*ratio))
    return {**path,'p':q,'t':tangent(q),'d':d,'length':float(d[-1]),'links':links,'link_offsets':offsets,'terminal_inset_applied':True,'terminal_offsets_m':[a,b]}
