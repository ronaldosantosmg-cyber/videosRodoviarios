"""Liberação de comboios por 10 s com entretempo até o último veículo desocupar."""
import math
import numpy as np
from shapely.geometry import LineString,Point
from shapely.ops import substring

class AlternatingTraffic:
    def __init__(self,settings,network):
        self.zones=[];self.gates=[[] for _ in network.paths];self.history=[];self.stops=0
        for config in getattr(settings,'alternating_zones',[]):
            if not config.enabled:continue
            route=next(r for r in settings.route_alignments if r.id==config.route_id)
            axis=LineString([(p.x,p.y) for p in route.points]);a=max(0,config.start_m-route.taper_m);b=min(axis.length,config.end_m+route.taper_m)
            corridor=substring(axis,a,b).buffer(max(8,route.lane_width_m*2),cap_style=2)
            zone=dict(config=config,phase='f',since=None,clearing=False,index=len(self.zones),geometry=corridor);self.zones.append(zone)
            for i,path in enumerate(network.paths):
                line=LineString(path['p']);intersection=line.intersection(corridor)
                if intersection.is_empty:continue
                # Não inventa uma travessia em outro nível.
                edges=[network.edges[e] for e in path.get('edges',[]) if 0<=e<len(network.edges)]
                if edges and all(int(e.get('level',0))!=route.level for e in edges):continue
                parts=list(intersection.geoms) if hasattr(intersection,'geoms') else [intersection]
                spans=[]
                for part in parts:
                    if part.geom_type!='LineString' or part.length<1:continue
                    xy=np.asarray(part.coords);stations=[line.project(Point(p)) for p in xy];lo,hi=min(stations),max(stations)
                    first=np.asarray(line.interpolate(lo).coords)[0];last=np.asarray(line.interpolate(hi).coords)[0]
                    sa=axis.project(Point(first));sb=axis.project(Point(last))
                    if abs(sb-sa)<max(5,(b-a)*.5):continue
                    spans.append(dict(zone=zone,a=lo,b=hi,direction='f' if sb>sa else 'r'))
                self.gates[i].extend(spans)
    def update(self,vehicles,t):
        for zone in self.zones:
            if zone['since'] is None:zone['since']=t
            if not zone['clearing'] and t-zone['since']>=zone['config'].release_s-1e-8:zone['clearing']=True
            occupied=False
            if zone['clearing']:
                for vehicle in vehicles:
                    paths=[(vehicle['p'],vehicle['s'])]
                    if vehicle.get('lc'):paths.append((vehicle['lc']['to'],vehicle['s']))
                    for path_i,s in paths:
                        if any(g['zone'] is zone and s+vehicle['L']/2>g['a'] and s-vehicle['L']/2<g['b'] for g in self.gates[path_i]):occupied=True;break
                    if occupied:break
                if not occupied:
                    zone['phase']='r' if zone['phase']=='f' else 'f';zone['clearing']=False;zone['since']=t
        states=[(z['phase'],z['clearing']) for z in self.zones]
        if not self.history or self.history[-1][1]!=states:self.history.append((float(t),states))
    def stop_gap(self,v):
        gap=math.inf
        for gate in self.gates[v['p']]:
            z=gate['zone'];front=v['s']+v['L']/2
            # Quem já entrou desocupa; uma fase contrária nunca é liberada com ocupantes.
            if front>gate['a']+.01:continue
            if z['clearing'] or z['phase']!=gate['direction']:gap=min(gap,gate['a']-front)
        return gap
    def report(self):
        return {'zones':len(self.zones),'release_s':[z['config'].release_s for z in self.zones],'clearance':'até o último veículo desocupar; sem inversão forçada','phase_changes':len(self.history)}
