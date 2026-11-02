"""2.69: ocultação reversível de intervalos de traços DXF, sem editar o modelo físico."""
import hashlib,json,math
from pathlib import Path
import numpy as np


def path(points,closed=False):
    p=np.asarray(points,float)
    if p.ndim!=2 or p.shape[1]!=2 or len(p)<2 or not np.isfinite(p).all():raise ValueError('Linha inválida para TRIM.')
    keep=np.r_[True,np.linalg.norm(np.diff(p,axis=0),axis=1)>1e-9];p=p[keep]
    if closed and np.linalg.norm(p[0]-p[-1])>1e-8:p=np.vstack([p,p[:1]])
    if len(p)<2:raise ValueError('Linha sem comprimento para TRIM.')
    ds=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    if ds[-1]<1e-6:raise ValueError('Linha degenerada para TRIM.')
    return p,ds


def source_id(e,ring=0):
    rings=[e['points']]+list(e.get('holes',[]));p,ds=path(rings[ring],bool(e.get('closed')))
    # A ordem é parte da identidade porque as distâncias são medidas desde o primeiro vértice.
    data=[str(e.get('overlay','base')),str(e.get('layer','')),int(ring),np.round(p,6).tolist()]
    return 'trim-'+hashlib.sha256(json.dumps(data,separators=(',',':')).encode()).hexdigest()[:40]


def source_ids(e):
    out=[]
    for j in range(1+len(e.get('holes',[]))):
        try:out.append(source_id(e,j))
        except ValueError:out.append('')
    return out


def merge_intervals(cuts,length):
    ranges=[]
    for cut in cuts:
        a=float(cut.start_m if hasattr(cut,'start_m') else cut['start_m']);b=float(cut.end_m if hasattr(cut,'end_m') else cut['end_m'])
        if not np.isfinite([a,b]).all() or a<0 or b<=a or b>length+1e-4:raise ValueError('Intervalo TRIM incompatível com a linha de origem.')
        ranges.append((max(0,a),min(length,b)))
    merged=[]
    for a,b in sorted(ranges):
        if merged and a<=merged[-1][1]+1e-8:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
        else:merged.append((a,b))
    return merged


def at(p,ds,s):
    s=float(np.clip(s,0,ds[-1]));i=min(len(ds)-2,max(0,int(np.searchsorted(ds,s,side='right'))-1));return p[i]+(p[i+1]-p[i])*(s-ds[i])/(ds[i+1]-ds[i])


def visible(points,closed=False,cuts=()):
    p,ds=path(points,closed);hidden=merge_intervals(cuts,float(ds[-1]));parts=[];cursor=0.
    for a,b in hidden+[(float(ds[-1]),float(ds[-1]))]:
        if a-cursor>1e-8:
            inner=p[(ds>cursor+1e-8)&(ds<a-1e-8)];parts.append(np.vstack([at(p,ds,cursor),inner,at(p,ds,a)]))
        cursor=max(cursor,b)
    return parts


def annotate(items,settings):
    if not settings.dxf_line_trims:return items,[]
    groups={}
    for cut in settings.dxf_line_trims:
        if cut.enabled:groups.setdefault(cut.source_id,[]).append(cut)
    result=[];found=set()
    for e in items:
        clone=dict(e);ranges={};ids=[]
        for i,ring in enumerate([e['points']]+list(e.get('holes',[]))):
            try:sid=source_id(e,i)
            except ValueError:ids.append('');continue
            ids.append(sid)
            if sid in groups:
                _,ds=path(ring,bool(e.get('closed')))
                try:ranges[i]=merge_intervals(groups[sid],float(ds[-1]));found.add(sid)
                except ValueError:pass  # origem incompatível fica preservada e é diagnosticada
        clone['_trim_ids']=ids;clone['_trim_ranges']=ranges;result.append(clone)
    return result,sorted(set(groups)-found)


def runs(e,ring=0):
    points=([e['points']]+list(e.get('holes',[])))[ring];cuts=e.get('_trim_ranges',{}).get(ring,[])
    if not cuts:
        try:p,_=path(points,bool(e.get('closed')))
        except ValueError:return []
        return [p]
    return visible(points,bool(e.get('closed')),[{'start_m':a,'end_m':b} for a,b in cuts])


def display_items(items):
    out=[]
    for e in items:
        if e.get('closed') or not e.get('_trim_ranges'):out.append(e);continue
        for p in runs(e):out.append({**e,'points':p,'_trim_ranges':{}})
    return out


def vector_stations(raw,simplified,closed=False):
    p,ds=path(raw,closed);result=[];cursor=0
    for q in np.asarray(simplified,float):
        while cursor<len(p)-1 and np.linalg.norm(p[cursor]-q)>1e-7:cursor+=1
        if np.linalg.norm(p[cursor]-q)>1e-7:raise ValueError('Simplificação alterou a ordem da linha.')
        result.append(float(ds[cursor]));cursor=min(len(p)-1,cursor+1)
    return result,float(ds[-1])


def context(directory):
    from .dependencies import digest,engine_geometria,input_stamps
    from .models import Settings
    f=Path(directory)/'config.json';s=Settings.model_validate_json(f.read_text(encoding='utf-8-sig')) if f.exists() else Settings()
    # Só parâmetros que mudam as fontes selecionáveis: câmera, tráfego e cadastros
    # desativados não podem invalidar uma linha CAD que continua idêntica.
    data=s.model_dump();keys=('crs','units_to_m','dxf_alignment','overlays','hatch_roles','hatch_auto','layer_split','custom_axis')
    selected={k:data.get(k) for k in keys}
    selected['layers']={role:sorted(names) for role,names in s.layers.items()}
    selected['hidden_layers']=sorted(s.hidden_layers);selected['frozen_layers']=sorted(s.frozen_layers)
    selected['pavement_areas']=[a for a in data.get('pavement_areas',[]) if a.get('enabled',True)]
    selected['shoulder_marks']=[a for a in data.get('shoulder_marks',[]) if a.get('enabled',True)]
    return digest([engine_geometria(),input_stamps(directory)[0],selected])


def pick(directory,x,y,tol=5,include_hidden=False):
    from .webmap import _lines,_dist
    from .models import Settings
    if not np.isfinite([x,y,tol]).all() or tol<=0 or tol>200:raise ValueError('Coordenadas ou tolerância inválidas.')
    data=_lines(directory)
    if data.get('trim_context')!=context(directory):raise ValueError('Atualize o projeto antes do TRIM: a seleção está ausente ou desatualizada.')
    f=Path(directory)/'config.json';s=Settings.model_validate_json(f.read_text(encoding='utf-8-sig')) if f.exists() else Settings();groups={}
    for cut in s.dxf_line_trims:
        if cut.enabled:groups.setdefault(cut.source_id,[]).append(cut)
    point=np.array([x,y]);best=None;B=data['box'];indices=np.flatnonzero((B[:,0]-tol<=x)&(B[:,2]+tol>=x)&(B[:,1]-tol<=y)&(B[:,3]+tol>=y))
    for i in indices:
        rings=[data['lines'][i]]+list(data['holes'][i]);ids=data['trim_ids'][i]
        for j,ring in enumerate(rings):
            if j>=len(ids) or not ids[j]:continue
            try:p,ds=path(ring,bool(data['closed'][i]));parts=[p] if include_hidden else visible(p,False,groups.get(ids[j],[]))
            except ValueError:continue
            dist=min((_dist(part,point)[0] for part in parts),default=math.inf)
            if dist<=tol and (best is None or dist<best[0]):best=(dist,int(i),j,p,ds,ids[j])
    if best is None:return None
    distance,i,j,p,ds,sid=best
    if len(p)>50000:raise ValueError('Linha muito detalhada: divida o desenho antes de usar TRIM.')
    return {'source_id':sid,'ring':j,'points':p.tolist(),'stations':ds.tolist(),'length_m':float(ds[-1]),'layer':data['names'][int(data['lay'][i])],'role':data['roles'][i],'closed':bool(data['closed'][i]),'distance_m':distance,'context':data['trim_context']}
