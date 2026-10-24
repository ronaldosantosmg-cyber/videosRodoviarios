"""Estaqueamento por distância percorrida ao longo do eixo.

km(P) = km inicial + sentido × fator × (s(P) − s(início)), onde s é a distância ao longo do eixo
até a projeção de P. Modos:
- automático: início no começo geométrico do eixo (já orientado pela inversão), sentido do eixo;
- manual: início clicado; o sentido vem da seta arrastada no clique ou da posição do ponto final.
Com ponto final e “ajuste proporcional”, o fator distribui a diferença entre o km final informado
e a distância medida (ex.: marcos oficiais). Sem ajuste, fator = 1 (distância pura).
"""
import numpy as np
import shapely
from shapely.geometry import LineString,Point

def _p(v):return None if v is None else ((v.x,v.y) if hasattr(v,'x') else (v['x'],v['y']) if isinstance(v,dict) else tuple(v))

class Stationing:
    def __init__(self,axis,km_start_m,start=None,end=None,direction=1,km_end_m=None,calibrate=False):
        self.axis=np.asarray(axis,float);self.line=LineString(self.axis);self.length=self.line.length;self.km_start=float(km_start_m)
        start=_p(start);end=_p(end);self.defined=start is not None
        self.s0=float(self.line.project(Point(*start))) if start is not None else 0.
        self.end_s=float(self.line.project(Point(*end))) if end is not None else None
        if self.end_s is not None and abs(self.end_s-self.s0)>1e-6:self.direction=1 if self.end_s>self.s0 else -1
        else:self.direction=1 if direction>=0 else -1
        self.scale=1.
        if calibrate and self.end_s is not None and km_end_m is not None and abs(self.end_s-self.s0)>1:
            self.scale=float((km_end_m-self.km_start)/(self.direction*(self.end_s-self.s0)))
            if self.scale<=0:raise ValueError('Km final menor que o inicial no sentido escolhido: confira o início, o fim e os km.')
        self.start_point=np.array(self.line.interpolate(self.s0).coords[0])
        self.end_point=np.array(self.line.interpolate(self.end_s).coords[0]) if self.end_s is not None else None
    @classmethod
    def from_settings(cls,axis,s):
        c=s.chainage;manual=c.mode=='manual'
        return cls(axis,s.km_start_m,c.start if manual else None,c.end if manual else None,getattr(c,'direction',1) if manual else 1,s.km_end_m,getattr(c,'calibrate',False))
    def geo(self,points):
        p=np.atleast_2d(np.asarray(points,float))
        return np.asarray(shapely.line_locate_point(self.line,shapely.points(p[:,0],p[:,1])),float)
    def distance(self,points):
        """Distância de estaqueamento (com sentido e fator) a partir do início."""
        return self.direction*self.scale*(self.geo(points)-self.s0)
    def km(self,points):
        v=self.km_start+self.distance(points)
        return float(v[0]) if np.ndim(points)==1 else v
    def offset(self,points):
        p=np.atleast_2d(np.asarray(points,float));return np.asarray(shapely.distance(self.line,shapely.points(p[:,0],p[:,1])),float)
    def chain(self,km_m):
        """Distância geométrica desde o início da polilinha correspondente a um km."""
        return float(np.clip(self.s0+self.direction*(float(km_m)-self.km_start)/self.scale,0,self.length))
    def point(self,km_m):return np.array(self.line.interpolate(self.chain(km_m)).coords[0])
    def km_range(self):
        a=self.km([*self.axis[0]]);b=self.km([*self.axis[-1]]);return min(a,b),max(a,b)
    def km_end_geometric(self):
        """Km do ponto final (marcado) ou da ponta do eixo no sentido do estaqueamento."""
        if self.end_s is not None:return self.km_start+self.direction*self.scale*(self.end_s-self.s0)
        tip=self.length if self.direction>0 else 0.
        return self.km_start+self.direction*self.scale*(tip-self.s0)
    def substring(self,a_km,b_km):
        from shapely.ops import substring
        a=self.chain(a_km);b=self.chain(b_km)
        return substring(self.line,min(a,b),max(a,b))
    def info(self):
        return {'defined':self.defined,'km_start_m':self.km_start,'s0_m':self.s0,'end_s_m':self.end_s,'direction':self.direction,'scale':self.scale,
                'start_point':self.start_point.tolist(),'end_point':None if self.end_point is None else self.end_point.tolist(),'km_end_geometric_m':self.km_end_geometric(),'axis_length_m':self.length}

def fmt(m):
    if m is None:return ''
    neg=m<0;v=int(round(abs(m)));return ('-' if neg else '')+f'{v//1000}+{v%1000:03d}'
