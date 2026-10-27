"""Corpos orientados e reservas espaciais; nenhum objeto é removido para ocultar uma colisão."""
import math
from collections import defaultdict
import numpy as np
from shapely.geometry import Polygon,MultiPoint,Point
from .vehicle_motion import PROFILES,axle_geometry_prepared

LATERAL_CLEARANCE=.3  # Distância livre total entre os corpos de dois veículos.
LATERAL_BUFFER=LATERAL_CLEARANCE/2
LONGITUDINAL_GAP=2.

def body(center,heading,length,width,buffer_m=0.):
    c=np.asarray(center,float);h=np.asarray(heading,float)
    if c.shape!=(2,) or h.shape!=(2,) or not np.isfinite([*c,*h,length,width,buffer_m]).all() or length<=0 or width<=0 or buffer_m<0 or math.hypot(*h)<1e-9:raise ValueError('Corpo veicular inválido.')
    h=h/math.hypot(*h);n=np.array([-h[1],h[0]])
    polygon=Polygon([c+h*a+n*b for a,b in [(-length/2,-width/2-buffer_m),(length/2,-width/2-buffer_m),(length/2,width/2+buffer_m),(-length/2,width/2+buffer_m)]])
    if not polygon.is_valid or not math.isfinite(polygon.area) or polygon.area<=0:raise ValueError('Corpo veicular degenerado.')
    return polygon

class SpatialReservations:
    def __init__(self):self.cells=defaultdict(list)
    def keys(self,geometry):
        x0,y0,x1,y1=geometry.bounds
        for x in range(math.floor(x0/20),math.floor(x1/20)+1):
            for y in range(math.floor(y0/20),math.floor(y1/20)+1):yield x,y
    def add(self,identity,geometry,level=0):
        row=(identity,geometry,level)
        for key in self.keys(geometry):self.cells[key].append(row)
    def clear(self,identity,geometry,level=0):
        seen=set()
        for key in self.keys(geometry):
            for other,poly,other_level in self.cells.get(key,()):
                if level is not None and other_level is not None and level!=other_level:continue
                if other==identity or id(poly) in seen:continue
                seen.add(id(poly))
                if geometry.intersects(poly) and geometry.intersection(poly).area>1e-7:return False
        return True

class PolygonSafety:
    def __init__(self,sim):self.sim=sim;self.interventions=0;self.narrow_holds=0;self.waiting={};self.bursts={};self.corridor_cache={};self.waiting_widths={}
    def level(self,v):
        try:
            _,link,_,_,_=self.sim.locate(v['p'],v['s'])
            if link[0]=='e' and link[1]>=0:return int(self.sim.net.edges[link[1]].get('level',0))
        except (AttributeError,KeyError,IndexError):pass
        return None
    def corridor_conflict(self,p,q,width,other_width):
        from shapely.geometry import LineString
        key=(p,q,width,other_width)
        if key not in self.corridor_cache:
            a=LineString(self.sim.paths[p]['p']);b=LineString(self.sim.paths[q]['p']);mid=a.interpolate(a.length/2);station=b.project(mid)
            h1=np.asarray(a.interpolate(a.length/2+1).coords)[0]-np.asarray(a.interpolate(a.length/2-1).coords)[0]
            h2=np.asarray(b.interpolate(min(b.length,station+1)).coords)[0]-np.asarray(b.interpolate(max(0,station-1)).coords)[0]
            cosine=float(h1@h2)/max(float(np.linalg.norm(h1)*np.linalg.norm(h2)),1e-9)
            overlap=0.
            if cosine<-.7:
                region=a.buffer(width/2+LATERAL_BUFFER,cap_style=2).intersection(b.buffer(other_width/2+LATERAL_BUFFER,cap_style=2))
                controller=getattr(self.sim,'alternating',None)
                # O trecho compartilhado já tem exclusão por sentido e cauda.
                # A fila deve formar-se nos seus portais, não fora do projeto.
                if controller:
                    from shapely.ops import unary_union
                    controlled=[g['zone']['geometry'] for g in controller.gates[p] if any(h['zone'] is g['zone'] and h['direction']!=g['direction'] for h in controller.gates[q])]
                    if controlled:region=region.difference(unary_union(controlled))
                overlap=region.area
            self.corridor_cache[key]=cosine<-.7 and overlap>min(a.length,b.length)*.05
        return self.corridor_cache[key]
    def narrow_admission(self,new,vehicles):
        p=new['p'];width=PROFILES.get(new.get('t','car'),PROFILES['car'])[1]
        for pair,wanted in self.waiting.items():
            if p in pair and wanted!=p:
                if not self.corridor_conflict(p,wanted,width,self.waiting_widths[pair][wanted]):continue
                phase,since=self.bursts.get(pair,(None,-1e9))
                if phase==p and getattr(self.sim,'time',0)-since<10:continue
                self.narrow_holds+=1;return False
        for other in vehicles:
            q=other['p'];other_width=PROFILES.get(other.get('t','car'),PROFILES['car'])[1]
            if p==q:continue
            if self.level(new) is not None and self.level(other) is not None and self.level(new)!=self.level(other):continue
            pair=tuple(sorted((p,q)))
            if self.corridor_conflict(p,q,width,other_width):
                probe=getattr(self.sim,'shoulder_probe',None)
                if probe and probe.try_pair(new,other):continue
                self.waiting.setdefault(pair,p);self.waiting_widths[pair]={p:width,q:other_width};self.bursts.setdefault(pair,(q,other.get('entered_s',getattr(self.sim,'time',0))));self.narrow_holds+=1;return False
        return True
    def admitted(self,new):
        width=PROFILES.get(new.get('t','car'),PROFILES['car'])[1]
        for pair,wanted in list(self.waiting.items()):
            other=pair[1] if pair[0]==wanted else pair[0]
            if wanted==new['p'] and self.corridor_conflict(wanted,other,width,self.waiting_widths[pair][other]):
                del self.waiting[pair];self.waiting_widths.pop(pair,None);self.bursts[pair]=(new['p'],getattr(self.sim,'time',0))
    def pose(self,v,forward=0.,dt=.2):
        probe=getattr(self.sim,'shoulder_probe',None)
        if probe is not None:
            shifted=probe.pose(v,forward)
            if shifted is not None:return shifted
        sim=self.sim;i=v['p'];s=v['s']+forward;vt=v.get('t','car');L,B,wb,_=PROFILES.get(vt,PROFILES['car']);lc=v.get('lc')
        if not lc:
            g=axle_geometry_prepared(*sim.motion_points[i],vt,np.array([s]));return g['center'][0],g['heading'][0]
        alpha=min(1.,lc['elapsed']/lc['duration']+min(dt/lc['duration'],forward/max(lc['travel_m'],1e-6)))
        if alpha<=1e-9:
            g=axle_geometry_prepared(*sim.motion_points[i],vt,np.array([s]));return g['center'][0],g['heading'][0]
        if alpha>=1-1e-9:
            target=lc['to'];g=axle_geometry_prepared(*sim.motion_points[target],vt,np.array([sim.map_s(i,target,s)]));return g['center'][0],g['heading'][0]
        center=sim._center(i,s,lc['to'],alpha)
        back=sim._center(i,s-wb/2,lc['to'],max(0,alpha-wb/2/lc['travel_m']))
        front=sim._center(i,s+wb/2,lc['to'],min(1,alpha+wb/2/lc['travel_m']))
        h=front-back;return center,h/max(float(np.linalg.norm(h)),1e-9)
    def footprint(self,v,forward=0.,dt=.2):
        c,h=self.pose(v,forward,dt);L,B,_,_=PROFILES.get(v.get('t','car'),PROFILES['car']);return body(c,h,L,B,LATERAL_BUFFER)
    def admission(self,new,vehicles):
        probe=getattr(self.sim,'shoulder_probe',None)
        pedestrians=getattr(self.sim,'pedestrians',None)
        if probe and probe.enabled:
            poly=self.footprint(new);level=self.level(new)
            for agent in getattr(pedestrians,'agents',[]):
                if agent['route']['kind']=='passarela':continue
                if level is not None and abs(agent['route']['height']-level)>2.5:continue
                if poly.intersects(Point(pedestrians.pose(agent)[0]).buffer(.4)):return False
        if not vehicles:return True
        if not self.narrow_admission(new,vehicles):return False
        poly=self.footprint(new);level=self.level(new)
        return all(poly.intersection(self.footprint(v)).area<1e-7 for v in vehicles if v['id']!=new['id'] and (level is None or self.level(v) is None or self.level(v)==level) and np.linalg.norm(self.pose(v)[0]-self.pose(new)[0])<40)
    def sweep(self,v,forward):
        if forward<1e-9:return self.footprint(v)
        points=[]
        for ds in np.linspace(0,forward,max(3,min(17,int(math.ceil(forward/.5))+1))):points.extend(self.footprint(v,float(ds),.2*float(ds)/forward).exterior.coords)
        hull=MultiPoint(points).convex_hull
        return hull.buffer(.03) if np.linalg.norm(self.pose(v)[1]-self.pose(v,forward)[1])>.002 else hull
    def resolve(self,vehicles,planned):
        if not vehicles:return planned
        reservations=SpatialReservations()
        probe=getattr(self.sim,'shoulder_probe',None)
        if probe and probe.enabled:
            pedestrians=getattr(self.sim,'pedestrians',None)
            for a in getattr(pedestrians,'agents',[]):
                if a['route']['kind']=='passarela':continue
                reservations.add(('pedestre',a['id']),Point(pedestrians.pose(a)[0]).buffer(.4),round(a['route']['height']))
            for index,block in enumerate(getattr(self.sim,'blocks',[])):
                if block.mode=='total' and (block.active(self.sim.time) or block.active(self.sim.time+.2)):reservations.add(('obra',index),block.poly,None)
            transport=getattr(self.sim,'transport',None)
            if transport:
                for at in (self.sim.time,self.sim.time+.2):
                    for index,part in enumerate(transport.train_parts(at)):
                        reservations.add(('trem',at,index),body(part['p'],part['heading'],part['length'],part['width']),part.get('level',0))
        for v in vehicles:reservations.add(v['id'],self.footprint(v),self.level(v))
        result=list(planned)
        for index in sorted(range(len(vehicles)),key=lambda j:(-vehicles[j]['s']/max(self.sim.paths[vehicles[j]['p']]['length'],1),vehicles[j]['id'])):
            v=vehicles[index];v['_risk_stop']=False;speed,distance=result[index];sweep=self.sweep(v,distance)
            if not reservations.clear(v['id'],sweep,self.level(v)):
                lo=0.;hi=distance
                for _ in range(9):
                    mid=(lo+hi)/2
                    if reservations.clear(v['id'],self.sweep(v,mid),self.level(v)):lo=mid
                    else:hi=mid
                distance=max(0.,lo-.03);speed=min(speed,distance/.2);self.interventions+=1;v['_risk_stop']=speed<.3;sweep=self.sweep(v,distance)
            result[index]=(speed,distance);reservations.add(v['id'],sweep,self.level(v))
        return result
