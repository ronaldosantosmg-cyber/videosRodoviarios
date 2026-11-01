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
    left:list[SectionBand]=Field(default_factory=list,max_length=8)
    right:list[SectionBand]=Field(default_factory=list,max_length=8)
    # 2.19: sentido de cada lado. Padrão = dois sentidos (direita segue o eixo, esquerda contrária).
    # 'mesmo' nos dois lados = eixo no MEIO de uma pista de um só sentido (sem canteiro); eixo no bordo = só um lado com pistas.
    left_dir:Literal['contrario','mesmo']='contrario'
    right_dir:Literal['mesmo','contrario']='mesmo'
    # 2.43: esta seção autoriza circulação onde NÃO há hachura de pavimento (ex.: túnel existente sem hachura)? None = vale o da rota (section_surface).
    authorize_surface:bool|None=None
    @model_validator(mode='after')
    def valid(self):
        if self.end_m<=self.start_m:raise ValueError('Fim da seção deve ser posterior ao início.')
        if self.type=='simples' and self.median_m!=0:raise ValueError('Pista simples não tem canteiro central.')
        if not any(b.kind=='pista' for b in (*self.left,*self.right)):raise ValueError('A seção precisa de pelo menos uma faixa de pista.')
        dirs=lane_directions(self)
        if len(dirs)==2 and not (any(b.kind=='pista' for b in self.left) and any(b.kind=='pista' for b in self.right)):raise ValueError('Dois sentidos exigem pista nos dois lados do eixo.')
        if self.median_m!=0 and not (any(b.kind=='pista' for b in self.left) and any(b.kind=='pista' for b in self.right)):raise ValueError('Canteiro exige pista dos dois lados do eixo (duas pistas separadas); com o eixo no bordo ou no meio de uma só pista o canteiro é 0.')
        return self

def side_direction(section,side):
    """'f' (sentido do eixo) ou 'r' (contrário) das faixas de um lado ('left'|'right')."""
    if side=='right':return 'f' if section.right_dir=='mesmo' else 'r'
    return 'r' if section.left_dir=='contrario' else 'f'

def lane_directions(section):
    return {side_direction(section,s) for s,bands in (('left',section.left),('right',section.right)) if any(b.kind=='pista' for b in bands)}

def band_layout(section):
    """Faixas de pista: {(sentido,índice): (deslocamento do centro, largura, circula)}.
    Índice 0 = faixa mais à ESQUERDA em relação ao sentido de marcha (interna na pista dupla); cresce para a direita."""
    rows=[]
    for sign,side,name in ((1,section.right,'right'),(-1,section.left,'left')):
        offset=section.median_m/2 if section.type=='dupla' else 0.;d=side_direction(section,name)
        for band in side:
            if band.kind=='pista':rows.append((d,sign*(offset+band.width_m/2),band.width_m,band.traffic_enabled))
            offset+=band.width_m
    out={}
    for d in ('f','r'):
        mine=sorted((r for r in rows if r[0]==d),key=lambda r:r[1],reverse=(d=='r'))
        for k,(_,off,w,on) in enumerate(mine):out[(d,k)]=(off,w,on)
    return out

def section_lane_widths(section):
    return {k:v[1] for k,v in band_layout(section).items()}

def section_offsets(route,stations,fallback):
    out=list(fallback)
    for section in route.cross_sections:
        offsets={k:v[0] for k,v in band_layout(section).items() if v[2]}
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
    release_s:float=Field(default=10,ge=5,le=120)   # com adaptive=True é o verde MÁXIMO
    adaptive:bool=True                                # 1.42.43: pare e siga inteligente (verde mínimo, prolongamento por fila, gap-out)
    min_release_s:float=Field(default=5,ge=3,le=120)
    margin_s:float=Field(default=2,ge=0,le=30)        # vermelho geral após o último veículo sair
    enabled:bool=True
    block_id:str=Field(default='',max_length=100)
    @model_validator(mode='after')
    def order(self):
        if self.end_m<=self.start_m:raise ValueError('Pare e siga: fim deve ser posterior ao início.')
        if self.min_release_s>self.release_s:self.min_release_s=self.release_s
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


def resolver_sobreposicao(sections,minimo=1.0):
    """A seção MAIS RECENTE (posterior na lista) prevalece: as anteriores são recortadas/divididas em vez de dar erro.
    Permite cadastrar, por exemplo, um trecho de pista simples dentro de um eixo que já tem seção duplicada."""
    import uuid
    atual=[]
    for novo in sections:
        saida=[]
        for x in atual:
            if x.end_m<=novo.start_m+1e-6 or x.start_m>=novo.end_m-1e-6:saida.append(x);continue
            if novo.start_m-x.start_m>=minimo:saida.append(x.model_copy(update={'end_m':novo.start_m}))
            if x.end_m-novo.end_m>=minimo:saida.append(x.model_copy(update={'id':uuid.uuid4().hex[:12],'start_m':novo.end_m}))
        saida.append(novo);atual=saida
    return sorted(atual,key=lambda s:s.start_m)


def authorized_intervals(route):
    """Intervalos (m) do alinhamento onde a seção AUTORIZA circulação fora da hachura de pavimento. Sem autorização → lista vazia (vale só a hachura DXF)."""
    out=[]
    for s in route.cross_sections:
        ok=s.authorize_surface if getattr(s,'authorize_surface',None) is not None else bool(getattr(route,'section_surface',False))
        if ok:out.append((float(s.start_m),float(s.end_m)))
    return out
