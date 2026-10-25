"""Cena WebGL local derivada da geometria e da simulação validadas do projeto."""
from pathlib import Path
from collections import defaultdict
import hashlib,json,math
import numpy as np
import shapely
from shapely.geometry import Polygon
from .models import Settings
from .store import write_json

MAX_VERTICES=600000
MAX_TRAFFIC_SAMPLES=120000
PREVIEW_SECONDS=60.


def revision(directory,settings=None):
    from .dependencies import revisions
    return revisions(directory,settings)['scene3d']


def build(directory,settings,status=lambda *a:None,cancel=lambda:False):
    from .render import Scene
    from .simulation import TrafficSim
    from .vehicle_motion import PROFILES
    from . import visual
    from functools import partial
    settings=Settings.model_validate(settings.model_dump())
    d=Path(directory);key=revision(d,settings)
    if (d/'config.json').exists() and Settings.model_validate_json((d/'config.json').read_text()).model_dump()!=settings.model_dump():raise ValueError('A configuração mudou. Gere a cena novamente.')
    def progress(p,text):
        if cancel():raise InterruptedError('Construção 3D cancelada.')
        status(p,text)
    progress(.02,'Lendo geometria para a cena 3D')
    scene=Scene.light(d,settings,lambda p,m:progress(.02+.22*p,m))
    bounds=np.asarray(scene.report['bounds'],float)
    if scene.image_context_items:
        points=np.concatenate([item['points'] for item in scene.image_context_items]);bounds=np.array([np.minimum(bounds[0],points.min(0)),np.maximum(bounds[1],points.max(0))])
    if bounds.shape!=(2,2) or not np.isfinite(bounds).all():raise ValueError('Limites inválidos para o 3D.')
    span=float(np.max(bounds[1]-bounds[0]))
    if span<=0 or span>200000:raise ValueError('Divida o projeto em trechos de até 200 km para visualizar em 3D.')
    origin=np.r_[bounds.mean(axis=0),0.];warnings=list(scene.report.get('warnings',[]))
    # MDT é opcional; um terreno plano é identificado explicitamente.
    center=bounds.mean(axis=0);half=max(span*.56,50.);box=[center[0]-half,center[1]-half,center[0]+half,center[1]+half];n=65
    dem=np.zeros((n,n),np.float32);terrain_label='Terreno plano — sem MDT';elevation_available=False
    if settings.elevation.source!='none':
        try:
            if not settings.coordinates_confirmed:raise ValueError('Confirme o CRS antes de aplicar o MDT.')
            from . import elevation as E
            if settings.elevation.source=='local':
                base=(d/'elevacao').resolve()
                for name in (settings.elevation.file,settings.elevation.world,settings.elevation.prj):
                    if name:
                        p=base/name
                        if not p.resolve().is_relative_to(base) or p.is_symlink():raise ValueError('Caminho de MDT fora da pasta permitida.')
                dem,terrain_label=E.local_dem(d,settings.elevation,settings.crs,box,n)
            else:dem,terrain_label=E.web_dem(d,settings.crs,box,n,status=lambda p,m:progress(.25,m))
            if not np.isfinite(dem).all():raise ValueError('MDT contém cotas não finitas.')
            elevation_available=True;origin[2]=float(np.median(dem))
        except (ValueError,OSError,RuntimeError) as exc:
            warnings.append('MDT não aplicado: '+str(exc)[:220]);dem=np.zeros((n,n),np.float32)
    cell=(box[2]-box[0])/n
    def height(points):
        p=np.asarray(points,float);u=np.clip((p[:,0]-box[0])/cell,0,n-1);v=np.clip((box[3]-p[:,1])/cell,0,n-1)
        i=u.astype(int);j=v.astype(int);i1=np.minimum(i+1,n-1);j1=np.minimum(j+1,n-1);a=u-i;b=v-j
        return (dem[j,i]*(1-a)*(1-b)+dem[j,i1]*a*(1-b)+dem[j1,i]*(1-a)*b+dem[j1,i1]*a*b-origin[2])*settings.elevation.exaggeration
    def local(points,lift=0):
        p=np.asarray(points,float);return np.column_stack([p[:,0]-origin[0],height(p)+lift,-(p[:,1]-origin[1])])
    context_meshes=[]
    context_items=scene.image_context_items
    from .image_context import meshes as context_geometry
    context_meshes=context_geometry(context_items,local)
    buffers=defaultdict(list);labels={};total=0
    for index,e in enumerate(scene.items):
        if index%100==0:progress(.3,'Construindo superfícies 3D')
        if not e.get('closed') or e['role'] not in ('pavement','existing_pavement','shoulder','median','oae','water','cut','fill'):continue
        p=np.asarray(e['points'],float)
        if len(p)<3 or not np.isfinite(p).all():continue
        geom=shapely.make_valid(Polygon(p,holes=e.get('holes',[])))
        if geom.is_empty:continue
        key_mesh=e['role']+'|'+str(e.get('layer',''))
        labels[key_mesh]={'role':e['role'],'layer':str(e.get('layer','')),'name':str(e.get('layer') or e['role'])}
        from .asset_catalog import CATALOG
        material=e.get('asset_material')
        if material in CATALOG:labels[key_mesh].update(asset_material=material,texture_pattern=CATALOG[material]['pattern'],color=settings.role_colors.get(e['role']) or CATALOG[material]['color'])
        for triangle in shapely.constrained_delaunay_triangles(geom).geoms:
            q=np.asarray(triangle.exterior.coords)[:3,:2];total+=3
            if total>MAX_VERTICES:raise ValueError('Cena 3D muito detalhada. Divida o desenho em trechos menores.')
            lift={'pavement':.06,'existing_pavement':.05,'shoulder':.04,'water':-.1}.get(e['role'],.02)
            buffers[key_mesh].extend(local(q,lift).ravel().tolist())
    meshes=[dict(labels[k],id=f'surface-{i}',positions=p) for i,(k,p) in enumerate(buffers.items())]
    from .engineering_assets import asset_meshes
    meshes.extend(asset_meshes(scene.items,local,settings.role_colors))
    if sum(len(m['positions'])//3 for m in meshes)>MAX_VERTICES:raise ValueError('Cena e interferências excedem o orçamento 3D; divida o trecho.')
    # Grade compartilhada: cotas reais quando há MDT, sem inventar relevo.
    xs=np.linspace(box[0],box[2],n);ys=np.linspace(box[3],box[1],n);X,Y=np.meshgrid(xs,ys);ground=local(np.column_stack([X.ravel(),Y.ravel()]),-.03)
    indices=[]
    for j in range(n-1):
        for i in range(n-1):
            a=j*n+i;indices.extend([a,a+n,a+1,a+1,a+n,a+n+1])
    terrain={'positions':ground.ravel().tolist(),'indices':indices,'label':terrain_label,'elevation_available':elevation_available}
    # Sinalização é física; fluxos coloridos são exclusivamente diagnósticos.
    markings=[]
    for a,b,color in scene.network.markings:
        markings.append({'p':local(np.array([a,b]),.12).ravel().tolist(),'yellow':tuple(color)==(244,200,70)})
    from .flow_diagnostics import flow_diagnostics
    diagnostics=[]
    for i,(raw,diag) in enumerate(zip(scene.network.raw_info,flow_diagnostics(scene.network))):
        if raw.get('automatic_excluded'):continue
        diagnostics.append({'id':i,'p':local(raw['points'],.2).ravel().tolist(),'status':diag['technical_status'],'message':diag['technical_message']})
    progress(.55,'Simulando o tráfego validado para a vista 3D')
    duration=min(float(settings.duration_s),PREVIEW_SECONDS)
    sim=TrafficSim(scene.network,settings,partial(visual.vehicle_type,mix=settings.vehicle_mix),duration=duration,status=lambda p,m:progress(.55+.25*p,m)) if settings.traffic and scene.network.paths else None
    tracks={};samples=0
    if sim:
        for t in np.r_[np.arange(0,duration,.2),duration]:
            progress(.82,'Preparando animação de veículos 3D')
            indicators=sim.indicators(float(t))
            for pos,heading,vid,identity,_ in sim.vehicles_ex(float(t)):
                vt=sim.info[vid][1]
                if vid not in tracks:
                    L,W,wb,_=PROFILES.get(vt,PROFILES['car']);color=visual.vehicle_color(identity,vt)
                    tracks[vid]={'id':int(vid),'type':vt,'length':L,'width':W,'wheelbase':wb,'color':'#'+''.join(f'{int(v):02x}' for v in color),'samples':[],'indicators':[]}
                q=local(np.array([pos]),.07)[0];samples+=1
                if samples>MAX_TRAFFIC_SAMPLES:raise ValueError('Tráfego excede o orçamento da prévia 3D. Reduza a densidade ou a duração.')
                tracks[vid]['samples'].append([round(float(t),4),*q.tolist(),float(heading[0]),0.,-float(heading[1])])
                tracks[vid]['indicators'].append([round(float(t),4),int(indicators.get(int(vid),0))])
    from .transport import Transport,timings,AMBER,CLEARANCE,at
    from .transport_render import geometry as transport_geometry
    transport=sim.transport if sim else Transport(settings,scene.network);tg=transport_geometry(transport)
    for role,polys,lift in [('rail_ballast',tg['beds'],.07),('crosswalk',tg['crosswalks'],.15)]:
        positions=[]
        for poly in polys:
            positions.extend(local(poly[[0,1,2,0,2,3]],lift).ravel().tolist())
        if positions:meshes.append({'id':role,'role':role,'layer':'Transportes','name':'Lastro ferroviário' if role=='rail_ballast' else 'Faixa de pedestres','positions':positions})
    transport_lines=[{'p':local(row['points'],.22 if row['kind']=='rail' else .16).ravel().tolist(),'kind':row['kind']} for row in tg['lines']]
    train_tracks={}
    for t in np.r_[np.arange(0,duration,.2),duration]:
        for part in transport.train_parts(float(t)):
            key_part=part['id']
            if key_part not in train_tracks:
                train_tracks[key_part]={'id':1000000+len(train_tracks),'type':'rail_locomotive' if part['locomotive'] else 'rail_wagon','length':part['length'],'width':part['width'],'wheelbase':part['length']*.65,'color':'#e2af2c' if part['locomotive'] else '#789eae' if part['model']=='passageiros' else '#955f42','samples':[]}
            samples+=1
            if samples>MAX_TRAFFIC_SAMPLES:raise ValueError('Trens e veículos excedem o limite da prévia 3D. Reduza a duração / densidade ou divida o projeto.')
            q=local(np.array([part['p']]),.25)[0];h=part['heading'];train_tracks[key_part]['samples'].append([round(float(t),4),*q.tolist(),float(h[0]),0.,-float(h[1])])
    heads=[{'p':local(np.array([h['point']]),.25)[0].tolist(),'signal':h['signal'],'axis':h['axis'],'kind':'signal','arm':local(np.array([h['arm_end']]),.25)[0].tolist()} for h in tg['heads']]
    rail_stops=[];seen=set()
    for stops in transport.stops:
        for stop in stops:
            if stop['kind']!='rail':continue
            point,_=at(stop['rail']['p'],stop['rail']['d'],stop['rail_s']);key_stop=tuple(np.round(point,2))
            if key_stop in seen:continue
            seen.add(key_stop);rail_stops.append(stop);heads.append({'p':local(np.array([point+np.array([4.,4.])]),.25)[0].tolist(),'kind':'rail','rail_index':len(rail_stops)-1})
    clock=set(np.round(np.arange(0,duration,.1),6).tolist()+[duration])
    for signal in transport.signals:
        greens,walk,cycle=timings(signal);offset=transport.offsets[signal.id];clearance=signal.clearance_s
        boundaries=[0,greens[0],greens[0]+AMBER,greens[0]+AMBER+clearance,greens[0]+AMBER+clearance+greens[1],sum(greens)+2*AMBER+clearance,sum(greens)+2*(AMBER+clearance)]
        for k in range(math.floor(-offset/cycle)-1,math.ceil((duration-offset)/cycle)+1):
            for boundary in boundaries:
                t=offset+k*cycle+boundary
                if 0<=t<=duration:clock.add(round(t,6))
    signal_ids=[s.id for s in transport.signals];states=[];codes={'red':0,'amber':1,'green':2,'off':-1}
    for t in sorted(clock):
        colors=[]
        for signal in transport.signals:
            a,b,walk=transport.signal_state(signal,t+1e-7);colors.extend([codes[a],codes[b],int(walk)])
        states.append([t,colors,[transport.rail_stop_closed(stop,t) for stop in rail_stops]])
    if sum(len(row['p'])//3 for row in transport_lines)>MAX_VERTICES or len(heads)>1000:raise ValueError('Transportes excedem o limite de detalhe. Divida o projeto em trechos.')
    transport_data={'lines':transport_lines,'heads':heads,'signal_ids':signal_ids,'states':states,'report':transport.report()}
    if any(e.get('level') for e in scene.network.edges) or scene.oae or any(r.level for r in settings.railways) or any(r.level for r in settings.traffic_signals):warnings.append('As cotas de OAE e os gabaritos verticais exigem conferência técnica; esta vista não certifica cruzamentos em desnível.')
    if cancel():raise InterruptedError('Construção 3D cancelada.')
    if sum(len(mesh['positions'])//3 for mesh in context_meshes+meshes)>MAX_VERTICES:raise ValueError('Cena e objetos da imagem excedem o orçamento 3D. Reduza a área.')
    data={'format':'rodovia-scene3d-1','revision':key,'origin_crs':origin.tolist(),'crs':settings.crs,'coordinates_confirmed':settings.coordinates_confirmed,'span_m':span,'meshes':context_meshes+meshes,'terrain':terrain,'markings':markings,'diagnostics':diagnostics,'vehicles':list(tracks.values())+list(train_tracks.values()),'transport':transport_data,'duration_s':duration,'source_duration_s':settings.duration_s,'simulation_report':sim.report() if sim else None,'warnings':warnings[-25:],'scope':'Visualização de projeto e tráfego. Diagnósticos técnicos não integram a captura de apresentação.'}
    if not np.isfinite(origin).all():raise ValueError('Origem 3D inválida.')
    if key!=revision(d):raise ValueError('O projeto mudou durante o processamento. Reconstrua o 3D.')
    encoded=json.dumps(data,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
    if len(encoded)>32*1024*1024:raise ValueError('Cena acima de 32 MB. Divida o projeto para a vista 3D.')
    write_json(d/'analysis.json',scene.report)
    write_json(d/'editor.json',scene.editor_data())
    try:
        from .webmap import write_vectors
        write_vectors(d,scene.items,scene.axis,settings.crs)
    except (ValueError,OSError) as exc:status(.98,'Cena pronta; vetores 2D precisam de nova análise: '+str(exc)[:120])
    tmp=d/'scene3d.json.tmp';tmp.write_bytes(encoded);tmp.replace(d/'scene3d.json')
    progress(1,'Cena 3D pronta')
    return data
