import json
from pathlib import Path
import numpy as np
import pytest
from shapely.geometry import box,Polygon,LineString
from app.models import Settings
from app.traffic import TrafficNetwork
from app.flow_terminals import terminal_offsets
from app.swept_inspection import inspect
from app.classic_traffic import ClassicTraffic
from app.simulation import TrafficSim


def network(settings,axis=None,roads=None,barriers=(),medians=()):
    p=np.array([[0.,0.],[600.,0.]]) if axis is None else axis
    return TrafficNetwork([box(-20,-30,650,60)] if roads is None else roads,list(barriers)+list(medians),[dict(points=p,role='axis',layer='EIXO')],p,np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))],settings,median_obstacles=medians)


def branch_settings(level=0,**kw):
    return Settings(hydrography=False,signage_detail='basic',min_route_segment_m=50,route_alignments=[dict(id='r',name='Retorno',type='unico',flow_role='retorno',flow_start='conexao',flow_end='saida',level=level,points=[dict(x=x,y=y) for x,y in [(300,0),(320,0),(360,10),(420,25),(600,25)]])],**kw)


def test_typed_return_contact_splits_principal_and_receives_vehicles():
    s=branch_settings();n=network(s)
    pairs=[(a,b) for a,outs in n.connections.items() for b in outs if n.edges[a].get('native_axis') and n.edges[b].get('route')=='r']
    assert pairs and any(any(b in p['edges'] for a,b in pairs) for p in n.paths)
    sim=TrafficSim(n,s.model_copy(update={'duration_s':20}),lambda *a:'car',duration=20)
    assert sim.spawned and sim.report()['flow_balance']['conserved']


def test_contact_at_different_level_does_not_create_crossing():
    n=network(branch_settings(level=1))
    assert not [(a,b) for a,outs in n.connections.items() for b in outs if n.edges[a].get('native_axis') and n.edges[b].get('route')=='r']


def test_external_portals_are_five_meters_inside_pavement_even_axis_overhangs():
    p=np.array([[-40.,0.],[440.,0.]])
    n=network(Settings(hydrography=False,signage_detail='basic'),p,[box(0,-6,400,6)])
    assert n.paths
    for path in n.paths:
        assert path['terminal_inset_applied']
        assert sorted([float(path['p'][0,0]),float(path['p'][-1,0])])==pytest.approx([5,395],abs=.05)
        assert path['links'][0][1]==0 and path['links'][-1][2]==pytest.approx(path['length'],abs=.01)
    sim=TrafficSim(n,Settings(duration_s=3,traffic_route_only=True),lambda *a:'car',duration=3)
    assert sim.spawned and all(5-.05<=p[0]<=395+.05 for t in np.arange(0,3,.2) for p,*_ in sim.vehicles_ex(float(t)))


def test_portal_trim_keeps_internal_node_and_physical_link_offsets():
    n=network(branch_settings())
    connected=[p for p in n.paths if any(n.edges[e].get('route')=='r' for e in p['edges']) and len(p['edges'])>1]
    assert connected
    for path in connected:
        assert len(path['links'])==len(path['link_offsets'])
        assert all(b>=a for _,a,b in path['links'])
        assert any(identity[0]=='c' for identity,_,_ in path['links'])
        assert all(abs(left[2]-right[1])<.05 for left,right in zip(path['links'],path['links'][1:]))


def test_classic_ignores_barriers_but_keeps_medians_and_never_reenables_manual_shutdown():
    barrier=box(295,-30,305,30)
    classic=Settings(traffic_classic=True,hydrography=False,signage_detail='basic',traffic_density=2)
    n=network(classic,barriers=[barrier]);assert any(LineString(p['p']).intersects(barrier) for p in n.paths)
    med=network(classic,medians=[barrier]);assert all(not LineString(p['p']).intersects(barrier) for p in med.paths)
    off=network(classic.model_copy(update={'route_directions':{'0':'off'}}));assert not off.paths
    sim=ClassicTraffic(n,classic,lambda *a:'car',duration=3)
    assert list(sim.vehicles_ex(1)) and sim.report()['collision_free'] is None and sim.report()['checks']==['canteiros','integridade_numerica']
    assert not Settings().traffic_classic


def test_classic_without_hatch_is_bounded_to_selected_axes_and_density_is_effective():
    low=Settings(traffic_classic=True,hydrography=False,signage_detail='basic',traffic_density=.2)
    n=network(low,roads=[]);assert n.paths
    a=ClassicTraffic(n,low,lambda *args:'car');b=ClassicTraffic(n,low.model_copy(update={'traffic_density':8}),lambda *args:'car')
    assert len(list(b.vehicles_ex(1)))>len(list(a.vehicles_ex(1)))
    assert n.allowed.area<50000


def test_swept_envelope_reports_real_body_conflicts_without_mutating_geometry():
    points=np.array([[0.,0.],[100.,0.],[100.,100.]])
    original=points.copy();allowed=LineString(points).buffer(2)
    r=inspect(points,allowed,'truck18',100,40)
    assert r['outside_samples']>0 and r['technical_only'] and len(r['bodies'])<=102
    assert all(np.isfinite(b['polygon']).all() for b in r['bodies'])
    np.testing.assert_array_equal(points,original)
    straight=inspect(np.array([[0.,0.],[200.,0.]]),box(-20,-3,220,3),'truck18',100,40)
    assert straight['outside_samples']==0


@pytest.mark.parametrize('points,station',[(np.array([[0.,0.],[float('nan'),0.]]),5),(np.array([[0.,0.],[10.,0.]]),float('inf')),(np.array([[0.,0.],[0.,0.]]),0)])
def test_swept_rejects_nonfinite_and_degenerate(points,station):
    with pytest.raises(ValueError):inspect(points,box(-20,-20,20,20),station=station)


def test_deleting_an_automatic_return_node_preserves_principal_and_never_retargets():
    from app.render import connection_data
    s=branch_settings();n=network(s);data=connection_data(n)
    link=next(c for c in data['connections'] if n.raw_info[c['from']].get('native_axis') and n.raw_info[c['to']].get('route')=='r')
    rule=dict(id='delete-node',name='Nó removido',a=dict(zip(('x','y'),link['a'])),b=dict(zip(('x','y'),link['b'])),from_key=n.raw_info[link['from']]['origin_key'],to_key=n.raw_info[link['to']]['origin_key'],action='deny')
    deleted=network(s.model_copy(update={'connection_rules':[__import__('app.models',fromlist=['ConnectionRule']).ConnectionRule(**rule)]}))
    assert deleted.rule_report[0]['applied']
    assert deleted.paths and any(all(deleted.edges[e].get('native_axis') for e in p['edges']) for p in deleted.paths)
    assert not any(any(deleted.edges[e].get('route')=='r' for e in p['edges']) for p in deleted.paths)
    rule['to_key']='0'*64
    untouched=network(s.model_copy(update={'connection_rules':[__import__('app.models',fromlist=['ConnectionRule']).ConnectionRule(**rule)]}))
    assert not untouched.rule_report[0]['applied'] and any(any(untouched.edges[e].get('route')=='r' for e in p['edges']) for p in untouched.paths)


def test_explicit_node_reuses_valid_contact_without_creating_a_duplicate_shortcut():
    from app.render import connection_data
    from app.models import ConnectionRule
    s=branch_settings();n=network(s);c=next(c for c in connection_data(n)['connections'] if n.raw_info[c['from']].get('native_axis') and n.raw_info[c['to']].get('route')=='r')
    rule=ConnectionRule(id='edit',action='force',a=dict(zip(('x','y'),c['a'])),b=dict(zip(('x','y'),c['b'])),from_key=n.raw_info[c['from']]['origin_key'],to_key=n.raw_info[c['to']]['origin_key'],share_pct=20)
    edited=network(s.model_copy(update={'connection_rules':[rule]}))
    assert edited.rule_report[0]['existing'] and len(edited.paths)==len(n.paths)
    assert len([(i,j) for i,js in edited.connections.items() for j in js if edited.edges[i].get('native_axis') and edited.edges[j].get('route')=='r'])==1


@pytest.mark.parametrize('vehicle',['truck18','long30'])
def test_heavy_body_can_enter_and_exit_short_paved_portals_without_crossing_boundary(vehicle):
    p=np.array([[-40.,0.],[440.,0.]]);s=Settings(duration_s=30,traffic_route_only=True,hydrography=False,signage_detail='basic')
    n=network(s,p,[box(0,-6,400,6)]);sim=TrafficSim(n,s,lambda *args:vehicle,duration=30)
    assert sim.spawned and sum(sim.exited_by_path)>0 and sim.report()['flow_balance']['conserved']
    seen=0
    for t in np.arange(0,30,.5):
        polygons=[Polygon(shape['polygon']) for shape in sim.vehicle_body_state(float(t))]
        for i,polygon in enumerate(polygons):
            assert box(0,-6,400,6).covers(polygon);seen+=1
            assert all(polygon.intersection(other).area<1e-6 for other in polygons[i+1:])
    assert seen>20
