"""Eixos CAD como fonte de circulação; junção derivada pequena e inequívoca."""
import math
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import LineString
from .vehicle_motion import prepare_points


def native_paths(axes, settings, allowed, tolerance=.25):
    if not math.isfinite(tolerance) or not 0<=tolerance<=.25:
        raise ValueError('Tolerância de junção inválida.')
    rows=[];invalid=0
    for i,axis in enumerate(axes):
        direction=settings.route_directions.get(str(i),'auto')
        if direction=='off':continue
        try:p,d=prepare_points(axis['points'])
        except (ValueError,TypeError,KeyError,OverflowError):invalid+=1;continue
        rows.append(dict(points=p.copy(),ids=[i],layer=str(axis.get('layer','')),
                         level=axis.get('level',0),direction=direction))
    if not rows:return [],dict(joined=0,invalid=invalid,max_gap_m=0.)
    endpoints=np.array([p for row in rows for p in row['points'][[0,-1]]])
    outward=np.array([v for row in rows for v in
                      (row['points'][0]-row['points'][1],row['points'][-1]-row['points'][-2])])
    outward/=np.linalg.norm(outward,axis=1)[:,None]
    tree=cKDTree(endpoints);counts=tree.query_ball_point(endpoints,tolerance,return_length=True)
    candidates={};cosine=math.cos(math.radians(10))
    protected=any(getattr(o,'target_key','') for name in ('flow_overrides','flow_cuts','flow_recoveries') for o in getattr(settings,name,[]))
    for e,point in enumerate(endpoints):
        if protected:continue  # Não combinar identidades que já possuem cortes/edições salvos.
        if counts[e]>16:continue  # Encontro ambíguo: não fabricar continuidade.
        row=rows[e//2];found=[]
        for other in tree.query_ball_point(point,tolerance):
            if other//2==e//2:continue
            peer=rows[other//2]
            if any(row[k]!=peer[k] for k in ('layer','level','direction')):continue
            if float(outward[e]@outward[other])>-cosine:continue
            gap=float(np.linalg.norm(point-endpoints[other]))
            # A pequena ponte só existe na derivação e precisa caber na pista.
            if gap>1e-6 and (allowed.is_empty or not allowed.covers(LineString([point,endpoints[other]]).buffer(.95))):continue
            found.append(other)
        if len(found)==1:candidates[e]=found[0]
    mates={e:o for e,o in candidates.items() if candidates.get(o)==e}
    seen=set();out=[];joined=0;max_gap=0.
    order=sorted(range(len(rows)),key=lambda i:sum(2*i+k in mates for k in (0,1)))
    for i in order:
        if i in seen:continue
        start=2*i if 2*i not in mates else 2*i+1
        current=start;parts=[];ids=[];base=rows[i]
        while current//2 not in seen:
            index=current//2;seen.add(index);row=rows[index]
            p=row['points'] if current%2==0 else row['points'][::-1]
            if parts:
                gap=float(np.linalg.norm(parts[-1][-1]-p[0]));max_gap=max(max_gap,gap);joined+=1
                if gap<1e-6:p=p[1:]
            parts.append(p);ids.extend(row['ids']);end=2*index+(1-current%2)
            if end not in mates:break
            current=mates[end]
            if current==start:
                if np.linalg.norm(parts[-1][-1]-parts[0][0])>1e-6:parts.append(parts[0][:1])
                break
        out.append(dict(points=np.vstack(parts),halfwidth=3.5,source=('Eixo KMZ · ' if base['layer']=='KMZ' else 'Eixo DXF · ')+','.join(str(v) for v in sorted(ids)),
                        level=base['level'],native_id=','.join(map(str,sorted(ids))),
                        native_axis=True,native_direction=base['direction'],native_joined=len(ids)-1))
    return out,dict(joined=joined,invalid=invalid,max_gap_m=round(max_gap,6))
