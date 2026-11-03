"""Corpos orientados e reservas espaciais; nenhum objeto é removido para ocultar uma colisão."""
from .falhas import registrar as _falha
import math
from collections import defaultdict
import numpy as np
import shapely
from shapely.geometry import Polygon,MultiPoint,Point
from .vehicle_motion import PROFILES,axle_geometry_prepared,axle_pose_prepared

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

def body_corners(center,heading,length,width,buffer_m=0.):
    """Os 4 cantos de body() sem criar o Polígono (mesmas validações e aritmética; retângulo de lados positivos é sempre válido)."""
    c=np.asarray(center,float);h=np.asarray(heading,float)
    if c.shape!=(2,) or h.shape!=(2,) or not np.isfinite([*c,*h,length,width,buffer_m]).all() or length<=0 or width<=0 or buffer_m<0 or math.hypot(*h)<1e-9:raise ValueError('Corpo veicular inválido.')
    h=h/math.hypot(*h);n=np.array([-h[1],h[0]])
    return [c+h*a+n*b for a,b in [(-length/2,-width/2-buffer_m),(length/2,-width/2-buffer_m),(length/2,width/2+buffer_m),(-length/2,width/2+buffer_m)]]

class SpatialReservations:
    def __init__(self):self.cells=defaultdict(list)
    def keys(self,geometry):
        x0,y0,x1,y1=geometry.bounds
        for x in range(math.floor(x0/20),math.floor(x1/20)+1):
            for y in range(math.floor(y0/20),math.floor(y1/20)+1):yield x,y
    def add(self,identity,geometry,level=0):
        row=(identity,geometry,level)
        for key in self.keys(geometry):self.cells[key].append(row)
    def clear(self,identity,geometry,level=0,ignore=None):
        seen=set()
        for key in self.keys(geometry):
            for other,poly,other_level in self.cells.get(key,()):
                if level is not None and other_level is not None and level!=other_level:continue
                if other==identity or id(poly) in seen:continue
                seen.add(id(poly))
                if geometry.intersects(poly) and geometry.intersection(poly).area>1e-7:
                    if ignore is not None and ignore(other,poly):continue
                    return False
        return True

class SpatialCenters:
    """Índice transitório para uma fase de admissão sem movimento da frota.

    Usa a pose física (inclusive troca de faixa/acostamento), nunca a estação
    longitudinal. O chamador adiciona cada novo veículo e descarta antes de mover.
    """
    def __init__(self,pose,vehicles=()):
        self.pose=pose;self.cells=defaultdict(list);self.count=0
        for vehicle in vehicles:self.add(vehicle)
    def add(self,vehicle):
        center=self.pose(vehicle)[0]
        key=(math.floor(float(center[0])/40),math.floor(float(center[1])/40))
        self.cells[key].append((self.count,vehicle));self.count+=1
    def nearby(self,vehicle):
        center=self.pose(vehicle)[0]
        x,y=math.floor(float(center[0])/40),math.floor(float(center[1])/40)
        rows=[row for dx in (-1,0,1) for dy in (-1,0,1) for row in self.cells.get((x+dx,y+dy),())]
        return [v for _,v in sorted(rows,key=lambda row:row[0])]

class PolygonSafety:
    def __init__(self,sim):self.sim=sim;self.interventions=0;self.narrow_holds=0;self.waiting={};self.bursts={};self.corridor_cache={};self.waiting_widths={};self.pose_cache={};self.level_cache={}
    def level(self,v):
        # A rede é imutável durante a simulação; cota depende só da rota/estação.
        key=(v['p'],v['s'])
        if key in self.level_cache:return self.level_cache[key]
        result=None
        try:
            _,link,_,_,_=self.sim.locate(*key)
            if link[0]=='e' and link[1]>=0:result=int(self.sim.net.edges[link[1]].get('level',0))
        except (AttributeError,KeyError,IndexError) as _e:_falha(__name__,_e)
        if len(self.level_cache)>=8192:self.level_cache.clear()
        self.level_cache[key]=result
        return result
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
        level=self.level(new);conflicts={}
        for other in vehicles:
            q=other['p'];other_width=PROFILES.get(other.get('t','car'),PROFILES['car'])[1]
            if p==q:continue
            # Corredores sem conflito são independentes da posição/cota dos veículos.
            # Nos conflitantes, mantém TODOS os veículos e a ordem para try_pair.
            key=(q,other_width)
            if key not in conflicts:conflicts[key]=self.corridor_conflict(p,q,width,other_width)
            if not conflicts[key]:continue
            other_level=self.level(other)
            if level is not None and other_level is not None and level!=other_level:continue
            pair=tuple(sorted((p,q)))
            if conflicts[key]:
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
            key=(i,s,vt)
            if key not in self.pose_cache:
                if len(self.pose_cache)>=4096:self.pose_cache.clear()
                self.pose_cache[key]=axle_pose_prepared(*sim.motion_points[i],vt,s)
            return self.pose_cache[key]
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
    def admission(self,new,vehicles,vehicle_check=True,near=None,narrow=None):
        """near/narrow (opcionais): filtros conservadores. `near` é lista ou consulta callable que inclui todos os centros a menos de 40 m (teste de sobreposição),
        `narrow` deve conter todos os veículos de corredores potencialmente conflitantes, na ordem original. Sem eles, o comportamento é o original."""
        pedestrians=getattr(self.sim,'pedestrians',None)
        if getattr(pedestrians,'agents',[]):
            poly=self.footprint(new);level=self.level(new)
            for agent in getattr(pedestrians,'agents',[]):
                if agent['route']['kind']=='passarela':continue
                if level is not None and abs(agent['route']['height']-level)>2.5:continue
                if poly.intersects(Point(pedestrians.pose(agent)[0]).buffer(.4)):return False
        if not vehicle_check or not vehicles:return True
        if not self.narrow_admission(new,vehicles if narrow is None else narrow):return False
        poly=self.footprint(new);level=self.level(new);pn=self.pose(new)[0]
        if near is not None:vehicles=near(new) if callable(near) else near
        return all(poly.intersection(self.footprint(v)).area<1e-7 for v in vehicles if v['id']!=new['id'] and (level is None or self.level(v) is None or self.level(v)==level) and np.linalg.norm(self.pose(v)[0]-pn)<40)
    def sweep(self,v,forward):
        if forward<1e-9:return self.footprint(v)
        points=[];L,B,_,_=PROFILES.get(v.get('t','car'),PROFILES['car'])
        probe=getattr(self.sim,'shoulder_probe',None)
        if not v.get('lc') and not (probe is not None and probe.events.get((int(v['id']),int(v['p'])))):
            # Caminho rápido (sem troca de faixa nem manobra de acostamento): uma única chamada vetorizada em vez de até 17 poses isoladas. Resultado idêntico.
            ds=np.linspace(0,forward,max(3,min(17,int(math.ceil(forward/.5))+1)))
            g=axle_geometry_prepared(*self.sim.motion_points[v['p']],v.get('t','car'),v['s']+ds)
            centers=g['center'];headings=g['heading'];norm=np.linalg.norm(headings,axis=1)
            if not np.isfinite(centers).all() or not np.isfinite(headings).all() or (norm<1e-9).any():raise ValueError('Corpo veicular inválido.')
            headings=headings/norm[:,None];normal=np.column_stack((-headings[:,1],headings[:,0]))
            longitudinal=np.array([-L/2,L/2,L/2,-L/2]);lateral=np.array([-B/2-LATERAL_BUFFER,-B/2-LATERAL_BUFFER,B/2+LATERAL_BUFFER,B/2+LATERAL_BUFFER])
            corners=centers[:,None,:]+headings[:,None,:]*longitudinal[None,:,None]+normal[:,None,:]*lateral[None,:,None]
            hull=shapely.convex_hull(shapely.multipoints(corners.reshape(-1,2)))
            return hull.buffer(.03) if np.linalg.norm(g['heading'][0]-g['heading'][-1])>.002 else hull
        for ds in np.linspace(0,forward,max(3,min(17,int(math.ceil(forward/.5))+1))):
            c,h=self.pose(v,float(ds),.2*float(ds)/forward);points.extend(body_corners(c,h,L,B,LATERAL_BUFFER))
        hull=shapely.convex_hull(shapely.multipoints(np.array(points)))
        return hull.buffer(.03) if np.linalg.norm(self.pose(v)[1]-self.pose(v,forward)[1])>.002 else hull
    def resolve(self,vehicles,planned,vehicle_check=True):
        if not vehicles:return planned
        reservations=SpatialReservations();train_info={};now=float(getattr(self.sim,'time',0))
        pedestrians=getattr(self.sim,'pedestrians',None)
        for a in getattr(pedestrians,'agents',[]):
            if a['route']['kind']=='passarela':continue
            reservations.add(('pedestre',a['id']),Point(pedestrians.pose(a)[0]).buffer(.4),round(a['route']['height']))
        for index,block in enumerate(getattr(self.sim,'blocks',[])):
            if block.mode=='total' and (block.active(now) or block.active(now+.2)):reservations.add(('obra',index),block.poly,None)
        transport=getattr(self.sim,'transport',None)
        if transport:
            for at in (now,now+.2):
                for index,part in enumerate(transport.train_parts(at)):
                    identity=('trem',at,index);train_info[identity]=part
                    reservations.add(identity,body(part['p'],part['heading'],part['length'],part['width']),part.get('level',0))
        if vehicle_check:
            for v in vehicles:reservations.add(v['id'],self.footprint(v),self.level(v))
        result=list(planned)
        for index in sorted(range(len(vehicles)),key=lambda j:(-vehicles[j]['s']/max(self.sim.paths[vehicles[j]['p']]['length'],1),vehicles[j]['id'])):
            v=vehicles[index];v['_risk_stop']=False;speed,distance=result[index];sweep=self.sweep(v,distance)
            def clear(shape):
                def separated(identity,poly):
                    if identity not in train_info:return False
                    from .engineering_assets import oae_grade_separated
                    from .oae_traffic import grade_separated
                    part=train_info[identity];point=shape.intersection(poly).representative_point();heading=self.pose(v)[1]
                    return oae_grade_separated(getattr(self.sim,'s',None),point,heading,part['heading'],self.level(v) or 0,part.get('level',0)) or grade_separated(getattr(self.sim.net,'oae_info',[]),point,heading,part['heading'])
                return reservations.clear(v['id'],shape,self.level(v),ignore=separated if train_info else None)
            if not clear(sweep):
                lo=0.;hi=distance
                for _ in range(9):
                    mid=(lo+hi)/2
                    if clear(self.sweep(v,mid)):lo=mid
                    else:hi=mid
                distance=max(0.,lo-.03);speed=min(speed,distance/.2);self.interventions+=1;v['_risk_stop']=speed<.3;sweep=self.sweep(v,distance)
            result[index]=(speed,distance)
            if vehicle_check:reservations.add(v['id'],sweep,self.level(v))
        return result
