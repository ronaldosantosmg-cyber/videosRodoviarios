"""Frente/traseira, continuidade, classe de veículo e restrições explícitas."""
import collections
from types import SimpleNamespace
import numpy as np
import pytest
from shapely.geometry import Polygon,box
from app.vehicle_motion import analyze_motion,axle_geometry,prepare_points
from app.traffic import TrafficNetwork,tangent
from app.simulation import TrafficSim


def arc(radius):
    a=np.linspace(-np.pi/2,np.pi/2,161);return np.c_[radius*np.cos(a),radius*np.sin(a)]


@pytest.mark.parametrize('bad',[None,[],[[0,0]],[[0,0],[0,0]],[[0,0],[float('nan'),0]],[[0,0],[float('inf'),0]]])
def test_invalid_motion_is_rejected(bad):
    assert not analyze_motion(bad)['ok']


def test_front_and_rear_coordinates_and_unit_heading():
    g=axle_geometry([[0,0],[100,0]],'car',np.array([10.,50.,90.]))
    assert np.allclose(g['front'][:,0]-g['rear'][:,0],4.5)
    assert np.allclose(g['front_axle'][:,0]-g['rear_axle'][:,0],2.7)
    assert np.allclose(np.linalg.norm(g['heading'],axis=1),1.)


@pytest.mark.parametrize('points',[np.array([[0,0],[50,0],[50,50]]),np.array([[0,0],[10,0],[8,0],[30,0]]),np.array([[0,0],[10,10],[0,10],[10,0]])])
def test_sharp_turn_reversal_and_crossing_are_rejected(points):
    result=analyze_motion(points);assert not result['ok'];assert result['reasons']


def test_close_zigzag_is_rejected_but_long_smooth_lane_change_allowed():
    x=np.linspace(0,80,401);zig=np.c_[x,5*np.sin(x/2)]
    assert not analyze_motion(zig)['ok']
    a=x/80;gentle=np.c_[x,3.5*(a*a*(3-2*a))]
    assert analyze_motion(gentle)['ok']


def test_real_vehicle_dimensions_change_steering_feasibility():
    assert analyze_motion(arc(6),'car')['ok']
    result=analyze_motion(arc(6),'truck')
    assert not result['ok'] and 'esterco_excessivo' in result['reasons']


def test_front_rear_body_must_stay_on_pavement():
    pts=np.array([[5.,0.],[95.,0.]])
    assert analyze_motion(pts,'car',box(0,-2,100,2))['ok']
    assert not analyze_motion(pts,'truck',box(0,-2,100,2))['ok']


def test_legitimate_smooth_return_and_roundabout_are_not_blanket_removed():
    assert analyze_motion(arc(15),'car')['ok']
    a=np.linspace(0,2*np.pi,401);circle=np.c_[20*np.cos(a),20*np.sin(a)]
    assert analyze_motion(circle)['ok']


def connector_fixture():
    net=TrafficNetwork.__new__(TrafficNetwork)
    net.nodes=[(np.array([0.,0.]),0)];net.no_connect=Polygon();net.bridges=Polygon();net.allowed=box(-100,-100,100,100)
    net.rejected_connectors=collections.Counter();net.rejected_nodes=set()
    a=np.c_[np.linspace(-30,-4,40),np.zeros(40)];b=np.c_[np.linspace(4,30,40),np.zeros(40)]
    def e(p,base):return {'p':p,'t':tangent(p),'end':0,'start':0,'base':base,'origin':base}
    return net,e(a,0),e(b,1)


def test_forced_connector_cannot_reverse_explicit_route_direction():
    net,a,b=connector_fixture();a.update(route='r',route_dir='f');b.update(route='r',route_dir='r')
    assert net.connector(a,b,force=True) is None
    assert net.rejected_connectors['contramao_rota']==1


def test_forced_connector_cannot_bypass_no_connection_zone():
    net,a,b=connector_fixture();net.no_connect=box(-2,-2,2,2)
    assert net.connector(a,b,force=True) is None


def test_zero_gap_collinear_connector_does_not_generate_loop():
    net,a,b=connector_fixture();a['p'][-1]=[0.,0.];b['p'][0]=[0.,0.]
    a['t']=tangent(a['p']);b['t']=tangent(b['p'])
    connector=net.connector(a,b)
    assert connector is not None and np.allclose(connector,[[0,0],[0,0]])


def test_vehicle_pose_is_continuous_between_samples_and_reports_front_rear():
    p=np.array([[0.,0.],[50.,0.],[100.,0.]])
    d=np.array([0.,50.,100.]);path={'p':p,'d':d,'t':tangent(p),'length':100.,'kinds':['main']}
    net=SimpleNamespace(paths=[path],edges=[],allowed=box(-20,-10,120,10))
    s=SimpleNamespace(traffic_speed_kmh=30,traffic_density=1,duration_s=2,lane_blocks=[],curve_speed=True)
    sim=TrafficSim(net,s,lambda *a:'car',duration=2)
    x0=sim._sample_pose(0,10.1)[0];x1=sim._sample_pose(0,10.2)[0]
    assert np.linalg.norm(x1-x0)==pytest.approx(.1)
    for record in sim.vehicle_body_state(1):assert np.linalg.norm(np.array(record['front'])-record['rear'])==pytest.approx(4.5)
    assert sim.report()['motion_profiles']['0:car']['ok']


def test_unsafe_class_is_not_spawned_on_tight_curve():
    points=arc(6);p,d=prepare_points(points);path={'p':p,'d':d,'t':tangent(p),'length':float(d[-1]),'kinds':['return']}
    net=SimpleNamespace(paths=[path],edges=[])
    settings=SimpleNamespace(traffic_speed_kmh=20,traffic_density=3,duration_s=3,lane_blocks=[],curve_speed=True)
    sim=TrafficSim(net,settings,lambda *a:'truck',duration=3)
    assert sim.spawned==0 and sim.report()['motion_blocked_vehicles']>0


def test_explicit_crossing_prohibition_beats_forced_or_free_mode():
    net,a,b=connector_fixture();net.main=[];net.islands=[];net.warnings=[]
    p=np.c_[np.linspace(-20,20,100),np.zeros(100)];net.edges=[dict(a,p=p,disabled=False),dict(b,disabled=False)]
    net.connectors={(0,1):p};net.connections={0:[1],1:[]};net.forced={(0,1)}
    zone=SimpleNamespace(kind='point',point=SimpleNamespace(x=0.,y=0.),radius_m=2.,mode='deny')
    net.s=SimpleNamespace(median_crossing='free',crossing_zones=[zone])
    net.crossing_rules()
    assert (0,1) not in net.connectors and net.edges[0]['disabled']


def test_long_lane_change_is_valid_but_short_sharp_shift_is_refused():
    p=np.c_[np.linspace(0,200,401),np.zeros(401)];q=p+[0,3.5]
    paths=[{'p':a,'d':np.linspace(0,200,401),'t':tangent(a),'length':200.,'kinds':['main']} for a in [p,q]]
    net=SimpleNamespace(paths=paths,edges=[],allowed=box(-20,-10,220,15))
    s=SimpleNamespace(traffic_speed_kmh=50,traffic_density=0,duration_s=1,lane_blocks=[],curve_speed=True)
    sim=TrafficSim(net,s,lambda *a:'car',duration=1)
    v={'p':0,'s':20.,'t':'car'}
    assert sim.maneuver_valid(v,1,50.)
    assert not sim.maneuver_valid(v,1,8.)
    assert not sim.maneuver_valid({**v,'s':195.},1,50.)


def test_curve_speed_envelope_respects_lateral_acceleration():
    from app.simulation import curve_envelope
    p,d=prepare_points(arc(15));speed=curve_envelope(p,d)
    assert np.max(speed[15:-15])<7.0  # sqrt(2.2 * 15) ≈ 5.75 m/s, com transições nas pontas.


def test_stopped_vehicle_does_not_slide_sideways_to_finish_lane_change():
    lc={'elapsed':1.,'duration':4.,'travel_m':24.}
    TrafficSim.advance_maneuver(lc,0.,.2);assert lc['elapsed']==1.
    TrafficSim.advance_maneuver(lc,float('nan'),.2);assert lc['elapsed']==1.
    TrafficSim.advance_maneuver(lc,1.,.2);assert 1.<lc['elapsed']<=1.2


def test_front_rear_profiles_match_rendered_vehicle_dimensions():
    from app.vehicle_motion import PROFILES
    from app.visual import TYPES
    for key,profile in PROFILES.items():assert tuple(profile[:2])==(TYPES[key]['L'],TYPES[key]['B'])


def test_organic_heading_and_forward_motion_on_continuous_curve():
    p,d=prepare_points(arc(25));path={'p':p,'d':d,'t':tangent(p),'length':float(d[-1]),'kinds':['return']}
    net=SimpleNamespace(paths=[path],edges=[])
    settings=SimpleNamespace(traffic_speed_kmh=20,traffic_density=2,duration_s=5,lane_blocks=[],curve_speed=True)
    sim=TrafficSim(net,settings,lambda *a:'car',duration=5)
    previous={};checked=0
    for t in np.linspace(0,5,151):
        for pos,heading,vid,_,_ in sim.vehicles_ex(float(t)):
            if vid in previous:
                p0,h0=previous[vid];assert np.dot(pos-p0,heading)>=-1e-5
                assert np.dot(h0,heading)>.995;checked+=1
            previous[vid]=(pos,heading)
    assert checked>30


def test_legacy_animation_has_same_class_audit_and_no_zero_division():
    net,a,b=connector_fixture();p,d=prepare_points(arc(6))
    net.paths=[{'p':p,'d':d,'t':tangent(p),'length':float(d[-1]),'kinds':['return']}]
    assert list(net.vehicles_ex(1,0))==[]
    assert list(net.vehicles_ex(1,10,lambda *a:'truck'))==[]
    assert net.legacy_motion_cache[(0,'truck')]['ok'] is False
