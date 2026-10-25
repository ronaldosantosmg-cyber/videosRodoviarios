"""Agentes locais determinísticos com espera, travessia e reservas de espaço."""
import math
import numpy as np
from shapely.geometry import LineString,Point
from .transport import at,stations,xy
from .vehicle_safety import SpatialReservations

MAX_PEOPLE=80
MAX_HISTORY_SAMPLES=800000


class PedestrianTraffic:
    def __init__(self,settings,network,transport,owner=None):
        self.settings=settings;self.net=network;self.transport=transport
        self.routes=[];self.agents=[];self.history=[];self.times=[];self.next_id=0
        self.waits=0;self.admitted=0;self.arrived=0;self.yields=0;self.rejected=0;self.warnings=[]
        self.rng=np.random.default_rng(getattr(settings,'pedestrian_seed',1))
        self.owner=owner;self.vehicle_collisions=0;self.people_collisions=0;self.train_collisions=0
        self.history_samples=0
        if not getattr(settings,'pedestrians',False):return
        for i,c in enumerate(getattr(settings,'crosswalks',[])):
            if c.show:
                p=np.array([[c.a.x,c.a.y],[c.b.x,c.b.y]])
                nearby=[signal for signal in transport.signals if signal.enabled and LineString(p).distance(Point(signal.point.x,signal.point.y))<20]
                signal=min(nearby,key=lambda signal:LineString(p).distance(Point(signal.point.x,signal.point.y))) if nearby else None
                self.add(p,'faixa',str(c.id or i),2,signal=signal)
        for signal in transport.signals:
            if not signal.enabled or signal.phases!=3:continue
            for i,a in enumerate(transport.approaches(signal)):
                c=a['center']+a['direction']*3;n=np.array([-a['direction'][1],a['direction'][0]])
                self.add(np.array([c-n*a['width']/2,c+n*a['width']/2]),'faixa',f'{signal.id}:{i}',2,signal=signal)
        for i,path in enumerate(getattr(settings,'pedestrian_paths',[])):
            if path.enabled:self.add(xy(path.points),'calcada',str(path.id or i),max(1,path.people_per_100m))
        from .structures import bridge_geometry
        for i,poi in enumerate(getattr(settings,'pois',[])):
            if poi.kind!='passarela':continue
            p=poi.model_dump();height=float(p.get('bridge_clearance_m',5.5))
            if height<5.5:self.warnings.append('Passarela sem gabarito de 5,5 m confirmado: pedestres não gerados.');continue
            center=np.array([poi.x,poi.y]);j=int(np.argmin(np.linalg.norm(network.dense-center,axis=1)))
            g=bridge_geometry(center,network.axis_t[j],p)
            endpoints=np.array([g['center']-g['v']*g['span']/2,g['center']+g['v']*g['span']/2]);deck=LineString(endpoints).buffer(float(poi.bridge_width_m)/2)
            levels=[float(edge.get('level',0)) for edge in network.edges if deck.intersects(LineString(edge['p']))]
            levels.extend(float(rail['config'].level) for rail in transport.rails if deck.intersects(rail['line']))
            height+=max([0.]+levels)
            if any(network.allowed.buffer(.5).covers(Point(end)) or any(rail['corridor'].buffer(.5).covers(Point(end)) for rail in transport.rails) for end in endpoints):
                self.warnings.append('Vão da passarela não alcança área segura fora da pista/ferrovia; ajuste o vão.');self.rejected+=1;continue
            self.add(endpoints,'passarela',str(poi.id or i),3,height=height,width=float(poi.bridge_width_m))

    def add(self,p,kind,identity,density,signal=None,height=0.,width=3.):
        if len(self.routes)>=300:
            if 'Limite de 300 percursos de pedestres atingido; divida o projeto.' not in self.warnings:self.warnings.append('Limite de 300 percursos de pedestres atingido; divida o projeto.')
            self.rejected+=1;return
        if p.ndim!=2 or p.shape[1]!=2 or len(p)<2 or not np.isfinite(p).all():self.rejected+=1;return
        d=stations(p)
        if d[-1]<1 or d[-1]>10000:self.rejected+=1;return
        if kind=='faixa':
            # Espera no passeio; não criar uma pessoa inicialmente dentro da pista.
            p=p.copy();direction=(p[-1]-p[0])/max(np.linalg.norm(p[-1]-p[0]),1e-9)
            for index,sign in [(0,-1),(-1,1)]:
                for _ in range(40):
                    if not self.net.allowed.buffer(1.2).covers(Point(p[index])):break
                    p[index]+=direction*sign
                else:self.rejected+=1;return
            d=stations(p)
        if signal is not None:
            from .transport import timings
            if signal.phases!=3:self.warnings.append('Faixa associada a semáforo sem fase exclusiva para pedestres; travessia permanece em espera.')
            elif timings(signal)[1]<d[-1]/1.6+1:self.warnings.append('Fase de pedestres curta para a extensão da faixa; confira a quantidade de faixas atravessadas e o desenho da travessia.')
        line=LineString(p)
        if not line.is_simple:self.rejected+=1;return
        if any(abs(r['height']-height)<2.5 and line.hausdorff_distance(r['line'])<1.8 for r in self.routes):return
        if kind=='calcada' and (line.buffer(.9).intersects(self.net.allowed) or any(line.buffer(.9).intersects(r['corridor']) for r in self.transport.rails)):
            self.warnings.append('Caminho informal intercepta pista/ferrovia: use faixa ou passarela; pedestres não gerados.');self.rejected+=1;return
        if kind=='faixa' and any(abs(float(rail['config'].level)-height)<4.8 and any(Point(end).buffer(.6).intersects(rail['corridor']) for end in (p[0],p[-1])) for rail in self.transport.rails):
            self.warnings.append('Extremidade da faixa coincide com ferrovia: mova a espera para área segura ou use passarela.');self.rejected+=1;return
        conflicts=[]
        if kind!='passarela':
            for pi,path in enumerate(self.net.paths):
                levels=[float(self.net.edges[e].get('level',0)) for e in path.get('edges',[]) if 0<=e<len(self.net.edges)]
                if levels and all(abs(height-level)>4.8 for level in levels):continue
                road=LineString(path['p']);overlap=road.intersection(line.buffer(1.1))
                if overlap.is_empty:continue
                positions=[road.project(Point(c)) for geom in getattr(overlap,'geoms',[overlap]) for c in getattr(geom,'coords',[])]
                if not positions:continue
                conflicts.append(dict(path=pi,a=max(0.,min(positions)-1.5),b=max(positions)+1.5))
        self.routes.append(dict(index=len(self.routes),p=p,d=d,line=line,kind=kind,id=identity,signal=signal,height=height,
                                width=width,conflicts=conflicts,next=0.,burst=None,release_after=0.,interval=max(2.,min(90.,(10. if kind=='faixa' else 100/1.3)/max(float(density),.2)))))

    def pose(self,a,station=None):
        r=a['route'];s=a['s'] if station is None else station
        point,h=at(r['p'],r['d'],s);direction=h*a['direction'];normal=np.array([-h[1],h[0]])
        return point+normal*.45*a['direction'],direction

    def railway_clear(self,r,t,horizon):
        if r['kind'] in ('passarela','calcada'):return True
        for rail in self.transport.rails:
            if not rail['config'].enabled or abs(float(rail['config'].level)-r['height'])>4.8:continue
            overlap=rail['line'].intersection(r['line'].buffer(50))
            if overlap.is_empty:continue
            for geom in getattr(overlap,'geoms',[overlap]):
                coords=list(getattr(geom,'coords',[]))
                for q in coords:
                    if self.transport.rail_closed(rail,rail['line'].project(Point(q)),t,warning_s=max(20.,horizon+3,50/(rail['config'].speed_kmh/3.6))):return False
        return True

    def can_enter(self,r,vehicles,t,speed):
        if t<r['release_after'] or r['burst'] is not None and t-r['burst']>10:return False
        if not self.railway_clear(r,t,r['d'][-1]/speed):return False
        if r['signal'] is not None:
            from .transport import timings
            if r['d'][-1]/speed+1>timings(r['signal'])[1]:return False
            if not self.transport.signal_state(r['signal'],t)[2] or not self.transport.signal_state(r['signal'],t+r['d'][-1]/speed+1)[2]:return False
        for c in r['conflicts']:
            for v in vehicles:
                paths={v['p']}
                if v.get('lc'):paths.add(v['lc']['to'])
                if c['path'] not in paths:continue
                station=v['s']
                if c['path']!=v['p']:
                    point,_=at(self.net.paths[v['p']]['p'],self.net.paths[v['p']]['d'],station)
                    station=LineString(self.net.paths[c['path']]['p']).project(Point(point))
                front=station+v['L']/2;rear=station-v['L']/2
                if front>=c['a'] and rear<=c['b']+1:return False
                if front<c['a'] and c['a']-front<max(5.,v['v']**2/4+v['v']*1.5+4):return False
        if self.owner and r['kind']!='passarela':
            for v in vehicles:
                if v.get('lc') and Point(self.owner.polygon_safety.pose(v)[0]).distance(r['line'])<50+v['L']:return False
                if r['line'].buffer(.9).intersects(self.owner.polygon_safety.footprint(v)):return False
        return True

    def stop_gap(self,v):
        best=math.inf
        for a in self.agents:
            if a['state']!='crossing' or a['route']['kind']=='passarela':continue
            for c in a['route']['conflicts']:
                targets=[(v['p'],v['s'])]
                if v.get('lc'):
                    q,_=at(self.net.paths[v['p']]['p'],self.net.paths[v['p']]['d'],v['s'])
                    targets.append((v['lc']['to'],LineString(self.net.paths[v['lc']['to']]['p']).project(Point(q))))
                for pi,s in targets:
                    gap=c['a']-s-v['L']/2
                    if pi==c['path'] and gap>=-.01:best=min(best,max(0.,gap))
        return best

    def lane_change_allowed(self,v,target,travel):
        if not self.owner:return True
        point,_=self.owner.polygon_safety.pose(v)
        return not any(a['state']=='crossing' and a['route']['kind']=='faixa' and Point(point).distance(a['route']['line'])<50+travel for a in self.agents)

    def admission_allowed(self,path,length):
        return not any(a['state']=='crossing' and any(c['path']==path and c['a']<length/2+3 for c in a['route']['conflicts']) for a in self.agents)

    def update(self,vehicles,t,dt=.2):
        if not self.routes or t<0:return
        for r in self.routes:
            if r['burst'] is not None and t-r['burst']>10 and not any(a['route'] is r and a['state']=='crossing' for a in self.agents):
                r['burst']=None;r['release_after']=t+6
        for r in self.routes:
            if t<0 or t<r['next']:continue
            r['next']=t+max(1.5,float(self.rng.exponential(r['interval'])))
            if len(self.agents)>=MAX_PEOPLE:continue
            sign=1 if self.rng.random()>.5 else -1
            a=dict(id=self.next_id,route=r,s=0. if sign>0 else float(r['d'][-1]),direction=sign,
                   speed=float(self.rng.uniform(1.05,1.6)),state='waiting')
            p,_=self.pose(a)
            if any(abs(other['route']['height']-r['height'])<2.5 and np.linalg.norm(self.pose(other)[0]-p)<.95 for other in self.agents):continue
            self.next_id+=1;self.agents.append(a)
        reservations=SpatialReservations()
        for a in self.agents:reservations.add(a['id'],Point(self.pose(a)[0]).buffer(.4),round(a['route']['height']))
        alive=[]
        for a in self.agents:
            r=a['route'];before,_=self.pose(a)
            if a['state']=='waiting':
                if not self.can_enter(r,vehicles,t,a['speed']):self.waits+=1;alive.append(a);continue
                a['state']='crossing';self.admitted+=1
                if r['burst'] is None:r['burst']=t
            target=float(np.clip(a['s']+a['direction']*a['speed']*dt,0,r['d'][-1]));after,_=self.pose(a,target)
            sweep=LineString([before,after]).buffer(.4) if np.linalg.norm(after-before)>1e-9 else Point(before).buffer(.4)
            if reservations.clear(a['id'],sweep,round(r['height'])):
                a['s']=target;reservations.add(a['id'],sweep,round(r['height']))
            else:
                self.waits+=1
                # Ceder espaço com um passo atrás desfaz impasses locais; não muda de rota.
                if any(other['id']<a['id'] and abs(other['route']['height']-r['height'])<2.5 and np.linalg.norm(self.pose(other)[0]-before)<1.5 for other in self.agents):
                    retreat=float(np.clip(a['s']-a['direction']*a['speed']*dt,0,r['d'][-1]));back,_=self.pose(a,retreat)
                    if np.linalg.norm(back-before)>1e-9:
                        yielding=LineString([before,back]).buffer(.4)
                        if reservations.clear(a['id'],yielding,round(r['height'])):
                            a['s']=retreat;reservations.add(a['id'],yielding,round(r['height']));self.yields+=1
            if not (a['direction']>0 and a['s']>=r['d'][-1] or a['direction']<0 and a['s']<=0):alive.append(a)
            else:self.arrived+=1
        self.agents=alive
        if t>=0:
            # Cinco números por pessoa em vez de dicionários de coordenadas por quadro.
            self.history_samples+=len(alive)
            if self.history_samples>MAX_HISTORY_SAMPLES:raise ValueError('Pedestres excedem o orçamento de histórico; reduza a duração/densidade.')
            rows=np.array([[a['id'],a['route']['index'],a['s'],a['direction'],int(a['state']=='crossing')] for a in alive],dtype=np.float64).reshape((-1,5))
            self.times.append(float(t));self.history.append(rows)

    def state(self,t):
        if not self.times:return []
        i=max(0,min(len(self.times)-1,int(np.searchsorted(self.times,t,side='right')-1)));out=[]
        alpha=0.;later={}
        if i<len(self.times)-1:
            alpha=float(np.clip((t-self.times[i])/max(self.times[i+1]-self.times[i],1e-9),0,1));later={int(r[0]):r for r in self.history[i+1]}
        for row in self.history[i]:
            identity,ri,station,direction,crossing=row;identity=int(identity);route=self.routes[int(ri)]
            if crossing and identity in later:station=station*(1-alpha)+later[identity][2]*alpha
            a={'route':route,'s':station,'direction':direction};p,h=self.pose(a)
            out.append(dict(id=identity,p=p.tolist(),heading=h.tolist(),height=route['height'],state='crossing' if crossing else 'waiting',kind=route['kind']))
        return out

    def report(self):return dict(routes=len(self.routes),admitted=self.admitted,arrived=self.arrived,yield_steps=self.yields,waiting_steps=self.waits,rejected_paths=self.rejected,
                                  maximum_agents=MAX_PEOPLE,vehicle_collisions=self.vehicle_collisions,people_collisions=self.people_collisions,train_collisions=self.train_collisions,history_samples=self.history_samples,history_bytes=sum(r.nbytes for r in self.history),warnings=list(dict.fromkeys(self.warnings)),scope='Agentes locais ilustrativos; sem calibração ou certificação normativa.')

    def check(self,vehicles,t=None):
        if not self.agents:return
        occupied=SpatialReservations()
        for a in self.agents:
            person=Point(self.pose(a)[0]).buffer(.35);level=round(a['route']['height'])
            if not occupied.clear(a['id'],person,level):
                self.people_collisions+=1;raise ValueError('Conflito entre pedestres: revise os caminhos antes de exportar.')
            occupied.add(a['id'],person,level)
        if t is not None:
            from .transport_render import rectangle
            from shapely.geometry import Polygon
            for part in self.transport.train_parts(t):
                for a in self.agents:
                    if abs(a['route']['height']-part.get('level',0))>4.8:continue
                    if np.linalg.norm(self.pose(a)[0]-part['p'])>part['length']/2+3:continue
                    if Point(self.pose(a)[0]).buffer(.35).intersects(Polygon(rectangle(part['p'],part['heading'],part['length'],part['width']))):
                        self.train_collisions+=1;raise ValueError('Conflito entre pedestre e trem: revise a travessia antes de exportar.')
        if not self.owner:return
        for a in self.agents:
            if a['route']['kind']=='passarela':continue
            p,_=self.pose(a);person=Point(p).buffer(.35)
            for v in vehicles:
                if abs(a['route']['height']-float(self.owner.polygon_safety.level(v) or 0))>4.8:continue
                center,_=self.owner.polygon_safety.pose(v)
                if np.linalg.norm(center-p)>v['L']/2+4:continue
                if person.intersects(self.owner.polygon_safety.footprint(v)):
                    self.vehicle_collisions+=1;raise ValueError('Conflito entre pedestre e veículo: revise a travessia antes de gerar o vídeo.')


def without_vehicles(settings,network,transport,duration):
    control=PedestrianTraffic(settings,network,transport)
    for t in np.arange(0,float(duration)+.2,.2):
        control.update([],float(t),.2);control.check([],float(t))
    return control
