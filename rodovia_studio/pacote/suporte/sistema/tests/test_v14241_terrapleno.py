"""1.42.41: terrapleno em grama (papel 'terrain') — textura de grama sobre a hachura, sem bloquear o fluxo."""
import numpy as np,ezdxf,pytest
from test_workflow import settings
from app.models import Settings

def S(**kw):return Settings(**{**settings().model_dump(),'duration_s':30,**kw})

def dxf(tmp_path):
    d=ezdxf.new();m=d.modelspace()
    for l in ['EIXO','PAV','GRAMADO_AREAS']:d.layers.new(l)
    m.add_lwpolyline([(500000,7800000),(500300,7800000)],dxfattribs={'layer':'EIXO'})
    for layer,x0,x1,y0,y1 in (('PAV',500000,500300,7799991,7800009),('GRAMADO_AREAS',500000,500300,7800012,7800040)):
        h=m.add_hatch(color=3,dxfattribs={'layer':layer});h.paths.add_polyline_path([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],is_closed=True)
    d.saveas(tmp_path/'input.dxf');return tmp_path

def test_modelo_e_perfil_aceitam_terrain():
    from app.models import HatchRole
    from app.layer_profiles import role_for,BUILTIN
    assert HatchRole(role='terrain').role=='terrain'
    assert role_for('F1-GRAMADO',BUILTIN['rules'])=='terrain' and role_for('AREA_VERDE',BUILTIN['rules'])=='terrain'

def test_terrapleno_vira_superficie_de_grama(tmp_path):
    from app.geometry import analyze
    from app.render import Scene
    from app import visual
    d=dxf(tmp_path);lay={'axis':['EIXO']}
    sig={h['layer']:h['sig'] for h in analyze(d,S(layers=lay,hatch_auto=False))[4]['hatches']}
    roles={sig['PAV']:{'role':'pavement'},sig['GRAMADO_AREAS']:{'role':'terrain'}}
    items=analyze(d,S(layers=lay,hatch_auto=False,hatch_roles=roles))[0]
    assert any(e['role']=='terrain' for e in items)
    sc=Scene(d,S(layers=lay,hatch_auto=False,hatch_roles=roles,imagery='neutral',width=1280))
    px=np.rint(sc.worldpx(np.array([[500150,7800026]],float))).astype(int)[0]
    assert int(sc.surface[px[1],px[0]])==visual.SURF['terrain']==5
    assert sc.overlay[px[1],px[0],1]>sc.overlay[px[1],px[0],0]       # verde dominante

def test_terrapleno_nao_bloqueia_fluxo(tmp_path):
    from app.geometry import analyze
    d=dxf(tmp_path)
    from app.flow_fit import physical_obstacles
    sig={h['layer']:h['sig'] for h in analyze(d,S(layers={'axis':['EIXO']},hatch_auto=False))[4]['hatches']}
    items=analyze(d,S(layers={'axis':['EIXO']},hatch_auto=False,hatch_roles={sig['GRAMADO_AREAS']:{'role':'terrain'}}))[0]
    axes=[dict(points=np.array([[500000.,7800000.],[500300.,7800000.]]))]
    assert physical_obstacles(items,axes)==[]
