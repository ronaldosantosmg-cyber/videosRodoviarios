"""Aplicação de sentido por intervalo projetado no eixo; fonte CAD permanece intacta."""
import numpy as np
from shapely.geometry import LineString,Point
from shapely.ops import substring


def split_intervals(raw,marks,tolerance=6.):
    if not marks:return raw,[]
    lines=[LineString(r['points']) for r in raw];assigned={};report=[]
    for mark in marks:
        a=Point(mark.start.x,mark.start.y);b=Point(mark.end.x,mark.end.y);mid=Point((a.x+b.x)/2,(a.y+b.y)/2);candidates=[]
        for i,line in enumerate(lines):
            if max(line.distance(a),line.distance(b))>tolerance:continue
            sa,sb=line.project(a),line.project(b)
            if abs(sb-sa)<1:continue
            lo,hi=sorted((sa,sb));direction=np.array([b.x-a.x,b.y-a.y]);t=np.array(line.interpolate(min(line.length,(lo+hi)/2+1)).coords)[0]-np.array(line.interpolate(max(0,(lo+hi)/2-1)).coords)[0]
            cosine=abs(float(t@direction))/max(float(np.linalg.norm(t)*np.linalg.norm(direction)),1e-9)
            if cosine<.5 and max(line.distance(a),line.distance(b))>.5:continue
            candidates.append((line.distance(mid),max(line.distance(a),line.distance(b)),i,lo,hi,sb>sa))
        if not candidates:report.append({'id':mark.id,'status':'unmatched'});continue
        candidates.sort();best=candidates[0]
        # Duas pistas igualmente próximas exigem selecionar a linha explicitamente.
        if len(candidates)>1 and abs(candidates[1][0]-best[0])<.05 and abs(candidates[1][1]-best[1])<.05:
            report.append({'id':mark.id,'status':'ambiguous'});continue
        _,_,i,lo,hi,forward=best
        if hi-lo<5:
            report.append({'id':mark.id,'status':'intervalo_curto','minimum_m':5});continue
        if raw[i].get('node_oriented'):
            report.append({'id':mark.id,'status':'applied' if forward else 'node_conflict','forward':bool(forward),'origin_key':raw[i].get('origin_key',''),'reason':'Sentido definido pelos nós; marcação contraditória não altera o percurso.' if not forward else 'Marcação compatível com os nós, sem recortar novamente a faixa.'})
            continue
        assigned.setdefault(i,[]).append((lo,hi,forward,mark.id))
        report.append({'id':mark.id,'status':'applied','start_m':round(lo,3),'end_m':round(hi,3),'forward':bool(forward),'origin_key':raw[i].get('origin_key','')})
    result=[]
    for i,(r,line) in enumerate(zip(raw,lines)):
        intervals=assigned.get(i)
        if not intervals:result.append(r);continue
        cuts=sorted({0.,line.length,*[v for a,b,_,_ in intervals for v in (a,b)]})
        for lo,hi in zip(cuts,cuts[1:]):
            if hi-lo<1e-6:continue
            item={**r,'points':np.asarray(substring(line,lo,hi).coords)}
            matches=[interval for interval in intervals if interval[0]-1e-6<=(lo+hi)/2<=interval[1]+1e-6]
            if matches:item.update(explicit_direction=bool(matches[-1][2]),direction_mark_id=matches[-1][3])
            if r.get('route_dir') in ('f','r'):
                a=float(r['route_start_m']);b=float(r['route_end_m']);span=b-a
                stations=[a+span*v/line.length if r['route_dir']=='f' else b-span*v/line.length for v in (lo,hi)]
                item['route_start_m'],item['route_end_m']=sorted(stations)
                if item.get('explicit_direction') is False:item['route_dir']='r' if r['route_dir']=='f' else 'f'
            result.append(item)
    return result,report
