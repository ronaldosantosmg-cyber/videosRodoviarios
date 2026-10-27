"""Sondagem excepcional de pesados; não cria faixa nem muda o pavimento cadastrado."""
import math
from collections import Counter
import numpy as np
from shapely.geometry import Polygon,Point,MultiPoint
from shapely.ops import unary_union
from .vehicle_motion import PROFILES,interpolate,analyze_motion
from .vehicle_safety import body,LATERAL_BUFFER

MAX_EDGE_EXTENSION=1.
HEAVY=frozenset(('truck','bus','carreta','truck18','long30'))


def envelope(pavement,obstacles,exclusions=(),bridges=None):
    """Só cresce exteriores. Vazios, canteiros, barreiras e OAE não são liberados."""
    if pavement.is_empty:return Polygon()
    polys=list(pavement.geoms) if hasattr(pavement,'geoms') else [pavement]
    holes=[Polygon(r) for p in polys if p.geom_type=='Polygon' for r in p.interiors]
    expanded=pavement.buffer(MAX_EDGE_EXTENSION)
    forbidden=list(obstacles)+list(exclusions)+holes
    if bridges is not None and not bridges.is_empty:
        # Não inventar apoio estrutural fora do tabuleiro.
        forbidden.append(bridges.buffer(MAX_EDGE_EXTENSION).difference(pavement))
    if forbidden:expanded=expanded.difference(unary_union(forbidden).buffer(.15))
    return expanded


class ShoulderProbe:
    def __init__(self,sim):
        self.sim=sim;self.enabled=bool(getattr(sim.s,'heavy_shoulder_probe',True))
        self.base=getattr(sim.net,'allowed',Polygon());self.area=getattr(sim.net,'shoulder_envelope',Polygon())
        self.pavement=getattr(sim.net,'operational_pavement',self.base)
        self.events={};self.curve_paths=set();self.counts=Counter();self.last_probe={}
    def enabled_for(self,vt):return self.enabled and vt in HEAVY and not self.area.is_empty
    def curve_fallback(self,i,vt,audit):
        if not self.enabled_for(vt) or set(audit.get('reasons',[]))!={'corpo_fora_da_pista'}:return None
        check=analyze_motion(self.sim.paths[i]['p'],vt,self.area)
        if not check['ok']:self.counts['curvas_recusadas']+=1;return None
        # Conferir o polígono completo, não apenas vértices amostrados.
        p,d=self.sim.motion_points[i];L,B,_,_=PROFILES[vt]
        ss=np.linspace(0,d[-1],max(3,int(math.ceil(d[-1]))+1))
        from .vehicle_motion import axle_geometry_prepared
        g=axle_geometry_prepared(p,d,vt,ss)
        if any(not self.area.covers(body(c,h,L,B)) for c,h in zip(g['center'],g['heading'])):
            self.counts['curvas_recusadas']+=1;return None
        self.curve_paths.add((i,vt));self.counts['curvas_com_arrasto_validado']+=1
        return {**check,'shoulder_probe':True,'scope':'Corpo rígido conservador, máximo 1 m além do bordo; não certifica composição articulada.'}
    def permits(self,i,vt):
        return self.enabled_for(vt) and ((i,vt) in self.curve_paths or any(e['path']==i and e['vehicle']==vt for rows in self.events.values() for e in rows))
    @staticmethod
    def offset(e,s):
        a,b,c,d=e['stations']
        if s<=a or s>=d:return 0.
        u=(s-a)/(b-a) if s<b else (d-s)/(d-c) if s>c else 1.
        u=float(np.clip(u,0,1));return e['offset']*u*u*(3-2*u)
    def event(self,v):
        return next((e for e in reversed(self.events.get((int(v['id']),int(v['p'])),[])) if e['stations'][0]<=v['s']<=e['stations'][-1]),None)
    def center(self,i,s,e):
        p,d=self.sim.motion_points[i];q=interpolate(p,d,np.array([s]))[0]
        front,back=interpolate(p,d,np.array([s+.25,s-.25]));h=front-back;h/=max(float(np.linalg.norm(h)),1e-9)
        return q+np.array([h[1],-h[0]])*self.offset(e,s)
    def pose(self,v,forward=0.):
        s=v['s']+forward;e=self.event({**v,'s':s})
        if not e or v.get('lc'):return None
        wb=PROFILES.get(v.get('t','car'),PROFILES['car'])[2]
        c=self.center(v['p'],s,e);h=self.center(v['p'],s+wb/2,e)-self.center(v['p'],s-wb/2,e)
        return c,h/max(float(np.linalg.norm(h)),1e-9)
    def geometry(self,v,station,e=None,clearance=True):
        state={**v,'s':station};pose=self.pose(state) if e is None else None
        if e is not None:
            wb=PROFILES[v['t']][2];c=self.center(v['p'],station,e);h=self.center(v['p'],station+wb/2,e)-self.center(v['p'],station-wb/2,e);h/=max(float(np.linalg.norm(h)),1e-9);pose=(c,h)
        if pose is None:pose=self.sim.polygon_safety.pose(state)
        L,B,_,_=PROFILES.get(v.get('t','car'),PROFILES['car']);return body(*pose,L,B,LATERAL_BUFFER if clearance else 0.)
    def try_pair(self,v,other):
        """Previsão limitada; a reserva real é refeita em cada passo da simulação."""
        vt=v.get('t','car')
        if not self.enabled_for(vt) or v.get('lc') or other.get('lc'):return False
        safety=self.sim.polygon_safety
        if safety.level(v) is not None and safety.level(other) is not None and safety.level(v)!=safety.level(other):return False
        key=(int(v['id']),int(v['p']))
        if self.event(v):return True
        if self.counts['manobras_aceitas']>=4096:return False
        t=float(getattr(self.sim,'time',0));last=self.last_probe.get(key,-1e9)
        if t-last<1:return False
        c,h=safety.pose(v);oc,oh=safety.pose(other)
        if np.linalg.norm(c-oc)>100 or float(h@oh)>-.3:return False
        self.last_probe[key]=t
        if len(self.last_probe)>8192:self.last_probe.pop(next(iter(self.last_probe)))
        L,B,wb,_=PROFILES[vt];speed=max(2.,v.get('v',0),min(v.get('v0',5),8.))
        ospeed=max(2.,other.get('v',0),min(other.get('v0',5),8.))
        # Somente perto do bordo direito; não atravessa uma faixa vizinha para alcançá-lo.
        if self.pavement.covers(Point(c+np.array([h[1],-h[0]])*(B/2+1.1))):return False
        ramp=max(16.,wb*3);hold=max(20.,L*2,float(np.linalg.norm(c-oc))*.6)
        start=float(v['s']);end=start+2*ramp+hold
        if end+L/2>=self.sim.paths[v['p']]['length']:return False
        ss=np.linspace(start,end,max(33,int((end-start)/.5)+1));dt=(ss-start)/speed
        future=np.clip(other['s']+dt*ospeed,0,self.sim.paths[other['p']]['length'])
        # Sem contato previsto, não usar o acostamento só por proximidade.
        others=[self.geometry(other,q) for q in future]
        if not any(self.geometry(v,s).intersects(other_poly) for s,other_poly in zip(ss,others)):return False
        for offset in (.25,.5,.75,1.):
            e={'path':v['p'],'vehicle':vt,'stations':(start,start+ramp,start+ramp+hold,end),'offset':offset,'created_s':t}
            points=np.array([self.center(v['p'],s,e) for s in ss])
            if not analyze_motion(points,vt,self.area)['ok']:continue
            bodies=[self.geometry(v,s,e,False) for s in ss]
            if any(not self.area.covers(p) for p in bodies):continue
            # Varredura conservadora entre amostras; sem atravessar ilhas/barreiras finas.
            if any(not self.area.covers(MultiPoint([*a.exterior.coords,*b.exterior.coords]).convex_hull) for a,b in zip(bodies,bodies[1:])):continue
            if any(self.geometry(v,s,e).intersection(other_poly).area>1e-7 for s,other_poly in zip(ss,others)):continue
            if any(any(bl.active(t+tau) and bl.poly.intersects(p) for tau,p in zip(dt,bodies)) for bl in self.sim.blocks):continue
            pedestrians=getattr(self.sim,'pedestrians',None)
            if any(a['route']['kind']!='passarela' and abs(a['route']['height']-float(safety.level(v) or 0))<2.5 and any(p.intersects(Point(pedestrians.pose(a)[0]).buffer(.4)) for p in bodies) for a in getattr(pedestrians,'agents',[])):continue
            self.events.setdefault(key,[]).append(e);self.counts['manobras_aceitas']+=1;return True
        self.counts['manobras_recusadas']+=1;return False
    def laterally_separated(self,v,w):
        """Dispensa só o seguimento escalar quando os corpos já estão lado a lado."""
        if not (self.event(v) or self.event(w)):return False
        a,h=self.sim.polygon_safety.pose(v);b,k=self.sim.polygon_safety.pose(w)
        if float(h@k)<.95:return False
        width=PROFILES[v['t']][1]/2+PROFILES[w['t']][1]/2+2*LATERAL_BUFFER
        return abs(float((b-a)@np.array([-h[1],h[0]])))>=width+.02 and not self.geometry(v,v['s']).intersects(self.geometry(w,w['s']))
    def try_overtake(self,v,other,vehicles):
        # Autorização explícita de ensaio, nunca uma faixa permanente.
        if not getattr(self.sim.s,'heavy_shoulder_overtake',False) or getattr(self.sim.s,'traffic_route_only',False) or not getattr(self.sim.s,'traffic_prevent_collisions',True) or not self.enabled_for(v.get('t')):return False
        if v.get('lc') or other.get('lc') or self.event(v) or v['p']!=other['p'] or other['s']<=v['s']:return False
        key=(int(v['id']),int(v['p']));now=float(getattr(self.sim,'time',0))
        if now-self.last_probe.get(('o',*key),-1e9)<2 or self.counts['ultrapassagens_aceitas']>=4096:return False
        self.last_probe[('o',*key)]=now
        if len(self.last_probe)>8192:self.last_probe.pop(next(iter(self.last_probe)))
        L,B,wb,_=PROFILES[v['t']];speed=min(12.,float(v['v0']));ospeed=max(0.,float(other['v']))
        if speed-ospeed<2 or v['v']>speed*1.1:return False
        distance=other['s']-v['s'];gap=distance-(L+other['L'])/2;ramp=max(24.,wb*4)
        if gap<max(4.,(speed-ospeed)*ramp/speed+3) or gap>80:return False
        a,h=self.sim.polygon_safety.pose(v);b,k=self.sim.polygon_safety.pose(other)
        if float(h@k)<.98:return False
        # Não atravessar outra faixa cadastrada para alcançar o acostamento.
        right=np.array([h[1],-h[0]])
        for lane in getattr(self.sim,'adjacent',{}).get(v['p'],()):
            points,stations=self.sim.motion_points[lane]
            near=points[int(np.argmin(np.linalg.norm(points-a,axis=1)))]
            if float((near-a)@right)>.5:return False
        start=float(v['s']);back_clear=(L+other['L'])/2+4
        return_at=start+speed*(distance+back_clear+ospeed*ramp/speed)/(speed-ospeed)
        return_at=max(start+ramp+10,return_at);end=return_at+ramp
        if end+L/2+5>=self.sim.paths[v['p']]['length'] or end-start>500:return False
        ss=np.linspace(start,end,max(65,int((end-start)/.5)+1));dt=(ss-start)/speed
        for offset in np.arange((B+PROFILES[other['t']][1])/2+2*LATERAL_BUFFER+.05,4.01,.1):
            e=dict(path=v['p'],vehicle=v['t'],stations=(start,start+ramp,return_at,end),offset=float(offset),created_s=now,kind='ultrapassagem',target=int(other['id']))
            points=np.array([self.center(v['p'],s,e) for s in ss])
            if not analyze_motion(points,v['t'],self.area)['ok']:continue
            bodies=[self.geometry(v,s,e,False) for s in ss]
            if any(not self.area.covers(p) for p in bodies):continue
            if any(not self.area.covers(MultiPoint([*a.exterior.coords,*b.exterior.coords]).convex_hull) for a,b in zip(bodies,bodies[1:])):continue
            padded=[self.geometry(v,s,e) for s in ss];blocked=False
            for w in vehicles:
                if w['id']==v['id']:continue
                future=np.clip(w['s']+dt*max(0.,w['v']),0,self.sim.paths[w['p']]['length'])
                if any(p.intersection(self.geometry(w,q)).area>1e-7 for p,q in zip(padded,future)):blocked=True;break
            if blocked:continue
            if any(any(bl.active(now+tau) and bl.poly.intersects(p) for tau,p in zip(dt,bodies)) for bl in self.sim.blocks):continue
            # A reserva espacial por passo continua protegendo pessoas/trens e o retorno.
            self.events.setdefault(key,[]).append(e);self.counts['ultrapassagens_aceitas']+=1;return True
        self.counts['ultrapassagens_sem_espaco']+=1;return False
    def prepare(self,vehicles):
        if not self.enabled:return
        # A seleção espacial evita comparar toda a frota; trabalho e memória limitados.
        from scipy.spatial import cKDTree
        if len(vehicles)<2:return
        centers=np.array([self.sim.polygon_safety.pose(v)[0] for v in vehicles]);tree=cKDTree(centers)
        for i,v in enumerate(vehicles):
            if not self.enabled_for(v.get('t')) or self.event(v):continue
            for j in sorted(tree.query_ball_point(centers[i],100))[:16]:
                if i!=j and (self.try_overtake(v,vehicles[j],vehicles) or self.try_pair(v,vehicles[j])):break
    def report(self):
        return {'enabled':self.enabled,'overtake_requested':bool(getattr(self.sim.s,'heavy_shoulder_overtake',False)),'overtake_scope':'Ensaio opcional; o próprio pesado passa à direita e retorna. Somente com reserva entre veículos ativa, espaço integral e sem faixa cadastrada à direita. Não autoriza circulação normativa pelo acostamento.','maximum_beyond_pavement_m':MAX_EDGE_EXTENSION,'counts':dict(self.counts),'maneuvers':sum(map(len,self.events.values())),'curve_profiles':len(self.curve_paths),'scope':'Sondagem local de pesados com corpo rígido conservador e reserva espacial; não é certificação de veículo articulado nem autorização normativa de uso do acostamento.'}
