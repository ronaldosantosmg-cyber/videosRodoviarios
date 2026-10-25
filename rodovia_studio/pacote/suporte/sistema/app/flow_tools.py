"""Cortes explícitos e junções validadas, sem modificar as fontes CAD."""
import numpy as np
from shapely.geometry import LineString,Point
from shapely.ops import substring
from .vehicle_motion import prepare_points,analyze_motion


def cut_raw_paths(raw,cuts,tolerance=6.,overrides=()):
    intervals={};reports=[];disabled_owners={}
    # Uma marca removida pelo próprio corte não pode reativar o restante da origem.
    for override in overrides:
        if not override.enabled or override.action!='disable':continue
        point=Point(override.x,override.y);best=None
        for i,r in enumerate(raw):
            if override.target_key and override.target_key!=r.get('origin_key'):continue
            line=LineString(r['points']);distance=line.distance(point)
            if distance<=tolerance and (best is None or distance<best[0]):best=(distance,i,line.project(point))
        if best is not None:disabled_owners.setdefault(best[1],[]).append((best[2],{'id':override.id,'x':override.x,'y':override.y,'target_key':override.target_key}))
    for cut in cuts:
        if not cut.enabled:continue
        a,b=Point(cut.start.x,cut.start.y),Point(cut.end.x,cut.end.y);best=None
        for i,r in enumerate(raw):
            if cut.target_key and cut.target_key!=r.get('origin_key'):continue
            ln=LineString(r['points']);distance=max(ln.distance(a),ln.distance(b))
            if distance<=tolerance and (best is None or distance<best[0]):best=(distance,i,ln)
        if best is None:reports.append({'id':cut.id,'status':'unmatched'});continue
        _,i,ln=best;x,y=sorted([ln.project(a),ln.project(b)])
        if y-x<.1:reports.append({'id':cut.id,'status':'degenerate'});continue
        intervals.setdefault(i,[]).append((x,y));reports.append({'id':cut.id,'status':'applied','excluded_m':y-x})
    out=[]
    for i,r in enumerate(raw):
        if i not in intervals:out.append(r);continue
        ln=LineString(r['points']);merged=[]
        for a,b in sorted(intervals[i]):
            if merged and a<=merged[-1][1]:merged[-1][1]=max(b,merged[-1][1])
            else:merged.append([a,b])
        protected_refs=[ref for station,ref in disabled_owners.get(i,[]) if any(a-.01<=station<=b+.01 for a,b in merged)]
        protected=[ref['id'] for ref in protected_refs]
        cursor=0.;run=0
        for a,b in merged+[[ln.length,ln.length]]:
            if a-cursor>=.1:
                points=np.asarray(substring(ln,cursor,a).coords)
                out.append({**r,'points':points,'cut_run':run,'explicit_cut':True,'cut_disable_ids':protected,'cut_disable_refs':protected_refs});run+=1
            cursor=max(cursor,b)
    return out,reports


def join_segments(first,second,allowed,minimum=50.):
    a,_=prepare_points(first['points']);b,_=prepare_points(second['points'])
    if not first.get('both') and not first.get('forward',True):a=a[::-1]
    if not second.get('both') and not second.get('forward',True):b=b[::-1]
    candidates=[(x,y) for x in ([a,a[::-1]] if first.get('both') else [a]) for y in ([b,b[::-1]] if second.get('both') else [b])]
    a,b=min(candidates,key=lambda pair:np.linalg.norm(pair[0][-1]-pair[1][0]))
    gap=float(np.linalg.norm(b[0]-a[-1]))
    if gap>20:raise ValueError('As pontas estão a mais de 20 m. Ajuste os segmentos antes de juntar.')
    if first.get('level',0)!=second.get('level',0):raise ValueError('Segmentos em níveis diferentes não podem ser unidos em planta.')
    if gap>.01:
        ta=a[-1]-a[-2];ta/=max(np.linalg.norm(ta),1e-9);tb=b[1]-b[0];tb/=max(np.linalg.norm(tb),1e-9)
        u=np.linspace(0,1,max(8,int(gap/.3)))[:,None];pa=a[-1];pb=b[0]
        bridge=(1-u)**3*pa+3*(1-u)**2*u*(pa+ta*gap*.4)+3*(1-u)*u**2*(pb-tb*gap*.4)+u**3*pb
        points=np.vstack([a,bridge[1:-1],b])
    else:points=np.vstack([a,b[1:]])
    points,d=prepare_points(points)
    if len(points)>20000:raise ValueError('Junção excede 20.000 vértices; divida a edição.')
    if d[-1]<minimum:raise ValueError('O fluxo unido permanece abaixo do limite do projeto.')
    audit=analyze_motion(points,allowed=allowed)
    if not audit['ok']:return {'ok':False,'audit':audit,'at':audit.get('front_xy'),'reason':audit['message']}
    return {'ok':True,'points':points.tolist(),'length_m':float(d[-1]),'gap_m':gap,'level':first.get('level',0),'join_from':a[-1].tolist(),'join_to':b[0].tolist(),'join_from_heading':((a[-1]-a[-2])/np.linalg.norm(a[-1]-a[-2])).tolist(),'join_to_heading':((b[1]-b[0])/np.linalg.norm(b[1]-b[0])).tolist()}
