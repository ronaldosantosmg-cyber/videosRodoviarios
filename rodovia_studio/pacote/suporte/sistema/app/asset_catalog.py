"""Catálogo local de materiais procedurais e padrões de nomes CAD."""
import hashlib
from functools import lru_cache
import numpy as np
import cv2

# chave, nome, classe, cor RGB, padrão e aliases CAD
ROWS=[
('concrete','Concreto de OAE','oae','#a1a5a5','grain',['*OAE*','*VIADUTO*','*PONTE*']),
('trees','Árvores e vegetação','vegetation','#4c8245','leaf',['*ARVOR*','*VEGETA*','*BOSQUE*']),
('rail','Ferrovia e dormentes','railway','#877765','rail',['*FERROVI*','*TRILHO*','*ESTRADA*FERRO*']),
('gas','Gasoduto — Gasmig','gas','#e8ac35','stripe',['*GASMIG*','*GASOD*','GAS','GAS_*','*-GAS*','*_GAS*','* GAS*']),
('electric','Rede elétrica','electric','#d9ad43','stripe',['*REDE*ELETR*','*LINHA*TRANSMISS*','*ENERGIA*','*CEMIG*']),
('pole','Poste','pole','#a3a3a0','grain',['*POSTE*']),
('building','Edificação — alvenaria','building','#ba9785','brick',['*EDIFICA*','*PREDIO*','*CONSTRUCAO*']),
('fiber','Fibra óptica','fiber','#a178c8','stripe',['*FIBRA*','*OPTICA*','*TELECOM*']),
('radar','Radar viário','radar','#527e9f','metal',['*RADAR*']),
('tower','Torre metálica','tower','#7e9099','metal',['*TORRE*']),
('erosion','Erosão e sulcos','erosion','#ad714c','rill',['*EROSAO*','*EROSÃO*','*VOÇORO*']),
('anchored_wall','Cortina atirantada','anchored_wall','#929993','anchors',['*CORTINA*ATIRANT*','*ATIRANT*']),
('gabion','Gabião','earthwork','#938e7b','stone',['*GABIAO*','*GABIÃO*']),
('earth','Terrapleno / offset','earthwork','#a4825a','soil',['*OFFSET*','*OFF SET*','*OFF_SET*','*OFF-SET*','*TERRAPLEN*']),
('water','Hidrologia e cursos d’água','water','#4f90b2','water',['*HIDROLOG*','*HIDROGRAF*']),
('asphalt','Asfalto novo','pavement','#50575c','grain',[]),
('asphalt_old','Asfalto existente','existing_pavement','#858887','grain',[]),
('soil_red','Solo vermelho','fill','#a55b3f','soil',[]),
('soil_sand','Solo arenoso','fill','#bca475','soil',[]),
('rock','Rocha aparente','cut','#8a8781','stone',[]),
('riprap','Enrocamento','fill','#83897f','stone',['*ENROC*']),
('shotcrete','Concreto projetado','anchored_wall','#999d98','grain',['*CONCRETO*PROJET*']),
('geomat','Biomanta e geomanta','erosion','#a89b72','grid',['*GEOMANTA*','*BIOMANTA*']),
('grass','Grama de canteiro','median','#6d8e50','leaf',[]),
('wood','Madeira','building','#967855','wood',[]),
('metal','Aço galvanizado','tower','#9ba9ad','metal',[]),
('roof_tile','Telha cerâmica','building','#ad6f53','roof',[]),
('roof_metal','Telha metálica','building','#a6adae','roof',[]),
('masonry','Muro de alvenaria','building','#a99a88','brick',['*ALVENARIA*']),
('gravel','Brita e lastro','railway','#8d8d83','stone',[]),
('drain','Canaleta de drenagem','water','#8e9997','grid',[]),
('fence','Cerca e alambrado','electric','#8e9992','grid',['*ALAMBRADO*'])]
CATALOG={key:{'id':key,'name':name,'role':role,'color':color,'pattern':pattern,'aliases':aliases} for key,name,role,color,pattern,aliases in ROWS}
ASSET_ROLES={'earthwork':'Terrapleno','vegetation':'Árvores / vegetação','railway':'Ferrovia','gas':'Gasoduto / Gasmig','electric':'Rede elétrica','pole':'Poste','building':'Edificação','fiber':'Fibra óptica','radar':'Radar','tower':'Torre','erosion':'Erosão','anchored_wall':'Cortina atirantada'}
DEFAULT={row['role']:key for key,row in reversed(list(CATALOG.items()))}
DEFAULT['earthwork']='earth'
DXF_RULES=[{'pattern':alias,'role':row['role'],'material':key} for key,row in CATALOG.items() for alias in row['aliases']]

def material_for(role,name='',overrides=None):
    if overrides and name in overrides and overrides[name] in CATALOG:return overrides[name]
    from .layer_profiles import matches
    return next((key for key,row in CATALOG.items() if row['role']==role and any(matches(a,name) for a in row['aliases'])),DEFAULT.get(role))

@lru_cache(maxsize=64)
def image(key,size=128):
    row=CATALOG[key];seed=int.from_bytes(hashlib.sha256(key.encode()).digest()[:4],'big');rng=np.random.default_rng(seed)
    y,x=np.indices((size,size));noise=rng.normal(0,9,(size,size));kind=row['pattern']
    if kind in ('stripe','grid'):noise-=((x%24<2)|((y%24<2)&(kind=='grid')))*45
    elif kind=='brick':noise-=((y%24<2)|((x+(y//24%2)*20)%40<2))*38
    elif kind=='stone':noise+=20*np.sin(x*.43+np.sin(y*.21))*np.cos(y*.31);noise-=((x//17+y//19)%3==0)*12
    elif kind=='rill':noise-=((x+5*np.sin(y*.08))%22<4)*45
    elif kind=='roof':noise+=18*np.sin(x*.45);noise-=(y%30<2)*25
    elif kind=='anchors':noise-=((x%32-16)**2+(y%32-16)**2<12)*65
    elif kind=='leaf':noise+=15*np.sin(x*.23)*np.cos(y*.31)
    elif kind=='water':noise+=12*np.sin(y*.35+np.cos(x*.09))
    elif kind=='wood':noise+=14*np.sin(x*.4+np.sin(y*.04))
    elif kind=='rail':noise-=((x%40<3)|(y%16<3))*50
    rgb=np.array([int(row['color'][i:i+2],16) for i in (1,3,5)])
    return np.clip(rgb+noise[:,:,None],0,255).astype(np.uint8)

def png(key):
    ok,data=cv2.imencode('.png',cv2.cvtColor(image(key),cv2.COLOR_RGB2BGR))
    if not ok:raise ValueError('Não foi possível gerar a textura.')
    return data.tobytes()
