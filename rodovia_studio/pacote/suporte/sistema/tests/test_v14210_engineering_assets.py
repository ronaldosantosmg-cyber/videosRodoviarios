import numpy as np
import pytest
from shapely.geometry import Point,box
from app.asset_catalog import CATALOG,image
from app.layer_profiles import BUILTIN,role_for,validate
from app.engineering_assets import oae_grade_separated,asset_meshes
from app.models import Settings

@pytest.mark.parametrize('name,expected',[
 ('HATCH_OAE','oae'),('POL_ARVORE','vegetation'),('LINHA_HIDROLOGIA','water'),
 ('EIXO_FERROVIA','railway'),('C-GASMIG','gas'),('REDE_GAS','gas'),
 ('LINHA DE TRANSMISSÃO','electric'),('POSTES','pole'),('EDIFICAÇÃO','building'),
 ('OFFSET','earthwork'),('OFF SET','earthwork'),('GABIÃO','earthwork'),
 ('EROSÃO','erosion'),('CORTINA ATIRANTADA','anchored_wall'),('FIBRA ÓPTICA','fiber'),
 ('RADAR','radar'),('TORRE','tower')])
def test_requested_cad_aliases(name,expected):
    assert role_for(name,BUILTIN['rules'])==expected


def test_material_catalog_has_distinct_local_textures_and_preserves_noise_seed():
    assert len(CATALOG)>=32
    signatures=set()
    for key in CATALOG:
        a=image(key);np.testing.assert_array_equal(a,image(key))
        assert a.shape==(128,128,3) and a.dtype==np.uint8
        signatures.add(a.tobytes())
    assert len(signatures)==len(CATALOG)
    assert role_for('ASFALTO_DESGASTE',BUILTIN['rules'])!='gas'
    assert validate({'name':'Meu padrão','rules':[{'pattern':'*MEU_NOME*','role':'gas','material':'gas'}]})['rules'][0]['material']=='gas'


def test_oae_elevation_prevents_rail_retention_only_for_matching_crossing():
    cfg=Settings(oae_marks=[dict(start=dict(x=-30,y=0),end=dict(x=30,y=0),width_m=14,level_m=6)])
    assert oae_grade_separated(cfg,Point(0,0),np.array([1.,0.]),np.array([0.,1.]),0,0)
    assert not oae_grade_separated(cfg,Point(100,100),np.array([1.,0.]),np.array([0.,1.]),0,0)
    cfg.oae_marks[0].level_m=0
    assert not oae_grade_separated(cfg,Point(0,0),np.array([1.,0.]),np.array([0.,1.]),0,0)


def test_symbols_produce_finite_3d_geometry_with_explicit_illustrative_dimensions():
    items=[dict(role=role,layer=role,points=np.array([[0.,0.],[40.,0.],[40.,40.],[0.,40.]]),closed=True,holes=[]) for role in ['building','vegetation','earthwork']]
    items += [dict(role=role,layer=role,points=np.array([[0.,0.],[40.,0.]]),closed=False,holes=[]) for role in ['gas','electric','fiber','railway','pole','tower','radar']]
    meshes=asset_meshes(items,lambda p,h:np.column_stack([p[:,0],np.full(len(p),h),-p[:,1]]))
    assert {m['role'] for m in meshes}>={'building','vegetation','earthwork','gas','electric','fiber','railway','pole','tower','radar'}
    assert all(np.isfinite(m['positions']).all() and len(m['positions'])%9==0 for m in meshes)
    assert all(m['illustrative_dimensions'] and m['asset_material'] in CATALOG for m in meshes)


def test_transport_does_not_stop_for_a_railway_below_a_declared_oae():
    from app.traffic import TrafficNetwork
    from app.transport import Transport
    axis=np.array([[-100.,0.],[100.,0.]])
    s=Settings(layers={'axis':['EIXO']},derive_traffic_paths=False,signage_detail='basic',railways=[dict(id='rail',points=[dict(x=0,y=-100),dict(x=0,y=100)])])
    network=TrafficNetwork([box(-110,-10,110,10)],[],[dict(points=axis,layer='EIXO',role='axis')],axis,np.array([0.,200.]),s)
    assert Transport(s,network).report()['crossings']>0
    s=Settings.model_validate(dict(s.model_dump(),oae_marks=[dict(start=dict(x=-30,y=0),end=dict(x=30,y=0),width_m=14,level_m=6)]))
    assert Transport(s,network).report()['crossings']==0
    s.oae_marks[0].level_m=0
    assert Transport(s,network).report()['crossings']>0


def test_named_asset_hatches_take_precedence_over_a_generic_grass_pattern(tmp_path):
    import ezdxf
    from app.geometry import analyze
    doc=ezdxf.new();model=doc.modelspace();doc.layers.new('EIXO');model.add_line((0,0),(150,0),dxfattribs={'layer':'EIXO'})
    for i,name in enumerate(['ARVORES','EROSAO','OFFSET','OAE']):
        doc.layers.new(name);hatch=model.add_hatch(dxfattribs={'layer':name});hatch.set_pattern_fill('GRASS');x=i*30
        hatch.paths.add_polyline_path([(x,20),(x+20,20),(x+20,40),(x,40)],is_closed=True)
    doc.saveas(tmp_path/'input.dxf')
    items,*_=analyze(tmp_path,Settings(hatch_auto=True,hydrography=False))
    assert {row['layer']:row['role'] for row in items if row['closed']}=={'ARVORES':'vegetation','EROSAO':'erosion','OFFSET':'earthwork','OAE':'oae'}
