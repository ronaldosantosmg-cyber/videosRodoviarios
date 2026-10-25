import numpy as np
import pytest
from shapely.geometry import box,Polygon
from app.models import Settings
from app.traffic import TrafficNetwork
from app.simulation import TrafficSim
from app.alternating_traffic import AlternatingTraffic


def network(settings):
    p=np.array([[0.,0.],[600.,0.]])
    return TrafficNetwork([box(-30,-12,630,12)],[],[dict(points=p)],p,np.array([0.,600.]),settings)

def configuration(**kw):
    data=dict(route_alignments=[dict(id='r',name='Qualquer projeto',points=[dict(x=0,y=0),dict(x=600,y=0)],type='simples',taper_m=60)],derive_traffic_paths=False,route_directions={'0':'off'},hydrography=False,traffic_density=4,duration_s=90,traffic_speed_kmh=50)
    data.update(kw);return Settings(**data)


def assert_polygon_clearance(sim,duration):
    previous={};samples=0
    for t in np.arange(0,duration,.5):
        shapes=sim.vehicle_body_state(float(t));polys=[Polygon(s['collision_envelope']) for s in shapes]
        for i,p in enumerate(polys):
            assert p.is_valid and np.isfinite(p.bounds).all()
            for q in polys[i+1:]:assert p.intersection(q).area<.002,(t,p.bounds,q.bounds)
        for vid,path,s,_,_ in sim.state(float(t)):
            key=(vid,path)
            if key in previous:assert s>=previous[key]-.002
            previous[key]=s;samples+=1
    assert samples>50


def test_explicit_opposite_lane_endpoints_are_portals_without_a_uturn():
    net=network(configuration());assert len(net.paths)==2
    assert all(not links for links in net.connections.values())
    assert not net.rejected_nodes
    sim=TrafficSim(net,configuration(),lambda *a:'car',duration=20)
    assert sim.report()['rear_collisions']==0 and sim.report()['min_gap_m']>=1.99
    assert_polygon_clearance(sim,20)


@pytest.mark.parametrize('lane_width',[3.3,3.5])
def test_wide_trucks_observe_half_meter_free_distance_and_use_both_directions(lane_width):
    s=configuration();s.route_alignments[0].lane_width_m=lane_width;net=network(s);sim=TrafficSim(net,s,lambda *a:'truck',duration=90)
    report=sim.report();assert report['rear_collisions']==0 and report['min_gap_m']>=1.99
    assert report['lateral_buffer_per_vehicle_m']==.25 and report['lateral_clearance_m']==.5
    if lane_width<3.5:assert report['narrow_corridor_admission_holds']>0
    assert {data[0] for data in sim.info.values()}=={0,1}
    assert_polygon_clearance(sim,90)


def test_pare_siga_never_reverses_while_tail_is_in_shared_corridor():
    s=configuration(alternating_zones=[dict(id='z',route_id='r',start_m=180,end_m=340,release_s=10)])
    net=network(s);sim=TrafficSim(net,s,lambda *a:'car',duration=90)
    assert len(net.paths)==2 and all(sim.alternating.gates)
    assert sim.report()['rear_collisions']==0 and sim.alternating.report()['phase_changes']>3
    assert 3 in {code for t in range(90) for code in sim.indicators(t).values()}
    assert_polygon_clearance(sim,90)
    for t in np.arange(0,90,.2):
        occupants=set()
        for vid,path,station,_,_ in sim.state(float(t)):
            length=4.5
            for gate in sim.alternating.gates[path]:
                if station+length/2>gate['a']+.03 and station-length/2<gate['b']-.03:occupants.add(gate['direction'])
        assert len(occupants)<=1,(t,occupants)
    # Estado isolado demonstra que 10 s não significam inverter com uma cauda presente.
    controller=AlternatingTraffic(s,net);gate=controller.gates[0][0];direction=gate['direction'];z=controller.zones[0];z['phase']=direction
    v=dict(id=1,p=0,s=gate['b']+1,L=18.6,lc=None)
    controller.update([v],0);controller.update([v],10)
    assert z['clearing'] and z['phase']==direction
    controller.update([],11);assert not z['clearing'] and z['phase']!=direction


def test_actual_overtakes_have_indicators_and_keep_lateral_reservations():
    from types import SimpleNamespace
    x=np.linspace(0,600,601);paths=[]
    for i,y in enumerate([0.,4.]):
        p=np.c_[x,np.full(len(x),y)];paths.append(dict(p=p,d=x.copy(),length=600.,kinds=['main'],route='overtake',route_dir='f',route_lane=i,lane_change='safe',route_start_m=0.,route_end_m=600.,links=[(('e',i),0.,600.)]))
    net=SimpleNamespace(paths=paths,edges=[dict(kind='main',level=0)]*2,allowed=box(-30,-8,630,12))
    s=Settings(traffic_density=3,traffic_speed_kmh=80,duration_s=90)
    sim=TrafficSim(net,s,lambda kinds,identity:'truck' if identity[1]%4==0 else 'car',duration=90)
    assert sim.lane_changes>0 and {1,2}&{code for t in np.arange(0,90,.2) for code in sim.indicators(float(t)).values()}
    assert sim.report()['rear_collisions']==sim.report()['side_collisions']==0
    assert_polygon_clearance(sim,90)


def test_vehicle_wider_than_selected_driving_band_cannot_enter():
    base=configuration();r=base.route_alignments[0].model_dump();r['cross_sections']=[dict(id='narrow',start_m=0,end_m=600,left=[dict(kind='pista',width_m=2.5)],right=[dict(kind='pista',width_m=2.5)])]
    s=configuration(route_alignments=[r]);sim=TrafficSim(network(s),s,lambda *a:'truck',duration=3)
    assert sim.report()['vehicles']==0 and sim.report()['motion_blocked_vehicles']>0
