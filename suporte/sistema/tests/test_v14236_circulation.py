import json
import numpy as np
from shapely.geometry import box,LineString
from app.models import Settings
from app.native_axes import native_paths,axis_fingerprint
from app.traffic import TrafficNetwork
from app.simulation import TrafficSim
from app.fleet_compatibility import compatibility
from app.flow_diagnostics import flow_diagnostics
from app.flow_nodes import direction


def test_direction_and_off_follow_physical_axis_when_order_changes():
    p=np.array([[0.,0.],[300.,0.]]);a=dict(points=p,role='axis',layer='EIXO');b={**a,'points':p+[0,20]}
    ka='axis:'+axis_fingerprint(p,'EIXO');kb='axis:'+axis_fingerprint(b['points'],'EIXO')
    s=Settings(layers={'axis':['EIXO']},route_directions={ka:'off',kb:'reverse'})
    for axes in ([a,b],[b,a]):
        paths,report=native_paths(axes,s,box(-50,-50,350,50))
        assert len(paths)==1 and np.all(paths[0]['points'][:,1]==20) and paths[0]['native_direction']=='reverse'
        assert not report['pending_directions']


def test_unknown_legacy_off_does_not_reenable_or_transfer():
    p=np.array([[0.,0.],[300.,0.]]);axes=[dict(points=p,role='axis',layer='EIXO'),dict(points=p+[0,20],role='axis',layer='EIXO')]
    s=Settings(layers={'axis':['EIXO']},route_directions={'0':'off','1':'forward'})
    paths,report=native_paths(axes,s,box(-50,-50,350,50));assert not paths and report['pending_directions']==2
    key='axis:'+axis_fingerprint(p,'EIXO');s.route_directions[key]='off'
    paths,report=native_paths(axes,s,box(-50,-50,350,50));assert not paths and report['pending_directions']==1


def curve():
    angle=np.linspace(-np.pi/2,0,41);arc=np.column_stack([15*np.cos(angle),15+15*np.sin(angle)])
    p=np.vstack([[-100.,0.],arc,[15.,115.]])
    s=Settings(signage_detail='basic',hydrography=False,duration_s=3,vehicle_mix='engenharia',route_alignments=[dict(id='curva',name='Curva',type='unico',points=[dict(x=float(x),y=float(y)) for x,y in p])])
    net=TrafficNetwork([LineString(p).buffer(3.6)],[],[],p,np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))],s)
    return s,net


def test_fleet_report_exposes_partial_compatibility_without_releasing_long_vehicle():
    s,n=curve();assert n.paths
    # Via principal inclui todas as classes definidas pela seleção de frota existente.
    for path in n.paths:path['kinds']=['main']
    sim=TrafficSim(n,s,lambda *a:'car6',duration=3);original=[p['p'].copy() for p in n.paths]
    report=compatibility(sim,n,s);row=report['paths'][0];by={v['type']:v for v in row['vehicles']}
    assert by['car6']['ok'] and not by['long30']['ok'] and by['long30']['point']
    diagnostic=flow_diagnostics(n)[0]
    assert diagnostic['technical_status']=='adjustment' and 'long30' in diagnostic['technical_fleet']['blocked']
    assert diagnostic['technical_circulation']['enabled']
    assert all(np.array_equal(p['p'],original[i]) for i,p in enumerate(n.paths))


def test_lightweight_report_does_not_audit_unattempted_classes():
    s,n=curve();n.paths[0]['kinds']=['main'];sim=TrafficSim(n,s,lambda *a:'car6',duration=3)
    before=set(sim.motion_cache);report=compatibility(sim,n,s,complete=False)
    assert set(sim.motion_cache)==before and any(not v['checked'] for v in report['paths'][0]['vehicles'])


def test_reversing_nodes_and_direction_preserves_geometry_and_disabled_state():
    s,n=curve();r=s.route_alignments[0];r.flow_start='entrada';r.flow_end='saida';r.flow_direction='crescente';r.enabled=False
    old=r.model_dump();copy=r.model_copy(update={'flow_start':r.flow_end,'flow_end':r.flow_start,'flow_direction':'decrescente'})
    assert direction(copy)==-1 and direction(r)==1 and not copy.enabled
    assert copy.model_dump()['points']==old['points']


def test_zero_oae_does_not_issue_direction_marks_but_confirmed_elevated_one_can():
    from app.markup import oae_direction_marks
    from types import SimpleNamespace
    base=dict(deck=box(0,-10,300,10),direction='decreasing',level_m=0)
    station=SimpleNamespace(direction=1)
    assert oae_direction_marks([base],station)==[]
    assert oae_direction_marks([{**base,'level_m':6}],station)[0][1]==-1
    assert not oae_direction_marks([{**base,'level_m':float('nan')}],station)


def test_oae_contour_without_grade_is_not_a_bridge_constraint_or_physical_barrier():
    from app.flow_fit import physical_obstacles
    p=np.array([[0.,0.],[300.,0.]])
    contour=dict(role='oae',closed=True,points=np.array([[100,-10],[130,-10],[130,10],[100,10]]),elevation_m=0)
    assert physical_obstacles([contour])==[]
    key='axis:'+axis_fingerprint(p,'EIXO')
    s=Settings(layers={'axis':['EIXO']},route_directions={key:'forward'},signage_detail='basic')
    n=TrafficNetwork([box(-20,-12,320,12)],[],[dict(points=p,layer='EIXO',role='axis')],p,np.array([0.,300.]),s,bridges=[box(100,-10,130,10)])
    assert n.paths and n.bridges.is_empty


def test_oae_direction_cannot_reverse_explicit_native_flow():
    p=np.array([[0.,0.],[300.,0.]])
    key='axis:'+axis_fingerprint(p,'EIXO');s=Settings(layers={'axis':['EIXO']},route_directions={key:'forward'},signage_detail='basic')
    n=TrafficNetwork([box(-20,-12,320,12)],[],[dict(points=p,layer='EIXO',role='axis')],p,np.array([0.,300.]),s,oae_dirs=[(box(-10,-20,310,20),-1)])
    assert n.paths and all(row['forward'] for row in n.raw_info)


def test_dxf_oae_zero_crossing_and_parallel_contours_preserve_circulation(tmp_path):
    import ezdxf
    from app.render import Scene
    from test_v1425_scene3d import project
    d,s=project(tmp_path);first=Scene(d,s);before=len(first.network.paths)
    doc=ezdxf.readfile(d/'input.dxf');doc.layers.new('OAE');m=doc.modelspace()
    m.add_lwpolyline([(500200,7799950),(500210,7800050)],dxfattribs={'layer':'OAE','elevation':0})
    m.add_lwpolyline([(500100,7800004),(500400,7800004)],dxfattribs={'layer':'OAE','elevation':0})
    hatch=m.add_hatch(dxfattribs={'layer':'OAE','elevation':(0,0,0)});hatch.paths.add_polyline_path([(500200,7799990),(500240,7799990),(500240,7800010),(500200,7800010)],is_closed=True)
    doc.saveas(d/'input.dxf');s.layers['oae']=['OAE'];source=(d/'input.dxf').read_bytes();scene=Scene(d,s)
    assert scene.network.bridges.is_empty and len(scene.network.paths)==before
    assert scene.network.oae_report and all(o['zero_reference'] for o in scene.network.oae_report)
    assert not any('OAE transversal com Z=0' in w for w in scene.network.warnings)
    assert scene.traffic().spawned>0 and (d/'input.dxf').read_bytes()==source


def test_origin_keys_and_manual_shutdown_survive_axis_reordering():
    import hashlib
    p=np.array([[0.,0.],[300.,0.]]);a=dict(points=p,role='axis',layer='EIXO');b={**a,'points':p+[0,20]}
    s=Settings(layers={'axis':['EIXO']},signage_detail='basic')
    def network(axes,settings):return TrafficNetwork([box(-20,-20,320,40)],[],axes,p,np.array([0.,300.]),settings)
    first=network([a,b],s);old=first.raw_info[0]['origin_key']
    second=network([b,a],s);corresponding=next(r for r in second.raw_info if abs(r['points'][:,1].mean())<1)
    assert corresponding['origin_key']==old
    s=Settings.model_validate({**s.model_dump(),'flow_overrides':[dict(id='off',x=150,y=0,target_key=old,action='disable',enabled=True)]})
    third=network([b,a],s);assert all(r['disabled'] for r in third.raw_info if abs(r['points'][:,1].mean())<1)


def test_changed_axis_does_not_silently_reenable_a_previous_stable_shutdown():
    p=np.array([[0.,0.],[300.,0.]]);old='axis:'+axis_fingerprint(p,'EIXO')
    changed=dict(points=p+[0,.5],role='axis',layer='EIXO')
    s=Settings(layers={'axis':['EIXO']},route_directions={old:'off'})
    rows,report=native_paths([changed],s,box(-20,-20,320,20))
    assert not rows and report['pending_directions']==1
    new='axis:'+axis_fingerprint(changed['points'],'EIXO');s.route_directions[new]='off'
    rows,report=native_paths([changed],s,box(-20,-20,320,20));assert not rows and report['pending_directions']==0


def test_older_runtime_refuses_new_direction_schema_instead_of_ignoring_shutdown():
    import zipfile,types
    from pathlib import Path
    from app.migration import SCHEMA_VERSION
    assert SCHEMA_VERSION==31
    old=Path(__file__).resolve().parents[5]/'atualizacoes/RodoviaStudio_1_42_35_atualizacao.zip'
    with zipfile.ZipFile(old) as z:source=z.read('pacote/suporte/sistema/app/migration.py').decode()
    module=types.ModuleType('previous_migration');exec(compile(source,'migration_14235.py','exec'),module.__dict__)
    config=Settings(route_directions={'axis:'+'a'*64:'off'}).model_dump()
    import pytest
    with pytest.raises(ValueError,match='mais nova'):module.migrate(config)
    assert config['route_directions']['axis:'+'a'*64]=='off'
