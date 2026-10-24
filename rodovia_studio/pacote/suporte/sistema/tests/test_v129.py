"""1.29: opções só válidas por tipo (erro do modo da interdição), nomes válidos, envio de DXF/KMZ/KML com nome e
remoção, texturas de taludes/canteiro por região, aparência da sinalização (cores, desgaste) e da água."""
import io,json,time,zipfile
import numpy as np,cv2,pytest
from fastapi.testclient import TestClient
from test_workflow import settings
from test_v110 import junction
from app.models import Settings

def S(**kw):return Settings(**{**settings().model_dump(),'duration_s':10,'layers':{'axis':['EIXO'],'pavement':['PAVIMENTO']},**kw})

def test_schema_enums_per_type():
    from app.server import app
    r=TestClient(app).get('/api/esquema').json()
    assert r['lane_blocks']['mode']['values']==['partial','total'] and r['crossing_zones']['mode']['values']==['allow','deny'] and r['accesses']['mode']['values']==['both','in','out']
    assert set(r['texture_areas']['surface']['values'])>={'talude_corte','talude_aterro','canteiro'}

def test_names_cleaned():
    s=Settings.model_validate({'name':'   ','highlights':[{'name':' <b> ','point':{'x':0,'y':0}},{'name':'...','point':{'x':0,'y':0}},{'name':'Poste / rede 3','point':{'x':0,'y':0}}]})
    assert s.name=='Novo trecho' and [h.name for h in s.highlights]==['b','Sem nome','Poste / rede 3']

def test_upload_dxf_kmz_kml_and_remove(junction,tmp_path):
    from app.server import app
    c=TestClient(app);pid=c.post('/api/projects',json=S().model_dump()).json()['id']
    r=c.post(f'/api/projects/{pid}/files',files={'file':('Projeto TH57 rev3.dxf',(junction/'input.dxf').read_bytes())}).json()
    assert r['files']['dxf']['name']=='Projeto TH57 rev3.dxf' and r['files']['kmz'] is None
    kml=b'<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"><Placemark><name>Eixo</name><LineString><coordinates>-45.0,-19.9 -45.001,-19.9</coordinates></LineString></Placemark></kml>'
    r=c.post(f'/api/projects/{pid}/files',files={'file':('eixo.kml',kml)}).json();assert r['files']['kmz']['name']=='eixo.kml' and r['files']['dxf'] is not None
    from app import store
    assert zipfile.ZipFile(store.directory(pid)/'input.kmz').read('doc.kml')==kml
    p=c.get(f'/api/projects/{pid}').json();assert p['files']=={'dxf':True,'kmz':True} and p['files_info']['dxf']['name']=='Projeto TH57 rev3.dxf'
    assert c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',b'PK\x03\x04 nao sou dxf')}).status_code==422
    assert 'DWG' in c.post(f'/api/projects/{pid}/files',files={'file':('x.dwg',b'AC1032')}).json()['detail']
    r=c.delete(f'/api/projects/{pid}/files/kmz').json();assert r['files']['kmz'] is None and not (store.directory(pid)/'input.kmz').exists()
    assert c.delete(f'/api/projects/{pid}/files/kmz').status_code==404

def test_texture_area_on_slope_and_median(junction):
    from app.render import Scene,texture_area_codes
    from app.visual import texture_lut
    area={'id':'t','name':'Corte km 0+100','surface':'pista_nova','points':[{'x':500050,'y':7799991},{'x':500150,'y':7799991},{'x':500150,'y':7800009},{'x':500050,'y':7800009}],'texture':{'grao':3,'brilho':-.25}}
    a=Scene(junction,S(traffic=False));b=Scene(junction,S(traffic=False,texture_areas=[area]))
    codes=np.unique(b.surface);assert 32 in codes and 32 not in np.unique(a.surface)
    inside=b.surface==32;assert inside.sum()>0 and (a.surface[inside]==1).all()       # só onde já era pista nova
    view=((500100,7800000),60);assert b.frame(5,view=view)[0].mean()<a.frame(5,view=view)[0].mean()-3
    # Superfície diferente (talude) dentro da região: nada muda (o pavimento continua igual).
    c=Scene(junction,S(traffic=False,texture_areas=[{**area,'surface':'talude_corte'}]));assert 32 not in np.unique(c.surface)
    assert Scene(junction,S(traffic=False,texture_areas=[{**area,'texture':None}])).texture_areas()==[]
    # Depois das áreas de pista com textura própria (32..), as regiões recebem os códigos seguintes.
    pav={'id':'p1','name':'P','kind':'existing_pavement','points':area['points'],'texture':{'grao':2}}
    d=Scene(junction,S(traffic=False,pavement_areas=[pav],texture_areas=[{**area,'surface':'pista_existente'}]));assert [x[0] for x in d.texture_areas()]==[33]
    L=texture_lut(None,[(40,6,{'grao':2,'tom':1,'remendos':1,'fissuras':1,'brilho':.1})]);assert L['bright'][40]==pytest.approx(.1)

def test_signage_paint_colors_and_wear(junction):
    from app.render import Scene
    view=((500200,7800000),40)
    a=Scene(junction,S(traffic=False));fa=a.frame(5,view=view)[0]
    b=Scene(junction,S(traffic=False,signage_paint={'white':'#ff0000'}));fb=b.frame(5,view=view)[0]
    red=(fb[:,:,0]>200)&(fb[:,:,1]<80)&(fb[:,:,2]<80);assert red.sum()>200 and ((fa[:,:,0]>200)&(fa[:,:,1]<80)&(fa[:,:,2]<80)).sum()<red.sum()/10
    c=Scene(junction,S(traffic=False,signage_paint={'wear':1}));fc=c.frame(5,view=view)[0]
    bright=lambda f:(f.min(2)>200).sum();assert bright(fc)<bright(fa)*.7
    d=Scene(junction,S(traffic=False,signage_paint={'opacity':.2}));assert bright(d.frame(5,view=view)[0])<bright(fa)*.3
    assert np.array_equal(Scene(junction,S(traffic=False,signage_paint={})).frame(5,view=view)[0],fa)   # neutro = igual
