import ezdxf,numpy as np
from app.models import Settings
from app.geometry import guess,hatch_signature,analyze
from app.webmap import vectors


def test_expropriation_name_wins_over_material_pattern_without_overwriting_manual_choice(tmp_path):
    from test_v1425_scene3d import project
    d,s=project(tmp_path);doc=ezdxf.readfile(d/'input.dxf');doc.layers.new('DESAPROPRIAÇÃO');h=doc.modelspace().add_hatch(dxfattribs={'layer':'DESAPROPRIAÇÃO'});h.set_pattern_fill('AR-SAND');h.paths.add_polyline_path([(500000,7799990),(500500,7799990),(500500,7800030)],is_closed=True)
    assert guess('DESAPROPRIAÇÃO')=='domain' and hatch_signature(h,'DESAPROPRIAÇÃO',doc)[1]['suggested_role']=='domain'
    assert guess('GE_HZ-HACOSTAMENTOPROJ')=='shoulder'
    doc.saveas(d/'input.dxf');s.hatch_auto=True;items,*_=analyze(d,s);assert [e for e in items if e['layer']=='DESAPROPRIAÇÃO'][0]['role']=='domain'
    s.layers['pavement'].append('DESAPROPRIAÇÃO');items,_,_,_,report=analyze(d,s);assert any(e['role']=='pavement' and e['layer']=='DESAPROPRIAÇÃO' for e in items)
    assert any('REVISARCONTORNOS' in w for w in report['warnings'])


def test_hatch_surface_does_not_become_cad_outline_or_generated_white_border(tmp_path):
    from test_v1425_scene3d import project
    from app.render import Scene
    d,s=project(tmp_path);s.imagery_pixels=2048;s.traffic=False
    scene=Scene.light(d,s);assert not any(src==-2 for src in scene.network.mark_src)
    data=vectors(scene.items,scene.axis);r=data['layers']['pavement'][0];assert r['hatch_outline'] and r['k']==list(range(len(r['p'])))
    assert scene.network.allowed.area>0
    s.derived_contours=True;old=Scene.light(d,s);assert any(src==-2 for src in old.network.mark_src) and scene.network.allowed.equals(old.network.allowed)
