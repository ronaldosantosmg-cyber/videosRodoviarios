"""1.37: abrir DWG (conversão pelo ODA File Converter), vegetação, pedestres e frota variada; esquema 29 (projetos
anteriores com a frota clássica e sem pedestres: vídeo idêntico)."""
import os,sys,stat,textwrap
import numpy as np,pytest
from fastapi.testclient import TestClient
from test_v116 import S  # noqa: F401
from test_v110 import junction  # noqa: F401

def conversor_falso(tmp_path,dxf):
    """Imita o ODAFileConverter: <entrada> <saída> <versão> DXF ... -> grava saída/desenho.dxf."""
    p=tmp_path/'ODAFileConverter';p.write_text(textwrap.dedent(f'''\
        #!{sys.executable}
        import sys,shutil,pathlib
        ent,sai=sys.argv[1],sys.argv[2]
        assert sys.argv[4]=='DXF' and list(pathlib.Path(ent).glob('*.dwg'))
        shutil.copy({str(dxf)!r},pathlib.Path(sai)/'desenho.dxf')
        '''));p.chmod(p.stat().st_mode|stat.S_IEXEC);return p

def test_dwg_conversao(junction,tmp_path,monkeypatch):
    from app import dwg
    monkeypatch.delenv('RODOVIA_ODA',raising=False);monkeypatch.setattr(dwg,'conversor',lambda:None)
    with pytest.raises(LookupError):dwg.converter(b'AC1032'+b'\0'*100)
    with pytest.raises(ValueError):dwg.converter(b'nao e dwg')
    monkeypatch.undo()
    monkeypatch.setenv('RODOVIA_ODA',str(conversor_falso(tmp_path,junction/'input.dxf')))
    assert dwg.conversor()==os.environ['RODOVIA_ODA']
    assert dwg.converter(b'AC1032'+b'\0'*100)==(junction/'input.dxf').read_bytes()

def test_api_dwg(junction,tmp_path,monkeypatch):
    from app.server import app
    from app import store
    c=TestClient(app);pid=c.post('/api/projects',json=S(name='DWG').model_dump()).json()['id']
    monkeypatch.setenv('RODOVIA_ODA',str(tmp_path/'nao_existe'))
    from app import dwg
    monkeypatch.setattr(dwg,'conversor',lambda:None)
    r=c.post(f'/api/projects/{pid}/files',files={'file':('trecho.dwg',b'AC1032'+b'\0'*200)});assert r.status_code==424 and 'ODA File Converter' in r.json()['detail']
    assert c.get('/api/dwg').json()['ok'] is False
    monkeypatch.undo();monkeypatch.setenv('RODOVIA_ODA',str(conversor_falso(tmp_path,junction/'input.dxf')))
    assert c.get('/api/dwg').json()['ok'] is True
    r=c.post(f'/api/projects/{pid}/files',files={'file':('trecho.dwg',b'AC1032'+b'\0'*200)});assert r.status_code==200,r.text
    d=store.directory(pid);assert (d/'input.dxf').read_bytes()==(junction/'input.dxf').read_bytes() and (d/'input.dwg').exists()
    assert r.json()['files']['dxf']['name']=='trecho.dwg' and r.json()['files']['dxf']['convertido']=='DWG'
    # Um DXF enviado depois substitui o DWG convertido.
    c.post(f'/api/projects/{pid}/files',files={'file':('x.dxf',(junction/'input.dxf').read_bytes())});assert not (d/'input.dwg').exists()
    assert c.post(f'/api/projects/{pid}/files',files={'file':('a.txt',b'x')}).status_code==415

def test_esquema_29_e_frota():
    from app.models import Settings
    from app.migration import SCHEMA_VERSION
    from app import visual
    assert SCHEMA_VERSION>=29
    old=Settings.model_validate({'schema_version':28,'km_start_m':0,'km_end_m':100});assert old.vehicle_mix=='classico' and old.pedestrians is False
    new=Settings();assert new.vehicle_mix=='variado' and new.pedestrians is True
    ids=[(i,k,c) for i in range(3) for k in range(60) for c in range(2)]
    assert {visual.vehicle_type(['main'],x) for x in ids}=={'car','truck','bus'}                       # clássica: como antes
    var={visual.vehicle_type(['main'],x,'variado') for x in ids};assert {'moto','van','pickup','carreta','truck','bus','car'}<=var
    im=np.zeros((80,120,3),np.uint8);scr=lambda P:np.asarray(P)*8+[60,40]
    for vt in ('moto','van','pickup','carreta'):visual.draw_vehicle(im,np.array([0.,0.]),np.array([1.,0.]),vt,(200,60,50),scr,1/8)
    assert im.any()

def test_vegetacao_e_pedestres_no_video(junction):
    from app.render import Scene
    v=((500150,7800045),70)
    base=Scene(junction,S()).frame(0,view=v)[0]
    A=[{'name':'Bosque','kind':'arvore','points':[{'x':500100,'y':7800030},{'x':500200,'y':7800030},{'x':500200,'y':7800060},{'x':500100,'y':7800060}],'density':15,'size_m':7}]
    sc=Scene(junction,S(vegetation_areas=A));veg=sc.frame(0,view=v)[0]
    assert np.abs(veg.astype(int)-base).sum(2).astype(bool).mean()>.05 and len(sc._veg['xy'])>=20
    # Área sobre a pista: as plantas não entram no pavimento.
    A2=[{**A[0],'points':[{'x':500100,'y':7799992},{'x':500200,'y':7799992},{'x':500200,'y':7800008},{'x':500100,'y':7800008}]}]
    s2=Scene(junction,S(vegetation_areas=A2));s2.frame(0,view=v);assert s2._veg is None or len(s2._veg['xy'])<3
    # Planta avulsa e sombra pelo sol: sombra muda de lado.
    P=[{'x':500150,'y':7800045,'kind':'ipe','size_m':10}]
    m=Scene(junction,S(vegetation_points=P,sun_shadows=True,sun_hour=7)).frame(0,view=v)[0];t=Scene(junction,S(vegetation_points=P,sun_shadows=True,sun_hour=17)).frame(0,view=v)[0]
    assert not np.array_equal(m,t)
    # Pedestres num caminho: aparecem e andam; desligados, nada muda.
    PP=[{'points':[{'x':500110,'y':7800045},{'x':500190,'y':7800045}],'people_per_100m':10}]
    sp=Scene(junction,S(pedestrian_paths=PP,pedestrians=True));a=sp.frame(1,view=v)[0];b=sp.frame(4,view=v)[0]
    assert not np.array_equal(a,b) and not np.array_equal(a,base)
    assert np.array_equal(Scene(junction,S(pedestrian_paths=PP,pedestrians=False)).frame(1,view=v)[0],base)
    # Faixa de pedestre também tem pessoas.
    CW=[{'a':{'x':500150,'y':7799990},'b':{'x':500150,'y':7800010}}];v2=((500150,7800000),40)
    c0=Scene(junction,S(crosswalks=CW,pedestrians=False)).frame(2,view=v2)[0];c1=Scene(junction,S(crosswalks=CW,pedestrians=True)).frame(2,view=v2)[0]
    assert not np.array_equal(c0,c1)
