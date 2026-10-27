import json
from types import SimpleNamespace
import numpy as np
import pytest
from shapely.geometry import box,Polygon,LineString
from app.models import Settings
from app.vehicle_motion import prepare_points,PROFILES
from app.vehicle_safety import PolygonSafety,body,LATERAL_CLEARANCE
from app.shoulder_probe import ShoulderProbe,envelope


def scene(obstacles=(),enabled=True,hatched=False):
    x=np.linspace(0,300,601);a=np.c_[x,np.full(len(x),-1.6)];b=np.c_[x[::-1],np.full(len(x),1.6)]
    paved=box(-20,-3.2,320,3.2);allowed=paved.difference(__import__('shapely').ops.unary_union(obstacles).buffer(.15))
    paths=[dict(p=p,d=np.linspace(0,300,len(p)),length=300,kinds=['main']) for p in [a,b]]
    sim=SimpleNamespace(s=Settings(heavy_shoulder_probe=enabled),net=SimpleNamespace(allowed=allowed,operational_pavement=paved,shoulder_envelope=envelope(paved,obstacles)),paths=paths,motion_points=[prepare_points(p['p']) for p in paths],blocks=[],time=0)
    sim.polygon_safety=PolygonSafety(sim);sim.shoulder_probe=ShoulderProbe(sim)
    v=dict(id=1,p=0,s=60.,v=8.,v0=8.,t='truck',L=12.,lc=None)
    w=dict(id=2,p=1,s=160.,v=8.,v0=8.,t='truck',L=12.,lc=None)
    return sim,v,w


def test_envelope_is_one_meter_from_pavement_not_shoulder_width_and_preserves_barriers_holes():
    p=Polygon([(0,-4),(100,-4),(100,4),(0,4)],holes=[[(40,-1),(60,-1),(60,1),(40,1)]])
    e=envelope(p,[box(70,-5,72,-3)])
    assert e.covers(box(10,-4.9,12,-4.1)) and not e.covers(box(10,-5.1,12,-4.1))
    assert not e.intersects(box(45,-.5,55,.5))
    assert not e.intersects(box(70,-4.8,72,-3.2))
    bridge=envelope(box(0,-4,100,4),[],bridges=box(30,-4,60,4))
    assert not bridge.covers(box(40,-4.8,50,-4.2))


@pytest.mark.parametrize('hatched',[False,True])
def test_heavy_encounter_uses_local_shoulder_with_safe_sweep_and_smooth_return(hatched):
    sim,v,w=scene(hatched=hatched);probe=sim.shoulder_probe
    assert probe.try_pair(v,w)
    e=probe.events[(1,0)][0];assert e['offset']<=1
    assert probe.offset(e,e['stations'][0])==0 and probe.offset(e,e['stations'][-1])==0
    for s in np.linspace(e['stations'][0],e['stations'][-1],161):
        assert probe.area.covers(probe.geometry(v,s,e,False))
        t=(s-v['s'])/8;other_s=w['s']+t*8
        assert probe.geometry(v,s,e).intersection(probe.geometry(w,other_s)).area<1e-7
    assert LATERAL_CLEARANCE==.3
    assert sim.net.allowed.bounds==(-20.,-3.2,320.,3.2)  # nenhuma ampliação da pista normal


def test_disabled_light_vehicle_barrier_and_insufficient_length_refuse():
    sim,v,w=scene(enabled=False);assert not sim.shoulder_probe.try_pair(v,w)
    sim,v,w=scene();v['t']='car';assert not sim.shoulder_probe.try_pair(v,w)
    sim,v,w=scene([box(60,-5,145,-2.9)]);assert not sim.shoulder_probe.try_pair(v,w)
    sim,v,w=scene();v['s']=270;w['s']=0;assert not sim.shoulder_probe.try_pair(v,w)


def test_replay_pose_matches_safety_and_does_not_slide_while_stopped():
    sim,v,w=scene();probe=sim.shoulder_probe;assert probe.try_pair(v,w)
    e=probe.events[(1,0)][0];v['s']=e['stations'][1]
    a=sim.polygon_safety.pose(v);b=probe.pose(v)
    assert np.allclose(a,b) and np.allclose(probe.pose(v,0),b)
    assert probe.pose({**v,'lc':dict(to=1)}) is None


def actual_network(enabled=True,obstacles=()):
    from app.traffic import TrafficNetwork
    s=Settings(heavy_shoulder_probe=enabled,hydrography=False,signage_detail='basic',derive_traffic_paths=False,route_directions={'0':'off'},traffic_density=4,traffic_speed_kmh=45,duration_s=12,
        route_alignments=[dict(id='r',name='Encontro genérico',points=[dict(x=0,y=0),dict(x=600,y=0)],lane_width_m=3.2,type='simples')])
    a=np.array([[0.,0.],[600.,0.]])
    net=TrafficNetwork([box(-30,-3.2,630,3.2)],list(obstacles),[],a,np.array([0.,600.]),s)
    return net,s


def test_actual_simulation_keeps_clearance_replays_probe_and_preserves_controls():
    from app.simulation import TrafficSim
    net,s=actual_network();sim=TrafficSim(net,s,lambda *a:'truck',duration=12)
    assert sim.spawned>0
    assert sim.shoulder_probe.events
    from shapely.geometry import Polygon
    observed=False
    for t in np.arange(0,12,.2):
        polys=[]
        for c,h,vid,identity,j in sim.vehicles_ex(float(t)):
            state=next(x for x in sim.state(float(t)) if x[0]==vid)
            v=dict(id=vid,p=state[1],s=state[2],t='truck')
            pose=sim.shoulder_probe.pose(v)
            if pose is not None:
                assert np.allclose(c,pose[0]) and np.allclose(h,pose[1]);observed|=abs(sim.shoulder_probe.offset(sim.shoulder_probe.event(v),v['s']))>.1
            assert net.shoulder_envelope.covers(body(c,h,12,3))
            p=body(c,h,12,3,.15)
            assert all(p.intersection(q).area<.002 for q in polys);polys.append(p)
    assert observed
    assert sim.report()['rear_collisions']==sim.report()['side_collisions']==0
    assert {1,2}&{c for t in np.arange(0,12,.2) for c in sim.indicators(float(t)).values()}


def test_curve_exception_does_not_allow_steering_failure_or_vehicle_wider_than_lane():
    sim,v,w=scene();probe=sim.shoulder_probe
    assert probe.curve_fallback(0,'truck',{'reasons':['esterco_excessivo']}) is None
    assert probe.curve_fallback(0,'car',{'reasons':['corpo_fora_da_pista']}) is None
    assert not probe.permits(0,'car')


def test_shoulder_hatch_does_not_expand_exception_to_its_full_width(tmp_path):
    from test_v1425_scene3d import project
    from app.render import Scene
    import ezdxf
    d,s=project(tmp_path)
    a=Scene.light(d,s);bounds=a.network.shoulder_envelope.bounds
    doc=ezdxf.readfile(d/'input.dxf');doc.layers.new('ACOSTAMENTO_EXISTENTE')
    h=doc.modelspace().add_hatch(dxfattribs={'layer':'ACOSTAMENTO_EXISTENTE'})
    h.paths.add_polyline_path([(500000,7799950),(500500,7799950),(500500,7799980),(500000,7799980)],is_closed=True)
    doc.saveas(d/'input.dxf');b=Scene.light(d,s)
    assert b.network.shoulder_envelope.bounds==bounds
    assert b.network.allowed.bounds==a.network.allowed.bounds
    assert b.network.shoulder_envelope.bounds[1]>=7799979  # bordo do pavimento=7799980


def test_curved_body_can_use_one_meter_but_not_an_impossible_steering_angle():
    from app.vehicle_motion import analyze_motion
    a=np.linspace(0,np.pi/2,161);p=np.c_[20*np.cos(a),20*np.sin(a)]
    v0=p[1]-p[0];v0/=np.linalg.norm(v0);v1=p[-1]-p[-2];v1/=np.linalg.norm(v1)
    pavement=LineString(np.vstack([p[0]-v0*15,p,p[-1]+v1*15])).buffer(1.8)
    sim,_,_=scene();sim.paths=[dict(p=p,d=prepare_points(p)[1],length=prepare_points(p)[1][-1],kinds=['main'])];sim.motion_points=[prepare_points(p)]
    sim.net=SimpleNamespace(allowed=pavement,operational_pavement=pavement,shoulder_envelope=envelope(pavement,[]))
    probe=ShoulderProbe(sim);audit=analyze_motion(p,'truck',pavement)
    assert 'corpo_fora_da_pista' in audit['reasons']
    result=probe.curve_fallback(0,'truck',audit)
    assert result and result['ok'] and probe.permits(0,'truck')


def test_works_block_rejects_exception_without_disabling_it():
    sim,v,w=scene();sim.blocks=[SimpleNamespace(active=lambda t:True,poly=box(50,-5,200,5))]
    assert not sim.shoulder_probe.try_pair(v,w)
    assert sim.shoulder_probe.enabled


def test_probe_refuses_waiting_person_and_current_step_reserves_pedestrians():
    sim,v,w=scene();person=dict(id=10,route=dict(kind='calcada',height=0))
    sim.pedestrians=SimpleNamespace(agents=[person],pose=lambda a:(np.array([100.,-3.3]),np.array([1.,0.])))
    assert not sim.shoulder_probe.try_pair(v,w)
    sim,v,w=scene();assert sim.shoulder_probe.try_pair(v,w)
    e=sim.shoulder_probe.events[(1,0)][0];v['s']=e['stations'][1]
    c,h=sim.shoulder_probe.pose(v);target=c+h*5
    sim.pedestrians=SimpleNamespace(agents=[person],pose=lambda a:(target,np.array([1.,0.])))
    sim.paths[0]['length']=300
    limited=sim.polygon_safety.resolve([v],[(10.,8.)])
    assert limited[0][1]<8


def test_second_maneuver_preserves_first_pose_for_video_replay():
    sim,v,w=scene();probe=sim.shoulder_probe;assert probe.try_pair(v,w)
    first=probe.events[(1,0)][0];old={**v,'s':first['stations'][1]};expected=probe.pose(old)
    v['s']=first['stations'][-1]+5;w['s']=300-(v['s']+80);sim.time=20
    assert probe.try_pair(v,w) and len(probe.events[(1,0)])==2
    assert np.allclose(probe.pose(old),expected)
    assert probe.report()['maneuvers']==2


def test_pedestrian_already_present_prevents_heavy_admission_without_other_vehicles():
    sim,v,w=scene();c,_=sim.polygon_safety.pose(v)
    person=dict(id=10,route=dict(kind='calcada',height=0))
    sim.pedestrians=SimpleNamespace(agents=[person],pose=lambda a:(c,np.array([1.,0.])))
    assert not sim.polygon_safety.admission(v,[])
    person['route']=dict(kind='passarela',height=6)
    assert sim.polygon_safety.admission(v,[])
