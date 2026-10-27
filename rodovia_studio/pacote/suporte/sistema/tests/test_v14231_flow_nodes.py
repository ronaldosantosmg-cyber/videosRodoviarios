import math
from types import SimpleNamespace
import numpy as np
import pytest
from shapely.geometry import box
from pydantic import ValidationError
from app.models import RouteAlignment,Settings
from app.routes import build_lanes
from app.flow_nodes import direction
from app.traffic_distribution import movement_weights,apply_distribution


def route(**kw):
    return RouteAlignment(points=[dict(x=0,y=0),dict(x=300,y=0)],**kw)


def test_legacy_default_keeps_two_existing_lanes_and_positions():
    lanes=build_lanes(route())
    assert len(lanes)==2
    assert sorted(float(np.median(v['points'][:,1])) for v in lanes)==[-1.75,1.75]


@pytest.mark.parametrize('sense,start,end,expected',[('crescente','entrada','saida',1),('decrescente','saida','entrada',-1)])
def test_nodes_orient_section_arrows_and_vehicle_path_from_same_lane(sense,start,end,expected):
    r=route(flow_role='principal',flow_start=start,flow_end=end,type='dupla',lanes=2,median_m=2)
    lanes=build_lanes(r);assert len(lanes)==2 and direction(r)==expected
    for lane in lanes:
        assert lane['dir']==('f' if expected>0 else 'r')
        p=lane['points'];assert (p[-1,0]-p[0,0])*expected>0
        assert np.median(p[:,1])*expected<0  # direita do sentido de deslocamento


def test_access_centered_and_return_on_right_and_disabled_side_not_resurrected():
    for role,y in [('acesso',0),('retorno',-1.75),('dispositivo',-1.75)]:
        lanes=build_lanes(route(flow_role=role));assert len(lanes)==1
        assert np.allclose(lanes[0]['points'][:,1],y)
    r=route(flow_role='principal',flow_start='saida',flow_end='entrada',cross_sections=[dict(id='s',start_m=0,end_m=300,left=[dict(kind='pista',width_m=3.6,traffic_enabled=False)],right=[dict(kind='pista',width_m=3.6)])],sections_only=True)
    assert build_lanes(r)==[]


@pytest.mark.parametrize('rotation,area_sign',[('horario',-1),('anti_horario',1)])
def test_roundabout_rotation_explicit_at_large_cad_coordinates(rotation,area_sign):
    theta=np.linspace(0,2*math.pi,129);points=[dict(x=730000+50*math.cos(a),y=7824000+50*math.sin(a)) for a in theta]
    r=RouteAlignment(points=points,flow_role='rotatoria',roundabout_rotation=rotation)
    lanes=build_lanes(r);assert len(lanes)==1
    p=lanes[0]['points'];q=p-p[0];area=np.sum(q[:-1,0]*q[1:,1]-q[1:,0]*q[:-1,1])
    assert area*area_sign>0


@pytest.mark.parametrize('kwargs',[
 dict(flow_start='entrada',flow_end='entrada'),dict(flow_start='entrada',flow_end='saida',flow_direction='decrescente'),
 dict(flow_role='rotatoria',roundabout_rotation='horario'),dict(roundabout_rotation='horario'),
 dict(flow_role='acesso',flow_direction='ambos'),dict(flow_role='acesso',external_demand_vph=100),
 dict(flow_role='acesso',flow_start='entrada',external_demand_vph=100,external_vdm=1000),
 dict(flow_role='acesso',flow_start='entrada',external_demand_vph=float('nan'))])
def test_invalid_contradictory_nodes_never_silently_reverse_or_invent_geometry(kwargs):
    with pytest.raises(ValidationError):route(**kwargs)


def fork():
    edges=[]
    for i,(rid,role) in enumerate([('P','principal'),('P','principal'),('A','acesso'),('B','acesso'),('R','retorno'),('D','dispositivo'),('O','rotatoria')]):
        edges.append(dict(route=rid,flow_role=role,origin=0 if rid=='P' else i,length=100,t=np.array([[1.,0.],[1.,0.]]),end=9))
    return SimpleNamespace(edges=edges,connections={0:[1,2,3,4,5,6]},rule_report=[],origin_info={0:(500,True)})


def test_category_totals_are_five_and_twenty_not_per_branch_and_sum_to_one():
    net=fork();weights,groups=movement_weights(net)
    assert weights[(0,1)]==pytest.approx(.75)
    assert [weights[(0,i)] for i in (2,3)]==pytest.approx([.025,.025])
    assert sum(weights[(0,i)] for i in (4,5,6))==pytest.approx(.20)
    assert sum(weights.values())==pytest.approx(1)
    assert groups[0]['node']==9 and groups[0]['rule']=='categorias_5_20'


def test_multiple_lanes_do_not_multiply_category_allocation():
    net=fork();net.edges.append({**net.edges[2]});net.connections[0].append(7)
    weights,_=movement_weights(net)
    assert weights[(0,2)]+weights[(0,7)]==pytest.approx(.025)
    assert weights[(0,3)]==pytest.approx(.025)


def test_external_arrival_adds_to_global_vdm_without_stealing_principal_demand():
    net=SimpleNamespace(axis=np.array([[0.,0.],[100.,0.]]),edges=[dict(route='P',flow_role='principal',flow_start='entrada',flow_end='saida',route_dir='f'),dict(route='A',flow_role='acesso',flow_start='entrada',flow_end='conexao',route_dir='f',external_demand_vph=400)],connections={},rule_report=[])
    sim=SimpleNamespace(net=net,s=Settings(traffic_vdm=10000,traffic_peak_hour_fraction=.1),siblings={0:[0],1:[1]},link_of=[[ (('e',0),0,100)],[(('e',1),0,100)]],paths=[dict(p=np.array([[0,0],[100,0]]))]*2,rate=[1.,1.])
    apply_distribution(sim)
    assert np.array(sim.rate)*3600==pytest.approx([1000,400])
    assert sum(sim.rate)*3600==pytest.approx(1400)
    assert sim.distribution_report['external_entries'][0]['vehicles_h']==400


def test_real_typed_y_junction_preserves_connections_and_conservation():
    from shapely.geometry import LineString,Point
    from app.traffic import TrafficNetwork
    from app.simulation import TrafficSim
    a=np.array([[0.,0.],[300.,0.]]);b=np.array([[150.,0.],[230.,80.]])
    s=Settings(hydrography=False,signage_detail='basic',duration_s=4,traffic_speed_kmh=35,route_directions={'0':'off'},route_alignments=[dict(id='P',name='Principal',points=[dict(x=x,y=y) for x,y in a],type='unico',flow_role='principal',flow_start='entrada',flow_end='saida'),dict(id='A',name='Acesso',points=[dict(x=x,y=y) for x,y in b],flow_role='acesso',flow_start='conexao',flow_end='saida')])
    net=TrafficNetwork([LineString(a).buffer(8),LineString(b).buffer(8),Point(150,0).buffer(20)],[],[],a,np.array([0.,300.]),s)
    assert len(net.paths)>=2
    assert any({net.edges[e].get('route') for e in p['edges']}=={'P','A'} for p in net.paths)
    sim=TrafficSim(net,s,lambda *a:'car',duration=4)
    report=sim.report();assert report['flow_balance']['conserved']
    assert report['rear_collisions']==report['side_collisions']==0
    assert any(any(v['percent']==5 for v in g['outputs']) for g in report['distribution']['movements'])


def test_external_merge_keeps_received_vehicles_and_global_demand_separate():
    from shapely.geometry import LineString,Point
    from app.traffic import TrafficNetwork
    from app.simulation import TrafficSim
    a=np.array([[-200.,0.],[300.,0.]]);b=np.array([[-100.,-100.],[50.,0.]])
    routes=[dict(id='P',name='Principal',points=[dict(x=x,y=y) for x,y in a],type='unico',flow_role='principal',flow_start='entrada',flow_end='saida'),dict(id='A',name='Entrada externa',points=[dict(x=x,y=y) for x,y in b],flow_role='acesso',flow_start='entrada',flow_end='conexao',external_demand_vph=400)]
    s=Settings(hydrography=False,signage_detail='basic',duration_s=4,traffic_speed_kmh=35,traffic_vdm=10000,traffic_peak_hour_fraction=.1,route_directions={'0':'off'},route_alignments=routes)
    net=TrafficNetwork([LineString(a).buffer(8),LineString(b).buffer(8),Point(50,0).buffer(20)],[],[],a,np.array([0.,500.]),s)
    sim=TrafficSim(net,s,lambda *a:'car',duration=4)
    assert sum(sim.rate)*3600==pytest.approx(1400)
    assert any({net.edges[e].get('route') for e in p['edges']}=={'P','A'} for p in net.paths)
    report=sim.report();assert report['flow_balance']['conserved']
    assert any(row['from_route']=='A' and row['to_route']=='P' and row['count']>0 for row in report['node_movements'])


def test_existing_manual_shutdown_is_preserved_after_classifying_access_on_center():
    from app.traffic import TrafficNetwork
    a=np.array([[0.,0.],[300.,0.]])
    r=dict(id='A',name='Rota existente',points=[dict(x=x,y=y) for x,y in a])
    s=Settings(hydrography=False,signage_detail='basic',route_alignments=[r])
    before=TrafficNetwork([box(-20,-10,320,10)],[],[],a,np.array([0.,300.]),s)
    key=next(e['origin_key'] for e in before.raw_info if e['route_dir']=='f')
    s.route_alignments[0].flow_role='acesso'
    s.flow_overrides=[__import__('app.models',fromlist=['FlowOverride']).FlowOverride(id='manual',x=150,y=-1.75,target_key=key,action='disable')]
    after=TrafficNetwork([box(-20,-10,320,10)],[],[],a,np.array([0.,300.]),s)
    assert after.raw_info and all(e['disabled'] for e in after.raw_info)
    assert not after.paths


def test_shared_approach_diversion_preserves_id_and_position_when_main_blocked():
    from app.simulation import TrafficSim
    sim=TrafficSim.__new__(TrafficSim);sim.s=Settings();sim.node_routing=True;sim.dynamic_reroutes=0
    sim.link_of=[[(('e',0),0,100),(('c',0,1),100,110),(('e',1),110,300)],[(('e',0),0,100),(('c',0,2),100,120),(('e',2),120,320)]]
    sim.link_offsets=[[0,0,0],[0,0,0]];sim.siblings={0:[0,1]};sim.entry={0:0,1:0}
    sim.shoulder_probe=SimpleNamespace(event=lambda v:None)
    sim.blocked_total=lambda path,t:path==0;sim.motion_valid=lambda *a:True
    sim.locate=lambda *a:(0,('e',0),0,100,45.)
    sim.polygon_safety=SimpleNamespace(pose=lambda v:(np.array([v['s'],0.]),np.array([1.,0.])))
    v=dict(id=7,p=0,s=45.,v=8.,t='car',li=0,lc=None)
    sim.reroute_at_shared_approach([v],10)
    assert v['id']==7 and v['p']==1 and v['s']==45 and sim.dynamic_reroutes==1
    v.update(p=0,s=45);sim.blocked_total=lambda *a:True
    sim.reroute_at_shared_approach([v],11);assert v['p']==0


def test_scheduled_total_closure_diverts_real_vehicles_before_node_without_respawning(monkeypatch):
    from app import simulation
    from app.traffic import TrafficNetwork
    from shapely.geometry import LineString,Point
    monkeypatch.setattr(simulation,'WARMUP',0)
    a=np.array([[0.,0.],[400.,0.]]);b=np.array([[150.,0.],[280.,100.]])
    s=Settings(hydrography=False,signage_detail='basic',duration_s=35,traffic_speed_kmh=35,traffic_demand_vphpl=1000,route_alignments=[dict(id='P',name='Principal',type='unico',flow_role='principal',flow_start='entrada',flow_end='saida',points=[dict(x=x,y=y) for x,y in a]),dict(id='A',name='Desvio',flow_role='acesso',flow_start='conexao',flow_end='saida',points=[dict(x=x,y=y) for x,y in b])],lane_blocks=[dict(id='obra',name='Bloqueio programado',mode='total',start_s=10,end_s=30,points=[dict(x=230,y=-6),dict(x=260,y=-6),dict(x=260,y=6),dict(x=230,y=6)])])
    net=TrafficNetwork([LineString(a).buffer(8),LineString(b).buffer(8),Point(150,0).buffer(20)],[],[],a,np.array([0.,400.]),s)
    sim=simulation.TrafficSim(net,s,lambda *a:'car',duration=35)
    report=sim.report();assert report['rerouted_at_nodes']>0 and report['flow_balance']['conserved']
    assert report['rear_collisions']==report['side_collisions']==0
    barrier=box(230,-6,260,6)
    for t in np.arange(10,30,.5):
        for c,h,vid,ident,j in sim.vehicles_ex(float(t)):
            from app.vehicle_safety import body
            assert body(c,h,4.6,1.8).intersection(barrier).area<1e-5


def test_direction_marks_cannot_reverse_node_oriented_route_but_legacy_marks_still_work():
    from app.direction_intervals import split_intervals
    r=dict(points=np.array([[0.,0.],[100.,0.]]),node_oriented=True)
    mark=SimpleNamespace(id='seta',start=SimpleNamespace(x=80,y=0),end=SimpleNamespace(x=20,y=0))
    rows,report=split_intervals([r],[mark]);assert report[0]['status']=='node_conflict'
    assert len(rows)==1 and np.array_equal(rows[0]['points'],r['points'])
    rows,report=split_intervals([{**r,'node_oriented':False}],[mark]);assert report[0]['status']=='applied'
    assert any(row.get('explicit_direction') is False for row in rows)
