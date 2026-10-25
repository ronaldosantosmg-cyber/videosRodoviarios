"""Objetos derivados de imagem, revisáveis e separados da geometria de circulação."""
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator
from .asset_catalog import CATALOG

ImageRole=Literal['building','water','railway','oae','vegetation','cut','electric','pavement','paint','unclassified']
LABELS={'building':'Edificações','water':'Hidrologia','railway':'Ferrovias','oae':'OAE','vegetation':'Vegetação densa','cut':'Taludes','electric':'Linhas de transmissão','pavement':'Rodovias','paint':'Faixas de sinalização','unclassified':'A classificar'}
DEFAULT_MATERIAL={'building':'roof_tile','water':'water','railway':'rail','oae':'concrete','vegetation':'trees','cut':'earth','electric':'electric','pavement':'asphalt_old','paint':'concrete','unclassified':'earth'}
class ImagePoint(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    x:float=Field(ge=-1e9,le=1e9)
    y:float=Field(ge=-1e9,le=1e9)
class ImageGroup(BaseModel):
    visible:bool=True
    render:bool=True
class ImageFeature(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    id:str=Field(min_length=1,max_length=80)
    name:str=Field(default='Objeto da imagem',min_length=1,max_length=100)
    role:ImageRole='unclassified'
    points:list[ImagePoint]=Field(min_length=3,max_length=2000)
    holes:list[list[ImagePoint]]=Field(default_factory=list,max_length=100)
    enabled:bool=True
    visible:bool=True
    render:bool=True
    reviewed:bool=False
    height_m:float=Field(default=0,ge=0,le=100)
    material:str='earth'
    wall_material:str='masonry'
    paint_color:Literal['white','yellow']='white'
    similarity_group:int=Field(default=0,ge=0,le=100)
    confidence:float=Field(default=0,ge=0,le=1)
    evidence:str=Field(default='',max_length=240)
    source_hash:str=Field(default='',pattern=r'^([a-f0-9]{64})?$')
    @model_validator(mode='after')
    def geometry(self):
        from shapely.geometry import Polygon
        if self.material not in CATALOG or self.wall_material not in CATALOG:raise ValueError('Material de imagem desconhecido.')
        if any(len(h)<3 or len(h)>2000 for h in self.holes):raise ValueError('Vazio do polígono inválido.')
        p=Polygon([(v.x,v.y) for v in self.points],holes=[[(v.x,v.y) for v in h] for h in self.holes])
        if not p.is_valid or p.area<.01:raise ValueError('Contorno inválido ou de área nula. Ajuste os vértices.')
        return self

class ImageSample(ImagePoint):
    role:ImageRole
class ImageRequest(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    bounds:list[float]=Field(min_length=4,max_length=4)
    crs:str=Field(min_length=1,max_length=120)
    source:Literal['local','web']='local'
    pixels:Literal[512,1024,1536,2048]=1024
    clusters:int=Field(default=12,ge=2,le=32)
    min_area_m2:float=Field(default=4,ge=.1,le=10000)
    samples:list[ImageSample]=Field(default_factory=list,max_length=100)
    @model_validator(mode='after')
    def box(self):
        x0,y0,x1,y1=self.bounds
        if not(0<x1-x0<=10000 and 0<y1-y0<=10000):raise ValueError('Selecione uma área de até 10 km de largura/altura.')
        span=max(x1-x0,y1-y0);cx=(x0+x1)/2;cy=(y0+y1)/2;self.bounds=[cx-span/2,cy-span/2,cx+span/2,cy+span/2]
        return self
class ImageProvenance(BaseModel):
    capture_hash:str=Field(default='',pattern=r'^([a-f0-9]{64})?$')
    signature:str=Field(pattern=r'^[a-f0-9]{64}$')
    request:ImageRequest
