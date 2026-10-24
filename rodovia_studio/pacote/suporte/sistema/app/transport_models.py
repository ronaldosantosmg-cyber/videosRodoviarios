"""Configuração persistente de ferrovia e controle semafórico ilustrativo."""
import math
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator

class XY(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False,extra='forbid')
    x:float=Field(ge=-1e9,le=1e9)
    y:float=Field(ge=-1e9,le=1e9)

class Railway(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False,extra='forbid')
    id:str=Field(min_length=1,max_length=80)
    name:str=Field(default='Ferrovia',min_length=1,max_length=100)
    points:list[XY]=Field(min_length=2,max_length=2000)
    tracks:Literal[1,2]=1
    direction:Literal['forward','reverse','both']='forward'
    model:Literal['carga','passageiros']='carga'
    enabled:bool=True
    level:int=Field(default=0,ge=-5,le=5)
    gauge_m:float=Field(default=1.6,ge=1,le=1.8)
    speed_kmh:float=Field(default=40,ge=10,le=100)
    interval_s:float=Field(default=120,ge=30,le=1800)
    start_s:float=Field(default=15,ge=0,le=1800)
    min_wagons:int=Field(default=5,ge=5,le=100,strict=True)
    max_wagons:int=Field(default=100,ge=5,le=100,strict=True)
    seed:int=Field(default=1729,ge=0,le=10**9)
    @model_validator(mode='after')
    def geometry(self):
        if self.min_wagons>self.max_wagons:raise ValueError('O mínimo de vagões não pode superar o máximo.')
        from shapely.geometry import LineString
        pts=[(p.x,p.y) for p in self.points];line=LineString(pts)
        if not 20<=line.length<=50000 or not line.is_simple:raise ValueError('Ferrovia deve ter de 20 m a 50 km e não pode cruzar a si própria.')
        for a,b in zip(pts,pts[1:]):
            if math.dist(a,b)<.05:raise ValueError('Remova pontos ferroviários repetidos ou muito próximos.')
        for a,b,c in zip(pts,pts[1:],pts[2:]):
            ab=math.dist(a,b);bc=math.dist(b,c);ac=math.dist(a,c);cross=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
            if ac<.05 or (cross>1e-8 and ab*bc*ac/(2*cross)<50):raise ValueError('Curva ferroviária muito fechada; use alinhamento com raio de pelo menos 50 m.')
        return self

class TrafficSignal(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False,extra='forbid')
    id:str=Field(min_length=1,max_length=80)
    name:str=Field(default='Semáforo',min_length=1,max_length=100)
    point:XY
    heading_deg:float=Field(default=0,ge=-360,le=360)
    heading_b_deg:float|None=Field(default=None,ge=-360,le=360)
    phases:Literal[2,3]=2
    # n = faixas da via transversal atravessadas pelo movimento liberado.
    lanes_a:int=Field(default=2,ge=1,le=8)
    lanes_b:int=Field(default=2,ge=1,le=8)
    lane_width_m:float=Field(default=3.5,ge=2.5,le=5)
    clearance_s:float=Field(default=12,ge=12,le=600)
    offset_s:float=Field(default=0,ge=0,le=3600)
    enabled:bool=True
    level:int=Field(default=0,ge=-5,le=5)

    @model_validator(mode='after')
    def axes(self):
        b=self.heading_deg+90 if self.heading_b_deg is None else self.heading_b_deg
        if abs(math.sin(math.radians(b-self.heading_deg)))<.15:raise ValueError('Eixos semafóricos quase paralelos: confira as direções dos movimentos A e B.')
        return self

class SignalLink(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False,extra='forbid')
    id:str=Field(min_length=1,max_length=80)
    source:str=Field(min_length=1,max_length=80)
    target:str=Field(min_length=1,max_length=80)
    speed_kmh:float=Field(default=40,ge=5,le=120)
    enabled:bool=True

def validate_network(settings):
    for rows in (settings.railways,settings.traffic_signals,settings.signal_links):
        ids=[x.id for x in rows]
        if len(ids)!=len(set(ids)):raise ValueError('Identificadores repetidos no controle de transportes.')
    for signal in settings.traffic_signals:
        b=signal.heading_deg+90 if signal.heading_b_deg is None else signal.heading_b_deg;skew=abs(math.sin(math.radians(b-signal.heading_deg)))
        minimum=(max(signal.lanes_a,signal.lanes_b)*signal.lane_width_m/skew+25)/max(.1,min(settings.traffic_speed_kmh/3.6,5.))+3
        signal.clearance_s=max(signal.clearance_s,round(minimum,3))
    signals={s.id:s for s in settings.traffic_signals};parents={}
    for link in settings.signal_links:
        if link.source not in signals or link.target not in signals:raise ValueError('Link semafórico aponta para semáforo inexistente.')
        if not link.enabled:continue
        if link.source==link.target or link.target in parents:raise ValueError('Cada semáforo pode receber somente um link e não pode ligar a si mesmo.')
        a,b=signals[link.source],signals[link.target]
        if (a.phases,a.lanes_a,a.lanes_b,a.clearance_s)!=(b.phases,b.lanes_a,b.lanes_b,b.clearance_s):raise ValueError('Onda verde exige mesmos tempos, limpeza de segurança e quantidades de faixas nos semáforos ligados.')
        parents[link.target]=link.source
    for node in parents:
        seen=set();n=node
        while n in parents:
            if n in seen:raise ValueError('Links de onda verde não podem formar ciclos.')
            seen.add(n);n=parents[n]
    return settings
