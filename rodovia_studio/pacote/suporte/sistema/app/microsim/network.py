"""Interfaces de entrada: faixas (eixos + limites das layers), sinais, linhas de retenção e interdições."""
import math,re
from dataclasses import dataclass,field
from enum import Enum
from typing import Optional
import numpy as np


class BoundaryKind(Enum):
    OPEN='open'              # tracejada: troca permitida
    SOLID_LINE='solid'       # linha contínua
    MEDIAN='median'          # canteiro central
    BARRIER='barrier'        # barreira física rígida
    EDGE='edge'              # bordo externo


@dataclass
class LayerRules:
    """Classifica o nome de uma layer do DXF num tipo de limite. A ordem importa: o mais restritivo vence."""
    patterns:list=field(default_factory=lambda:[
        (BoundaryKind.BARRIER,r'barreira|new.?jersey|defensa|guard.?rail|muro'),
        (BoundaryKind.MEDIAN,r'canteiro|median|separador'),
        (BoundaryKind.EDGE,r'bordo|borda|edge|acostament'),
        (BoundaryKind.SOLID_LINE,r'continu|solid|dupla|proibid'),
        (BoundaryKind.OPEN,r'tracej|dashed|seccion|pontilh')])

    def classify(self,layer_name:str,default=BoundaryKind.SOLID_LINE):
        for kind,rx in self.patterns:
            if re.search(rx,layer_name or '',re.I):return kind
        return default      # layer desconhecida = não cruzável (falha para o lado seguro)


@dataclass
class Lane:
    """Faixa = eixo (polilinha em metros no CRS do projeto) + vizinhas e tipo dos limites laterais.
    left/right são relativos ao sentido de marcha."""
    id:str
    center:np.ndarray
    width:float=3.5
    v0:float=16.7
    left:Optional[str]=None
    right:Optional[str]=None
    left_boundary:BoundaryKind=BoundaryKind.EDGE
    right_boundary:BoundaryKind=BoundaryKind.EDGE
    successors:list=field(default_factory=list)
    dead_end_stops:bool=False

    def __post_init__(self):
        c=np.asarray(self.center,float)
        if c.ndim!=2 or c.shape[1]!=2 or len(c)<2:raise ValueError(f'Faixa {self.id}: eixo inválido.')
        keep=np.r_[True,np.linalg.norm(np.diff(c,axis=0),axis=1)>1e-6];c=c[keep]
        if len(c)<2:raise ValueError(f'Faixa {self.id}: eixo sem comprimento.')
        self.center=c;d=np.diff(c,axis=0);self._seg=np.linalg.norm(d,axis=1)
        self._cum=np.r_[0.,np.cumsum(self._seg)];self.length=float(self._cum[-1]);self._head=np.arctan2(d[:,1],d[:,0])

    def poses(self,s):
        """Posição e rumo (rad) do eixo nas abscissas `s` (vetorizado; fora do eixo prolonga o primeiro/último trecho)."""
        s=np.asarray(s,float);i=np.clip(np.searchsorted(self._cum,s,side='right')-1,0,len(self._seg)-1)
        t=s-self._cum[i];h=self._head[i];p=self.center[i]+np.stack([np.cos(h)*t,np.sin(h)*t],axis=-1)
        return p,h

    def project(self,xy):
        """Abscissa do ponto do eixo mais próximo de `xy`."""
        p=np.asarray(xy,float);a=self.center[:-1];d=self.center[1:]-a
        t=np.clip(np.einsum('ij,ij->i',p-a,d)/np.maximum(self._seg**2,1e-12),0,1)
        q=a+d*t[:,None];k=int(np.argmin(np.einsum('ij,ij->i',q-p,q-p)));return float(self._cum[k]+t[k]*self._seg[k])

    def neighbor(self,side):return self.left if side>0 else self.right

    def boundary(self,side):return self.left_boundary if side>0 else self.right_boundary


@dataclass
class TrafficSignal:
    id:str
    phases:list=field(default_factory=lambda:[('green',30.),('yellow',3.),('red',27.)])
    offset:float=0.
    manual:Optional[str]=None      # força um estado vindo do sistema ('green'|'yellow'|'red')

    def state(self,t):
        if self.manual:return self.manual
        cyc=sum(d for _,d in self.phases);x=(t+self.offset)%cyc
        for name,d in self.phases:
            if x<d:return name
            x-=d
        return self.phases[-1][0]


@dataclass
class StopLine:
    """Linha de retenção ligada a um sinal (semáforo ou faixa de pedestres). Fechada → líder virtual parado."""
    lane_id:str
    s:float
    signal_id:Optional[str]=None
    kind:str='signal'              # 'signal' | 'crosswalk'


@dataclass
class LaneClosure:
    lane_id:str
    s_start:float
    s_end:float
    active:bool=True


class RoadNetwork:
    def __init__(self):
        self.lanes={};self.signals={};self.stop_lines=[];self.closures=[]

    def add_lane(self,lane):
        if lane.id in self.lanes:raise ValueError('Faixa duplicada: '+lane.id)
        self.lanes[lane.id]=lane;return lane

    def add_signal(self,sig):self.signals[sig.id]=sig;return sig
    def add_stop_line(self,sl):self.stop_lines.append(sl);return sl
    def add_closure(self,c):self.closures.append(c);return c

    def predecessors(self):
        out={k:[] for k in self.lanes}
        for k,l in self.lanes.items():
            for n in l.successors:out.get(n,[]).append(k)
        return out

    def validate(self):
        """Vizinhas recíprocas e tipos de limite coerentes; devolve a lista de problemas (vazia = ok)."""
        err=[]
        for k,l in self.lanes.items():
            for side,nid in((1,l.left),(-1,l.right)):
                if nid is None:continue
                o=self.lanes.get(nid)
                if o is None:err.append(f'{k}: vizinha {nid} não existe');continue
                back=o.right if side>0 else o.left
                if back!=k:err.append(f'{k}↔{nid}: vizinhança não recíproca')
                elif o.boundary(-side)!=l.boundary(side):err.append(f'{k}↔{nid}: limite diferente nos dois lados')
        for sl in self.stop_lines:
            if sl.lane_id not in self.lanes:err.append(f'linha de retenção em faixa inexistente: {sl.lane_id}')
            if sl.signal_id and sl.signal_id not in self.signals:err.append(f'sinal inexistente: {sl.signal_id}')
        return err


def parallel_lanes(prefix,axis,n,width=3.5,v0=16.7,between=None,outer_left=BoundaryKind.EDGE,outer_right=BoundaryKind.EDGE):
    """Cria `n` faixas paralelas a partir do eixo (lane 0 = direita; sentido do eixo). `between[i]` = limite entre a
    faixa i e i+1 (padrão: OPEN). Usa os limites das layers como `outer_*` e `between`."""
    from shapely.geometry import LineString
    between=list(between) if between is not None else [BoundaryKind.OPEN]*(n-1)
    if len(between)!=n-1:raise ValueError('between precisa ter n-1 itens.')
    base=LineString(np.asarray(axis,float));lanes=[]
    for i in range(n):
        off=(i-(n-1)/2)*width
        g=base if abs(off)<1e-9 else base.offset_curve(off)
        if g.geom_type=='MultiLineString':g=max(g.geoms,key=lambda x:x.length)
        pts=np.asarray(g.coords)
        if np.linalg.norm(pts[0]-np.asarray(axis[0]))>np.linalg.norm(pts[-1]-np.asarray(axis[0])):pts=pts[::-1]
        lanes.append(Lane(f'{prefix}{i}',pts,width,v0,left=f'{prefix}{i+1}' if i<n-1 else None,right=f'{prefix}{i-1}' if i>0 else None,
                          left_boundary=between[i] if i<n-1 else outer_left,right_boundary=between[i-1] if i>0 else outer_right))
    return lanes
