import numpy as np
import pytest
from shapely.geometry import Point,Polygon
from app.models import Settings
from app.simulation import TrafficSim
from app.transport import Transport
from app.pedestrian_traffic import PedestrianTraffic,without_vehicles
from app.rail_smoke import particles
from test_v1426_transport import network,rail,signal


def settings(**kw):
    data=dict(derive_traffic_paths=False,hydrography=False,duration_s=70,traffic_density=3,traffic_speed_kmh=45,pedestrian_seed=21,
              crosswalks=[dict(id='faixa',a=dict(x=200,y=-12),b=dict(x=200,y=12))])
    data.update(kw);return Settings(**data)


def test_pedestrian_crossings_hold_real_vehicles_and_have_no_body_overlap():
    s=settings();n=network(s);sim=TrafficSim(n,s,lambda *a:'car',duration=70)
    report=sim.pedestrians.report();assert report['admitted']>0 and report['waiting_steps']>0
    assert report['vehicle_collisions']==report['people_collisions']==report['train_collisions']==0
    assert report['history_bytes']<32*1024*1024
    for t in np.arange(0,70,.1):
        people=sim.pedestrians.state(float(t));cars=sim.vehicle_body_state(float(t))
        for i,p in enumerate(people):
            circle=Point(p['p']).buffer(.3)
            for car in cars:assert not circle.intersects(Polygon(car['polygon']))
            for other in people[i+1:]:assert Point(other['p']).distance(Point(p['p']))>=.69


def test_informal_path_through_road_is_rejected_and_sidewalk_seed_reproduces():
    s=settings(crosswalks=[],pedestrian_paths=[dict(id='bad',points=[dict(x=200,y=-30),dict(x=200,y=30)]),dict(id='good',points=[dict(x=20,y=20),dict(x=200,y=20)])])
    n=network(s);a=without_vehicles(s,n,Transport(s,n),10);b=without_vehicles(s,n,Transport(s,n),10)
    assert a.rejected==1 and len(a.routes)==1 and a.routes[0]['kind']=='calcada'
    assert a.state(8.1)==b.state(8.1)
    assert all(not n.allowed.covers(Point(p['p'])) for p in a.state(8.1))


def test_near_train_prevents_crossing_and_tail_clears_before_admission():
    s=settings(railways=[{**rail(start_s=0,speed_kmh=30,min_wagons=5,max_wagons=5),'points':[dict(x=0,y=0),dict(x=600,y=0)]}])
    n=network(s);transport=Transport(s,n);control=without_vehicles(s,n,transport,70)
    assert control.waits>0 and control.train_collisions==0
    for t in np.arange(0,70,.2):
        for person in control.state(float(t)):
            if person['state']=='crossing':assert control.railway_clear(control.routes[0],float(t),0)


def test_three_phase_pedestrian_admission_occurs_only_in_walk_phase():
    s=settings(traffic_signals=[signal(phases=3,lanes_a=6,lanes_b=6)],traffic=False)
    n=network(s);c=PedestrianTraffic(s,n,Transport(s,n));previous=set()
    for t in np.arange(0,150,.2):
        c.update([],float(t));c.check([],float(t));current={a['id'] for a in c.agents if a['state']=='crossing'}
        if current-previous:assert c.transport.signal_state(c.transport.signals[0],float(t))[2]
        previous=current
    assert c.admitted>0


@pytest.mark.parametrize('heading',[[1.,0.],[-1.,0.],[.6,.8]])
def test_smoke_never_goes_forward_is_deterministic_and_can_be_disabled(heading):
    part=dict(id='0:1:0',p=np.array([120.,300.]),heading=np.array(heading),locomotive=True,speed_mps=12)
    for t in [0,.1,3.1,7.2]:
        rows=particles([part],t)
        assert len(rows)==10
        for p in rows:assert np.dot(p['p']-part['p'],part['heading'])<=0 and np.isfinite(p['p']).all()
        np.testing.assert_array_equal(rows[0]['p'],particles([part],t)[0]['p'])
    assert not particles([part],1,False)


def test_passarela_uses_clearance_above_road_and_does_not_stop_traffic():
    s=settings(crosswalks=[],pois=[dict(id='b',title='Passarela',kind='passarela',x=200,y=0,bridge_span_m=40)])
    n=network(s);control=without_vehicles(s,n,Transport(s,n),10)
    assert control.routes[0]['kind']=='passarela' and control.routes[0]['height']>=5.5
    assert control.admitted>0 and not control.routes[0]['conflicts']


def test_crosswalk_waiting_position_on_rail_is_rejected_instead_of_spawning_people():
    s=settings(railways=[rail(start_s=0)]);n=network(s);c=PedestrianTraffic(s,n,Transport(s,n))
    assert c.rejected==1 and not c.routes and 'ferrovia' in c.warnings[0]


def test_pedestrian_configuration_invalidates_traffic_but_smoke_only_presentation(tmp_path):
    from app.dependencies import revisions
    s=settings();a=revisions(tmp_path,s.model_dump());b=revisions(tmp_path,{**s.model_dump(),'pedestrian_seed':22})
    assert a['traffic']!=b['traffic']
    c=revisions(tmp_path,{**s.model_dump(),'rail_smoke':False});assert a['traffic']==c['traffic'] and a['scene3d']!=c['scene3d']


def test_extremely_short_passarela_is_rejected_before_people_appear_on_road_supports():
    s=settings(crosswalks=[],pois=[dict(id='b',title='Passarela',kind='passarela',x=200,y=0,bridge_span_m=10)])
    n=network(s);control=PedestrianTraffic(s,n,Transport(s,n))
    assert control.rejected==1 and not control.routes and 'Vão' in control.warnings[0]


@pytest.mark.parametrize('value',[None,float('nan'),float('inf')])
def test_smoke_invalid_clock_never_generates_invalid_coordinates(value):
    assert not particles([],value)


def test_crossing_sidewalk_agents_yield_without_colliding_or_getting_permanently_stuck():
    s=settings(crosswalks=[],pedestrian_paths=[dict(id='a',points=[dict(x=180,y=20),dict(x=220,y=20)],people_per_100m=15),dict(id='b',points=[dict(x=200,y=13),dict(x=200,y=50)],people_per_100m=15)])
    n=network(s);control=without_vehicles(s,n,Transport(s,n),90)
    assert control.arrived>5 and control.people_collisions==0
    assert control.report()['history_bytes']<32*1024*1024


def test_smoke_advects_backwards_in_world_for_a_straight_moving_train():
    for h in (np.array([1.,0.]),np.array([-1.,0.])):
        speed=12.;start=dict(id='0:0:0',p=np.array([0.,0.]),heading=h,locomotive=True,speed_mps=speed)
        end={**start,'p':start['p']+h*speed*.01}
        a=particles([start],.2)[0]['p'];b=particles([end],.21)[0]['p']
        assert (b-a)@h<0


def test_full_one_hundred_wagon_tail_keeps_people_waiting_then_releases():
    s=settings(duration_s=300,railways=[{**rail(start_s=0,speed_kmh=30,min_wagons=100,max_wagons=100),'points':[dict(x=0,y=0),dict(x=600,y=0)]}])
    n=network(s);control=without_vehicles(s,n,Transport(s,n),300)
    assert all(row['state']=='waiting' for row in control.state(60))
    assert control.admitted>0 and control.train_collisions==0
