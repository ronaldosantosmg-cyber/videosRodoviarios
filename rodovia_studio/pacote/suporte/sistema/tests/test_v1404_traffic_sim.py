import numpy as np
from types import SimpleNamespace
from app.models import RouteAlignment, Point, LaneChangeSection
from app.simulation import TrafficSim


def _sim_with_path(sections=None, mode='marked'):
    sim=TrafficSim.__new__(TrafficSim)
    sim.paths=[{
        'length':1000.0,'route':'r1','route_dir':'f','route_lane':0,
        'route_start_m':0.0,'route_end_m':1000.0,'lane_change':mode,
        'lane_change_sections':sections or []
    }]
    sim.link_of=[[(('e',0),0.0,1000.0)]]
    sim.starts=[[0.0]]
    sim.safety_interventions=0
    return sim


def test_route_lane_change_defaults_are_conservative():
    r=RouteAlignment(name='Rota 1',points=[Point(x=0,y=0),Point(x=1000,y=0)])
    assert r.lane_change=='marked'
    assert r.lane_change_sections==[]


def test_lane_change_entire_manoeuvre_must_fit_allowed_window():
    allow={'start_m':100,'end_m':300,'mode':'allow'}
    sim=_sim_with_path([allow])
    assert sim.lane_change_window_allowed(0,120,100) is True
    assert sim.lane_change_window_allowed(0,250,100) is False  # começa permitido, termina fora


def test_deny_zone_blocks_even_safe_mode():
    deny={'start_m':180,'end_m':220,'mode':'deny'}
    sim=_sim_with_path([deny],mode='safe')
    assert sim.lane_change_window_allowed(0,100,50) is True
    assert sim.lane_change_window_allowed(0,150,100) is False


def test_hard_separation_repairs_overlap_before_frame_is_recorded():
    sim=_sim_with_path([],mode='off')
    v1={'id':1,'p':0,'s':100.0,'v':20.0,'L':4.6,'li':0,'lc':None}
    v2={'id':2,'p':0,'s':103.0,'v':10.0,'L':4.6,'li':0,'lc':None}
    sim.enforce_hard_separation([v1,v2])
    gap=v2['s']-v1['s']-(v1['L']+v2['L'])/2
    assert gap >= sim.HARD_GAP-1e-6
    assert sim.safety_interventions > 0


def test_route_lane_change_section_orders_values():
    z=LaneChangeSection(start_m=300,end_m=100,mode='allow')
    assert z.start_m==100 and z.end_m==300

def test_safe_overtake_starts_only_to_adjacent_lane_when_window_is_allowed():
    sim=TrafficSim.__new__(TrafficSim)
    base={'length':1000.0,'route':'r1','route_dir':'f','route_start_m':0.0,'route_end_m':1000.0,
          'lane_change':'marked','lane_change_sections':[{'start_m':0,'end_m':1000,'mode':'allow'}]}
    sim.paths=[dict(base,route_lane=0),dict(base,route_lane=1)]
    from shapely.geometry import box
    from types import SimpleNamespace
    for k,path in enumerate(sim.paths):
        path['p']=np.c_[np.linspace(0,1000,1001),np.full(1001,k*3.5)]
        path['d']=np.linspace(0,1000,1001);path['t']=np.tile([1.,0.],(1001,1))
    sim.net=SimpleNamespace(allowed=box(-20,-10,1020,15));sim.motion_cache={};sim.lc_blocked_geometry=0

    from app.vehicle_motion import prepare_points
    from app.vehicle_safety import PolygonSafety
    sim.motion_points=[prepare_points(p['p']) for p in sim.paths]
    sim.polygon_safety=PolygonSafety(sim);sim.lane_events=[]
    sim.link_of=[[(('e',0),0.0,1000.0)],[(('e',1),0.0,1000.0)]]
    sim.starts=[[0.0],[0.0]];sim.adjacent={0:[1],1:[0]}
    sim.lane_changes=sim.lc_blocked_rules=sim.lc_blocked_safety=0
    rear={'id':1,'p':0,'s':100.0,'v':10.0,'L':4.6,'v0':20.0,'li':0,'lc':None,'lc_cooldown':-1}
    lead={'id':2,'p':0,'s':120.0,'v':8.0,'L':4.6,'v0':20.0,'li':0,'lc':None,'lc_cooldown':-1}
    V=[rear,lead];occ=sim.occupancy(V)
    sim.consider_lane_changes(V,10.0,occ)
    assert rear['lc'] is not None
    assert rear['lc']['to']==1
    assert sim.lane_changes==1
