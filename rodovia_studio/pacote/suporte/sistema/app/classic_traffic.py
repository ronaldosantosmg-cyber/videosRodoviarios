"""Modo ilustrativo explícito: não é validação de segurança de tráfego."""
import math
import numpy as np
from .vehicle_motion import prepare_points,axle_geometry_prepared,PROFILES
from .vehicle_safety import body


def numerical_audit(points,allowed=None):
    try:
        p,d=prepare_points(points)
        if len(p)>200001 or d[-1]>100000:raise ValueError('Rota excede o orçamento numérico.')
        if allowed is not None:
            g=axle_geometry_prepared(p,d,'car',np.linspace(0,d[-1],min(200001,max(3,int(d[-1]/.5)+1))))
            bad=next((c for c,h in zip(g['center'],g['heading']) if not allowed.covers(body(c,h,4.5,1.8))),None)
            if bad is not None:
                return {'ok':False,'reasons':['canteiro_ou_limite_do_corredor'],'critical_center_xy':bad.tolist()}
        return {'ok':True,'reasons':[],'max_steering_deg':0.,'mode':'classico_ilustrativo'}
    except (ValueError,TypeError,OverflowError):return {'ok':False,'reasons':['geometria_invalida']}


class ClassicTraffic:
    def __init__(self,network,settings,vtype,duration=None,status=lambda *a:None):
        from .transport import Transport
        from .pedestrian_traffic import without_vehicles
        self.net=network;self.s=settings;self.vtype=vtype;self.info={};self.identities={};self.points={};self.last_count=0
        self.transport=Transport(settings,network)
        self.pedestrians=without_vehicles(settings,network,self.transport,float(duration or settings.duration_s))
    def indicators(self,t):return {}
    def vehicles_ex(self,t):
        speed=float(self.s.traffic_speed_kmh)/3.6
        if not math.isfinite(float(t)) or speed<=0:return
        count_total=0
        for i,path in enumerate(self.net.paths):
            length=float(path['length']);count=max(1,min(32,int(length/180*self.s.traffic_density)));period=length/speed+5
            if i not in self.points:self.points[i]=prepare_points(path['p'])
            for k in range(count):
                phase=float(t)+(k+.2)*period/count+i*1.37;cycle=math.floor(phase/period);position=(phase-cycle*period)*speed
                if position>=length:continue
                identity=(i,k,cycle);vt=self.vtype(path['kinds'],identity)
                g=axle_geometry_prepared(*self.points[i],vt,np.array([position]));center,heading=g['center'][0],g['heading'][0]
                L,W,*_=PROFILES.get(vt,PROFILES['car'])
                if not self.net.medians.is_empty and body(center,heading,L,W).intersects(self.net.medians):continue
                vid=self.identities.setdefault(identity,len(self.identities));self.info[vid]=(identity,vt)
                count_total+=1
                if count_total>512:return
                yield center,heading,vid,identity,int(np.searchsorted(path['d'],position))
        self.last_count=count_total
    def vehicle_body_state(self,t):
        return [{'id':vid,'center':p.tolist(),'heading':h.tolist(),'type':self.info[vid][1]} for p,h,vid,_,_ in self.vehicles_ex(t)][:20]
    def report(self):
        return {'model':'classico_ilustrativo','mode':'ensaio','checks':['canteiros','integridade_numerica'],'collision_free':None,'signals_respected':False,'density':self.s.traffic_density,'scope':'Somente apresentação. Sem validação de colisões, semáforos, pessoas, barreiras, interdições ou indicadores quantitativos de capacidade.'}
