import ezdxf
from app.models import Settings
from app.geometry import analyze


def test_material_only_choice_inherits_layer_role_and_survives_reload(tmp_path):
    doc=ezdxf.new();doc.layers.new('EIXO');doc.layers.new('PISTA')
    m=doc.modelspace();m.add_lwpolyline([(0,0),(200,0)],dxfattribs={'layer':'EIXO'})
    h=m.add_hatch(dxfattribs={'layer':'PISTA'});h.paths.add_polyline_path([(0,-5),(200,-5),(200,5),(0,5)],is_closed=True)
    doc.saveas(tmp_path/'input.dxf')
    cfg=Settings(layers={'axis':['EIXO'],'existing_pavement':['PISTA']},hydrography=False)
    *_,report=analyze(tmp_path,cfg)
    sig=next(x['sig'] for x in report['hatches'] if x['layer']=='PISTA')
    cfg=Settings.model_validate({**cfg.model_dump(),'hatch_roles':{sig:{'role':'','material':'rigido'}}})
    cfg=Settings.model_validate_json(cfg.model_dump_json())
    entities,axis,*_=analyze(tmp_path,cfg)
    surface=next(e for e in entities if e['layer']=='PISTA')
    assert surface['role']=='existing_pavement'
    assert surface['material']=='rigido'
    from app.webmap import vectors
    data=vectors(entities,axis)
    assert any(r.get('material')=='rigido' for r in data['layers']['existing_pavement'])
