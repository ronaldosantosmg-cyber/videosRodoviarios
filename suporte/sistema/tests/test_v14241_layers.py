"""1.42.41: relatório de interpretação das layers."""
import ezdxf,pytest
from pathlib import Path
from app.models import Settings
from app.layer_report import interpret,interpret_directory
from app.geometry import walk

def _doc():
    d=ezdxf.new();m=d.modelspace()
    for l in ('EIXO','HPAVPROJ','LIXO','TEXTOS','ACOSTAMENTO'):d.layers.new(l)
    m.add_lwpolyline([(0,0),(100,0)],dxfattribs={'layer':'EIXO'})
    h=m.add_hatch(dxfattribs={'layer':'HPAVPROJ'});h.paths.add_polyline_path([(0,-5),(100,-5),(100,5),(0,5)],is_closed=True)
    m.add_lwpolyline([(0,0),(10,10)],dxfattribs={'layer':'LIXO'})
    m.add_text('x',dxfattribs={'layer':'TEXTOS'})
    m.add_lwpolyline([(0,-6),(100,-6)],dxfattribs={'layer':'ACOSTAMENTO'})
    return d

def test_papeis_origem_e_alertas():
    r=interpret(walk(_doc().modelspace()),Settings())
    by={x['layer']:x for x in r['layers']}
    assert by['EIXO']['role']=='axis' and by['EIXO']['origin']=='perfil'
    assert by['HPAVPROJ']['role']=='pavement' and by['HPAVPROJ']['dominant']=='areal'
    assert by['LIXO']['role'] is None and any(a['code']=='sem_papel' for a in by['LIXO']['alerts'])
    assert not any(a['code']=='sem_papel' for a in by['TEXTOS']['alerts'])
    assert not by['ACOSTAMENTO']['alerts'] or all(a['code']!='incoerente' for a in by['ACOSTAMENTO']['alerts'])

def test_projeto_prevalece_e_incoerencia():
    s=Settings(layers={'pavement':['EIXO'],'axis':['LIXO']})
    by={x['layer']:x for x in interpret(walk(_doc().modelspace()),s)['layers']}
    assert by['EIXO']['origin']=='projeto' and by['EIXO']['role']=='pavement'
    assert any(a['code']=='incoerente' for a in by['EIXO']['alerts'])
    assert by['LIXO']['role']=='axis'

def test_papel_ausente_e_layer_inexistente_sem_erro():
    s=Settings(layers={'axis':['NAOEXISTE']})
    d=ezdxf.new();d.modelspace().add_lwpolyline([(0,0),(5,5)],dxfattribs={'layer':'X'})
    r=interpret(walk(d.modelspace()),s)
    codes={a['code'] for a in r['alerts']}
    assert {'ausente','papel_ausente'}<=codes

def test_diretorio_sem_dxf(tmp_path):
    r=interpret_directory(tmp_path,Settings());assert r['alerts'][0]['code']=='sem_dxf'

@pytest.mark.skipif(not Path('/tmp/claude-0/th57d/input.dxf').exists(),reason='DXF do TH57 ausente')
def test_th57_real():
    r=interpret_directory('/tmp/claude-0/th57d',Settings())
    roles=r['summary']['roles'];assert 'axis' in roles and 'pavement' in roles and 'oae' in roles
