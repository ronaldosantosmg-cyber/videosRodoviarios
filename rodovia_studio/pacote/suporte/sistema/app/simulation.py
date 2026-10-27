"""1.12: tráfego simulado sem colisões (modelo de seguimento IDM), com engarrafamento, interdições e desvios.

Os veículos seguem os itinerários validados da rede (arestas + conectores). Cada trecho físico é
compartilhado por todos os itinerários que passam por ele, então o veículo de trás sempre "vê" o da
frente, mesmo vindo de outra origem. Nas convergências, quem vem da via principal tem prioridade e o
ramo cede passagem (sem sobreposição). A simulação é calculada uma vez, antes da montagem, com passo de
0,2 s e aquecimento de 90 s, e o quadro t só interpola posições: o resultado é idêntico em qualquer
número de processos.

Limitações: uma trajetória por sentido em cada pista (sem troca de faixa); ilustrativo, não é um
modelo de tráfego calibrado.
"""
from .tempo import tempo
from .vehicle_motion import analyze_motion,axle_geometry_prepared,prepare_points,interpolate,PROFILES
import math,bisect,collections
import numpy as np
from shapely.geometry import Polygon,Point,LineString
from shapely import contains_xy

DT=.2
WARMUP=90.
IDM={'a':1.2,'b':2.0,'s0':2.5,'T':1.4}
SPEED_FACTOR={'car':1.0,'truck':.82,'bus':.88,'moto':1.04,'van':.95,'pickup':1.0,'carreta':.78}
# 1.40.5: dinâmica por classe. PCU controla a descarga/capacidade da faixa; veículos pesados
# aceleram/freiam de forma mais lenta e induzem maior headway no seguidor.
TYPE_DYN={
 'car':{'a':1.35,'b':2.2,'T':1.35,'s0':2.3,'pcu':1.0,'heavy':False},
 'pickup':{'a':1.2,'b':2.1,'T':1.4,'s0':2.5,'pcu':1.0,'heavy':False},
 'van':{'a':1.05,'b':2.0,'T':1.5,'s0':2.8,'pcu':1.1,'heavy':False},
 'moto':{'a':1.5,'b':2.4,'T':1.15,'s0':1.8,'pcu':.55,'heavy':False},
 'truck':{'a':.72,'b':1.45,'T':2.05,'s0':3.5,'pcu':2.0,'heavy':True},
 'bus':{'a':.78,'b':1.5,'T':1.95,'s0':3.3,'pcu':1.8,'heavy':True},
 'carreta':{'a':.58,'b':1.25,'T':2.3,'s0':4.2,'pcu':2.5,'heavy':True},
}

for _alias,_base in [('car6','car'),('moto2','moto'),('truck18','truck'),('long30','carreta')]:
    SPEED_FACTOR[_alias]=SPEED_FACTOR[_base];TYPE_DYN[_alias]=dict(TYPE_DYN[_base])

def _xy(p):return (p.x,p.y) if hasattr(p,'x') else (p['x'],p['y'])

class Block:
    def __init__(self,b):
        self.poly=Polygon([_xy(v) for v in b.points]).buffer(0);self.mode=b.mode;self.speed=max(1.,b.speed_kmh/3.6)
        self.start=float(b.start_s or 0);self.end=float(b.end_s) if b.end_s is not None else math.inf;self.name=b.name
    def active(self,t):return self.start<=t<self.end

LAT_ACC=2.2    # m/s² de aceleração lateral confortável nas curvas
DECEL_ENV=1.6  # m/s² de desaceleração antecipada antes da curva

def curve_envelope(p,d,smooth_m=6.,lateral_acc=LAT_ACC):
    """1.27: velocidade máxima ao longo do itinerário: sqrt(a_lat/curvatura), já com a frenagem antecipada."""
    p=np.asarray(p,float);d=np.asarray(d,float);n=len(p)
    if n<5:return None
    t=np.gradient(p,axis=0);ang=np.unwrap(np.arctan2(t[:,1],t[:,0]));ds=np.gradient(d);ds[ds<1e-6]=1e-6
    k=np.abs(np.gradient(ang)/ds)
    step=max(1e-6,float(np.median(np.diff(d))));w=min(n,max(1,int(round(smooth_m/step))))
    if w>1:k=np.convolve(k,np.ones(w)/w,mode='same')
    v=np.sqrt(lateral_acc/np.maximum(k,1e-6));v=np.clip(v,1.,60.)
    for i in range(n-2,-1,-1):v[i]=min(v[i],math.sqrt(v[i+1]**2+2*DECEL_ENV*(d[i+1]-d[i])))
    return v.astype(np.float32)

class TrafficSim:
    """Microssimulação longitudinal + mudança de faixa segura (1.40.4).

    Princípios:
    - IDM controla o seguimento normal;
    - uma barreira física de segurança limita o deslocamento antes da integração, portanto a animação
      não depende de detectar colisão depois que ela já aconteceu;
    - mudança de faixa é negada por padrão quando a rota está em modo ``marked`` e só é aceita quando
      TODA a manobra cabe num trecho ``allow`` sem cruzar nenhum trecho ``deny``;
    - veículos em mudança de faixa ocupam simultaneamente a faixa de origem e a de destino para impedir
      sobreposição/side-swipe;
    - raios/curvaturas reduzem a velocidade e são reportados; a geometria nunca é modificada aqui.
    """
    HARD_GAP=2.0
    LC_DURATION=4.0
    LC_COOLDOWN=5.0
    LC_GAIN=12.0

    def __init__(self,network,settings,vtype,duration=None,status=lambda *a:None):
        self.net=network;s=settings;self.s=s
        self.v0=s.traffic_speed_kmh/3.6;self.density=float(getattr(s,'traffic_density',1.))
        self.duration=float(duration if duration is not None else s.duration_s)
        self.paths=network.paths;self.vtype=vtype;self.motion_cache={};self.motion_blocked=0;self.lc_blocked_geometry=0
        self.capacity_vphpl=float(getattr(s,'traffic_capacity_vphpl',1900.))
        self.capacity_model=bool(getattr(s,'queue_capacity_model',True))
        self.heavy_reaction=bool(getattr(s,'heavy_vehicle_reaction',True))
        self.blocks=[Block(b) for b in getattr(s,'lane_blocks',[]) if len(b.points)>=3]
        self.prepare();
        from .transport import Transport
        self.transport=Transport(settings,network);self.control_stops=0;self.node_routing=any(e.get('flow_role','automatico')!='automatico' for e in network.edges);self.dynamic_reroutes=0
        from .alternating_traffic import AlternatingTraffic
        from .vehicle_safety import PolygonSafety
        self.alternating=AlternatingTraffic(settings,network);self.polygon_safety=PolygonSafety(self)
        from .shoulder_probe import ShoulderProbe
        self.shoulder_probe=ShoulderProbe(self)
        from .pedestrian_traffic import PedestrianTraffic
        self.pedestrians=PedestrianTraffic(settings,network,self.transport,self)
        self.lane_events=[]
        self.run(status)

    # ---------- preparação ----------
    def prepare(self):
        P=self.paths;self.link_of=[];self.link_offsets=[];self.starts=[];self.motion_points=[prepare_points(p["p"]) for p in P]
        for i,path in enumerate(P):
            links=path.get('links') or [(('e',-1-i),0.,float(path['length']))]
            total=links[-1][2] or 1.;k=float(path['length'])/total
            L=[(lid,a*k,b*k) for lid,a,b in links];L[0]=(L[0][0],0.,L[0][2]);L[-1]=(L[-1][0],L[-1][1],float(path['length']))
            self.link_of.append(L);self.link_offsets.append(list(path.get('link_offsets',[0.]*len(L))));self.starts.append([a for _,a,_ in L])
        kinds={}
        for i,path in enumerate(P):
            for lid,a,b in self.link_of[i]:
                if lid[0]=='e':kinds[lid]=self.net.edges[lid[1]]['kind'] if lid[1]>=0 else 'main'
        self.kind=kinds;self.feeders=collections.defaultdict(set)
        for L in self.link_of:
            for (a,_,_),(b,_,_) in zip(L[:-1],L[1:]):self.feeders[b].add(a)
        self.zones=[]
        for i,path in enumerate(P):
            zs=[]
            for bi,bl in enumerate(self.blocks):
                inside=contains_xy(bl.poly,path['p'][:,0],path['p'][:,1])
                if inside.any():
                    idx=np.flatnonzero(inside);zs.append((bi,float(path['d'][idx[0]]),float(path['d'][idx[-1]])))
            self.zones.append(zs)
        self.entry=[L[0][0] for L in self.link_of]

        by_entry=collections.defaultdict(list)
        for i,e in enumerate(self.entry):by_entry[e].append(i)
        self.siblings=by_entry
        self.speedz=[];self.curve_env=[];curve=bool(getattr(self.s,'curve_speed',False))
        for i,path in enumerate(P):
            z=[]
            for lid,a,b in self.link_of[i]:
                if lid[0]=='e' and lid[1]>=0:
                    sp=self.net.edges[lid[1]].get('speed')
                    if sp:z.append((a,b,float(sp)))
            self.speedz.append(z);self.curve_env.append(curve_envelope(path['p'],path['d'],lateral_acc=LAT_ACC if curve else 4.0))
        self.rate=[];self.capacity_rate=[]
        explicit_demand=getattr(self.s,'traffic_demand_vphpl',None)
        for path in P:
            L=float(path['length']);count=max(1,min(16,int(L/350)));self.rate.append(self.density*count/(L/self.v0+5) if explicit_demand is None else float(explicit_demand)/3600/len(self.siblings[self.entry[len(self.rate)]]))
            # Cada path explícito representa uma faixa. A capacidade é por faixa e não altera a geometria.
            # Ramos/dispositivos recebem capacidade um pouco menor que a pista principal.
            k=str(path.get('kind') or (path.get('kinds') or ['main'])[0]).lower()
            factor=.78 if k in ('device','return') else .88 if k=='marginal' else 1.0
            self.capacity_rate.append(max(1e-6,self.capacity_vphpl*factor/3600.))

        from .traffic_distribution import apply_distribution
        apply_distribution(self)
        self.entry_demand_study=[]
        if explicit_demand is not None or getattr(self.s,'traffic_vdm',None) is not None:
            for entry,path_ids in self.siblings.items():
                factors=[TYPE_DYN.get(self.vtype(P[i]['kinds'],(i,j,0)),TYPE_DYN['car'])['pcu'] for i in path_ids for j in range(128)]
                mean_pcu=float(np.mean(factors));demand=sum(self.rate[i] for i in path_ids)*3600;capacity=min(self.capacity_rate[i] for i in path_ids)*3600
                self.entry_demand_study.append({'entry':str(entry),'demand_vehicles_h':round(demand,3),'mean_pcu_per_vehicle':round(mean_pcu,4),'demand_pcu_h':round(demand*mean_pcu,3),'capacity_pcu_h':round(capacity,3),'ratio':round(demand*mean_pcu/max(capacity,1e-6),3)})
        # Faixas irmãs: somente rotas explícitas do mesmo alinhamento e mesmo sentido podem trocar entre si.
        groups=collections.defaultdict(dict)
        for i,path in enumerate(P):
            if path.get('route') is None or path.get('route_lane') is None or path.get('route_dir') not in ('f','r'):continue
            groups[(str(path['route']),str(path['route_dir']))][int(path['route_lane'])]=i
        self.adjacent={}
        for lanes in groups.values():
            for lane,i in lanes.items():self.adjacent[i]=[lanes[x] for x in (lane-1,lane+1) if x in lanes]

    def terminal_padding(self,path_i,vehicle):
        if not self.paths[path_i].get('terminal_inset_applied'):return 0.
        # O recuo de 5 m é do centro; um corpo longo precisa de espaço adicional.
        return max(0.,PROFILES.get(vehicle,PROFILES['car'])[0]/2-float(self.s.traffic_entry_inset_m)+.2)

    def motion_valid(self,path_i,vehicle):
        key=(path_i,vehicle)
        if key not in self.motion_cache:
            points=self.paths[path_i]['p'];padding=self.terminal_padding(path_i,vehicle)
            if padding:
                from shapely.geometry import LineString
                from shapely.ops import substring
                line=LineString(points)
                if line.length<=2*padding+1:
                    self.motion_cache[key]={'ok':False,'reasons':['sem_espaco_nos_portais']};return False
                points=np.asarray(substring(line,padding,line.length-padding).coords)
            self.motion_cache[key]=analyze_motion(points,vehicle,getattr(self.net,'allowed',None))
            probe=getattr(self,'shoulder_probe',None)
            if probe is not None:
                fallback=probe.curve_fallback(path_i,vehicle,self.motion_cache[key])
                if fallback:self.motion_cache[key]=fallback
            if PROFILES.get(vehicle,PROFILES['car'])[1]>self.paths[path_i].get('route_lane_width_m',math.inf)+1e-6:
                self.motion_cache[key]={**self.motion_cache[key],'ok':False,'reasons':list(self.motion_cache[key]['reasons'])+['veiculo_mais_largo_que_faixa']}
        return self.motion_cache[key]['ok']
    def maneuver_valid(self,v,target,travel):
        if not self.motion_valid(target,v.get('t','car')):return False
        src=self.paths[v['p']];dst=self.paths[target]
        span=min(float(src['length'])-v['s'],travel)
        if span<travel-1e-6:return False
        if span<max(12.,PROFILES.get(v.get('t','car'),PROFILES['car'])[2]*6):return False
        ss=np.linspace(v['s'],v['s']+span,max(25,int(span/.5)+1));alpha=np.linspace(0,1,len(ss));w=alpha*alpha*(3-2*alpha)
        a=interpolate(src['p'],src['d'],ss);sd=ss/max(float(src['length']),1e-9)*float(dst['length']);b=interpolate(dst['p'],dst['d'],sd)
        return analyze_motion(a*(1-w[:,None])+b*w[:,None],v.get('t','car'),getattr(self.net,'allowed',None))['ok']

    @staticmethod
    def advance_maneuver(lc,forward_m,dt):
        if not math.isfinite(forward_m) or forward_m<0 or not math.isfinite(dt) or dt<=0:return
        lc['elapsed']=min(lc['duration'],lc['elapsed']+min(dt,lc['duration']*forward_m/max(lc['travel_m'],1e-6)))

    def admission_headway(self,path_i,vtype):
        """Headway mínimo de entrada pela capacidade da faixa, ponderado por equivalente veicular (PCU)."""
        dyn=TYPE_DYN.get(vtype,TYPE_DYN['car'])
        return (1.0/max(self.capacity_rate[path_i],1e-6))*float(dyn['pcu'])

    def admission_order(self,pending,rng):
        # Uma cabeça de fila por entrada física; a escolha não muda a cada
        # tentativa negada por capacidade/sinal. Evita favorecer o índice menor.
        if not hasattr(self,'_entry_choices'):self._entry_choices={}
        out=[]
        for entry,ids in self.siblings.items():
            available=[i for i in ids if pending[i]>0]
            if not available:self._entry_choices.pop(entry,None);continue
            chosen=self._entry_choices.get(entry)
            if chosen not in available:
                weights=np.array([self.rate[i] for i in available],float)
                chosen=available[0] if len(available)==1 else int(rng.choice(available,p=weights/weights.sum() if weights.sum()>0 else None))
                self._entry_choices[entry]=chosen
            out.append(chosen)
        return out

    def blocked_total(self,i,t):
        return any(self.blocks[bi].mode=='total' and self.blocks[bi].active(t) for bi,_,_ in self.zones[i])
    def choose_path(self,i,t,rng):
        if not self.blocked_total(i,t):return i
        alt=[j for j in self.siblings[self.entry[i]] if j!=i and self.rate[j]>0 and not self.blocked_total(j,t)]
        return int(alt[rng.integers(len(alt))]) if alt else i

    def reroute_at_shared_approach(self,vehicles,t):
        """Troca somente o futuro do itinerário; nunca transporta o veículo ao nó."""
        if not getattr(self,'node_routing',False) or getattr(self.s,'traffic_route_only',False):return
        for v in vehicles:
            if v.get('lc') or self.shoulder_probe.event(v) or not self.blocked_total(v['p'],t):continue
            current=v['p'];j,lid,a,b,offset=self.locate(current,v['s'])
            if lid[0]!='e':continue
            prefix=[x[0] for x in self.link_of[current][:j+1]]
            for target in self.siblings[self.entry[current]]:
                if target==current or self.blocked_total(target,t):continue
                links=self.link_of[target]
                if len(links)<=j or [x[0] for x in links[:j+1]]!=prefix:continue
                start_offset=self.link_offsets[target][j]
                station=links[j][1]+offset-start_offset
                if station<links[j][1] or station>links[j][2] or not self.motion_valid(target,v['t']):continue
                candidate={**v,'p':target,'s':station,'li':j}
                c,h=self.polygon_safety.pose(v);q,k=self.polygon_safety.pose(candidate)
                if np.linalg.norm(c-q)>.10 or float(h@k)<.999:continue
                v.update(p=target,s=station,li=j);self.dynamic_reroutes+=1;break

    # ---------- geometria/ocupação ----------
    def locate(self,path_i,s):
        st=self.starts[path_i];j=max(0,min(len(st)-1,bisect.bisect_right(st,s)-1));lid,a,b=self.link_of[path_i][j]
        offset=self.link_offsets[path_i][j] if hasattr(self,'link_offsets') else 0.
        return j,lid,a,b,offset+max(0.,s-a)
    def map_s(self,src,dst,s):
        a=max(1e-6,float(self.paths[src]['length']));return float(np.clip(s/a,0,1))*float(self.paths[dst]['length'])
    def route_station(self,path_i,s):
        p=self.paths[path_i];a=float(p.get('route_start_m',0));b=float(p.get('route_end_m',p['length']))
        f=float(np.clip(s/max(float(p['length']),1e-6),0,1))
        return a+(b-a)*f if p.get('route_dir')!='r' else b-(b-a)*f
    @staticmethod
    def _sec_value(sec,key,default=None):return sec.get(key,default) if isinstance(sec,dict) else getattr(sec,key,default)
    def lane_change_window_allowed(self,path_i,s,travel_m):
        if not isinstance(path_i,int) or path_i<0 or path_i>=len(self.paths):return False
        if not np.isfinite(float(s)) or not np.isfinite(float(travel_m)) or float(travel_m)<=0:return False
        p=self.paths[path_i];mode=p.get('lane_change','marked')
        if not np.isfinite(float(p.get('length',0))) or float(p.get('length',0))<=0:return False
        if mode=='off':return False
        a=self.route_station(path_i,s);b=self.route_station(path_i,min(float(p['length']),s+max(0.,travel_m)))
        lo,hi=sorted((a,b));secs=p.get('lane_change_sections') or []
        def overlap(sec):
            x,y=sorted((float(self._sec_value(sec,'start_m',0)),float(self._sec_value(sec,'end_m',0))))
            return max(lo,x)<=min(hi,y)+1e-6
        if any(self._sec_value(sec,'mode')=='deny' and overlap(sec) for sec in secs):return False
        if mode=='safe':return True
        # marked: toda a manobra precisa caber numa mesma janela allow.
        for sec in secs:
            if self._sec_value(sec,'mode')!='allow':continue
            x,y=sorted((float(self._sec_value(sec,'start_m',0)),float(self._sec_value(sec,'end_m',0))))
            if x-1e-6<=lo and hi<=y+1e-6:return True
        return False
    def occupancy(self,V):
        occ=collections.defaultdict(list)
        def add(v,path_i,s):
            j,lid,a,b,o=self.locate(path_i,s);occ[lid].append((o,v,path_i,s));
            if path_i==v['p']:v['li']=j
        for v in V:
            add(v,v['p'],v['s'])
            lc=v.get('lc')
            if lc is not None:add(v,lc['to'],self.map_s(v['p'],lc['to'],v['s']))
        for lst in occ.values():lst.sort(key=lambda x:x[0])
        return occ
    def leader_state(self,v,occ,look=150.,path_i=None,s=None):
        path_i=v['p'] if path_i is None else path_i;s=v['s'] if s is None else s
        L=self.link_of[path_i];j,lid,a,b,off=self.locate(path_i,s);acc=0.
        for k in range(j,len(L)):
            lid,a,b=L[k]
            for o,w,wp,ws in occ.get(lid,[]):
                if w is v:continue
                if getattr(self,'shoulder_probe',None) and self.shoulder_probe.laterally_separated(v,w):continue
                if k==j:
                    if o>off+1e-6 or (abs(o-off)<=1e-6 and w['id']<v['id']):return o-off-(w['L']+v['L'])/2,w['v'],w
                else:
                    entry_offset=self.link_offsets[path_i][k] if hasattr(self,'link_offsets') else 0.
                    if o>=entry_offset:return acc+o-entry_offset-(w['L']+v['L'])/2,w['v'],w
            offset=self.link_offsets[path_i][k] if hasattr(self,'link_offsets') else 0.
            acc+=(b-a)-(off-offset if k==j else 0.)
            if acc>look:break
        return math.inf,0.,None
    def leader(self,v,occ,look=150.,path_i=None,s=None):
        g,sp,_=self.leader_state(v,occ,look,path_i,s);return g,sp
    def follower_on_path(self,v,V,path_i,s,look=100.):
        best=(math.inf,0.,0.)
        for w in V:
            if w is v:continue
            candidates=[]
            if w['p']==path_i:candidates.append(w['s'])
            if w.get('lc') is not None and w['lc']['to']==path_i:candidates.append(self.map_s(w['p'],path_i,w['s']))
            for sw in candidates:
                if sw>=s:continue
                gap=s-sw-(w['L']+v['L'])/2
                if gap<best[0] and gap<look:best=(gap,w['v'],w['L'])
        return best

    # ---------- mudança de faixa ----------
    def consider_lane_changes(self,V,t,occ):
        for v in sorted(V,key=lambda x:x['id']):
            if getattr(self.s,'traffic_route_only',False):continue
            if v.get('lc') is not None or t<v.get('lc_cooldown',-math.inf):continue
            if getattr(self,'shoulder_probe',None) and self.shoulder_probe.event(v):continue
            cand=self.adjacent.get(v['p'],())
            if not cand:continue
            gap,_,lead=self.leader_state(v,occ,look=120.)
            if gap>55 or v['v']>.92*v['v0']:continue
            travel=max(18.,6*PROFILES.get(v.get('t','car'),PROFILES['car'])[2],v['v']*self.LC_DURATION+8.)
            if not self.lane_change_window_allowed(v['p'],v['s'],travel):
                self.lc_blocked_rules+=1;continue
            best=None
            for target in cand:
                if not self.pedestrians.lane_change_allowed(v,target,travel):continue
                st=self.map_s(v['p'],target,v['s'])
                fg,fv=self.leader(v,occ,look=180.,path_i=target,s=st)
                rg,rv,rL=self.follower_on_path(v,V,target,st)
                front_need=max(8.,IDM['s0']+v['v']*1.1)
                rear_need=max(8.,IDM['s0']+rv*1.1)
                if fg<front_need or rg<rear_need:continue
                gain=(fg if math.isfinite(fg) else 250)-(gap if math.isfinite(gap) else 250)
                need=self.LC_GAIN*(.55 if getattr(self,'heavy_reaction',True) and lead is not None and TYPE_DYN.get(lead.get('t'),{}).get('heavy') else 1.0)
                if gain<need:continue
                if not self.maneuver_valid(v,target,travel):self.lc_blocked_geometry+=1;continue
                if best is None or gain>best[0]:best=(gain,target)
            if best is None:
                self.lc_blocked_safety+=1;continue
            self.lane_events.append(dict(id=v['id'],time=t,source=v['p'],target=best[1],travel=travel))
            v['lc']={'from':v['p'],'to':best[1],'elapsed':0.,'duration':self.LC_DURATION,'travel_m':travel}
            if not self.polygon_safety.admission(v,V):
                v['lc']=None;self.lc_blocked_safety+=1;self.lane_events.pop();continue
            self.lane_changes+=1
            # A partir daqui o veículo passa a reservar também a faixa de destino.
            occ=self.occupancy(V)
        return occ

    # ---------- simulação ----------
    def run(self,status):
        rng=np.random.default_rng(1729);n=len(self.paths);t0=0. if getattr(self.s,'traffic_route_only',False) else -WARMUP;steps=int(math.ceil((self.duration-t0)/DT))+2
        nextspawn=[t0 if r>0 and getattr(self.s,'traffic_route_only',False) else t0+rng.exponential(1/max(r,1e-6)) if r>0 else math.inf for r in self.rate];pending=[0]*n;V=[]
        last_admit=collections.defaultdict(lambda:-math.inf);queue_area=[0.0]*n;max_queue_lane=[0]*n;queue_discharged=[0]*n
        self.info={};self.exited_by_path=[0]*n;self.node_transfers=collections.Counter();self.spawned_by_path=[0]*n;frames=[];self.warning_frames=[];vid=0;first=int(round(-t0/DT))
        self.collisions=0;self.side_collisions=0;self.min_gap=math.inf;self.max_queue=0;self.rerouted=0;self.spawned=0
        self.safety_interventions=0;self.lane_changes=0;self.lc_blocked_rules=0;self.lc_blocked_safety=0
        for k in range(steps):
            t=t0+k*DT;self.time=t
            for i in range(n):
                while nextspawn[i]<=t:
                    pending[i]+=1;nextspawn[i]=math.inf if getattr(self.s,'traffic_route_only',False) else nextspawn[i]+rng.exponential(1/self.rate[i])
            self.reroute_at_shared_approach(V,t)
            occ=self.occupancy(V)
            for i in self.admission_order(pending,rng):
                if not pending[i]:continue
                j=self.choose_path(i,t,rng)
                if j!=i:self.rerouted+=1
                ident=(j,vid,0);vt=self.vtype(self.paths[j]['kinds'],ident)
                if not self.motion_valid(j,vt):
                    self.motion_blocked+=1;pending[i]-=1;vid+=1;self._entry_choices.pop(self.entry[i],None);continue
                if getattr(self.s,'traffic_route_only',False) and any(w['p']==j for w in V):continue
                Lv=_LEN[vt];v0=self.v0*SPEED_FACTOR[vt]*(.92+.16*rng.random())
                new={'id':vid,'p':j,'s':self.terminal_padding(j,vt) if self.paths[j].get('terminal_inset_applied') else min(float(getattr(self.s,'traffic_entry_inset_m',5)),max(0.,self.paths[j]['length']-Lv/2-1)), 'v':0.,'L':Lv,'v0':v0,'t':vt,'li':0,'lc':None,'lc_cooldown':-math.inf,'entered_s':t}
                dyn=TYPE_DYN.get(vt,TYPE_DYN['car'])
                if not self.polygon_safety.admission(new,V,vehicle_check=getattr(self.s,'traffic_prevent_collisions',True)):continue
                if not self.transport.admission_allowed(j,t,Lv+2*new['s']) or not self.pedestrians.admission_allowed(j,Lv+2*new['s']):continue
                if self.capacity_model:
                    # Capacidade da faixa: a fila permanece na entrada e é descarregada por headway equivalente PCU.
                    min_headway=self.admission_headway(j,vt)
                    if t-last_admit[self.entry[j]] < min_headway:continue
                gap,vl=self.leader(new,occ)
                behind=[w for o,w,wp,ws in occ.get(self.link_of[j][0][0],[]) if o<Lv+IDM['s0']]
                if gap<IDM['s0']+1 or behind:continue
                new['v']=min(.9*v0,math.sqrt(max(0.,2*IDM['b']*(gap-IDM['s0'])))+vl*.5) if gap<math.inf else .9*v0
                V.append(new);self.polygon_safety.admitted(new);self.info[vid]=(j,vt,ident);vid+=1;pending[i]-=1;self.spawned+=1;self.spawned_by_path[j]+=1;self._entry_choices.pop(self.entry[i],None);last_admit[self.entry[j]]=t;queue_discharged[j]+=1;occ=self.occupancy(V)
            self.max_queue=max(self.max_queue,sum(pending))
            for qi,q in enumerate(pending):
                queue_area[qi]+=q*DT;max_queue_lane[qi]=max(max_queue_lane[qi],q)
            if k%max(1,int(round(1.0/DT)))==0:occ=self.consider_lane_changes(V,t,occ)
            self.alternating.update(V,t)
            self.pedestrians.update(V,t,DT)
            self.shoulder_probe.prepare(V)
            acc=[self.accel(v,occ,t) for v in V]
            planned=[]
            for v,a in zip(V,acc):
                nv=max(0.,v['v']+a*DT);ds=max(0.,(v['v']+nv)/2*DT)
                gap,_=self.leader(v,occ,look=max(30.,ds+10.))
                if v.get('lc'):
                    target=v['lc']['to'];target_gap,_=self.leader(v,occ,path_i=target,s=self.map_s(v['p'],target,v['s']));gap=min(gap,target_gap)
                control=min(self.transport.stop_gap(v,t,gap),self.transport.stop_gap(v,t+DT,gap),self.alternating.stop_gap(v),self.pedestrians.stop_gap(v))
                if control<math.inf:
                    if ds>max(0.,control-self.HARD_GAP):self.control_stops+=1
                    gap=min(gap,control)
                if math.isfinite(gap):
                    safe=max(0.,gap-self.HARD_GAP)
                    if ds>safe+1e-9:
                        ds=safe;nv=min(nv,ds/DT if DT>0 else 0.);self.safety_interventions+=1
                if self.paths[v['p']].get('terminal_inset_applied'):
                    ds=min(ds,max(0.,self.paths[v['p']]['length']-.5-self.terminal_padding(v['p'],v.get('t','car'))-v['s']))
                planned.append((nv,ds))
            planned=self.polygon_safety.resolve(V,planned,vehicle_check=getattr(self.s,'traffic_prevent_collisions',True))
            alive=[]
            for v,(nv,ds) in zip(V,planned):
                v['_previous_s']=v['s'];v['v']=nv;v['s']+=ds
                for link,a,b in self.link_of[v['p']]:
                    if link[0]=='c' and v['_previous_s']<b<=v['s']:self.node_transfers[(link[1],link[2])]+=1
                lc=v.get('lc')
                if lc is not None:
                    self.advance_maneuver(lc,ds,DT)
                    if lc['elapsed']>=lc['duration']:
                        target=lc['to'];v['s']=self.map_s(v['p'],target,v['s']);v['p']=target;v['lc']=None;v['lc_cooldown']=t+self.LC_COOLDOWN
                if v['s']<self.paths[v['p']]['length']-.5-self.terminal_padding(v['p'],v.get('t','car'))-1e-6:alive.append(v)
                else:self.exited_by_path[v['p']]+=1
            V=alive
            if getattr(self.s,'traffic_route_only',False):
                occupied_paths={v['p'] for v in V}
                for i in range(n):
                    if self.rate[i]>0 and i not in occupied_paths and not pending[i]:pending[i]=1
            # Última barreira numérica: qualquer eventual sobreposição é resolvida antes de gravar o quadro.
            if getattr(self.s,'traffic_prevent_collisions',True):self.enforce_hard_separation(V)
            self.pedestrians.check(V,t)
            if k>=first:
                ids=np.array([v['id'] for v in V],np.int32);ss=np.array([v['s'] for v in V],np.float64);ps=np.array([v['p'] for v in V],np.int32)
                to=np.array([v['lc']['to'] if v.get('lc') is not None else -1 for v in V],np.int32)
                al=np.array([min(1.,v['lc']['elapsed']/v['lc']['duration']) if v.get('lc') is not None else 0. for v in V],np.float64)
                frames.append((ids,ss,ps,to,al));self.warning_frames.append({v['id'] for v in V if v['v']<.3 and (v.get('_risk_stop') or math.isfinite(self.alternating.stop_gap(v)) or any(self.blocks[bi].active(t) and a-120<v['s']<b for bi,a,b in self.zones[v['p']]))});self.check(V)
            if k%(25 if self.shoulder_probe.enabled else 250)==0:status(.22+.03*k/steps,f'Simulando tráfego: {tempo(max(0.,t))} de {tempo(self.duration)}')
        self.active_end=len(V);self.frames=frames;self.t_first=t0+first*DT
        self.queue_area_vehicle_s=queue_area;self.max_queue_lane=max_queue_lane;self.queue_discharged=queue_discharged;self.current_queue=list(pending)

    def enforce_hard_separation(self,V):
        for _ in range(3):
            occ=self.occupancy(V);changed=False
            for lst in occ.values():
                # Uma mesma viatura pode aparecer como sombra de mudança de faixa: remove duplicidade por id mantendo ordem.
                clean=[];seen=set()
                for row in lst:
                    if row[1]['id'] in seen:continue
                    seen.add(row[1]['id']);clean.append(row)
                for (o1,w1,p1,s1),(o2,w2,p2,s2) in zip(clean[:-1],clean[1:]):
                    gap=o2-o1-(w1['L']+w2['L'])/2
                    if getattr(self,'shoulder_probe',None) and self.shoulder_probe.laterally_separated(w1,w2):continue
                    if gap<self.HARD_GAP:
                        deficit=self.HARD_GAP-gap;w1['s']=max(w1.get('_previous_s',0.),w1['s']-deficit);w1['v']=min(w1['v'],w2['v']);self.safety_interventions+=1;changed=True
            if not changed:break

    def approach_priority(self,links,k):
        for m in range(k-1,-1,-1):
            if links[m][0][0]=='e':return self.priority(links[m][0])
        return 0
    def merge_conflict(self,v,occ,look=70.):
        L=self.link_of[v['p']];j=v['li'];best=(math.inf,0.)
        for k in range(j+1,len(L)):
            nl=L[k][0];dist=L[k][1]-v['s']
            if dist>look:break
            feeders=self.feeders.get(nl,())
            if len(feeders)<2:continue
            mine=self.approach_priority(L,k);own=L[k-1][0];cand=[]
            for f in feeders:
                if f==own:continue
                cand.extend(w for _,w,_,_ in occ.get(f,[]))
                for g in self.feeders.get(f,()):cand.extend(w for _,w,_,_ in occ.get(g,[]))
            for w in cand:
                if w is v:continue
                Lw=self.link_of[w['p']];idx=None
                for q in range(w['li'],min(len(Lw),w['li']+4)):
                    if Lw[q][0]==nl:idx=q;break
                if idx is None:continue
                dw=Lw[idx][1]-w['s']
                if dw>look or dw<-w['L']:continue
                other=self.approach_priority(Lw,idx);tv=dist/max(v['v'],.5);tw=max(dw,0.)/max(w['v'],.5)
                if other>mine or (other==mine and (tw<tv or (tw==tv and w['id']<v['id']))):
                    if other>mine and tw-tv>4.:continue
                    gap,vl=(dist-dw-(w['L']+v['L'])/2,w['v']) if dw<dist else (dist-v['L']/2-1.5,0.)
                    if gap<best[0]:best=(gap,vl)
        return best
    def priority(self,lid):
        if lid[0]!='e':return 0
        category=2 if self.kind.get(lid)=='main' else 1 if self.kind.get(lid)=='marginal' else 0
        edges=getattr(getattr(self,'net',None),'edges',[]);length=0.
        if 0<=lid[1]<len(edges):
            edge=edges[lid[1]];length=float(getattr(self.net,'origin_info',{}).get(edge.get('origin'),(0.,))[0])
        return category+min(max(length,0.),200000.)/1000000.

    def accel(self,v,occ,t):
        dyn=TYPE_DYN.get(v.get('t'),TYPE_DYN['car']);v0=v['v0'];T=float(dyn['T']);s0=float(dyn['s0']);a_comf=float(dyn['a']);b_comf=float(dyn['b']);s=v['s'];k0=v0/max(self.v0,.1)
        for a,b,sp in self.speedz[v['p']]:
            if a-30<=s<=b:v0=min(v0,sp*k0)
        env=self.curve_env[v['p']]
        if env is not None:
            d=self.paths[v['p']]['d'];j=min(len(env)-1,int(np.searchsorted(d,s)));v0=min(v0,float(env[j])*min(1.,k0*1.05))
        for bi,a,b in self.zones[v['p']]:
            bl=self.blocks[bi]
            if not bl.active(t):continue
            if bl.mode=='partial' and a-40<=s<=b:v0=min(v0,bl.speed);T=max(T,2.4)
            elif bl.mode=='total' and s<a:v['_stop']=a-2-v['L']/2-s
        gap,vl,lead=self.leader_state(v,occ);stop=min(v.pop('_stop',math.inf),self.transport.stop_gap(v,t,gap),self.alternating.stop_gap(v),self.pedestrians.stop_gap(v))
        if self.heavy_reaction and lead is not None and TYPE_DYN.get(lead.get('t'),{}).get('heavy'):
            # Reação a pesados: seguidor abre headway e aceita menor velocidade até existir ultrapassagem segura.
            T=max(T,2.05 if not TYPE_DYN.get(v.get('t'),TYPE_DYN['car'])['heavy'] else 2.35);s0=max(s0,3.2)
        if stop<gap:gap,vl=stop,0.
        mg,mv=self.merge_conflict(v,occ)
        if mg<gap:gap,vl=mg,mv
        vv=v['v'];dv=vv-vl;star=s0+max(0.,vv*T+vv*dv/(2*math.sqrt(max(a_comf*b_comf,1e-6))));free=1-(vv/max(v0,.1))**4
        a=a_comf*(free-(star/max(gap,.1))**2) if gap<math.inf else a_comf*free
        return max(-9.,min(a_comf,a))
    def check(self,V):
        if not getattr(self.s,'traffic_prevent_collisions',True):return
        from .vehicle_safety import SpatialReservations
        spatial=SpatialReservations()
        for vehicle in V:
            poly=self.polygon_safety.footprint(vehicle);level=self.polygon_safety.level(vehicle)
            if not spatial.clear(vehicle['id'],poly,level):
                self.side_collisions+=1
                raise ValueError('Reserva lateral insuficiente na simulação. Revise a seção, o desvio ou as conexões; vídeo bloqueado.')
            spatial.add(vehicle['id'],poly,level)
        occ=self.occupancy(V)
        for lst in occ.values():
            clean=[];seen=set()
            for row in lst:
                if row[1]['id'] in seen:continue
                seen.add(row[1]['id']);clean.append(row)
            for (o1,w1,_,_),(o2,w2,_,_) in zip(clean[:-1],clean[1:]):
                g=o2-o1-(w1['L']+w2['L'])/2
                if getattr(self,'shoulder_probe',None) and self.shoulder_probe.laterally_separated(w1,w2):continue
                if g<self.min_gap:self.min_gap=g
                if g<-.01:self.collisions+=1

    # ---------- consulta por quadro ----------
    def state(self,t):
        if not self.frames:return []
        x=(t-self.t_first)/DT;k=int(np.clip(math.floor(x),0,len(self.frames)-1));f=float(np.clip(x-k,0,1));ids,ss,ps,to,al=self.frames[k]
        if k+1<len(self.frames) and f>0:
            ids2,ss2,ps2,to2,al2=self.frames[k+1];m={i:(s,p,q,a) for i,s,p,q,a in zip(ids2.tolist(),ss2.tolist(),ps2.tolist(),to2.tolist(),al2.tolist())}
            vals=[]
            for i,s,p,q,a in zip(ids.tolist(),ss.tolist(),ps.tolist(),to.tolist(),al.tolist()):
                if i in m and m[i][1]==p and m[i][2]==q:
                    s2,_,_,a2=m[i];s=s+(s2-s)*f;a=a+(a2-a)*f
                vals.append((i,p,s,q,a))
            return vals
        return list(zip(ids.tolist(),ps.tolist(),ss.tolist(),to.tolist(),al.tolist()))
    def _sample_pose(self,path_i,s):
        path=self.paths[path_i];j=min(len(path['p'])-1,int(np.searchsorted(path['d'],s)));g=axle_geometry_prepared(*self.motion_points[path_i],'car',np.array([s]));return g['center'][0],g['heading'][0],j
    def _center(self,i,s,to,a):
        p0=interpolate(*self.motion_points[i],np.array([s]))[0]
        if to>=0 and a>0:
            p1=interpolate(*self.motion_points[to],np.array([self.map_s(i,to,s)]))[0];w=a*a*(3-2*a);return p0*(1-w)+p1*w
        return p0
    def vehicles_ex(self,t,speed=None):
        states=self.state(t)
        for vid,i,s,to,a in states:
            vt=self.info[vid][1];path=self.paths[i];g=axle_geometry_prepared(*self.motion_points[i],vt,np.array([s]));pos=self._center(i,s,to,a);tan=g['heading'][0]
            if to<0 and getattr(self,'shoulder_probe',None):
                probe_pose=self.shoulder_probe.pose({'id':vid,'p':i,'s':s,'t':vt})
                if probe_pose is not None:pos,tan=probe_pose
            if to>=0:
                event=next((e for e in reversed(self.lane_events) if e['id']==vid and e['source']==i and e['target']==to and e['time']<=t+DT),None)
                if event:
                    wb=PROFILES.get(vt,PROFILES['car'])[2];travel=event['travel']
                    left=self._center(i,s-wb/2,to,max(0,a-wb/2/travel));right=self._center(i,s+wb/2,to,min(1,a+wb/2/travel));delta=right-left
                    if np.linalg.norm(delta)>1e-5:tan=delta/np.linalg.norm(delta)
            j=min(len(path['p'])-1,int(np.searchsorted(path['d'],s)))
            yield pos,tan,vid,self.info[vid][2],j
    def vehicle_body_state(self,t):
        out=[]
        for pos,tan,vid,identity,j in self.vehicles_ex(t):
            length=PROFILES.get(self.info[vid][1],PROFILES['car'])[0]
            from .vehicle_safety import body,LATERAL_BUFFER
            width=PROFILES.get(self.info[vid][1],PROFILES['car'])[1]
            out.append({'width_m':width,'polygon':list(body(pos,tan,length,width).exterior.coords),'collision_envelope':list(body(pos,tan,length,width,LATERAL_BUFFER).exterior.coords),'id':int(vid),'front':(pos+tan*length/2).tolist(),'rear':(pos-tan*length/2).tolist(),'heading':tan.tolist()})
        return out
    def indicators(self,t):
        if not self.frames:return {}
        k=int(np.clip(math.floor((t-self.t_first)/DT),0,len(self.frames)-1));hazards=self.warning_frames[k];out={}
        for vid,i,s,to,alpha in self.state(t):
            code=3 if vid in hazards else 0
            if to>=0 and not code:
                c,h,_=self._sample_pose(i,s);delta=self._center(to,self.map_s(i,to,s),-1,0)-c
                code=1 if np.array([-h[1],h[0]])@delta>0 else 2
            probe=getattr(self,'shoulder_probe',None);event=probe.event({'id':vid,'p':i,'s':s}) if probe else None
            if event and not code:
                code=2 if s<event['stations'][1] else 1 if s>event['stations'][2] else 0
            out[int(vid)]=code
        return out

    def report(self):
        ratio=max([row['ratio'] for row in self.entry_demand_study],default=None)
        from .vehicle_safety import LATERAL_CLEARANCE,LATERAL_BUFFER
        return {'model':'microssimulacao','flow_balance':{'entered':self.spawned,'exited':sum(self.exited_by_path),'active_end':self.active_end,'conserved':self.spawned==sum(self.exited_by_path)+self.active_end,'scope':'Contagem inclui o aquecimento; veículos derivados mantêm identidade.'},'rerouted_at_nodes':self.dynamic_reroutes,'node_movements':[{'from_edge':a,'to_edge':b,'count':n,'from_route':self.net.edges[a].get('route'),'to_route':self.net.edges[b].get('route')} for (a,b),n in sorted(self.node_transfers.items())],'distribution':{**self.distribution_report,'actual_spawned_by_path':self.spawned_by_path,'count_scope':'Contagem inclui o aquecimento quando ativo.'},'entry_inset_m':getattr(self.s,'traffic_entry_inset_m',5),'route_only':getattr(self.s,'traffic_route_only',False),'collision_prevention':getattr(self.s,'traffic_prevent_collisions',True),'signals_respected':getattr(self.s,'traffic_respect_signals',True),'shoulder_probe':self.shoulder_probe.report(),'lateral_clearance_m':LATERAL_CLEARANCE,'lateral_buffer_per_vehicle_m':LATERAL_BUFFER,'narrow_corridor_admission_holds':self.polygon_safety.narrow_holds,'minimum_following_gap_m':self.HARD_GAP,'polygon_safety_interventions':self.polygon_safety.interventions,'alternating_traffic':self.alternating.report(),'pedestrians':self.pedestrians.report(),'vehicles':self.spawned,'rear_collisions':self.collisions,'side_collisions':self.side_collisions,
                'min_gap_m':None if self.min_gap==math.inf else round(self.min_gap,2),'max_waiting_at_entries':self.max_queue,
                'transport_controls':self.transport.report(),'control_stop_interventions':self.control_stops,'rerouted':self.rerouted,'rerouted_at_nodes':self.dynamic_reroutes,'blocks':len(self.blocks),'density':self.density,'lane_changes':self.lane_changes,
                'lane_change_blocked_rule':self.lc_blocked_rules,'lane_change_blocked_safety':self.lc_blocked_safety,
                'safety_interventions':self.safety_interventions,'collision_free':(self.collisions==0 and self.side_collisions==0) if getattr(self.s,'traffic_prevent_collisions',True) else None,
                'demand_vph_per_lane':getattr(self.s,'traffic_demand_vphpl',None),'capacity_vph_per_lane':round(self.capacity_vphpl),'entry_demand_study':self.entry_demand_study,'saturation_indicator':{'status':'sobressaturado — indicativo de F' if ratio is not None and ratio>1 else 'nível de serviço não determinado','demand_capacity_ratio':ratio,'scope':'Estimativa com fatores de equivalência internos; não é classificação DNIT/HCM. Depende de tipo de via, velocidade, densidade, atrasos e método aplicável.'},'motion_blocked_vehicles':self.motion_blocked,'lane_change_blocked_geometry':self.lc_blocked_geometry,'motion_profiles':{f'{p}:{v}':a for (p,v),a in self.motion_cache.items()},
                'max_queue_by_lane':list(getattr(self,'max_queue_lane',[])),
                'current_queue_by_lane':list(getattr(self,'current_queue',[])),
                'queue_vehicle_seconds_by_lane':[round(x,1) for x in getattr(self,'queue_area_vehicle_s',[])],
                'queue_discharged_by_lane':list(getattr(self,'queue_discharged',[]))}

from .visual import TYPES as _T
_LEN={k:v['L'] for k,v in _T.items()}
