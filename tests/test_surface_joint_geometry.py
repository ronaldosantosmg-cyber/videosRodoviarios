import numpy as np
import pytest
from shapely.geometry import LineString,Polygon
from app.pavement import JointField,surface_details
from app.models import Settings
from app.surface_marks import items
from app.marking_policy import paint_only_layer
from app.flow_fit import physical_obstacles


def test_rotated_joint_grid_follows_axis_and_preserves_holes():
    u=np.array([.6,.8]);n=np.array([-.8,.6]);axis=np.array([u*0,u*100])
    road=LineString(axis).buffer(7,cap_style=2)
    hole=Polygon([u*20+n*-2,u*25+n*-2,u*25+n*2,u*20+n*2]);road=road.difference(hole)
    details=surface_details(road,JointField([axis]),5,3.5)
    assert details['joints']
    cross=long=0
    for line in details['joints']:
        g=LineString(line);assert road.buffer(1e-8).covers(g)
        v=np.asarray(line[-1])-line[0];v/=np.linalg.norm(v);dot=abs(float(v@u))
        assert dot<1e-7 or dot>1-1e-7
        cross+=dot<1e-7;long+=dot>1-1e-7
    assert cross>10 and long>1


def test_bridge_barriers_are_lateral_and_do_not_close_portals():
    road=Polygon([(0,-7),(100,-7),(100,7),(0,7)])
    details=surface_details(road,JointField([[(0,0),(100,0)]]),30,3.5,True)
    assert details['rails'] and details['joints']
    for line in details['rails']:assert abs(line[-1][1]-line[0][1])<1e-8


def test_named_slope_is_reclassified_without_changing_its_polygon():
    cfg=Settings(pavement_areas=[{'id':'s','name':'TALUDE','kind':'pavement','material':'rigido','points':[{'x':0,'y':0},{'x':30,'y':0},{'x':30,'y':10},{'x':0,'y':10}]}])
    a=cfg.pavement_areas[0];assert a.kind=='terrain' and a.material=='auto'
    result=items(cfg,[],[]);assert result[0]['role']=='terrain' and result[0]['material']=='auto'
    assert Polygon(result[0]['points']).area==300


@pytest.mark.parametrize('layer',['ZEBRADO','sinC-SH_ZPA(0.40)-branca','SETAS','EIXO_SECCIONADO','sinC-SH_LCA(0.15)-amarela'])
def test_paint_cannot_become_obstacle_even_if_misclassified(layer):
    assert paint_only_layer(layer)
    record={'layer':layer,'role':'barrier','closed':True,'points':[(0,0),(10,0),(10,10),(0,10)]}
    assert physical_obstacles([record])==[]
    record['layer']='BARREIRA FISICA'
    assert physical_obstacles([record])


def test_explicit_border_remains_distinct_from_paint():
    assert not paint_only_layer('sinC-SH_LBO(0.15)-branca')
    assert not paint_only_layer('F-HZ-BORDO')


def test_bridge_preview_contains_joints_and_lateral_barriers(tmp_path):
    from test_traffic_pipeline import project
    from app.scene3d import build
    cfg=project(tmp_path).model_copy(update={'traffic':False})
    cfg.pavement_areas=Settings(pavement_areas=[{'name':'OAE','kind':'oae','points':[{'x':500100,'y':7799993},{'x':500200,'y':7799993},{'x':500200,'y':7800007},{'x':500100,'y':7800007}]}]).pavement_areas
    (tmp_path/'config.json').write_text(cfg.model_dump_json())
    before=(tmp_path/'input.dxf').read_bytes();scene=build(tmp_path,cfg)
    assert any('New Jersey' in m.get('name','') for m in scene['meshes'])
    assert any('junta' in m.get('name','').lower() for m in scene['meshes'])
    assert (tmp_path/'input.dxf').read_bytes()==before
