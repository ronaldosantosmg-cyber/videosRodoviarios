"""Relógio compartilhado de trens, passagens em nível e semáforos. Sem estado de quadro."""
import math,hashlib
import numpy as np
from shapely.geometry import LineString,Point

AMBER=3.
CLEARANCE=12.
RAIL_WARNING=20.

def xy(points):return np.array([[p.x,p.y] for p in points],float)
def stations(p):return np.r_[0.,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
def at(p,d,s):
    s=float(np.clip(s,0,d[-1]));i=min(len(p)-2,max(0,int(np.searchsorted(d,s,side='right'))-1));v=p[i+1]-p[i];v=v/max(float(np.linalg.norm(v)),1e-9)
    return p[i]+v*(s-d[i]),v

def intersections(line,other):
    g=line.intersection(other)
    if g.is_empty:return []
    if g.geom_type=='Point':return [g]
    if g.geom_type in ('MultiPoint','GeometryCollection'):return [p for sub in g.geoms for p in intersections(line,sub)]
    # Coincidência longitudinal não é uma passagem em nível.
    return []

def timings(s):
    extra=5 if s.phases==2 else 15
    greens=[2*s.lanes_a+extra,2*s.lanes_b+extra]
    walk=2*max(s.lanes_a,s.lanes_b)+15 if s.phases==3 else 0
    return greens,walk,sum(greens)+2*(AMBER+s.clearance_s)+walk

def phase(s,t,offset=0):
    greens,walk,cycle=timings(s);u=(float(t)-offset)%cycle
    for axis,duration in enumerate(greens):
        if u<duration:return ('green' if axis==0 else 'red','green' if axis==1 else 'red',False)
        u-=duration
        if u<AMBER:return ('amber' if axis==0 else 'red','amber' if axis==1 else 'red',False)
        u-=AMBER
        if u<s.clearance_s:return ('red','red',False)
        u-=s.clearance_s
    return ('red','red',bool(walk))

class Transport:
    def __init__(self,settings,network=None):
        self.s=settings;self.rails=[];self.signals=list(getattr(settings,'traffic_signals',[]));self.offsets={s.id:float(s.offset_s) for s in self.signals};self.by_id={s.id:s for s in self.signals}
        links={l.target:l for l in getattr(settings,'signal_links',[]) if l.enabled and self.by_id[l.source].enabled and self.by_id[l.target].enabled}
        def offset(node):
            if node not in links:return self.offsets[node]
            link=links[node];a,b=self.by_id[link.source],self.by_id[node]
            return offset(a.id)+math.hypot(a.point.x-b.point.x,a.point.y-b.point.y)/(link.speed_kmh/3.6)
        for node in self.offsets:self.offsets[node]=offset(node)
        for r in getattr(settings,'railways',[]):
            p=xy(r.points);d=stations(p);t=np.gradient(p,axis=0);t/=np.maximum(np.linalg.norm(t,axis=1)[:,None],1e-9);normal=np.column_stack([-t[:,1],t[:,0]])
            for track in range(r.tracks):
                points=p+normal*((track-.5)*4.5 if r.tracks==2 else 0);dd=stations(points)
                self.rails.append({'config':r,'track':track,'p':points,'d':dd,'line':LineString(points),'corridor':LineString(points).buffer(3.3,cap_style=2),'length':float(dd[-1]),'period':float(max(r.interval_s,(dd[-1]+20+r.max_wagons*15)/(r.speed_kmh/3.6)+2*RAIL_WARNING+15))})
        self.stops=[];self.path_lines=[]
        if network is not None:self.prepare(network)
    def event(self,rail,t):
        r=rail['config'];period=rail['period'];k=math.floor((t-r.start_s)/period);elapsed=t-r.start_s-k*period
        seed=hashlib.sha256(f'{r.id}:{r.seed}:{rail["track"]}:{k}'.encode()).digest();wagons=r.min_wagons+int.from_bytes(seed[:4],'big')%(r.max_wagons-r.min_wagons+1)
        reverse=r.direction=='reverse' or r.direction=='both' and (rail['track']==1 if r.tracks==2 else k%2==1)
        front=elapsed*r.speed_kmh/3.6-20
        return {'cycle':k,'wagons':wagons,'reverse':reverse,'front':front,'rear':front-(20+wagons*15),'length':20+wagons*15}
    def rail_closed(self,rail,station,t,warning_s=RAIL_WARNING):
        if not rail['config'].enabled:return False
        v=rail['config'].speed_kmh/3.6
        # A próxima composição já deve fechar a passagem antes de entrar no alinhamento.
        for shift in (0.,rail['period']):
            e=self.event(rail,t+shift);s=rail['length']-station if e['reverse'] else station
            front=e['front']-v*shift;rear=e['rear']-v*shift
            if front+v*warning_s>=s-5 and rear-v*3<=s+5:return True
        return False
    def rail_stop_closed(self,stop,t):
        return bool(stop.get('permanent') or self.rail_closed(stop['rail'],stop['rail_s'],t,stop.get('warning_s',RAIL_WARNING)))
    def signal_state(self,s,t):return phase(s,t,self.offsets[s.id]) if s.enabled else ('off','off',False)
    def signal_axis(self,s,heading):
        a=math.radians(s.heading_deg);b=math.radians(s.heading_deg+90 if s.heading_b_deg is None else s.heading_b_deg)
        return 0 if abs(float(heading@np.array([math.cos(a),math.sin(a)])))>=abs(float(heading@np.array([math.cos(b),math.sin(b)]))) else 1
    def approaches(self,s):
        a=math.radians(s.heading_deg);b=math.radians(s.heading_deg+90 if s.heading_b_deg is None else s.heading_b_deg);u=np.array([math.cos(a),math.sin(a)]);v=np.array([math.cos(b),math.sin(b)]);skew=max(.15,abs(math.sin(b-a)));c=np.array([s.point.x,s.point.y]);rows=[]
        for axis,(heading,cross,count,other) in enumerate([(u,v,s.lanes_b,s.lanes_a),(v,u,s.lanes_a,s.lanes_b)]):
            for sign in (1,-1):
                cross=np.array([-heading[1],heading[0]]);direction=heading*sign;station=c-direction*(other*s.lane_width_m/(2*skew)+8);half=count*s.lane_width_m/2+1
                rows.append({'axis':axis,'center':station,'direction':direction,'a':station-cross*half,'b':station+cross*half,'width':half*2,'clear_span':other*s.lane_width_m/skew+16})
        return rows
    def prepare(self,network):
        for path in network.paths:
            line=LineString(path['p']);self.path_lines.append(line);stops=[]
            envelope=None
            if any(r['config'].enabled for r in self.rails):
                from .simulation import curve_envelope
                envelope=curve_envelope(path['p'],path['d'],lateral_acc=2.2 if getattr(self.s,'curve_speed',False) else 4.)
            def level_at(station):
                for lid,a,b in path.get('links',[]):
                    if a-1<=station<=b+1 and lid[0]=='e' and lid[1]>=0:return network.edges[lid[1]].get('level',0)
                return 0
            for rail in self.rails:
                if not rail['config'].enabled:continue
                crossing=line.intersection(rail['line']);points=[(q,False) for q in intersections(line,rail['line'])];overlap=crossing.geom_type in ('LineString','MultiLineString') and not crossing.is_empty
                if overlap:
                    pieces=list(crossing.geoms) if hasattr(crossing,'geoms') else [crossing]
                    points.extend((Point(piece.coords[0]),True) for piece in pieces if piece.length>.05)
                nearby=line.intersection(rail['corridor'])
                nearby_parts=list(nearby.geoms) if hasattr(nearby,'geoms') else [nearby]
                for part in nearby_parts:
                    if part.geom_type!='LineString' or part.length<5:continue
                    mid=part.interpolate(.5,normalized=True);_,rh=at(path['p'],path['d'],line.project(mid));_,th=at(rail['p'],rail['d'],rail['line'].project(mid))
                    if abs(float(rh[0]*th[1]-rh[1]*th[0]))<.15:points.append((Point(part.coords[0]),True))
                for q,ambiguous in points:
                    d=line.project(q)
                    if level_at(d)!=rail['config'].level:continue
                    rs=rail['line'].project(q);_,road_h=at(path['p'],path['d'],d);_,rail_h=at(rail['p'],rail['d'],rs)
                    from .engineering_assets import oae_grade_separated
                    if oae_grade_separated(self.s,q,road_h,rail_h,level_at(d),rail['config'].level):continue
                    sine=abs(float(road_h[0]*rail_h[1]-road_h[1]*rail_h[0]));permanent=ambiguous or sine<.15
                    speed=max(.1,self.s.traffic_speed_kmh/3.6*.7*.8)
                    if envelope is not None:
                        mask=np.abs(path['d']-d)<(6/max(sine,.15)+60)
                        if mask.any():speed=min(speed,max(.1,float(np.min(envelope[mask]))*.7*.8))
                    warning=max(RAIL_WARNING,(6/max(sine,.15)+25)/speed+5)
                    stops.append({'kind':'rail','s':max(0.,d-9),'cross':d,'rail':rail,'rail_s':rs,'warning_s':warning,'clear_after_m':max(12.,3/max(sine,.15)+5),'permanent':permanent})
            for signal in self.signals:
                if not signal.enabled:continue
                for approach in self.approaches(signal):
                    for q in intersections(line,LineString([approach['a'],approach['b']])):
                        d=line.project(q);_,heading=at(path['p'],path['d'],d)
                        if level_at(d)==signal.level and self.signal_axis(signal,heading)==approach['axis'] and float(heading@approach['direction'])>.7:stops.append({'kind':'signal','s':d,'signal':signal,'axis':approach['axis'],'clear_span':approach['clear_span']})
            start=path['p'][0];_,heading=at(path['p'],path['d'],0.)
            for signal in self.signals:
                radius=max(signal.lanes_a,signal.lanes_b)*signal.lane_width_m/2+8
                if not signal.enabled or level_at(0)!=signal.level or np.linalg.norm(start-np.array([signal.point.x,signal.point.y]))>radius:continue
                axis=self.signal_axis(signal,heading)
                stops.append({'kind':'signal','s':0.,'signal':signal,'axis':axis,'entry_only':True})
            self.stops.append(sorted(stops,key=lambda r:r['s']))
    def stop_gap(self,v,t,leader_gap=math.inf):
        best=math.inf
        targets=[(v['p'],v['s'])]
        if v.get('lc') is not None:
            position,_=at(np.asarray(self.path_lines[v['p']].coords),stations(np.asarray(self.path_lines[v['p']].coords)),v['s']);target=v['lc']['to'];targets.append((target,self.path_lines[target].project(Point(position))))
        for pi,station in targets:
            for stop in self.stops[pi]:
                gap=stop['s']-station-v['L']/2
                if gap<-.01:continue # veículo comprometido com a travessia deve sair, nunca voltar.
                if stop['kind']=='signal':
                    signal=stop['signal'];other=signal.lanes_a if stop['axis']==0 else signal.lanes_b
                    closed=self.signal_state(signal,t)[stop['axis']]!='green' or leader_gap<stop['s']+stop.get('clear_span',other*signal.lane_width_m+16)+v['L']/2-station
                else:closed=self.rail_stop_closed(stop,t) or leader_gap<stop['cross']+stop.get('clear_after_m',12)+v['L']/2-station
                if closed:best=min(best,max(0.,gap))
        return best
    def admission_allowed(self,path,t,length):
        for stop in self.stops[path]:
            if stop['s']>length/2+1:continue
            if stop['kind']=='signal' and self.signal_state(stop['signal'],t)[stop['axis']]!='green':return False
            if stop['kind']=='rail' and self.rail_stop_closed(stop,t):return False
        return True
    def train_parts(self,t):
        out=[]
        for i,rail in enumerate(self.rails):
            if not rail['config'].enabled:continue
            e=self.event(rail,t)
            for j in range(e['wagons']+1):
                s=e['front']-(10 if j==0 else 20+(j-.5)*15)
                if not 0<=s<=rail['length']:continue
                original_s=rail['length']-s if e['reverse'] else s;p,h=at(rail['p'],rail['d'],original_s)
                half=10. if j==0 else 7.;front,_=at(rail['p'],rail['d'],original_s+half);rear,_=at(rail['p'],rail['d'],original_s-half);heading=front-rear
                if np.linalg.norm(heading)>1e-8:h=heading/np.linalg.norm(heading)
                if e['reverse']:h=-h
                out.append({'id':f'{i}:{e["cycle"]}:{j}','p':p,'heading':h,'length':20. if j==0 else 14.,'width':3.,'locomotive':j==0,'level':float(rail['config'].level),'speed_mps':float(rail['config'].speed_kmh)/3.6,'model':rail['config'].model,'wagons':e['wagons']})
        return out
    def report(self):
        coverage=[{'id':signal.id,'name':signal.name,'axis_a':sum(stop['kind']=='signal' and stop['signal'].id==signal.id and stop['axis']==0 for rows in self.stops for stop in rows),'axis_b':sum(stop['kind']=='signal' and stop['signal'].id==signal.id and stop['axis']==1 for rows in self.stops for stop in rows)} for signal in self.signals if signal.enabled]
        warnings=[f'Semáforo {row["name"]}: confira alinhamento, sentido e número de faixas; existe eixo sem rota interceptada.' for row in coverage if not row['axis_a'] or not row['axis_b']]
        conflicts={stop['rail']['config'].name for rows in self.stops for stop in rows if stop.get('permanent')}
        warnings.extend('Ferrovia '+name+': coincidência ou encontro quase paralelo com trajetória rodoviária no mesmo nível. Veículos bloqueados; revise o traçado / nível ou desative o fluxo compartilhado.' for name in sorted(conflicts))
        return {'coverage':coverage,'warnings':warnings,'ambiguous_railway_conflicts':len(conflicts),'railways':len({r['config'].id for r in self.rails}),'signals':len(self.signals),'crossings':sum(s['kind']=='rail' for rows in self.stops for s in rows),'stop_lines':sum(s['kind']=='signal' for rows in self.stops for s in rows),'signal_offsets_s':self.offsets,'scope':'Simulação ilustrativa com temporização informada pelo usuário; sem certificação de sinalização.'}
