import json
from types import SimpleNamespace
import numpy as np
import pytest
from shapely.geometry import box,Point
from app.models import Settings,ConnectionRule
from app.traffic_distribution import movement_weights,apply_distribution


def fork(share=None):
    edges=[dict(origin=0,length=100,t=np.array([[1.,0.],[1.,0.]])),dict(origin=0,length=200,t=np.array([[1.,0.],[1.,0.]])),dict(origin=1,length=80,t=np.array([[.8,.6],[.8,.6]]))]
    rules=[] if share is None else [dict(action='force',applied=True,from_edge=0,to_edge=2,share_pct=share)]
    return SimpleNamespace(edges=edges,connections={0:[1,2],1:[],2:[]},rule_report=rules,origin_info={0:(300,True),1:(80,True)},axis=np.array([[0.,0.],[300.,0.]]))


@pytest.mark.parametrize('share,expected',[(None,.2),(35,.35),(0,0),(100,1)])
def test_branch_percentages_keep_main_and_secondary_mass_conservation(share,expected):
    net=fork(share);weights,groups=movement_weights(net)
    assert weights[(0,2)]==pytest.approx(expected) and weights[(0,1)]==pytest.approx(1-expected)
    s=Settings(traffic_demand_vphpl=1000)
    sim=SimpleNamespace(net=net,s=s,siblings={('e',0):[0,1]},paths=[dict(p=np.array([[0.,0.],[300.,0.]])),dict(p=np.array([[0.,0.],[200.,60.]]))],link_of=[[(('e',0),0,100),(('c',0,1),100,101)],[(('e',0),0,100),(('c',0,2),100,101)]],rate=[1.,1.])
    apply_distribution(sim)
    assert sum(sim.rate)*3600==pytest.approx(1000) and sim.rate[1]*3600==pytest.approx(1000*expected)


def test_invalid_or_conflicting_percentages_are_not_silently_normalized():
    net=fork(80);net.rule_report.append(dict(action='force',applied=True,from_edge=0,to_edge=1,share_pct=80))
    with pytest.raises(ValueError,match='100%'):movement_weights(net)
    with pytest.raises(ValueError):ConnectionRule(a=dict(x=0,y=0),b=dict(x=1,y=0),share_pct=float('nan'))


def test_vdm_applies_once_to_entries_and_does_not_drop_half_on_one_way_network():
    net=fork();sim=SimpleNamespace(net=net,s=Settings(traffic_vdm=10000,traffic_peak_hour_fraction=.1),siblings={('e',0):[0,1]},paths=[dict(p=np.array([[0.,0.],[300.,0.]])),dict(p=np.array([[0.,0.],[200.,60.]]))],link_of=[[(('e',0),0,100),(('c',0,1),100,101)],[(('e',0),0,100),(('c',0,2),100,101)]],rate=[1.,1.])
    apply_distribution(sim);assert sum(sim.rate)*3600==pytest.approx(1000)
    assert sim.distribution_report['mode']=='VDM'


def test_entry_is_inside_by_five_meters_without_disabling_signals_or_collisions():
    from test_v14212_traffic_safety import network,configuration
    from app.simulation import TrafficSim
    s=configuration(traffic_route_only=True,duration_s=3)
    sim=TrafficSim(network(s),s,lambda *a:'car',duration=3)
    assert sim.spawned>0 and sim.report()['entry_inset_m']==5
    # As estações são relativas ao itinerário já recuado nas duas pontas.
    assert all(path['terminal_inset_applied'] for path in sim.paths)
    assert all(5<=float(p[0])<=595 for t in np.arange(0,3,.2) for p,_,_,_,_ in sim.vehicles_ex(float(t)))
    assert sim.lane_changes==0 and s.traffic_prevent_collisions and s.traffic_respect_signals


def test_confirmed_alignment_can_have_an_operational_corridor_without_a_hatch():
    from app.traffic import TrafficNetwork
    a=np.array([[0.,0.],[300.,0.]])
    route=dict(id='r',name='Eixo confirmado',points=[dict(x=x,y=y) for x,y in a],outside_pavement=True)
    s=Settings(route_alignments=[route],hydrography=False,signage_detail='basic')
    n=TrafficNetwork([],[],[],a,np.array([0.,300.]),s);assert len(n.paths)==2
    route['outside_pavement']=False
    n2=TrafficNetwork([],[],[],a,np.array([0.,300.]),Settings(route_alignments=[route],hydrography=False,signage_detail='basic'));assert not n2.paths
    n3=TrafficNetwork([],[box(145,-10,155,10)],[],a,np.array([0.,300.]),s)
    assert all(not(p['p'][:,0].min()<145 and p['p'][:,0].max()>155) for p in n3.paths)


def test_oae_zero_or_longitudinal_does_not_invent_an_obstacle_or_elevation():
    from app.oae_traffic import classify,grade_separated
    deck=box(90,-20,110,20);line=np.array([[100.,-20.],[100.,20.]])
    info=[dict(id='OAE',deck=deck,line=line,level_m=0)]
    report,warnings=classify(info,[dict(points=np.array([[0.,0.],[200.,0.]]))])
    assert warnings and report[0]['transverse'] and not report[0]['grade_separation_known']
    assert not grade_separated(info,Point(100,0),np.array([1.,0.]),np.array([0.,1.]))
    info[0]['level_m']=720
    assert not grade_separated(info,Point(100,0),np.array([1.,0.]),np.array([0.,1.]))
    info[0]['level_m']=6;info[0]['grade_confirmed']=True
    assert grade_separated(info,Point(100,0),np.array([1.,0.]),np.array([0.,1.]))


def test_contact_turn_gets_a_tangent_curve_only_inside_real_pavement():
    from app.traffic import TrafficNetwork,tangent,sample
    from shapely.geometry import Polygon
    net=TrafficNetwork.__new__(TrafficNetwork);net.nodes=[(np.array([0.,0.]),0)];net.no_connect=Polygon();net.bridges=Polygon();net.allowed=box(-100,-100,100,100)
    import collections
    net.rejected_connectors=collections.Counter();net.rejected_nodes=set()
    pa=np.c_[np.linspace(-80,0,161),np.zeros(161)];pb=np.c_[np.zeros(161),np.linspace(0,80,161)]
    def edge(p,base):return dict(p=p,t=tangent(p),end=0,start=0,base=base,origin=base,level=0)
    a,b=edge(pa,0),edge(pb,1);curve=net.connector(a,b)
    assert curve is not None and curve[0,0]<-4 and curve[-1,1]>4
    from app.vehicle_motion import analyze_motion
    assert analyze_motion(np.vstack([pa[pa[:,0]<curve[0,0]],curve,pb[pb[:,1]>curve[-1,1]]]),allowed=net.allowed)['ok']
    b['level']=1;assert net.connector(a,b) is None
    b['level']=0;net.allowed=box(-100,-1,1,1).union(box(-1,-1,1,100));assert net.connector(a,b) is None


def test_trimmed_merge_uses_physical_edge_offsets_for_following():
    from app.simulation import TrafficSim
    sim=TrafficSim.__new__(TrafficSim);sim.starts=[[0.],[0.]];sim.link_of=[[(('e',0),0.,100.)],[(('e',0),0.,80.)]];sim.link_offsets=[[0.],[20.]]
    v=dict(id=1,p=0,s=50.,v=10,L=6,lc=None);w=dict(id=2,p=1,s=40.,v=8,L=6,lc=None)
    occ=sim.occupancy([v,w]);gap,_,lead=sim.leader_state(v,occ)
    assert gap==pytest.approx(4) and lead is w


def test_engineering_fleet_dimensions_match_bodies_without_changing_legacy_profiles():
    from app.vehicle_motion import PROFILES
    from app.visual import TYPES,vehicle_type
    for key,L,B in [('car6',6,2),('moto2',2,.5),('truck18',18,3),('long30',30,3)]:
        assert PROFILES[key][:2]==(L,B) and TYPES[key]['L']==L and TYPES[key]['B']==B
    assert PROFILES['car'][:2]==(4.5,1.8)
    types={vehicle_type(['main'],(0,i,0),'engenharia') for i in range(100)}
    assert {'car6','moto2','truck18','long30'}<=types


def test_actual_y_junction_has_derived_itineraries_and_continuity_with_distribution():
    from app.traffic import TrafficNetwork
    from shapely.geometry import LineString,Point
    from app.simulation import TrafficSim
    a=np.array([[0.,0.],[300.,0.]]);b=np.array([[150.,0.],[230.,80.]])
    roads=[LineString(a).buffer(8),LineString(b).buffer(8),Point(150,0).buffer(18)]
    axes=[dict(points=a,layer='EIXO PRINCIPAL',role='axis'),dict(points=b,layer='EIXO RAMAL',role='axis')]
    s=Settings(hydrography=False,signage_detail='basic',duration_s=3,traffic_speed_kmh=35,min_route_segment_m=50,route_directions={'0':'forward','1':'forward'})
    net=TrafficNetwork(roads,[],axes,a,np.array([0.,300.]),s)
    assert len(net.paths)>=2 and any(len({net.edges[k]['origin'] for k in p['edges']})>1 for p in net.paths)
    weights,groups=movement_weights(net);assert groups
    assert any(any(abs(o['percent']-20)<1e-6 for o in g['outputs']) for g in groups)
    sim=TrafficSim(net,s,lambda *a:'car',duration=3)
    assert sim.spawned>0 and sim.collisions==sim.side_collisions==0
    for group in sim.distribution_report['entries']:
        assert sum(row['percent'] for row in group['itineraries'])==pytest.approx(100,abs=1e-4)


def test_no_median_checkbox_overrides_permitted_return_without_touching_parallel_flow():
    from app.traffic import TrafficNetwork
    from shapely.geometry import Polygon
    n=TrafficNetwork.__new__(TrafficNetwork)
    n.s=Settings(traffic_no_median_crossing=True,crossing_zones=[dict(id='z',point=dict(x=0,y=0),mode='allow',radius_m=20)])
    n.edges=[dict(p=np.array([[0.,-8.],[0.,8.]]),kind='return',disabled=False),dict(p=np.array([[-10.,-8.],[10.,-8.]]),kind='main',disabled=False)]
    n.connectors={};n.connections={0:[],1:[]};n.main=[1,2];n.islands=[];n.bridges=Polygon();n.warnings=[];n.side=lambda p:1 if p[1]>0 else -1
    n.crossing_rules();assert n.edges[0]['disabled'] and not n.edges[1]['disabled']


def test_dxf_oae_elevation_is_preserved_instead_of_assigning_a_fake_height():
    import ezdxf
    from app.geometry import convert
    doc=ezdxf.new();e=doc.modelspace().add_lwpolyline([(0,0),(100,0),(100,10),(0,10)],close=True,dxfattribs={'elevation':6})
    entities=[];convert(e,'OAE','oae',1,entities,[])
    assert entities[0]['elevation_m']==6


def test_density_does_not_double_just_because_a_branch_was_added():
    net=fork();sim=SimpleNamespace(net=net,s=Settings(),siblings={('e',0):[0,1]},paths=[dict(p=np.array([[0.,0.],[300.,0.]])),dict(p=np.array([[0.,0.],[200.,60.]]))],link_of=[[(('e',0),0,100),(('c',0,1),100,101)],[(('e',0),0,100),(('c',0,2),100,101)]],rate=[.1,.08])
    apply_distribution(sim);assert sum(sim.rate)==pytest.approx(.1)


def test_saturated_entry_keeps_weighted_choice_until_admission_instead_of_starving_branch():
    from app.simulation import TrafficSim
    sim=TrafficSim.__new__(TrafficSim);sim.siblings={('e',0):[0,1]};sim.rate=[.8,.2];rng=np.random.default_rng(49);secondary=0
    for _ in range(10000):
        choice=sim.admission_order([10,10],rng)[0]
        assert sim.admission_order([10,10],rng)[0]==choice
        secondary+=choice==1;sim._entry_choices.clear()
    assert .18<secondary/10000<.22


def test_vehicle_collision_toggle_keeps_people_and_oae_grade_separation_independent():
    from test_v14229_shoulder_probe import scene
    from app.models import OAEMark
    sim,v,_=scene();v['s']=80.;sim.shoulder_probe.enabled=False
    center,heading=sim.polygon_safety.pose(v)
    person=dict(id=1,route=dict(kind='calcada',height=0))
    sim.pedestrians=SimpleNamespace(agents=[person],pose=lambda a:(center+heading*5,heading))
    assert sim.polygon_safety.resolve([v],[(10.,12.)],vehicle_check=False)[0][1]<12
    sim.pedestrians.pose=lambda a:(center,heading)
    assert not sim.polygon_safety.admission(v,[],vehicle_check=False)
    sim.pedestrians.agents=[]
    train=dict(p=np.array([100.,0.]),heading=np.array([0.,1.]),length=20.,width=3.,level=0)
    sim.transport=SimpleNamespace(train_parts=lambda t:[train]);sim.s.oae_marks=[OAEMark(start=dict(x=70,y=-1.6),end=dict(x=130,y=-1.6),width_m=14,level_m=6)]
    assert sim.polygon_safety.resolve([v],[(10.,40.)],vehicle_check=False)[0][1]==40
    sim.s.oae_marks[0].level_m=0
    assert sim.polygon_safety.resolve([v],[(10.,40.)],vehicle_check=False)[0][1]<40


def test_larger_axis_has_merge_priority_within_same_road_category():
    from app.simulation import TrafficSim
    sim=TrafficSim.__new__(TrafficSim);sim.net=fork();sim.kind={('e',0):'main',('e',2):'main'}
    assert sim.priority(('e',0))>sim.priority(('e',2))


@pytest.mark.parametrize('invalid',[None,float('nan'),float('inf')])
def test_invalid_oae_z_never_releases_a_crossing_or_leaks_non_finite_json(invalid):
    from app.oae_traffic import classify,valid_grade,grade_separated
    item=dict(id='OAE',deck=box(0,-10,100,10),line=np.array([[0.,0.],[100.,0.]]),level_m=invalid,grade_confirmed=True)
    rows,warnings=classify([item],[])
    assert warnings and rows[0]['z_m'] is None and not valid_grade(item)
    json.dumps(rows,allow_nan=False)
    assert not grade_separated([item],Point(50,0),np.array([1.,0.]),np.array([0.,1.]))


def test_route_only_keeps_a_vehicle_available_after_first_pass_without_increasing_density():
    from app.simulation import TrafficSim
    from app.traffic import TrafficNetwork
    a=np.array([[0.,0.],[80.,0.]])
    s=Settings(traffic_route_only=True,traffic_speed_kmh=70,duration_s=20,hydrography=False,signage_detail='basic',route_alignments=[dict(id='r',name='Conferência',points=[dict(x=x,y=y) for x,y in a],type='unico',lanes=1)])
    net=TrafficNetwork([box(-20,-10,100,10)],[],[],a,np.array([0.,80.]),s);sim=TrafficSim(net,s,lambda *a:'car',duration=20)
    assert sim.spawned>=3 and sim.distribution_report['effective_mode']=='rotas'
    assert list(sim.vehicles_ex(10)) and list(sim.vehicles_ex(19))
    assert max(len(list(sim.vehicles_ex(float(t)))) for t in np.arange(0,20,.2))<=1


def test_route_inspection_preflight_does_not_hide_initial_vehicles_with_cinematic_reveal(monkeypatch):
    from app import traffic_presentation as presentation
    scene=SimpleNamespace(s=Settings(traffic_route_only=True,duration_s=3,short_video_mode='auto'),network=SimpleNamespace(paths=[1]),reveal_opacity=.25,pose=lambda t:(None,100,0))
    def sample(scene,t,cam,width,progress):
        assert progress==1 and scene.reveal_opacity==1
        return [],dict(active=1,drawn=1,subpixel=0)
    monkeypatch.setattr(presentation,'visible',sample)
    assert presentation.preflight(scene)['status']=='visivel'
    assert scene.reveal_opacity==.25
