import math
from dataclasses import dataclass,field,replace
from enum import Enum
from typing import Optional
from .params import VehicleParams


class Phase(Enum):
    IDLE='idle';PREPARING='preparing';CHANGING='changing'


def smoothstep(x):
    x=0. if x<0 else 1. if x>1 else x
    return x*x*(3-2*x)


def smoothstep_rate(x):
    x=0. if x<0 else 1. if x>1 else x
    return 6*x*(1-x)


@dataclass
class LaneChange:
    side:int                  # +1 esquerda, -1 direita
    to_lane:str
    from_lane:str
    reason:str                # 'mobil' | 'closure' | 'return'
    mandatory:bool=False
    prep:float=0.             # tempo de seta já cumprido (s)
    wait:float=0.
    t:float=0.                # progresso da transição (s)
    T:float=4.                # duração (s)
    off0:float=0.             # deslocamento lateral inicial em relação ao eixo de destino (m)
    s_delta:float=0.          # s_destino - s_origem na troca (posição do "fantasma" na faixa de origem)


@dataclass
class Overtake:
    home_lane:str
    passed_id:str
    side:int                  # lado da saída; o retorno usa -side


@dataclass
class Vehicle:
    id:str
    lane_id:str
    s:float
    v:float=0.
    params:VehicleParams=field(default_factory=VehicleParams)
    route:list=field(default_factory=list)      # sequência opcional de faixas a seguir
    a:float=0.
    lat:float=0.              # deslocamento lateral em relação ao eixo da faixa (m, + esquerda)
    indicator:str='off'       # 'off' | 'left' | 'right'
    phase:Phase=Phase.IDLE
    lc:Optional[LaneChange]=None
    overtake:Optional[Overtake]=None
    cooldown:float=0.
    next_decision:float=0.
    x:float=0.;y:float=0.;heading:float=0.
    alive:bool=True
    frozen:bool=False
    leader_id:Optional[str]=None

    @property
    def length(self):return self.params.length

    @property
    def width(self):return self.params.width

    def save(self):
        return (self.lane_id,self.s,self.v,self.a,self.lat,self.indicator,self.phase,replace(self.lc) if self.lc else None,
                self.overtake,self.cooldown,self.x,self.y,self.heading,self.alive)

    def restore(self,st):
        (self.lane_id,self.s,self.v,self.a,self.lat,self.indicator,self.phase,self.lc,self.overtake,self.cooldown,self.x,self.y,self.heading,self.alive)=st

    def next_lane(self,lane):
        if self.route and lane.id in self.route:
            i=self.route.index(lane.id)
            return self.route[i+1] if i+1<len(self.route) else None
        return lane.successors[0] if lane.successors else None
