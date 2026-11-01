"""Connected, directed illustrative traffic. No XY-only turns at bridge crossings."""
from .geom_rapida import hausdorff as _hausdorff
from .seguro import sdiv as _sdiv
from .falhas import registrar as _falha
import math,collections,hashlib
import numpy as np
import cv2
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter1d,label,binary_dilation,distance_transform_edt
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union,substring
from shapely import contains_xy
from .markup import zones_geometry,assign
from . import signage
from .vehicle_motion import analyze_motion

STEP=.6

def sample(points,step=STEP):
    p=np.asarray(points,float);ds=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];keep=np.r_[True,np.diff(ds)>1e-5];p=p[keep];ds=ds[keep]
    if len(p)<2:return p,np.array([0.])
    ss=np.linspace(0,ds[-1],max(2,int(ds[-1]/step)+1));return np.column_stack([np.interp(ss,ds,p[:,k]) for k in range(2)]),ss

def tangent(p):
    t=np.gradient(p,axis=0);return t/np.maximum(np.linalg.norm(t,axis=1)[:,None],1e-8)

def valid_centers(allowed,p,L=4.6,B=1.9):
    if len(p)<2 or allowed.is_empty:return np.zeros(len(p),bool)
    t=tangent(p);n=np.column_stack([t[:,1],-t[:,0]]);valid=contains_xy(allowed,p[:,0],p[:,1])
    for x,y in [(-L/2,-B/2),(-L/2,B/2),(L/2,-B/2),(L/2,B/2)]:
        q=p+t*x+n*y;valid&=contains_xy(allowed,q[:,0],q[:,1])
    return valid

def skeleton_paths(allowed,axis,cap=18000000,prune=False):
    from skimage.morphology import skeletonize
    origin=axis[0];v=axis[-1]-axis[0];v/=max(np.linalg.norm(v),1e-8);R=np.column_stack([v,[-v[1],v[0]]])
    polys=list(allowed.geoms) if hasattr(allowed,'geoms') else [allowed];polys=[p for p in polys if p.geom_type=='Polygon' and p.area>15]
    if not polys:return []
    allp=np.concatenate([np.asarray(p.exterior.coords) for p in polys]);q=(allp-origin)@R;lo=q.min(0)-4;hi=q.max(0)+4;size=hi-lo;res=max(.45,math.sqrt(float(np.prod(size))/cap));w,h=np.ceil(size/res).astype(int)+1
    mask=np.zeros((h,w),np.uint8)
    def px(p):return np.rint(((np.asarray(p)-origin)@R-lo)/res).astype(np.int32)
    for poly in polys:
        cv2.fillPoly(mask,[px(poly.exterior.coords)],1)
        for ring in poly.interiors:cv2.fillPoly(mask,[px(ring.coords)],0)
    sk=skeletonize(mask>0);width=distance_transform_edt(mask)*res
    ys,xs=np.nonzero(sk);pixels=set(zip(ys.tolist(),xs.tolist()))
    def neighbors(p):
        y,x=p;return [(y+dy,x+dx) for dy,dx in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)] if (y+dy,x+dx) in pixels]
    adj={p:neighbors(p) for p in pixels};junction=np.zeros_like(sk)
    for p in pixels:
        if len(adj[p])!=2:junction[p]=True
    nodes,nn=label(binary_dilation(junction,iterations=1)&sk,structure=np.ones((3,3)))
    for p in pixels:
        if nodes[p]==0 and len(adj[p])==0:nn+=1;nodes[p]=nn
    nodepixels=collections.defaultdict(list)
    for p in pixels:
        if nodes[p]:nodepixels[int(nodes[p])].append(p)
    centers={k:np.mean([(x,y) for y,x in ps],axis=0) for k,ps in nodepixels.items()};visited=set();paths=[]
    def trace(start,nxt,nid):
        ps=[start,nxt];prev=start;cur=nxt;visited.add(tuple(sorted((start,nxt))))
        while nodes[cur]==0:
            opts=[v for v in adj[cur] if v!=prev]
            if not opts:break
            nxt=opts[0];visited.add(tuple(sorted((cur,nxt))));ps.append(nxt);prev,cur=cur,nxt
            if len(ps)>len(pixels):break
        end=int(nodes[cur]);pts=np.array([(x,y) for y,x in ps],float)
        if nid in centers:pts[0]=centers[nid]
        if end in centers:pts[-1]=centers[end]
        if len(pts)<3:return
        pp=origin+(pts*res+lo)@R.T
        if np.sum(np.linalg.norm(np.diff(pp,axis=0),axis=1))<5:return
        smooth=gaussian_filter1d(pp,1.,axis=0,mode='nearest');smooth[0]=pp[0];smooth[-1]=pp[-1]
        if contains_xy(allowed,smooth[:,0],smooth[:,1]).all():pp=smooth
        paths.append({'points':pp,'halfwidth':float(np.median([width[p] for p in ps])),'source':'superfície DXF','level':0})
    for nid,ps in nodepixels.items():
        for p in ps:
            for q in adj[p]:
                if nodes[q]==nid or tuple(sorted((p,q))) in visited:continue
                trace(p,q,nid)
    # Closed components without a junction (roundabouts/isolated rings).
    for p in pixels:
        for q in adj[p]:
            if (nodes[p] and nodes[p]==nodes[q]) or tuple(sorted((p,q))) in visited:continue
            if nodes[p]==0:
                nn+=1;nodes[p]=nn;centers[nn]=np.array([p[1],p[0]],float)
            trace(p,q,int(nodes[p]))
    if prune and paths:
        # 1.12: ramos curtos sem saída (pontas do esqueleto em alargamentos e cantos) não viram trajetória.
        key=lambda v:(round(float(v[0])/2),round(float(v[1])/2))
        cnt=collections.Counter()
        for r in paths:cnt[key(r['points'][0])]+=1;cnt[key(r['points'][-1])]+=1
        def spur(r):
            L=float(np.sum(np.linalg.norm(np.diff(r['points'],axis=0),axis=1)))
            return L<14 and (cnt[key(r['points'][0])]==1 or cnt[key(r['points'][-1])]==1)
        paths=[r for r in paths if not spur(r)]
    return paths

def drop_backtracks(P,min_step=.05):
    """Remove pontos que voltam para trás (emendas de trechos sobrepostas) e pontos repetidos."""
    P=np.asarray(P,float);keep=[P[0]]
    for q in P[1:]:
        v=q-keep[-1];n=float(np.hypot(*v))
        if n<min_step:continue
        if len(keep)>=2:
            u=keep[-1]-keep[-2]
            if float(np.dot(u,v))<=0 and n<5:
                # Ponto atrás do anterior: descarta o anterior se o novo segue adiante do penúltimo.
                w=q-keep[-2]
                if float(np.dot(u,w))>0 and len(keep)>2:keep[-1]=q
                continue
        keep.append(q)
    return np.asarray(keep)

def steady_path(P,allowed,sigma_m=3.,step=STEP):
    """1.20: trajetória contínua para os veículos andarem em linha reta: sem recuos nas emendas e sem
    degraus/zigue-zague do esqueleto. Suaviza só onde o veículo continua inteiro dentro da pista."""
    Q=drop_backtracks(P)
    if len(Q)<3:return None,None
    p,d=sample(Q,step)
    if len(p)<10:return p,d
    sg=sigma_m/step;sm=gaussian_filter1d(p,sg,axis=0,mode='nearest')
    # Pontas fixas (ligação com entradas e saídas), com transição suave.
    n=len(p);ramp=np.clip(np.minimum(np.arange(n),np.arange(n)[::-1])/max(sg*2,1),0,1)[:,None]
    sm=p*(1-ramp)+sm*ramp
    ok=valid_centers(allowed,sm)
    if not ok.all():
        bad=gaussian_filter1d((~ok).astype(float),sg,mode='nearest')
        w=np.clip(1-bad*3,0,1)[:,None];sm=sm*w+p*(1-w)
        if not valid_centers(allowed,sm).all():sm=np.where(valid_centers(allowed,sm)[:,None],sm,p)
    p,d=sample(sm,step)
    return p,d

class TrafficNetwork:
    def __init__(self,roads,obstacles,axes,axis,ds,settings,bridges=(),oae_dirs=(),edge_lines=(),dxf_signage=(),dxf_signs=(),directory=None,oae_info=None,median_obstacles=None,virtual_chords=()):
        # 1.20: trajetórias suavizadas e sentido pelo eixo ('anterior' reproduz a 1.19).
        self.classic=bool(getattr(settings,'traffic_classic',False));self.medians=unary_union(obstacles if median_obstacles is None else median_obstacles)
        self.smooth_paths=getattr(settings,'vehicle_paths','smooth')=='smooth';self.axis_dir=getattr(settings,'direction_reference','axis')=='axis'
        self.oae_dirs=list(oae_dirs);self.dxf_edges=[np.asarray(p,float) for p in edge_lines];self.s=settings;self.axis=axis;self.ds=ds;self.bridges=Polygon()  # Contorno isolado, sem cota confirmada, não é impedimento.
        self.oae_info=list(oae_info or [])
        from shapely.geometry import MultiLineString
        self.virtual=MultiLineString([[tuple(a),tuple(b)] for a,b in virtual_chords]) if virtual_chords else None;self.virtual_dropped=0   # 2.18: fechamentos de hachura inexistentes no DXF
        self.oae_report=[];oae_warnings=[]
        if oae_info is not None:
            from .oae_traffic import classify,valid_grade
            self.oae_report,oae_warnings=classify(self.oae_info,axes)
            elevated=[o['deck'] for o in self.oae_info if valid_grade(o)]
            self.bridges=unary_union(elevated).buffer(1) if elevated else Polygon()
        # Cruzamentos sem conexão marcados pelo usuário: nenhum giro/troca de via dentro deles.
        self.no_connect=zones_geometry(getattr(settings,'no_connection_zones',[]))
        self.min_route=float(getattr(settings,'min_route_segment_m',50) or 0);self.ghost_zones=[];self.auto_pruned=[];self.pruned_contacts=collections.defaultdict(list);self.original_terminals={}
        self.raw_info=[];self.rejected_paths=[];self.rejected_connectors=collections.Counter();self.rejected_edge_ids=set();self.rejected_nodes=set()
        from .routes import section_corridors,confirmed_corridors
        from .route_lane_cache import RouteLaneCache
        self.route_lane_cache=RouteLaneCache(directory)
        from .routes import make_chain,km_context
        try:
            from .chainage import Stationing
            self.km_dir=int(Stationing.from_settings(np.asarray(axis,float),settings).direction) or 1   # 2.39: sentido em que o KM cresce (início/fim, “inverter eixo”, estaqueamento manual)
        except Exception:self.km_dir=1
        self._km_chain=make_chain(axis,ds,self.km_dir)   # 2.39: seções seguem o km do eixo principal (inclusive “inverter eixo”)
        roads_dxf=list(roads)
        with km_context(self._km_chain):roads=list(roads)+section_corridors(settings,self.route_lane_cache)+confirmed_corridors(settings,self.route_lane_cache)
        from .flow_fit import close_seams,edge_guide
        self.dxf_pavement=close_seams(unary_union(list(roads_dxf))) if len(roads_dxf) else Polygon()   # 2.43: só a hachura DXF (sem corredores das seções) — base do diagnóstico “sem pavimento”
        self.lane_coverage=[]
        self.operational_pavement=close_seams(unary_union(roads)) if roads else Polygon()   # 1.42.40: juntas de hachura não são vazio
        if self.classic:
            # Corredores finitos vinculados aos eixos; somente canteiros limitam o ensaio.
            sources=[np.asarray(a['points'],float) for a in axes]+[np.array([[v.x,v.y] for v in r.points]) for r in settings.route_alignments if r.enabled]
            corridors=[LineString(q).buffer(max(8.,settings.lane_width_m*settings.lanes_per_direction+3)) for q in sources if len(q)>=2 and np.isfinite(q).all()]
            roads=roads+corridors;obstacles=[self.medians] if not self.medians.is_empty else []
            self.no_connect=Polygon()
        from .shoulder_probe import envelope
        exclusions=[Polygon([(p.x,p.y) for p in a]) for a in settings.exclusions]
        self.shoulder_envelope=envelope(self.operational_pavement,obstacles,exclusions,self.bridges)
        self.allowed=close_seams(unary_union(roads)).difference(unary_union(obstacles).buffer(.15)).buffer(-.12) if roads else Polygon()
        self.paved=self.allowed  # superfície para as linhas de bordo (sem as exclusões de limpeza)
        self.edge_guide_report={}
        _boundary=self.operational_pavement.boundary if not self.operational_pavement.is_empty else None
        self.edge_guide=edge_guide(self.dxf_edges,axes,boundary=_boundary,report=self.edge_guide_report) if getattr(settings,'edge_line_guide',True) and not self.classic else None
        if self.edge_guide is not None and not self.allowed.is_empty:self.allowed=self.allowed.difference(self.edge_guide)   # a linha de bordo conduz: o corpo não a atravessa
        if settings.exclusions and not self.classic:self.allowed=self.allowed.difference(unary_union([Polygon([(p.x,p.y) for p in a]) for a in settings.exclusions]))
        # 1.15: sinalização completa (faixas pela largura, zebrados, setas de faixa, retenções e placas).
        self.full=getattr(settings,'signage_style','clean')=='clean' and getattr(settings,'signage_detail','full')=='full'
        self.dxf_h=list(dxf_signage);self.dxf_v=list(dxf_signs);self.lane_info={};self.fills=[];self.signs=[];self.arrow_kinds=[];self.arrow_anchors=[]
        self.lane_zones=[(Polygon([(p.x,p.y) for p in z.points]).buffer(0),z.lanes) for z in getattr(settings,'lane_zones',[]) or [] if len(z.points)>=3]
        if self.full:
            self.ext=signage.Extents(self.paved)
        self.stations=np.arange(0,ds[-1]+1,2.);self.dense=np.column_stack([np.interp(self.stations,ds,axis[:,k]) for k in range(2)]);self.tree=cKDTree(self.dense);self.axis_t=tangent(self.dense)
        long=[]
        for a in axes:
            if LineString(a['points']).length<ds[-1]*.6:continue
            p,_=sample(a['points'],3)
            if self.chain(p[-1:])[0]<self.chain(p[:1])[0]:p=p[::-1]
            if any(np.median(cKDTree(q).query(p)[0])<.7 for q in long):continue
            long.append(p)
        self.main=long[:2];self.main_trees=[cKDTree(p) for p in self.main];self.main_sign=[]
        for i,p in enumerate(self.main):
            if len(self.main)>1:
                other=self.main[1-i];near=other[cKDTree(other).query(p)[1]];t=self.axis_t[self.tree.query(p)[1]];right=np.column_stack([t[:,1],-t[:,0]]);self.main_sign.append(1 if np.median(np.sum((p-near)*right,axis=1))>=0 else -1)
            else:self.main_sign.append(1)
        self.markings=[];self.mark_src=[];self.arrows=[];self.edges=[];self.paths=[];self.warnings=[]
        self.clean=getattr(settings,'signage_style','clean')=='clean';self.arrow_mode=getattr(settings,'flow_arrows','km_conflicts')
        # Somente eixos designados e trajetórias explicitamente escolhidas.
        # A hachura de pavimento não autoriza inventar eixos por esqueleto.
        raw=[]
        from .native_axes import native_paths
        native,self.native_axis_report=native_paths(axes,settings,self.allowed)
        try:
            from .native_axes import direction_diagnostics
            dd=direction_diagnostics(axes,settings);self.native_axis_report.update(dd)
            if dd['orphan_keys']:self.warnings.append(f"Sentido por eixo: {dd['orphan_keys']} escolha(s) salva(s) não corresponde(m) a nenhum eixo atual (o desenho mudou). Escolha o sentido por layer (comando SENTIDOEIXO) ou refaça a seleção.")
            from .direction_policy import relatorio
            for it in relatorio(axes,settings)['eixos']:
                for c in it['conflitos']:self.warnings.append(f"Sentido do eixo {it['layer']}: {c}.")
            if dd['axes_without_choice'] and settings.route_directions:self.warnings.append('Sentido automático (sem escolha aplicada) nos eixos: '+', '.join(dd['axes_without_choice'])+'.')
        except Exception as exc:_falha(__name__,exc)
        if not native and not any(p.enabled for p in settings.traffic_paths) and not any(r.enabled for r in settings.route_alignments):self.warnings.append('Nenhum eixo autorizado para tráfego: cadastre a camada como Eixo ou selecione uma linha como rota com sentido explícito. Sugestão pelo nome não autoriza circulação. O pavimento sozinho não cria fluxos.')
        self.source_registration={'policy':'explicit_axis_required','native_authorized':len(native),'native_pending_directions':self.native_axis_report.get('pending_directions',0),'native_disabled':self.native_axis_report.get('manually_disabled',0),'ignored_unregistered':self.native_axis_report['ignored_sources'],'manual_axes':sum(p.enabled for p in settings.traffic_paths),'registered_alignments':sum(r.enabled for r in settings.route_alignments)}
        if self.native_axis_report.get('pending_directions'):self.warnings.append('Sentidos antigos vinculados a índices precisam de conferência em Sentidos e nós. Fontes não conferidas permanecem sem circulação; nenhuma decisão foi transferida para outro eixo.')
        raw=native
        if native and self.allowed.is_empty:self.warnings.append('Sem hachura/textura de pavimento reconhecida: os veículos não são apresentados e nenhum erro é gerado. Cadastre a área de pavimento para circular.')
        for r in settings.traffic_paths:
            if not getattr(r,'enabled',True):continue
            raw.append({'points':np.array([[p.x,p.y] for p in r.points]),'halfwidth':3.,'source':r.name,'source_id':r.id or r.name,'level':r.level,'kind':r.kind,'direction':r.direction,'manual':True,**({'fixed':True,'nopaint':True} if r.direction=='auto' else {}),'speed_kmh':getattr(r,'speed_kmh',None)})
        # 1.30: faixas dos alinhamentos de rota (pista simples, dupla por sentido ou sentido único).
        if getattr(settings,'route_alignments',None):
            from .routes import raw_paths
            from .routes import km_context
            with km_context(self._km_chain):raw.extend(raw_paths(settings,self.route_lane_cache))
        for i,r in enumerate(raw):
            r.setdefault('origin',i)
            coordinates=np.round(r.get('identity_points',r['points']),3).astype('<f8');geometry_key=min(coordinates.tobytes(),coordinates[::-1].tobytes())
            r['origin_key']=hashlib.sha256((str(r.get('source_id') or r.get('route') or r.get('native_id') or r.get('source',''))+'|'+str(r.get('level',0))).encode()+geometry_key).hexdigest()
            r['origin_aliases']=[r['origin_key']]
            if r.get('native_axis'):
                r['origin_aliases'].append(hashlib.sha256((str(r['native_id'])+'|'+str(r.get('level',0))).encode()+geometry_key).hexdigest())
            for old in r.get('legacy_identity_points',[]):
                q=np.round(old,3).astype('<f8');key=min(q.tobytes(),q[::-1].tobytes())
                r['origin_aliases'].append(hashlib.sha256((str(r.get('route') or r.get('source',''))+'|'+str(r.get('level',0))).encode()+key).hexdigest())
            if r.get('native_axis') and ',' not in r['native_id']:
                # A revisão anterior reamostrava apenas os eixos principais.
                # Seus cortes e desativações continuam vinculados à mesma fonte.
                source=axes[int(r['native_id'])]['points'];old,_=sample(source,3)
                if self.chain(old[-1:])[0]<self.chain(old[:1])[0]:old=old[::-1]
                old=np.round(old,3).astype('<f8');key=min(old.tobytes(),old[::-1].tobytes())
                r['origin_aliases'].append(hashlib.sha256(('eixo principal DXF|'+str(r['level'])).encode()+key).hexdigest())
        raw=self.prune_automatic(raw,'original')
        from .flow_tools import cut_raw_paths
        raw,self.cut_report=cut_raw_paths(raw,getattr(settings,'flow_cuts',[]),overrides=getattr(settings,'flow_overrides',[]))
        unmatched=sum(row['status']!='applied' for row in self.cut_report)
        if unmatched:self.warnings.append(f'{unmatched} corte(s) não foram associados ao traçado atual. Revise os intervalos após a alteração de geometria.')
        # 1.39: comprimento de cada trecho original (antes dos cortes nos encontros) para ignorar os curtos nas rotas.
        self.original_terminals={r['origin']:np.asarray(r['points'],float)[[0,-1]].copy() for r in raw}
        self.origin_info={}
        for r in raw:
            o=r['origin'];L=float(LineString(r['points']).length) if len(r['points'])>1 else 0.
            keep=bool(r.get('manual') or r.get('fixed') or r.get('kind')=='main')
            a=self.origin_info.get(o,(0.,False));self.origin_info[o]=(a[0]+L,a[1] or keep)
        from .direction_intervals import split_intervals
        raw,self.direction_report=split_intervals(raw,getattr(settings,'direction_marks',[]))
        conflicts=sum(row['status']=='node_conflict' for row in self.direction_report)
        if conflicts:self.warnings.append(f'{conflicts} marcação(ões) de sentido contradizem os nós. O percurso válido foi mantido; ajuste os nós ou remova a marcação contraditória.')
        unresolved=sum(row['status'] not in ('applied','node_conflict') for row in self.direction_report)
        if unresolved:self.warnings.append(f'{unresolved} indicação(ões) de sentido curta(s) ou sem eixo único associado; use intervalo de pelo menos 5 m, selecione a linha explicitamente e confira início/fim.')
        raw=self.prune_automatic(self.split_contacts(raw),'contato')
        # Setas e cliques do usuário são resolvidos uma vez, sobre os trechos finais.
        sampled=[sample(r['points'])[0] for r in raw]
        from types import SimpleNamespace
        recovery_marks=[SimpleNamespace(id=o.id,x=o.x,y=o.y,enabled=o.enabled,action='reconstruct' if o.reconstruct else 'recover',target_key=o.target_key) for o in getattr(settings,'flow_recoveries',[])]
        marks=assign(sampled,list(getattr(settings,'flow_overrides',[]))+recovery_marks,[],path_keys=[r['origin_aliases'] for r in raw])
        keys={key for r in raw for key in r['origin_aliases']};unmatched=sum(o.enabled and bool(o.target_key) and o.target_key not in keys for o in getattr(settings,'flow_recoveries',[]))
        if unmatched:self.warnings.append(f'{unmatched} recuperação(ões) não correspondem mais à geometria atual. Selecione novamente o eixo para revisar.')
        recovery_origins={r['origin'] for r,m in zip(raw,marks.values()) if m.get('recover') or m.get('reconstruct')}
        rebuild_origins={r['origin'] for r,m in zip(raw,marks.values()) if m.get('reconstruct')}
        for r,m in zip(raw,marks.values()):
            if r.get('cut_disable_ids'):m={**m,'disable':True,'override_ids':list(dict.fromkeys(m['override_ids']+r['cut_disable_ids']))}
            r['user']={**m,'recover':r['origin'] in recovery_origins or r.get('explicit_cut',False),'reconstruct':r['origin'] in rebuild_origins}
        # Roundabout islands supply a counter-clockwise direction field.
        self.islands=[];self.splitters=[]
        for poly in (list(self.allowed.geoms) if hasattr(self.allowed,'geoms') else [self.allowed]):
            if poly.geom_type!='Polygon':continue
            for ring in poly.interiors:
                hole=Polygon(ring);r=math.sqrt(hole.area/math.pi)
                if 2<r<24 and 4*math.pi*hole.area/max(hole.length**2,.001)>.55:self.islands.append((np.array(hole.centroid.coords[0]),r))
                elif 40<hole.area<3000 and hole.length<200:self.splitters.append(hole)
        self.nodes=[]
        for i,r in enumerate(raw):self.add_raw(r,i,axes)
        # Trechos longos inviáveis continuam vermelhos para correção; só minigeometrias saem do estudo.
        for r in self.raw_info:r['automatic_excluded']=not (r.get('manual') or r.get('route_fixed')) and (self.origin_info.get(r.get('origin_id'),(0,False))[0] if r.get('native_axis') else float(LineString(r['points']).length))<max(20.,self.min_route)
        self.connections={i:[] for i in range(len(self.edges))};self.connectors={}
        for i,a in enumerate(self.edges):
            if a['disabled']:continue
            for j,b in enumerate(self.edges):
                if b['disabled'] or a['end']!=b['start'] or a['base']==b['base']:continue
                connector=self.connector(a,b)
                if connector is not None:self.connections[i].append(j);self.connectors[(i,j)]=connector
        self.apply_connection_rules()
        if not self.classic:self.crossing_rules()
        else:self.crossings_blocked=0
        self.min_route=float(getattr(settings,'min_route_segment_m',50) or 0)
        nw=len(self.warnings)
        self.make_itineraries(self.min_route)
        if not self.paths and self.min_route>0:
            # Segurança visual: nunca reabilita automaticamente micro-rotas. Melhor ficar sem veículos
            # do que produzir zigue-zague/cintilação por itinerários menores que o limite configurado.
            self.warnings.append(f'Nenhuma rota segura permaneceu após excluir trechos menores que {self.min_route:g} m; tráfego não foi habilitado nesses trechos.')
        if self.rejected_connectors:self.warnings.append(f'{sum(self.rejected_connectors.values())} tentativa(s) de ligação recusada(s) por geometria ou sentido incompatível. Consulte o diagnóstico de circulação.')
        self.finalize_signage()
        from .road_sections import continuity_report
        sections=[r for route in settings.route_alignments if (r:=continuity_report(route)) is not None]
        self.warnings.extend(oae_warnings)
        self.report={'oae':self.oae_report,'section_continuity':sections,'route_lane_cache':self.route_lane_cache.report(),'edge_lines_ignored_inside_pavement':getattr(self,'edge_guide_report',{}).get('ignored',0),'directed_edges':len(self.edges),'connections':sum(map(len,self.connections.values())),'itineraries':len(self.paths),'coverage':dict(collections.Counter(e['kind'] for e in self.edges)),'used_kinds':dict(collections.Counter(k for p in self.paths for k in p['kinds'])),'warnings':self.warnings,'signage':getattr(self,'report_signage',{}),'automatic_segments_pruned':len(self.auto_pruned),'minimum_flow_length_m':self.min_route,'short_segments_ignored':len(self.short_ignored),'explicit_flow_cuts':getattr(self,'cut_report',[]),'recovered_principal_paths':getattr(self,'recovered_paths',0),'motion_rejected_paths':len(self.rejected_paths),'motion_rejected_connections':dict(self.rejected_connectors),'motion_scope':'Geometria e restrições disponíveis no projeto; sem certificação CONTRAN.'}
        self.report['native_axes']=self.native_axis_report
        self.report['source_registration']=self.source_registration
        self.report['source_policy']='somente_eixos_designados_ou_selecao_explicita'
        self.report['direction_intervals']=self.direction_report
    def prune_automatic(self,raw,stage):
        """Candidatos curtos não chegam aos nós, conectores ou ao desenho de fluxos.

        A fonte DXF e rotas manuais são preservadas. Várias pontas curtas num
        mesmo nó não podem recriar um leque de micro-rotas nem novas entradas.
        """
        minimum=max(20.,self.min_route);kept=[]
        for r in raw:
            if stage=='contato' and r.get('native_axis') and getattr(self,'origin_info',{}).get(r.get('origin'),(0,False))[0]>=minimum:
                kept.append(r);continue  # Subtrecho de um eixo longo, não uma mini-rota independente.
            if r.get('manual') or r.get('fixed'):
                kept.append(r);continue
            p=np.asarray(r.get('points',[]),float)
            valid=p.ndim==2 and p.shape[1]==2 and len(p)>=2 and np.isfinite(p).all()
            length=float(np.sum(np.linalg.norm(np.diff(p,axis=0),axis=1))) if valid else 0.
            if not valid or length<minimum:
                if stage=='contato' and valid:self.pruned_contacts[r.get('origin')].extend([p[0].copy(),p[-1].copy()])
                self.auto_pruned.append({'source':r.get('source','automático'),'length_m':round(length,3),'stage':stage,'reason':'mini_rota_automatica'})
            else:kept.append(r)
        if len(kept)<len(raw):self.warnings.append(f'{len(raw)-len(kept)} mini-rota(s) automática(s) excluída(s) antes da rede ({stage}; limite {minimum:g} m). Crie a ligação manualmente se necessária.')
        return kept
    def axis_offset(self,p):
        idx=self.tree.query(p)[1];t=self.axis_t[idx];return float(np.dot(np.asarray(p)-self.dense[idx],np.array([t[1],-t[0]])))
    def inside(self,q):return contains_xy(self.paved,q[:,0],q[:,1])
    def coverage_warnings(self,limit=12):
        """2.43: avisos legíveis sobre faixas de seção sem circulação (e sobre circulação fora da hachura autorizada pela seção)."""
        out=[]
        for c in getattr(self,'lane_coverage',[]):
            nome='«%s» faixa %d (%s)'%(c['route_name'],c['lane']+1,'sentido do eixo' if c['dir']=='f' else 'sentido oposto')
            if c['gaps']:
                tot=sum(g['end_m']-g['start_m'] for g in c['gaps']);ex='; '.join('%.0f–%.0f m (%s)'%(g['start_m'],g['end_m'],g['reason']) for g in c['gaps'][:3])
                out.append('Seção %s: %.0f m sem circulação (%.0f%% da faixa circulável): %s%s. Ajuste a posição/larguras da seção ou autorize a seção a circular fora da hachura.'%(nome,tot,c['circulavel_pct'],ex,' …' if len(c['gaps'])>3 else ''))
            if c['autorizado_fora_da_hachura']:
                tot=sum(g['end_m']-g['start_m'] for g in c['autorizado_fora_da_hachura']);ex='; '.join('%.0f–%.0f m'%(g['start_m'],g['end_m']) for g in c['autorizado_fora_da_hachura'][:3])
                out.append('Seção %s: %.0f m circulam FORA da hachura de pavimento porque a seção autoriza (%s). Desmarque “Usar a seção como pavimento” nesse trecho se ali não há pista.'%(nome,tot,ex))
        return out[:limit]
    def _cobertura(self,r,lane,valid,forward):
        """2.43: por faixa de seção, quanto do trecho NÃO tem circulação e por quê (sem hachura de pavimento x barreira/canteiro/exclusão)."""
        n=len(lane)
        if n<2:return
        a=float(r.get('route_start_m',0.));b=float(r.get('route_end_m',a))
        st=a+(b-a)*np.arange(n)/(n-1)
        if r.get('route_dir')=='r':st=st[::-1]
        dxf=contains_xy(self.dxf_pavement,lane[:,0],lane[:,1]) if not self.dxf_pavement.is_empty else np.zeros(n,bool)
        ok=np.asarray(valid,bool);gaps=[]
        bad=~ok
        if bad.any():
            ch=np.diff(np.r_[False,bad,False].astype(np.int8));ini=np.flatnonzero(ch==1);fim=np.flatnonzero(ch==-1)
            for i,j in zip(ini,fim):
                s0,s1=float(st[i:j].min()),float(st[i:j].max())
                if s1-s0<3:continue
                motivo='sem hachura de pavimento' if not dxf[i:j].mean()>.5 else 'barreira, canteiro ou exclusão'
                gaps.append({'start_m':round(s0,1),'end_m':round(s1,1),'reason':motivo})
        # trecho que SÓ circula porque a seção autoriza (fora da hachura): é onde a pessoa vê veículo sobre “área sem pavimento”
        fora=ok&~dxf;extra=[]
        if fora.any():
            ch=np.diff(np.r_[False,fora,False].astype(np.int8))
            for i,j in zip(np.flatnonzero(ch==1),np.flatnonzero(ch==-1)):
                s0,s1=float(st[i:j].min()),float(st[i:j].max())
                if s1-s0>=3:extra.append({'start_m':round(s0,1),'end_m':round(s1,1)})
        self.lane_coverage.append({'route':r.get('route'),'route_name':r.get('route_name',''),'dir':r.get('route_dir'),'lane':int(r.get('route_lane',0)),'length_m':round(float(b-a),1),
            'circulavel_pct':round(100.*float(ok.mean()),1),'gaps':gaps[:40],'autorizado_fora_da_hachura':extra[:40]})
    def chain(self,p):return self.stations[self.tree.query(np.asarray(p))[1]]
    def motion_audit(self,points,vehicle='car',allowed=None):
        if getattr(self,'classic',False):
            from .classic_traffic import numerical_audit
            return numerical_audit(points,allowed)
        return analyze_motion(points,vehicle,allowed)
    def flow(self,p):
        if self.main:
            i=int(np.argmin([tr.query(p)[0] for tr in self.main_trees]));return self.main_sign[i],float(self.main_trees[i].query(p)[0])
        idx=self.tree.query(p)[1];t=self.axis_t[idx];right=np.array([t[1],-t[0]]);return (1 if np.dot(p-self.dense[idx],right)>=0 else -1),float(np.linalg.norm(p-self.dense[idx]))
    def split_contacts(self,raw):
        lines=[LineString(r['points']) for r in raw];cuts=[{0.,ln.length} for ln in lines]
        for i,ln in enumerate(lines):
            for p in [ln.coords[0],ln.coords[-1]]:
                point=Point(p);best=None
                for j,other in enumerate(lines):
                    if j==i or raw[i]['level']!=raw[j]['level']:continue
                    # 1.30: a ponta de uma faixa de rota não corta os demais trechos (a pintura deles não muda).
                    # Contatos de ramais tipados também dividem o eixo principal.
                    d=other.distance(point);s=other.project(point)
                    if d<3.5 and 5<s<other.length-5 and (best is None or d<best[0]):best=(d,j,s)
                if best and not self.no_connect.is_empty and self.no_connect.covers(point):best=None
                if best:cuts[best[1]].add(best[2])
        for rule in getattr(self.s,'connection_rules',[]):
            if not rule.enabled or rule.action=='deny':continue
            for anchor,key in ((rule.a,rule.from_key),(rule.b,rule.to_key)):
                point=Point(anchor.x,anchor.y)
                candidates=[(ln.distance(point),j,ln.project(point)) for j,ln in enumerate(lines) if not key or key in raw[j].get('origin_aliases',[])]
                if candidates:
                    distance,j,station=min(candidates)
                    if distance<=8 and 3<station<lines[j].length-3 and all(abs(station-cut)>30 for cut in cuts[j]):cuts[j].add(station)
        result=[]
        for r,ln,values in zip(raw,lines,cuts):
            values=sorted(values)
            if r.get('native_axis'):
                # Contatos quase coincidentes compartilham um encontro; não
                # recortar e depois descartar 1–3 m do próprio eixo CAD.
                retained=[0.]
                for value in values[1:-1]:
                    if value-retained[-1]>=4.5 and ln.length-value>=4.5:retained.append(value)
                values=retained+[ln.length]
            for a,b in zip(values[:-1],values[1:]):
                if b-a<3:continue
                seg=substring(ln,a,b)
                if seg.geom_type=='LineString':result.append({**r,'points':np.asarray(seg.coords)})
        return result
    def node(self,p,level):
        for i,(q,l) in enumerate(self.nodes):
            if l==level and np.linalg.norm(p-q)<3.6:return i
        self.nodes.append((p.copy(),level));return len(self.nodes)-1
    def add_raw(self,r,base,axes):
        p,ss=sample(r['points']);L=ss[-1]
        if len(p)<3 or L<4:return
        ch=self.chain(p);delta=ch[-1]-ch[0];sign,dist=self.flow(p[len(p)//2]);kind=r.get('kind') or ('main' if abs(delta)>.65*L and dist<13 else 'marginal' if abs(delta)>.65*L else 'return' if delta*delta<.20*L*L else 'device')
        direction=r.get('direction','auto');forward=delta*sign>=0;both=abs(delta)<max(5,L*.18) and r['halfwidth']>2.6;ring=False
        if self.axis_dir and abs(delta)>.65*L:
            # 1.20: trecho paralelo ao eixo e sem seta: o sentido vem do eixo do projeto (mão de direção:
            # à direita do eixo, km crescente; à esquerda, decrescente). Sobre o eixo (pista simples), mantém o cálculo.
            off=self.axis_offset(p[len(p)//2])
            if abs(off)>1.:forward=delta*(1 if off>=0 else -1)>=0
        # Circulation is counter-clockwise around actual island holes.
        for center,rad in self.islands:
            v=p-center;rr=np.linalg.norm(v,axis=1)
            if np.mean((rr>rad)&(rr<rad+9))>.65:
                if self.clean and not r.get('native_axis'):
                    # 1.12: anel da rotatória vira arco de círculo (sem o zigue-zague do esqueleto).
                    band=(rr>rad)&(rr<rad+9);Rm=float(np.median(rr[band]))
                    w=np.clip(1-np.abs(rr-Rm)/6,0,1)[:,None]*band[:,None]
                    p=p*(1-w)+(center+v/np.maximum(rr,1e-9)[:,None]*Rm)*w
                    p0,p1=p[0].copy(),p[-1].copy();p=gaussian_filter1d(p,2.,axis=0,mode='nearest');p[0],p[-1]=p0,p1;p,ss=sample(p);L=ss[-1];v=p-center
                t=tangent(p);wanted=np.column_stack([-v[:,1],v[:,0]]);forward=np.median(np.sum(t*wanted,axis=1))>0;both=False;kind='device';ring=True;break
        else:
            # 1.12: mão de direção (tráfego pela direita): ilhas divisórias ficam à esquerda do motorista,
            # ou seja, a circulação em volta delas é anti-horária (como nas rotatórias).
            if self.clean and (kind!='main' or L<60):
                for hole in self.splitters:
                    import shapely as _sh
                    near=_sh.distance(hole.exterior,_sh.points(p[::3]))
                    if np.mean(near<8)>=.5:
                        c=np.asarray(hole.centroid.coords[0]);v=p-c;t=tangent(p);wanted=np.column_stack([-v[:,1],v[:,0]])
                        forward=bool(np.median(np.sum(t*wanted,axis=1))>0);both=False;break
        from .routes import km_ambiguo
        if km_ambiguo(delta,L):delta=1.   # 2.41: ramo/laço não paralelo ao eixo principal: o km não dá sentido; Crescente/Decrescente valem pela ordem do desenho
        kd=getattr(self,'km_dir',1)   # 2.39: Crescente/Decrescente = km exibido (não a ordem do eixo principal)
        if direction=='growing':forward=delta*kd>=0;both=False
        elif direction=='decreasing':forward=delta*kd<=0;both=False
        elif direction=='both':both=True
        if axes and not r.get('manual'):
            if 'native_direction' in r:d=r['native_direction']
            else:
                k=min(range(len(axes)),key=lambda j:LineString(axes[j]['points']).distance(Point(p[len(p)//2])))
                from .native_axes import axis_fingerprint
                a=axes[k];from .native_axes import direction_for;d=direction_for(self.s.route_directions,'axis:'+axis_fingerprint(a['points'],a.get('layer',''),a.get('level',0)),a.get('layer',''))
            if d=='off':return
            if d=='forward':forward=delta*kd>=0;both=False
            elif d=='reverse':forward=delta*kd<=0;both=False
        # Prioridade: seta desenhada sobre a pista > fluxo do eixo > sugestão automática.
        user=r.get('user') or {}
        if user.get('arrow') is not None:forward=user['arrow'];both=False
        # Sentido definido na OAE (1.11): vale para os trechos que passam pelo tabuleiro.
        for deck,sgn in self.oae_dirs:
            if r.get('native_direction') in ('forward','reverse') or r.get('direction') in ('growing','decreasing') or user.get('arrow') is not None:continue
            inside=np.flatnonzero(contains_xy(deck,p[:,0],p[:,1]))
            if len(inside)<10:continue
            delta=self.chain(p[inside[-1:]])[0]-self.chain(p[inside[:1]])[0]
            if abs(delta)>2:forward=bool(delta*sgn>0);both=False
        if r.get('fixed'):forward=True;both=False   # 1.30: faixa de rota: o sentido é o dos pontos
        if 'explicit_direction' in r:forward=bool(r['explicit_direction']);both=False
        reversed_by_user=bool(user.get('reverse'))
        if reversed_by_user and (r.get('fixed') or r.get('direction') in ('growing','decreasing')):
            user=dict(user,disable=True);self.warnings.append('Inversão recusada: o trecho tem sentido explícito definido pela rota.')
        elif reversed_by_user and not both:forward=not forward
        disabled=bool(user.get('disable'))
        spd=user.get('speed_kmh') or r.get('speed_kmh')
        route_meta={k:r.get(k) for k in ('flow_role','flow_start','flow_end','external_demand_vph','external_vdm','native_axis','native_id','native_joined','route','route_name','route_dir','route_lane','route_lane_width_m','route_start_m','route_end_m','lane_change','lane_change_sections','axis_type') if r.get(k) is not None}
        self.raw_info.append({'base':base,'points':p,'kind':kind,'forward':bool(forward),'both':bool(both),'disabled':disabled,'reversed':reversed_by_user,'source':r['source'],'manual':bool(r.get('manual')),'override_ids':user.get('override_ids',[]),'protected_overrides':r.get('cut_disable_refs',[]),'recovery_enabled':bool(user.get('recover')),'recovery_reports':[],'origin_id':r.get('origin',base),'origin_key':r.get('origin_key',''),'level':r['level'],'speed_kmh':float(spd) if spd else None,**route_meta,**({'route_fixed':True} if r.get('fixed') else {}),**({'direction_mark_id':r['direction_mark_id'],'explicit_direction':r['explicit_direction']} if 'explicit_direction' in r else {})})
        # Paint belongs to the road center, not to an individual vehicle track.
        # 1.10: trechos curtos do esqueleto (ramos de junção) não recebem pintura no modo limpo.
        if r.get('nopaint'):pass   # 1.30: faixas de rota só conduzem veículos (sem pintura)
        elif not self.clean:self.paint(p,r['halfwidth'],both,len(self.raw_info)-1)
        elif kind in ('main','marginal') and L>=60:
            if self.full:signage.lane_lines(self,p,both,len(self.raw_info)-1,bool(forward))
            else:self.paint(p,r['halfwidth'],both,len(self.raw_info)-1,edges=False)
        for f in ([True,False] if both else [forward]):
            q=p.copy() if f else p[::-1].copy();t=tangent(q);n=np.column_stack([t[:,1],-t[:,0]])
            offset=0. if r.get('fixed') else min(1.65,max(0.,r['halfwidth']-1.35)) if both or kind in ['main','marginal'] else 0.
            if r.get('free') or r.get('fixed'):
                lane=q+n*offset;valid=np.ones(len(lane),bool) if r.get('free') else valid_centers(self.allowed,lane)
                if r.get('fixed') and r.get('route'):self._cobertura(r,lane,valid,f)
            else:
                from .flow_fit import fit_offset
                lane,valid,fit=fit_offset(q,n,offset,self.allowed,both)
                if fit:
                    self.raw_info[-1].setdefault('lateral_fits',[]).append(fit)
                    offset=fit['applied_m']
            # Invalid interior samples split the edge: no jumps across gaps or barriers.
            changes=np.diff(np.r_[False,valid,False].astype(np.int8))
            runs=list(zip(np.flatnonzero(changes==1),np.flatnonzero(changes==-1)))
            if getattr(self.s,'traffic_bridge_gaps',False) and r.get('native_axis') and not disabled:runs=self._bridge_runs(lane,runs);self.apply_ghost_zones()
            for run_index,(a,b) in enumerate(runs):
                if b-a<8:continue
                segment=lane[a:b];tt=tangent(segment);d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(segment,axis=0),axis=1))]
                if d[-1]<4:continue
                if not r.get('manual') and not r.get('fixed') and not r.get('native_axis') and d[-1]<max(20.,self.min_route):
                    self.pruned_contacts[r.get('origin')].extend([segment[0].copy(),segment[-1].copy()])
                    self.auto_pruned.append({'source':r['source'],'length_m':float(d[-1]),'stage':'superficie','reason':'mini_rota_automatica'});continue
                recovered=[segment]
                if user.get('recover') and not disabled:
                    from .flow_recovery import recover_sections
                    recovered,recovery_report=recover_sections(segment,self.allowed,max(1.,self.min_route),reconstruct=user.get('reconstruct',False) and not r.get('explicit_cut',False))
                    self.raw_info[-1]['recovery_reports'].append(recovery_report)
                for safe_segment in recovered:
                    portals=(run_index==0,run_index==len(runs)-1)
                    self._add_flow_edge(safe_segment,q,a,b,r,base,kind,disabled,ring,both,offset,route_meta,spd,bool(user.get('recover')),portals)
                if self.arrow_mode=='dense':
                    for k in np.arange(15,d[-1],65 if kind=='main' else 30):
                        j=min(len(segment)-1,np.searchsorted(d,k));self.arrows.append((segment[j],tt[j]))
    def apply_ghost_zones(self):
        # 1.42.44: incremental; chamado logo após _bridge_runs para que recover_sections já enxergue o vão como permitido.
        n=len(self.ghost_zones);done=getattr(self,'_ghost_n',0)
        if n<=done:return
        self._ghost_n=n
        self.ghost_union=unary_union(self.ghost_zones)
        self.allowed=self.allowed.union(unary_union(self.ghost_zones[done:]))
    def is_ghost(self,pt):
        g=getattr(self,'ghost_union',None)
        return g is not None and not g.is_empty and bool(contains_xy(g,float(pt[0]),float(pt[1])))
    def _bridge_runs(self,lane,runs):
        """1.42.43: une trechos válidos do eixo separados por vazio de pavimento (canteiro, semáforo/faixa de pedestre, obra).
        O eixo precisa continuar e o pavimento precisa reaparecer depois; o vazio fica registrado em ``ghost_zones`` (veículo oculto, sem impedimento)."""
        good=[(int(a),int(b)) for a,b in runs if b-a>=8]
        if len(good)<2:return runs
        maxm=float(getattr(self.s,'traffic_bridge_max_m',150.));lead=float(getattr(self.s,'traffic_bridge_lead_m',5.))
        d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(lane,axis=0),axis=1))]
        merged=[good[0]]
        for a,b in good[1:]:
            pa,pb=merged[-1]
            gap=float(d[min(a,len(d)-1)]-d[pb-1])
            if gap>maxm:merged.append((a,b));continue
            # 2.12: só a AUSÊNCIA de pavimento é atravessada; canteiro/barreira real no vão continua sendo impedimento.
            med=getattr(self,'medians',None)
            if med is not None and not med.is_empty and LineString(lane[pb-1:a+1]).intersects(med):merged.append((a,b));continue
            start=float(d[pb-1])-lead;i0=max(0,int(np.searchsorted(d,start)))
            span=lane[i0:a+1]
            if len(span)>=2:
                half=max(2.,float(self.s.lane_width_m)/2+1.) if hasattr(self.s,'lane_width_m') else 3.5
                self.ghost_zones.append(LineString(span).buffer(half,cap_style=2))
                if not hasattr(self,'ghost_info'):self.ghost_info=[]
                self.ghost_info.append({'length_m':round(float(d[a]-d[pb-1]),1),'hidden_from_m':round(float(d[pb-1])-lead,1)})
            merged[-1]=(pa,b)
        return merged
    def _add_flow_edge(self,segment,q,a,b,r,base,kind,disabled,ring,both,offset,route_meta,spd,recovery,portals=(False,False)):
        tt=tangent(segment);d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(segment,axis=0),axis=1))]
        startpt=q[0] if np.linalg.norm(q[a]-q[0])<10 else q[a]
        endpt=q[-1] if np.linalg.norm(q[b-1]-q[-1])<10 else q[b-1]
        if recovery:startpt,endpt=segment[0],segment[-1]
        start=self.node(startpt,r['level']);end=self.node(endpt,r['level'])
        self.edges.append({'p':segment,'t':tt,'d':d,'length':d[-1],'start':start,'end':end,'base':base,'origin':r.get('origin',base),'origin_key':r.get('origin_key',''),'origin_aliases':r.get('origin_aliases',[]),'kind':kind,'source':r['source'],'sign':1 if self.chain(segment[-1:])[0]>=self.chain(segment[:1])[0] else -1,'level':r['level'],'cut_run':r.get('cut_run'),'disabled':disabled,'recovery':recovery,'ring':ring,'both':bool(both),'offset':float(offset),**route_meta,**({'route_fixed':True} if r.get('fixed') else {}),**({'speed':float(spd)/3.6} if spd else {})})
        if r.get('native_axis'):
            ends=self.original_terminals.get(r.get('origin'),[])
            self.edges[-1].update(native_start_portal=portals[0] and any(np.linalg.norm(q[0]-p)<.2 for p in ends),
                                  native_end_portal=portals[1] and any(np.linalg.norm(q[-1]-p)<.2 for p in ends))
    def paint(self,p,half,both,src=-1,edges=True):
        t=tangent(p);n=np.column_stack([t[:,1],-t[:,0]])
        specs=[(-max(1.3,half-.25),'edge'),(max(1.3,half-.25),'edge')] if edges else []
        if both:specs += [(-.12,'opposite'),(.12,'opposite')]
        elif half>3:specs += [(0,'same')]
        for offset,kind in specs:
            q=p+n*offset;valid=contains_xy(self.allowed,q[:,0],q[:,1]);stride=20 if kind=='same' else 3;length=7 if kind=='same' else 4
            for j in range(0,len(q)-2,stride):
                b=min(len(q),j+length)
                if valid[j:b].all():self.markings.append((q[j],q[b-1],(244,200,70) if kind=='opposite' else (244,242,226)));self.mark_src.append(src)
    def conflict_nodes(self):
        """Nós onde se encontram três ou mais trechos, ou onde vias de origens diferentes se ligam (convergência/divergência)."""
        deg=collections.Counter()
        for e in self.edges:
            if not e['disabled']:deg[e['start']]+=1;deg[e['end']]+=1
        out={n for n,c in deg.items() if c>=3}
        for (i,j) in self.connectors:
            if self.edges[i]['disabled'] or self.edges[j]['disabled']:continue
            if self.edges[i].get('origin')!=self.edges[j].get('origin'):out.add(self.edges[i]['end'])
        return out
    def smart_arrows(self,spacing):
        """Setas a cada `spacing` metros do eixo nas vias principais/marginais e antes/depois de cada ponto de conflito."""
        conflict=self.conflict_nodes();out=[]
        def at(e,d):
            j=int(min(len(e['p'])-1,max(0,np.searchsorted(e['d'],d))));return (e['p'][j],e['t'][j])
        for e in self.edges:
            if e['disabled'] or len(e['p'])<2:continue
            L=float(e['length'])
            if L<=0:continue
            if e['kind'] in ('main','marginal'):
                ch=self.chain(e['p']);k=np.floor(ch/max(spacing,1.))
                for j in np.flatnonzero(np.diff(k)!=0)+1:
                    if 12<e['d'][j]<L-12:out.append((e['p'][j],e['t'][j]))
                if L>=80:out.append(at(e,min(40.,L*.25)))
            if L>=20:
                if e['end'] in conflict:out.append(at(e,max(L*.5,L-25)))
                if e['start'] in conflict:out.append(at(e,min(L*.5,25.)))
        # 1.12: toda faixa direcional (ramos, alças, aproximações e anéis de rotatória) recebe ao menos uma seta.
        for e in self.edges:
            if e['disabled'] or len(e['p'])<2:continue
            L=float(e['length'])
            if L<8:continue
            have=[p for p,_ in out if np.min(np.linalg.norm(e['p']-p,axis=1))<1.5]
            if e['kind'] in ('main','marginal') and have:continue
            n=1 if L<90 else int(min(6,L//60))
            for k in range(n):
                d=(_sdiv(L*(k+.5), n))
                if any(np.linalg.norm(at(e,d)[0]-q)<20 for q in have):continue
                out.append(at(e,d))
        # Trechos do desenho sem itinerário de veículos também mostram o sentido (ex.: faixa curta junto à ilha).
        for r in self.raw_info:
            p=r['points']
            if r.get('route') or r['disabled'] or r['both'] or len(p)<10 or np.linalg.norm(p[-1]-p[0])<3:continue
            L=float(np.sum(np.linalg.norm(np.diff(p,axis=0),axis=1)))
            if L<10 or any(np.min(np.linalg.norm(p-q,axis=1))<2.5 for q,_ in out):continue
            j=len(p)//2;t=tangent(p)[j]*(1 if r['forward'] else -1)
            if contains_xy(self.allowed,p[j:j+1,0],p[j:j+1,1])[0]:out.append((p[j].copy(),t))
        kept=[]
        for pt,t in out:
            if all(np.linalg.norm(pt-q)>=12 or float(np.dot(t,u))<.7 for q,u in kept):kept.append((pt,t))
        self.conflicts=[self.nodes[n][0] for n in conflict]
        return kept
    def declutter(self):
        """Remove pinturas que se cruzam ou se sobrepõem vindas de trechos diferentes e as de ramos curtos junto a junções."""
        if not self.markings:return
        keep_edges=[m for m,s_ in zip(self.markings,self.mark_src) if s_==-2]
        self.markings=[m for m,s_ in zip(self.markings,self.mark_src) if s_!=-2];self.mark_src=[s_ for s_ in self.mark_src if s_!=-2]
        if not self.markings:
            self.markings=keep_edges;self.mark_src=[-2]*len(keep_edges);return
        A=np.array([m[0] for m in self.markings],float);B=np.array([m[1] for m in self.markings],float);src=np.array(self.mark_src)
        lengths={i:LineString(r['points']).length if len(r['points'])>1 else 0. for i,r in enumerate(self.raw_info)}
        rank=np.array([lengths.get(int(k),0.) for k in src]);kinds=[self.raw_info[int(k)]['kind'] if 0<=k<len(self.raw_info) else '' for k in src]
        D=B-A;L=np.linalg.norm(D,axis=1);U=D/np.maximum(L,1e-9)[:,None];M=(A+B)/2;drop=np.zeros(len(A),bool)
        drop|=L<.3
        def pseg(P,a,b):
            v=b-a;w=P-a;t=np.clip(np.sum(w*v,axis=-1)/np.maximum(np.sum(v*v,axis=-1),1e-12),0,1);return np.linalg.norm(w-v*t[...,None],axis=-1)
        pairs=cKDTree(M).query_pairs(3.2,output_type='ndarray').reshape(-1,2)
        if len(pairs):
            i,j=pairs[:,0],pairs[:,1];diff=src[i]!=src[j];i,j=i[diff],j[diff]
            dist=np.minimum.reduce([pseg(A[i],A[j],B[j]),pseg(B[i],A[j],B[j]),pseg(A[j],A[i],B[i]),pseg(B[j],A[i],B[i])])
            cos=np.abs(np.sum(U[i]*U[j],axis=1))
            bad=((cos<.906)&(dist<.8))|((cos>=.906)&(dist<.45))
            loser=np.where(rank[i[bad]]<rank[j[bad]],i[bad],j[bad])
            drop[loser]=True
        conf=getattr(self,'conflicts',None)
        if conf is None:conf=[self.nodes[n][0] for n in self.conflict_nodes()]
        if len(conf):
            near=cKDTree(np.array(conf)).query(M)[0]<7
            drop|=near&np.array([k!='main' for k in kinds])
        self.markings=[m for m,d in zip(self.markings,drop) if not d]+keep_edges;self.mark_src=[m for m,d in zip(self.mark_src,drop) if not d]+[-2]*len(keep_edges)
    def authoritative_lines(self):
        """2.15: linhas definidas pelo DXF (contorno do hatch de pavimento e Bordo). Quando uma linha gerada coincide com elas, a do DXF vence."""
        if getattr(self,'_auth',False) is not False:return self._auth
        parts=[]
        g=self.paved
        if g is not None and not g.is_empty:parts.append(g.boundary)
        parts+=[LineString(p) for p in self.dxf_edges if len(p)>=2]
        self._auth=unary_union(parts) if parts else None
        return self._auth
    def near_authoritative(self,mids,tol):
        auth=self.authoritative_lines();mids=np.asarray(mids,float)
        if auth is None or auth.is_empty or len(mids)==0:return np.zeros(len(mids),bool)
        import shapely
        return shapely.distance(auth,shapely.points(mids[:,0],mids[:,1]))<tol
    def axis_field(self):
        """Pontos e tangentes de todos os eixos (principal e nativos) para medir a perpendicularidade de linhas."""
        f=getattr(self,'_axis_field',None)
        if f is not None:return f
        pts=[self.dense];tans=[self.axis_t]
        for r in self.raw_info:
            q=np.asarray(r['points'],float)
            if len(q)>=3:
                q=q[::max(1,len(q)//400)]
                if len(q)>=3:pts.append(q);tans.append(tangent(q))
        P=np.vstack(pts);T=np.vstack(tans);self._axis_field=(cKDTree(P),T)
        return self._axis_field
    def perpendicular_to_axis(self,a,b,reach=30.,cos_max=.5):
        """True se o segmento a-b é transversal (> 60°) ao eixo mais próximo (até ``reach`` m): ex.: fim de bloco de hatch."""
        tree,T=self.axis_field();m=(np.asarray(a)+np.asarray(b))/2;d,i=tree.query(m)
        if d>reach:return False
        v=np.asarray(b)-np.asarray(a);n=float(np.linalg.norm(v))
        if n<1e-9:return False
        return abs((_sdiv(float(v@T[i]), n)))<cos_max
    def edge_lines(self,inset=.35,step=2.):
        """Linhas de bordo contínuas pelo contorno real do pavimento (inclusive rotatórias e alças), sem depender do esqueleto."""
        g=self.paved
        if g is None or g.is_empty:return
        # Fecha frestas entre hachuras vizinhas (evita linhas atravessando a pista).
        g=g.buffer(.6,join_style='mitre',mitre_limit=2.).buffer(-.6,join_style='mitre',mitre_limit=2.)
        inner=g.buffer(-inset,join_style='mitre',mitre_limit=2.)
        for poly in (list(inner.geoms) if hasattr(inner,'geoms') else [inner]):
            if poly.geom_type!='Polygon' or poly.is_empty:continue
            for ring in [poly.exterior]+list(poly.interiors):
                if ring.length<15:continue
                ln=LineString(ring.coords);n=max(2,int(ln.length/step))
                q=np.array([ln.interpolate(v).coords[0] for v in np.linspace(0,ln.length,n+1)])
                for a,b in zip(q[:-1],q[1:]):
                    if self.virtual is not None and self.virtual.distance(Point((a[0]+b[0])/2,(a[1]+b[1])/2))<1.2:self.virtual_dropped+=1;continue   # 2.18
                    if self.perpendicular_to_axis(a,b):self.perp_dropped=getattr(self,'perp_dropped',0)+1;continue   # 2.15: sem linhas fantasma perpendiculares ao eixo
                    self.markings.append((a,b,(244,242,226)));self.mark_src.append(-2)
    def add_dxf_edges(self,step=2.):
        """Bordos desenhados no DXF (tipo 'Bordo'): usados no lugar das linhas calculadas pelo contorno."""
        for p in self.dxf_edges:
            ln=LineString(p)
            if ln.length<2:continue
            n=max(1,int(ln.length/step));q=np.array([ln.interpolate(v).coords[0] for v in np.linspace(0,ln.length,n+1)])
            for a,b in zip(q[:-1],q[1:]):self.markings.append((a,b,(244,242,226)));self.mark_src.append(-2)
    def junction_zones(self):
        shapes=[Point(*self.nodes[n][0]).buffer(22) for n in self.conflict_nodes()]
        shapes+=[Point(*c).buffer(r+14) for c,r in getattr(self,'islands',[])]
        return unary_union(shapes) if shapes else Polygon()
    def finalize_signage(self):
        # 1.30: faixas de rota não entram na sinalização (pintura, setas, zebrados, linhas de parada).
        hide=[e for e in self.edges if e.get('route') and not e['disabled']]
        for e in hide:e['disabled']=True
        try:self._finalize_signage()
        finally:
            for e in hide:e['disabled']=False
    def _finalize_signage(self):
        if self.clean:
            # 1.12: eixos/divisórias só fora das junções; bordos pelo contorno do pavimento em todo o modelo.
            z=self.junction_zones()
            self._jz=z
            if not z.is_empty and self.markings:
                M=np.array([(m[0]+m[1])/2 for m in self.markings]);inside=contains_xy(z,M[:,0],M[:,1])
                self.markings=[m for m,k in zip(self.markings,inside) if not k];self.mark_src=[m for m,k in zip(self.mark_src,inside) if not k]
            if self.dxf_edges:self.add_dxf_edges()
            else:self.edge_lines()
        if self.arrow_mode=='km_conflicts':self.arrows=self.smart_arrows(float(getattr(self.s,'flow_arrow_spacing_m',1000)))
        elif self.arrow_mode=='off':self.arrows=[]
        if self.clean:self.declutter()
        if self.full:signage.build(self,self.dxf_h,self.dxf_v)
        areas=[Polygon([(p.x,p.y) for p in a]).buffer(0) for a in getattr(self.s,'clean_areas',[]) if len(a)>=3]
        if areas:
            g=unary_union(areas)
            if self.markings:
                M=np.array([(m[0]+m[1])/2 for m in self.markings]);inside=contains_xy(g,M[:,0],M[:,1])
                self.markings=[m for m,k in zip(self.markings,inside) if not k];self.mark_src=[m for m,k in zip(self.mark_src,inside) if not k]
            if self.arrows:
                P=np.array([a[0] for a in self.arrows]);inside=contains_xy(g,P[:,0],P[:,1])
                if len(self.arrow_kinds)==len(self.arrows):self.arrow_kinds=[a for a,k in zip(self.arrow_kinds,inside) if not k]
                if len(self.arrow_anchors)==len(self.arrows):self.arrow_anchors=[a for a,k in zip(self.arrow_anchors,inside) if not k]
                self.arrows=[a for a,k in zip(self.arrows,inside) if not k]
            signage.clean(self,g)
        self.report_signage={'markings':len(self.markings),'arrows':len(self.arrows),'mode':self.arrow_mode,'clean':self.clean,'full':self.full,'paint':len(self.fills),'signs':len(self.signs),'arrow_kinds':dict(collections.Counter(self.arrow_kinds))}
    def connector(self,a,b,force=False):
        if a.get('level',0)!=b.get('level',0):return None
        # Pontas dos sentidos opostos da mesma rota não são retornos. Recusar
        # essa ligação não pode invalidar os portais legítimos de ambas as faixas.
        if a.get('route') is not None and a.get('route')==b.get('route') and a.get('route_dir')!=b.get('route_dir'):
            self.rejected_connectors['contramao_rota']+=1;return None
        if a.get('origin')==b.get('origin') and a.get('cut_run')!=b.get('cut_run'):return None
        ta=a['t'][-1];tb=b['t'][0];cos=float(np.dot(ta,tb))
        node=self.nodes[a['end']][0]
        if force:
            pa=a['p'][-1];pb=b['p'][0];gap=np.linalg.norm(pb-pa)
            if gap>30 or cos<-.85:return None
        if not self.no_connect.is_empty and self.no_connect.covers(Point(node)):
            # Dentro do cruzamento sem conexão só existe continuidade da mesma via.
            if a.get('origin')!=b.get('origin') or cos<.9:return None
        if not getattr(self,'classic',False) and not self.bridges.is_empty and self.bridges.covers(Point(node)) and cos<.72:return None
        if cos<-.85:
            self.rejected_nodes.update((a['end'],b['start']));return None
        if a.get('route') is not None and a.get('route')==b.get('route') and a.get('route_dir')!=b.get('route_dir'):
            self.rejected_connectors['contramao_rota']+=1;self.rejected_nodes.update((a['end'],b['start']));return None
        pa=a['p'][-1];pb=b['p'][0];gap=np.linalg.norm(pb-pa)
        if gap>(30 if force else 18):return None
        lateral=abs(float(ta[0]*(pb-pa)[1]-ta[1]*(pb-pa)[0]))
        explicit=force or a.get('route') is not None or b.get('route') is not None
        if 1e-6<=gap<6 and (cos<.9 or explicit and lateral>.02):
            rounded=self.rounded_contact(a,b)
            if rounded is not None:return rounded
        if gap<1e-6:
            if cos<.995:return self.rounded_contact(a,b)
            return np.vstack([pa,pb])
        control=max(.05,gap*.55);u=np.linspace(0,1,max(8,int((gap+control*2)/.35)));c1=pa+ta*control;c2=pb-tb*control
        p=(1-u[:,None])**3*pa+3*(1-u[:,None])**2*u[:,None]*c1+3*(1-u[:,None])*u[:,None]**2*c2+u[:,None]**3*pb
        p,_=sample(p,.35)
        if not self.no_connect.is_empty and a.get('origin')!=b.get('origin') and LineString(p).intersects(self.no_connect):return None
        audit=self.motion_audit(np.vstack([a['p'][-min(len(a['p']),20):],p[1:-1],b['p'][:min(len(b['p']),20)]]))
        if not audit['ok']:
            self.rejected_connectors.update(audit['reasons']);self.rejected_nodes.update((a['end'],b['start']));return None
        if not valid_centers(self.allowed,p).all():return None
        for pt,t in zip(p[::2],tangent(p)[::2]):
            n=np.array([-t[1],t[0]]);body=Polygon([pt+t*x+n*y for x,y in [(-2.3,-.95),(2.3,-.95),(2.3,.95),(-2.3,.95)]])
            if not self.allowed.covers(body):return None
        return p
    def rounded_contact(self,a,b):
        """Ligação tangente com recuo local; só quando cabe no pavimento real."""
        if len(a['p'])<2 or len(b['p'])<2:return None   # 2.27: trajetória degenerada não pode derrubar o cálculo
        first,second=LineString(a['p']),LineString(b['p'])
        for requested in (8.,12.,18.,24.):
            setback=min(requested,first.length*.4,second.length*.4)
            if setback<5:continue
            pa=np.array(first.interpolate(first.length-setback).coords[0]);pb=np.array(second.interpolate(setback).coords[0])
            ta=np.array(first.interpolate(first.length-setback+.25).coords[0])-np.array(first.interpolate(first.length-setback-.25).coords[0]);ta/=max(float(np.linalg.norm(ta)),1e-9)
            tb=np.array(second.interpolate(setback+.25).coords[0])-np.array(second.interpolate(setback-.25).coords[0]);tb/=max(float(np.linalg.norm(tb)),1e-9)
            u=np.linspace(0,1,max(33,int(setback*4)));v=u[:,None];c1=pa+ta*setback*.65;c2=pb-tb*setback*.65
            p=(1-v)**3*pa+3*(1-v)**2*v*c1+3*(1-v)*v*v*c2+v**3*pb
            if not self.no_connect.is_empty and LineString(p).intersects(self.no_connect):continue
            before=np.array(substring(first,max(0,first.length-setback-15),first.length-setback).coords)
            after=np.array(substring(second,setback,min(second.length,setback+15)).coords)
            if not self.motion_audit(np.vstack([before,p[1:-1],after]),allowed=self.allowed)['ok']:continue
            if not valid_centers(self.allowed,p).all():continue
            from .vehicle_safety import body
            if any(not self.allowed.covers(body(c,h,4.6,1.9)) for c,h in zip(p,tangent(p))):continue
            return p
        return None

    def apply_connection_rules(self):
        """1.27: regras do usuário: proibir um movimento (trecho de chegada -> trecho de saída) ou forçar uma ligação."""
        self.forced=set();self.denied=[];self.rule_report=[]
        rules=[r for r in getattr(self.s,'connection_rules',[]) or [] if r.enabled]
        if not rules:return
        def dist(e,q):
            P=e['p'];return float(np.min(np.linalg.norm(P[::2]-q,axis=1))) if len(P) else math.inf
        for r in rules:
            A=np.array([r.a.x,r.a.y]);B=np.array([r.b.x,r.b.y])
            dA={i:dist(e,A) for i,e in enumerate(self.edges) if not e['disabled'] and (not r.from_key or r.from_key in e.get('origin_aliases',[]))};dB={i:dist(e,B) for i,e in enumerate(self.edges) if not e['disabled'] and (not r.to_key or r.to_key in e.get('origin_aliases',[]))}
            ins=[i for i,d in dA.items() if d<=8];outs=[j for j,d in dB.items() if d<=8]
            best=None
            if r.action=='deny':
                for i in ins:
                    for j in self.connections.get(i,[]):
                        if j in outs and (best is None or dA[i]+dB[j]<best[0]):best=(dA[i]+dB[j],i,j)
                if best:
                    _,i,j=best;self.connections[i]=[x for x in self.connections[i] if x!=j];self.denied.append((i,j,self.connectors.pop((i,j)),r.id or r.name))
                    self.rule_report.append({'rule':r.id or r.name,'action':'deny','applied':True})
                else:self.rule_report.append({'rule':r.id or r.name,'action':'deny','applied':False});self.warnings.append(f'Regra de ligação “{r.name}”: movimento não encontrado (confira os pontos sobre os dois trechos).')
            else:
                existing=[(i,j) for i in ins for j in self.connections.get(i,[]) if j in outs]
                if existing:
                    i,j=min(existing,key=lambda pair:dA[pair[0]]+dB[pair[1]])
                    self.rule_report.append({'rule':r.id or r.name,'action':'force','applied':True,'existing':True,'from_edge':i,'to_edge':j,'share_pct':r.share_pct});continue
                for i in ins:
                    for j in outs:
                        if i==j or self.edges[i]['base']==self.edges[j]['base'] or j in self.connections.get(i,[]) or any(x==i and y==j for x,y,_,_ in self.denied):continue
                        g=float(np.linalg.norm(self.edges[j]['p'][0]-self.edges[i]['p'][-1]))
                        if g>30:continue
                        sc=dA[i]+dB[j]+g*.2
                        if best is None or sc<best[0]:best=(sc,i,j)
                if best is None and any(j in outs for i in ins for j in self.connections.get(i,[])):
                    i,j=min(((i,j) for i in ins for j in self.connections.get(i,[]) if j in outs),key=lambda ij:dA[ij[0]]+dB[ij[1]])
                    self.rule_report.append({'rule':r.id or r.name,'action':'force','applied':True,'existing':True,'from_edge':i,'to_edge':j,'share_pct':r.share_pct});continue
                c=self.connector(self.edges[best[1]],self.edges[best[2]],force=True) if best else None
                if c is not None:
                    _,i,j=best;self.connections[i].append(j);self.connectors[(i,j)]=c;self.forced.add((i,j))
                    self.rule_report.append({'rule':r.id or r.name,'action':'force','applied':True,'from_edge':i,'to_edge':j,'share_pct':r.share_pct})
                else:
                    self.rule_report.append({'rule':r.id or r.name,'action':'force','applied':False})
                    self.warnings.append(f'Regra de ligação “{r.name}”: não foi possível ligar os trechos (pontas a mais de 30 m, retorno de 180° ou a ligação sairia da pista).')
    def bfs(self,start,targets,adj):
        queue=collections.deque([(start,[start])]);seen={start}
        while queue:
            n,path=queue.popleft()
            if n in targets:return path
            for nxt in adj.get(n,[]):
                if nxt not in seen:seen.add(nxt);queue.append((nxt,path+[nxt]))
        return None
    def side(self,p):
        """Pista (índice do eixo principal mais próximo) quando o ponto está nela; None fora das pistas principais."""
        if len(self.main)<2:return None
        d=[float(tr.query(p)[0]) for tr in self.main_trees];i=int(np.argmin(d))
        return i if d[i]<12 else None
    def crossing_rules(self):
        """Travessia do canteiro central só em retornos (em desnível pela OAE, rotatórias ou retorno em nível)
        ou em locais permitidos pelo operador. Trechos e ligações que trocam de pista fora disso ficam sem veículos."""
        mode='none' if getattr(self.s,'traffic_no_median_crossing',False) else getattr(self.s,'median_crossing','returns');self.crossings_blocked=0
        zones=getattr(self.s,'crossing_zones',[]) or []
        def zone(z):
            from .markup import _xy
            return Point(*_xy(z.point)).buffer(z.radius_m) if z.kind=='point' else Polygon([_xy(v) for v in z.points]).buffer(0)
        allow=unary_union([zone(z) for z in zones if z.mode=='allow']) if any(z.mode=='allow' for z in zones) else Polygon()
        deny=unary_union([zone(z) for z in zones if z.mode=='deny']) if any(z.mode=='deny' for z in zones) else Polygon()
        if not deny.is_empty:
            for e in self.edges:
                if not e['disabled'] and LineString(e['p']).intersects(deny):e['disabled']=True;e['crossing_blocked']=True;self.crossings_blocked+=1
            for (i,j),c in list(self.connectors.items()):
                if LineString(c).intersects(deny):
                    self.connections[i]=[x for x in self.connections[i] if x!=j];del self.connectors[(i,j)];self.crossings_blocked+=1
        if mode=='free' or len(self.main)<2:
            if self.crossings_blocked:self.warnings.append(f'{self.crossings_blocked} movimentos excluídos por proibição explícita de travessia.')
            return
        rings=unary_union([Point(*c).buffer(r+12) for c,r in self.islands]) if self.islands else Polygon()
        def ok(pts,kind):
            line=LineString(pts) if len(pts)>1 else Point(pts[0])
            if not deny.is_empty and line.intersects(deny):return False
            if mode=='none':return False
            if not allow.is_empty and line.intersects(allow):return True
            if not self.bridges.is_empty and line.intersects(self.bridges):return True
            if not rings.is_empty and line.intersects(rings):return True
            return mode=='returns' and kind=='return' and line.length>=6
        for i,e in enumerate(self.edges):
            if e['disabled']:continue
            # Um eixo CAD nativo não troca de pista só porque outra linha
            # perpendicular passou a ser a referência mais próxima. Obstáculos
            # físicos já recortam allowed; proibições explícitas foram aplicadas acima.
            if e.get('native_axis'):continue
            a=self.side(e['p'][0]);b=self.side(e['p'][-1])
            if a is not None and b is not None and a!=b and not ok(e['p'],e['kind']):e['disabled']=True;e['crossing_blocked']=True;self.crossings_blocked+=1
        for (i,j),c in list(self.connectors.items()):
            first,second=self.edges[i],self.edges[j]
            if first.get('native_axis') and second.get('native_axis') and first.get('origin')==second.get('origin'):continue
            a=self.side(self.edges[i]['p'][-1]);b=self.side(self.edges[j]['p'][0])
            if a is not None and b is not None and a!=b and not ok(c,'connector'):
                self.connections[i]=[x for x in self.connections[i] if x!=j];del self.connectors[(i,j)];self.crossings_blocked+=1
        if self.crossings_blocked:self.warnings.append(f'{self.crossings_blocked} trecho(s)/ligação(ões) atravessavam o canteiro fora de retornos e ficaram sem veículos (ajuste com "Travessia permitida").')
    def short_edges(self,min_len):
        """1.39: trechos (fora do eixo principal do DXF, não desenhados pelo operador, fora do anel das rotatórias) cujo trecho original
        tem menos de min_len metros: são ramos curtos do esqueleto nos encontros, que faziam os veículos ziguezaguear."""
        if min_len<=0:return set()
        out=set()
        for i,e in enumerate(self.edges):
            L,keep=self.origin_info.get(e.get('origin'),(e['length'],False))
            if L<min_len:out.add(i)
        return out
    def portal_allowed(self,edge,start):
        p=edge['p'][0 if start else -1];origin=edge.get('origin')
        ends=getattr(self,'original_terminals',{}).get(origin,[])
        flag='native_start_portal' if start else 'native_end_portal'
        if any(edge.get(k,'automatico')!='automatico' for k in ('flow_role','flow_start','flow_end')) and any(np.linalg.norm(p-q)<4 for q in ends):
            from .flow_nodes import endpoint_kind
            kind=endpoint_kind(edge,start)
            if start and kind in ('saida','fim'):return False
            if not start and kind=='entrada':return False
            if kind=='conexao':return False
        if edge.get('native_axis') and flag in edge:return edge[flag]
        if any(np.linalg.norm(p-q)<4 for q in ends):return True
        if edge.get('native_axis'):return False  # Lacunas internas não viram entradas/saídas.
        return not any(np.linalg.norm(p-q)<4 for q in getattr(self,'pruned_contacts',{}).get(origin,[]))
    def endpoint_available(self,edge,start):
        node=edge['start' if start else 'end']
        if node not in self.rejected_nodes:return True
        if not (edge.get('route_fixed') or edge.get('native_axis')):return False
        if edge.get('native_axis'):return self.portal_allowed(edge,start)
        # Um conector recusado de outra via não fecha a ponta explicitamente
        # desenhada da rota. Cortes internos/superfície inválida não ganham portais.
        p=edge['p'][0 if start else -1]
        return any(np.linalg.norm(p-q)<.2 for q in self.original_terminals.get(edge.get('origin'),[]))

    def make_itineraries(self,min_len=0.):
        self.paths=[]
        short=self.short_edges(min_len);self.short_ignored=short
        for i in list(self.connections):
            if self.edges[i]['disabled']:self.connections[i]=[]
        # As ligações físicas continuam; só as rotas deixam de usar os trechos curtos.
        conn={i:([] if i in short else [j for j in bs if j not in short]) for i,bs in self.connections.items()}
        cx=dict(self.connectors);self.route_connectors={}   # atalhos só das rotas (não entram na pintura nem no editor)
        if short:
            # Atalho: quem chegava ao trecho curto liga direto (curva suave dentro da pista) a quem saía dele.
            rev={}
            for a,bs in self.connections.items():
                for b in bs:rev.setdefault(b,[]).append(a)
            def ends(k,fwd,seen):
                # Trechos não curtos alcançados atravessando só trechos curtos (no máximo 4).
                out=[]
                for x in (self.connections.get(k,[]) if fwd else rev.get(k,[])):
                    if self.edges[x]['disabled'] or x in seen:continue
                    if x in short:
                        if len(seen)<4:out+=ends(x,fwd,seen|{x})
                    else:out.append(x)
                return out
            for k in short:
                if self.edges[k]['disabled']:continue
                for a in set(ends(k,False,{k})):
                    for b in set(ends(k,True,{k})):
                        if a==b or b in conn[a] or self.edges[a]['base']==self.edges[b]['base'] or any(x==a and y==b for x,y,_,_ in getattr(self,'denied',[])):continue
                        sa=self.side(self.edges[a]['p'][-1]);sb=self.side(self.edges[b]['p'][0])
                        if sa is not None and sb is not None and sa!=sb and getattr(self.s,'median_crossing','returns')!='free':continue
                        c=self.connectors.get((a,b))
                        if c is None:c=self.connector(self.edges[a],self.edges[b],force=True)
                        if c is not None:conn[a].append(b);cx[(a,b)]=c;self.route_connectors[(a,b)]=c
        reverse={i:[] for i in conn}
        for a,bs in conn.items():
            for b in bs:reverse[b].append(a)
        live={i for i in conn if not self.edges[i]['disabled'] and i not in short}
        for k in list(reverse):reverse[k]=[a for a in reverse[k] if not self.edges[a]['disabled']]
        # Origem/destino pela rede completa: tirar um trecho curto não cria pontas novas no meio da via.
        rfull={i:[] for i in self.connections}
        for a_,bs_ in self.connections.items():
            for b_ in bs_:
                if not self.edges[a_]['disabled']:rfull[b_].append(a_)
        entries={i for i in live if not reverse[i] and not rfull[i] and self.endpoint_available(self.edges[i],True) and self.portal_allowed(self.edges[i],True)};exits={i for i in live if not conn[i] and not self.connections[i] and self.endpoint_available(self.edges[i],False) and self.portal_allowed(self.edges[i],False)}
        main_entries={i for i in entries if self.edges[i]['kind']=='main'};main_exits={i for i in exits if self.edges[i]['kind']=='main'}
        entries=(main_entries|{i for i in entries if self.edges[i].get('native_axis') or self.edges[i].get('flow_role','automatico')!='automatico'}) or entries
        exits=(main_exits|{i for i in exits if self.edges[i].get('native_axis') or self.edges[i].get('flow_role','automatico')!='automatico'}) or exits
        # 1.18: a ponta de um acesso desenhado pelo operador também é origem/destino dos veículos.
        ends=[np.array([a.points[-1].x,a.points[-1].y]) for a in getattr(self.s,'accesses',[]) or [] if a.enabled and len(a.points)>=2]
        if ends:
            E_=np.array(ends)
            near=lambda p:float(np.min(np.linalg.norm(E_-p,axis=1)))<15
            entries=entries|{i for i in live if not reverse[i] and not rfull[i] and near(self.edges[i]['p'][0])}
            exits=exits|{i for i in live if not conn[i] and not self.connections[i] and near(self.edges[i]['p'][-1])}
        self.apply_ghost_zones()
        seen=set();covered=set();self.missing_reasons={}
        todos=[i for i in range(len(self.edges)) if not self.edges[i]['disabled'] and i not in short]
        # 1.42.38 (2.00): a ordem só muda quando há mais trechos que o limite de rotas, para o corte não cair no eixo principal; abaixo disso o resultado é idêntico ao anterior.
        targets=sorted(todos,key=(lambda i:self.edges[i]['kind']!='main') if len(todos)>256 else (lambda i:self.edges[i]['kind']=='main'))
        for i in targets:
            before=self.bfs(i,entries,reverse);after=self.bfs(i,exits,conn)
            if not before or not after:self.missing_reasons.setdefault(i,'sem ligação até uma entrada' if not before else 'sem ligação até uma saída');continue
            seq=list(reversed(before))+after[1:];key=tuple(seq)
            if key in seen:continue
            pts=[];marks=[];invalid=False
            for j,e in enumerate(seq):
                edge_line=LineString(self.edges[e]['p']);start=0.;end=edge_line.length
                if j:
                    previous_curve=cx[(seq[j-1],e)];start=edge_line.project(Point(previous_curve[-1]));pts.extend(previous_curve[1:-1])
                if j+1<len(seq):end=edge_line.project(Point(cx[(e,seq[j+1])][0]))
                if end-start<.1:invalid=True;break
                part=np.asarray(substring(edge_line,start,end).coords)
                marks.append((e,len(pts)));pts.extend(part);marks[-1]=(e,marks[-1][1],len(pts)-1,float(start))
            if invalid:self.missing_reasons.setdefault(i,'trecho curto demais entre conectores');continue
            P=np.asarray(pts);cum=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))]
            p,d=sample(P,STEP)
            if self.smooth_paths:
                # Suavizada > só sem recuos > como antes: vale a primeira que mantém o veículo dentro da pista.
                native=all(self.edges[e].get('native_axis') for e in seq)
                candidates=(lambda:steady_path(P,self.allowed,sigma_m=.8),) if native else (lambda:steady_path(P,self.allowed),lambda:sample(drop_backtracks(P),STEP))
                for cand in candidates:
                    q,dq=cand()
                    if native and q is not None and _hausdorff(q,P)>.5:continue
                    if q is not None and len(q)>=10 and valid_centers(self.allowed,q).all():p,d=q,dq;break
            if len(p)<10 or d[-1]<max(1.,min_len) or not valid_centers(self.allowed,p).all():self.missing_reasons.setdefault(i,'rota curta ou fora da pista');continue
            audit=self.motion_audit(p,allowed=self.allowed)
            if not audit['ok']:
                self.rejected_paths.append({'edges':list(seq),'audit':audit})
                self.rejected_edge_ids.update(seq)
                for e_ in seq:self.missing_reasons.setdefault(e_,'reprovado na análise de frente/traseira ou esterçamento')
                continue
            # 1.12: trechos físicos do itinerário (arestas e conectores) para a simulação sem colisão.
            links=[];link_offsets=[];prev=None
            for e,a,b,offset in marks:
                if prev is not None:links.append((('c',prev[0],e),float(cum[prev[2]]),float(cum[a])));link_offsets.append(0.)
                links.append((('e',e),float(cum[a]),float(cum[b])));link_offsets.append(offset);prev=(e,a,b)
            meta={}
            route_edges=[self.edges[e] for e in seq if self.edges[e].get('route') is not None]
            if route_edges and len(route_edges)==len(seq):
                rid={e.get('route') for e in route_edges};rdir={e.get('route_dir') for e in route_edges};rlane={e.get('route_lane') for e in route_edges}
                if len(rid)==len(rdir)==len(rlane)==1:
                    e0=route_edges[0];meta={k:e0.get(k) for k in ('route','route_name','route_dir','route_lane','route_lane_width_m','route_start_m','route_end_m','lane_change','lane_change_sections','axis_type') if e0.get(k) is not None}
            from .flow_terminals import inset_path
            path=inset_path({'p':p,'t':tangent(p),'d':d,'length':d[-1],'edges':seq,'kinds':sorted({self.edges[e]['kind'] for e in seq}),'links':links,'link_offsets':link_offsets,**meta},self.operational_pavement,float(self.s.traffic_entry_inset_m))
            if path is None or path['length']<max(1.,min_len):self.missing_reasons.setdefault(i,'rota curta após o recuo dos portais');continue
            self.paths.append(path);seen.add(key);covered.update(seq)
            if len(self.paths)>=256:break
        # Recuperação solicitada: os restos válidos são fluxos separados, nunca atalhos.
        recovered_paths=0
        for i,e in enumerate(self.edges):
            if i in covered or e.get('disabled') or i in short or not e.get('recovery'):continue
            if len(self.paths)>=256:break
            p=e['p'];d=e['d']
            if d[-1]<max(1.,min_len) or not self.motion_audit(p,allowed=self.allowed)['ok']:continue
            self.paths.append({'p':p,'t':tangent(p),'d':d,'length':d[-1],'edges':[i],'kinds':[e['kind']],'links':[(('e',i),0.,float(d[-1]))],**{k:e[k] for k in ('route','route_name','route_dir','route_lane','route_lane_width_m','lane_change','lane_change_sections','axis_type') if k in e}})
            covered.add(i);recovered_paths+=1
        self.recovered_paths=sum(any(self.edges[k].get('recovery') for k in row['edges']) for row in self.paths)
        recovered_paths=self.recovered_paths
        if recovered_paths:self.warnings.append(f'{recovered_paths} fluxo(s) principal(is) recuperado(s) por solicitação do usuário; partes reprovadas permanecem sem veículos e sem ligação através das lacunas.')
        missing=[i for i in range(len(self.edges)) if i not in covered and not self.edges[i]['disabled'] and i not in short]
        off=sum(1 for e in self.edges if e['disabled'] and not e.get('crossing_blocked'))
        if off:self.warnings.append(f'{off} segmentos desativados pelo usuário (geometria preservada; reative em Fluxos).')
        if len(self.paths)>=256 and missing:self.warnings.append(f'Limite de 256 rotas atingido: {len(missing)} segmento(s) podem ficar sem veículos por causa desse limite (não por defeito de geometria). Reduza o trecho analisado ou desative fluxos que não precisam circular.')
        if missing:
            motivos=collections.Counter(self.missing_reasons.get(i,'limite de rotas' if len(self.paths)>=256 else 'não alcançado por nenhuma rota') for i in missing)
            self.missing_summary=dict(motivos)
            self.warnings.append(f'{len(missing)} segmentos sem itinerário seguro completo; confira os eixos/conexões na prévia. Esses segmentos não recebem veículos isolados. Motivos: '+'; '.join(f'{n} {m}' for m,n in motivos.most_common())+'.')
        if short:self.warnings.append(f'{len(short)} trecho(s) curto(s) (< {min_len:g} m) ignorados nas rotas dos veículos (sem ziguezague).')
        # Aresta usada por uma alternativa válida não é marcada como excluída.
        self.rejected_edge_ids.update(i for i,e in enumerate(self.edges) if (e['start'] in self.rejected_nodes or e['end'] in self.rejected_nodes) and i not in covered)
        self.rejected_edge_ids.difference_update(covered)
        if self.rejected_paths:self.warnings.append(f'{len(self.rejected_paths)} itinerário(s) recusado(s) pela análise de frente/traseira, esterçamento ou continuidade. Não recebem veículos.')
        self.covered=covered
    def vehicles(self,t,speed):
        for pt,tan,k,identity,j in self.vehicles_ex(t,speed):yield pt,tan,k,identity
    def vehicles_ex(self,t,speed,vehicle_type=None):
        from .vehicle_motion import prepare_points,axle_geometry_prepared
        if not math.isfinite(float(speed)) or speed<=0 or not math.isfinite(float(t)):return
        if not hasattr(self,'legacy_motion_cache'):self.legacy_motion_cache={};self.legacy_motion_points={}
        for i,path in enumerate(self.paths):
            L=float(path['length'])
            if not math.isfinite(L) or L<=0:continue
            if (i,'car') not in self.legacy_motion_cache:self.legacy_motion_cache[(i,'car')]=self.motion_audit(path['p'],'car',self.allowed)
            audit=self.legacy_motion_cache[(i,'car')]
            if not audit['ok']:continue
            angle=math.radians(audit['max_steering_deg'] or 0.)
            radius=2.7/max(math.tan(angle),1e-9);route_speed=min(speed,math.sqrt(2.2*radius))
            duration=L/route_speed;count=max(1,min(16,int(L/350)));period=duration+5
            for k in range(count):
                phase=t+(k+.3)*period/count+i*2.1;cycle=math.floor(phase/period);local=phase-cycle*period
                if local>=duration:continue
                identity=(i,k,cycle);vt=vehicle_type(path['kinds'],identity) if vehicle_type else 'car';key=(i,vt)
                if key not in self.legacy_motion_cache:self.legacy_motion_cache[key]=self.motion_audit(path['p'],vt,self.allowed)
                if not self.legacy_motion_cache[key]['ok']:continue
                if i not in self.legacy_motion_points:self.legacy_motion_points[i]=prepare_points(path['p'])
                distance=local*route_speed;j=min(len(path['p'])-1,int(np.searchsorted(path['d'],distance)))
                g=axle_geometry_prepared(*self.legacy_motion_points[i],vt,np.array([distance]))
                yield g['center'][0],g['heading'][0],i*17+k,identity,j
