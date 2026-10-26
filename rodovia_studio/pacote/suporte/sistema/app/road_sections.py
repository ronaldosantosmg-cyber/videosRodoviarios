"""Seções explícitas por lado do eixo, sem tráfego em acostamentos ou faixas de segurança."""
import numpy as np
from pydantic import BaseModel,ConfigDict,Field,model_validator
from typing import Literal

class SectionBand(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    kind:Literal['pista','acostamento','seguranca']='pista'
    width_m:float=Field(default=3.5,ge=.2,le=10)
    traffic_enabled:bool=True
    @model_validator(mode='after')
    def driving_width(self):
        if self.kind=='pista' and self.width_m<2.5:raise ValueError('Faixa de pista precisa de pelo menos 2,5 m.')
        return self

class CrossSection(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    id:str=Field(min_length=1,max_length=80)
    name:str=Field(default='Seção',min_length=1,max_length=80)
    start_m:float=Field(ge=0)
    end_m:float=Field(gt=0)
    type:Literal['simples','dupla']='simples'
    median_m:float=Field(default=0,ge=0,le=60)
    left:list[SectionBand]=Field(min_length=1,max_length=8)
    right:list[SectionBand]=Field(min_length=1,max_length=8)
    @model_validator(mode='after')
    def valid(self):
        if self.end_m<=self.start_m:raise ValueError('Fim da seção deve ser posterior ao início.')
        if self.type=='simples' and self.median_m!=0:raise ValueError('Pista simples não tem canteiro central.')
        if not all(any(b.kind=='pista' for b in side) for side in (self.left,self.right)):raise ValueError('Cada lado deve conter uma faixa de pista.')
        return self

def section_offsets(route,stations,fallback):
    out=list(fallback)
    for section in route.cross_sections:
        offsets={}
        for sign,side,direction in [(1,section.right,'f'),(-1,section.left,'r')]:
            offset=section.median_m/2 if section.type=='dupla' else 0.;lane=0
            for band in side:
                if band.kind=='pista':
                    if band.traffic_enabled:offsets[(direction,lane)]=sign*(offset+band.width_m/2)
                    lane+=1
                offset+=band.width_m
        for i in np.flatnonzero((stations>=section.start_m)&(stations<section.end_m+1e-8)):out[i]=dict(offsets)
    return out

def continuity_report(route):
    """Lacunas declaradas, sem preencher intervalos ou reativar faixas."""
    if not route.enabled or not route.sections_only:return None
    p=np.array([[p.x,p.y] for p in route.points],float)
    length=float(np.linalg.norm(np.diff(p,axis=0),axis=1).sum())
    gaps=[];cursor=0.
    for section in sorted(route.cross_sections,key=lambda s:s.start_m):
        start,end=max(0.,section.start_m),min(length,section.end_m)
        if start>=length or end<=start:continue
        if start>cursor+1e-6:gaps.append({'start_m':cursor,'end_m':start})
        cursor=max(cursor,end)
    if cursor<length-1e-6:gaps.append({'start_m':cursor,'end_m':length})
    return {'route_id':route.id,'name':route.name,'length_m':length,'gaps':gaps,'scope':'Intervalos sem seção cadastrada. Não são preenchidos automaticamente.'}

class AlternatingZone(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    id:str=Field(min_length=1,max_length=80)
    name:str=Field(default='Pare e siga',min_length=1,max_length=80)
    route_id:str=Field(min_length=1,max_length=100)
    start_m:float=Field(ge=0)
    end_m:float=Field(gt=0)
    side:Literal['right','left']='right'
    release_s:float=Field(default=10,ge=5,le=120)
    enabled:bool=True
    block_id:str=Field(default='',max_length=100)
    @model_validator(mode='after')
    def order(self):
        if self.end_m<=self.start_m:raise ValueError('Pare e siga: fim deve ser posterior ao início.')
        return self

def alternating_offsets(route,settings,stations,offsets):
    """Ambos sentidos usam a faixa operacional, com transições dentro da pista validada."""
    for zone in getattr(settings,'alternating_zones',[]):
        if not zone.enabled or zone.route_id!=route.id:continue
        taper=route.taper_m
        alpha=np.minimum(np.clip((stations-(zone.start_m-taper))/taper,0,1),np.clip((zone.end_m+taper-stations)/taper,0,1));alpha=alpha*alpha*(3-2*alpha)
        shared=(1 if zone.side=='right' else -1)*route.lane_width_m/2
        for i,a in enumerate(alpha):
            if a<=0:continue
            for key in offsets[i]:offsets[i][key]=(1-a)*offsets[i][key]+a*shared
    return offsets
