import numpy as np
import pytest
from shapely.geometry import box,LineString
from app.flow_recovery import recover_sections
from app.vehicle_motion import analyze_motion
from app.models import Settings
from app.traffic import TrafficNetwork


def test_valid_axis_is_kept_without_geometric_changes():
    p=np.array([[0.,0.],[200.,0.]])
    pieces,report=recover_sections(p,box(-10,-10,210,10),50)
    assert report['status']=='unchanged' and report['excluded']==[]
    np.testing.assert_array_equal(p,pieces[0])


def test_local_sharp_corner_is_excluded_without_a_shortcut():
    p=np.array([[0.,0.],[150.,0.],[150.,150.]])
    original=p.copy();surface=box(-10,-10,160,160)
    pieces,report=recover_sections(p,surface,50)
    assert len(pieces)==2 and report['status']=='partial'
    assert report['excluded'] and all(analyze_motion(q,allowed=surface)['ok'] for q in pieces)
    assert all(LineString(q).difference(LineString(p).buffer(.00001)).length==0 for q in pieces)
    assert np.linalg.norm(pieces[0][-1]-pieces[1][0])>10
    np.testing.assert_array_equal(original,p)


def test_self_crossing_is_removed_without_joining_the_remaining_pieces():
    pieces,report=recover_sections([[0,0],[100,100],[0,100],[100,0]],box(-10,-10,110,110),20)
    assert pieces and report['status']=='partial'
    assert all(analyze_motion(q,allowed=box(-10,-10,110,110))['ok'] for q in pieces)
    assert all(LineString(q).is_simple for q in pieces)

@pytest.mark.parametrize('points',[[[0,0],[None,0]],[[0,0],[float('inf'),0]],[[0,0],[0,0]]])
def test_invalid_geometry_remains_blocked(points):
    assert not recover_sections(points,box(-10,-10,100,100),20)[0]


def test_network_only_recovers_when_explicitly_requested_and_respects_disable():
    axis=np.array([[0.,0.],[150.,0.],[150.,150.]])
    kwargs=dict(derive_traffic_paths=False,hydrography=False,signage_detail='basic',vehicle_paths='anterior',min_route_segment_m=50)
    def network(overrides):
        s=Settings(**kwargs,flow_overrides=[o for o in overrides if o['action']!='recover'],flow_recoveries=[{k:v for k,v in o.items() if k!='action'} for o in overrides if o['action']=='recover'])
        return TrafficNetwork([box(-10,-10,160,160)],[],[{'points':axis}],axis,np.array([0.,150.,300.]),s)
    base=network([])
    recovered=network([dict(x=100,y=0,action='recover')])
    assert not base.paths
    assert recovered.paths and recovered.recovered_paths
    assert all(analyze_motion(p['p'],allowed=recovered.allowed)['ok'] for p in recovered.paths)
    assert all(len(p['edges'])==1 for p in recovered.paths)
    assert not network([dict(x=100,y=0,action='recover'),dict(x=100,y=0,action='disable')]).paths


def test_recovery_configuration_can_be_read_by_the_previous_release(tmp_path):
    import sys,types,zipfile
    from pathlib import Path
    archive=Path(__file__).resolve().parents[5]/'atualizacoes/RodoviaStudio_1_42_9_atualizacao.zip'
    assert archive.is_file()
    with zipfile.ZipFile(archive) as z:code=z.read('pacote/suporte/sistema/app/models.py')
    module=types.ModuleType('app._previous_recovery_test');sys.modules[module.__name__]=module
    try:
        exec(compile(code,'models_1_42_9.py','exec'),module.__dict__)
        current=Settings(flow_recoveries=[dict(id='recovery',x=100,y=0)])
        previous=module.Settings.model_validate_json(current.model_dump_json())
        assert previous.flow_overrides==[]
        assert previous.name==current.name
    finally:sys.modules.pop(module.__name__,None)


def test_recovery_rechecks_vehicle_body_and_never_creates_short_remnants():
    surface=box(-10,-10,90,10).union(box(110,-10,210,10))
    pieces,report=recover_sections([[0.,0.],[200.,0.]],surface,50.)
    assert len(pieces)==2 and report['excluded']
    assert all(LineString(p).length>=50 for p in pieces)
    assert all(analyze_motion(p,allowed=surface)['ok'] for p in pieces)
    assert all(not LineString(p).intersects(box(91,-10,109,10)) for p in pieces)
    assert report['excluded_geometry'] and report['retained_geometry']


def test_recovery_keeps_a_manual_route_direction_and_disables_no_other_route():
    axis=np.array([[0.,0.],[300.,0.]])
    route=dict(id='main',name='Qualquer eixo',points=[dict(x=0,y=0),dict(x=300,y=0)],type='unico')
    s=Settings(derive_traffic_paths=False,route_alignments=[route],flow_recoveries=[dict(x=100,y=0)],signage_detail='basic',min_route_segment_m=50)
    n=TrafficNetwork([box(-10,-10,310,10)],[],[],axis,np.array([0.,300.]),s)
    assert n.paths
    assert all(p['p'][-1,0]>p['p'][0,0] for p in n.paths)
    assert s.route_alignments[0].enabled


def test_recovery_cannot_enable_traffic_without_a_valid_pavement():
    from shapely.geometry import Polygon
    assert not recover_sections([[0,0],[200,0]],Polygon(),50)[0]
    assert not recover_sections([[0,0],[200,0]],None,50)[0]


def test_a_small_defect_is_smoothed_before_removing_valid_route_length():
    x=np.arange(0.,150.1,.25);points=np.column_stack([x,.2*np.sin(x*2*np.pi/1.5)]);original=points.copy();allowed=box(-20,-20,170,20)
    assert not analyze_motion(points,allowed=allowed)['ok']
    pieces,report=recover_sections(points,allowed,50)
    assert report['status']=='smoothed' and report['max_deviation_m']<=.5 and not report['excluded']
    assert len(pieces)==1 and analyze_motion(pieces[0],allowed=allowed)['ok']
    np.testing.assert_array_equal(points,original)


def test_changing_only_the_manual_axis_name_keeps_its_recovery_identity():
    axis=np.array([[0.,0.],[300.,0.]])
    cfg=Settings(derive_traffic_paths=False,signage_detail='basic',traffic_paths=[dict(id='stable-axis',name='Antes',points=[dict(x=0,y=0),dict(x=300,y=0)],kind='main',direction='growing')])
    def network():return TrafficNetwork([box(-10,-10,310,10)],[],[],axis,np.array([0.,300.]),cfg)
    key=network().raw_info[0]['origin_key'];cfg.traffic_paths[0].name='Depois'
    assert network().raw_info[0]['origin_key']==key
