import math
import numpy as np
import pytest
from shapely.geometry import box
from app.models import Settings
from app.transport_models import TrafficSignal
from app.transport import Transport,phase,timings
from app.traffic import TrafficNetwork
from app.simulation import TrafficSim

def rail(**kw):return dict(id='R',points=[{'x':200,'y':-300},{'x':200,'y':300}],**kw)
def signal(**kw):return dict(id='S',point={'x':200,'y':0},**kw)
def network(s):
    p=np.array([[0.,0.],[600.,0.]])
    return TrafficNetwork([box(-30,-12,630,12)],[],[{'points':p}],p,np.array([0.,600.]),s)

@pytest.mark.parametrize('phases,extra',[(2,5),(3,15)])
def test_exact_formulas_mutual_exclusion_and_pedestrian_phase(phases,extra):
    s=TrafficSignal(**signal(phases=phases,lanes_a=2,lanes_b=3));g,walk,cycle=timings(s)
    assert g==[4+extra,6+extra] and bool(walk)==(phases==3)
    states=[phase(s,t) for t in np.arange(0,cycle,.1)]
    assert all(not(a=='green' and b=='green') for a,b,_ in states)
    assert all(a==b=='red' for a,b,p in states if p)
    assert any(p for _,_,p in states)==(phases==3)

def test_train_counts_determinism_single_double_and_full_tail_clearance():
    s=Settings(railways=[rail(direction='both',max_wagons=10)]);c=Transport(s);r=c.rails[0]
    counts={c.event(r,i*r['period']+20)['wagons'] for i in range(40)};assert min(counts)==5 and max(counts)==10
    copy=Transport(s)
    assert all(c.event(r,t)==copy.event(copy.rails[0],t) for t in [0,20,150])
    t=s.railways[0].start_s+320/(40/3.6)
    assert all(c.rail_closed(r,300,t+dt) for dt in [0,2,5])
    assert not c.rail_closed(r,300,t+25)
    assert c.event(r,20)['reverse']!=c.event(r,20+r['period'])['reverse']
    d=Transport(Settings(railways=[rail(tracks=2,direction='both')]))
    assert len(d.rails)==2 and d.event(d.rails[0],20)['reverse']!=d.event(d.rails[1],20)['reverse']

def test_wave_offset_and_invalid_links():
    signals=[signal(),dict(id='T',point={'x':600,'y':0})];link=dict(id='L',source='S',target='T',speed_kmh=36)
    s=Settings(traffic_signals=signals,signal_links=[link]);c=Transport(s)
    assert c.offsets['T']==40
    assert c.signal_state(s.traffic_signals[0],5)==c.signal_state(s.traffic_signals[1],45)
    with pytest.raises(ValueError):Settings(traffic_signals=signals,signal_links=[link,dict(id='X',source='T',target='S')])
    with pytest.raises(ValueError):Settings(traffic_signals=signals,signal_links=[dict(link,target='ausente')])
    signals[1]['phases']=3
    with pytest.raises(ValueError):Settings(traffic_signals=signals,signal_links=[link])

@pytest.mark.parametrize('bad',[float('nan'),float('inf'),None,'',0,-1])
def test_invalid_speeds_cannot_reach_motor(bad):
    with pytest.raises(ValueError):Settings(railways=[rail(speed_kmh=bad)])

def test_disabled_and_separate_levels_do_not_block():
    s=Settings(derive_traffic_paths=False,hydrography=False,railways=[rail(enabled=False)],traffic_signals=[signal(enabled=False)])
    assert not any(Transport(s,network(s)).stops)
    s=Settings(derive_traffic_paths=False,hydrography=False,railways=[rail(level=1)],traffic_signals=[signal(level=1)])
    assert not any(Transport(s,network(s)).stops)

@pytest.mark.parametrize('kind',['rail','signal'])
def test_real_simulation_stops_and_releases(kind):
    opts={'railways':[rail(start_s=0)]} if kind=='rail' else {'traffic_signals':[signal(lanes_a=1,lanes_b=1)]}
    s=Settings(derive_traffic_paths=False,hydrography=False,duration_s=150,traffic_density=4,traffic_speed_kmh=40,**opts)
    n=network(s);sim=TrafficSim(n,s,lambda *a:'car',duration=150)
    assert sim.report()['rear_collisions']==0 and any(sim.transport.stops)
    stopped=0;crossed=0;previous={}
    for k in range(len(sim.frames)):
        t=k*.2
        for vid,pi,station,_,_ in sim.state(t):
            if vid in previous:
                old=previous[vid];ds=station-old
                for stop in sim.transport.stops[pi]:
                    closed=sim.transport.rail_closed(stop['rail'],stop['rail_s'],t) if kind=='rail' else sim.transport.signal_state(stop['signal'],t)[stop['axis']]!='green'
                    if closed and 0<=stop['s']-station-2.25<12 and ds<.03:stopped+=1
                    if old+2.25<stop['s']<=station+2.25:
                        assert not closed,'Veículo entrou durante vermelho / passagem do trem'
                        crossed+=1
            previous[vid]=station
    assert stopped>5 and crossed>0


def test_adjustable_five_to_one_hundred_wagons_and_safe_interval():
    c=Transport(Settings(railways=[rail()]));r=c.rails[0]
    counts={c.event(r,i*r['period']+20)['wagons'] for i in range(1000)}
    assert min(counts)==5 and max(counts)==100
    assert r['period']>=(r['length']+1520)/(40/3.6)+55
    fixed=Transport(Settings(railways=[rail(min_wagons=100,max_wagons=100)]))
    assert all(fixed.event(fixed.rails[0],t)['wagons']==100 for t in [0,30,200,500])
    for lo,hi in [(4,100),(5,101),(20,19),(None,100),(5,float('nan')),(5,7.5)]:
        with pytest.raises(ValueError):Settings(railways=[rail(min_wagons=lo,max_wagons=hi)])


def test_all_one_hundred_wagons_exist_and_last_tail_holds_crossing():
    c=Transport(Settings(railways=[dict(rail(min_wagons=100,max_wagons=100),points=[{'x':200,'y':-2500},{'x':200,'y':2500}])]))
    r=c.rails[0];parts=c.train_parts(200)
    assert len(parts)==101 and sum(p['locomotive'] for p in parts)==1
    arrival=15+2520/(40/3.6)
    assert c.rail_closed(r,2500,arrival+100)
    assert not c.rail_closed(r,2500,arrival+150)


def test_entry_inside_intersection_does_not_spawn_during_red_and_long_crossing_gets_clearance():
    s=Settings(derive_traffic_paths=False,hydrography=False,traffic_signals=[dict(signal(),point={'x':0,'y':0})])
    c=Transport(s,network(s));assert any(st.get('entry_only') for row in c.stops for st in row)
    assert c.admission_allowed(0,1,4.5) and not c.admission_allowed(0,15,4.5)
    slow=Settings(traffic_speed_kmh=5,traffic_signals=[signal(lanes_a=8,lanes_b=8,lane_width_m=5)])
    assert slow.traffic_signals[0].clearance_s>40


def test_extreme_coordinates_rejected_before_projection():
    with pytest.raises(ValueError):Settings(traffic_signals=[dict(signal(),point={'x':1e308,'y':0})])


def test_skew_intersection_controls_both_axes_and_rejects_parallel_plans():
    from types import SimpleNamespace
    a=np.array([[-100.,0.],[100.,0.]]);v=np.array([.5,math.sqrt(3)/2]);b=np.array([-100*v,100*v])
    paths=[{'p':p,'d':np.array([0.,200.])} for p in [a,b]]
    s=Settings(traffic_signals=[dict(signal(heading_b_deg=60),point={'x':0,'y':0})]);c=Transport(s,SimpleNamespace(paths=paths,edges=[]))
    assert any(stop['axis']==0 for stop in c.stops[0]) and any(stop['axis']==1 for stop in c.stops[1])
    with pytest.raises(ValueError):Settings(traffic_signals=[signal(heading_b_deg=0)])


def test_short_alignment_warns_before_train_enters_and_across_cycle_boundary():
    s=Settings(railways=[dict(rail(start_s=0,min_wagons=5,max_wagons=5),points=[{'x':40,'y':-15},{'x':40,'y':15}])]);c=Transport(s);r=c.rails[0]
    assert c.rail_closed(r,15,-10),'O aviso deve começar antes do trem entrar no alinhamento'
    assert c.rail_closed(r,15,r['period']-10),'Não pode piscar verde na troca de ciclos'
    assert not c.rail_closed(r,15,-30)


def test_short_crossing_clears_heavy_vehicle_bodies_before_train_arrival():
    from app.transport_render import rectangle
    from app.vehicle_motion import PROFILES
    from shapely.geometry import Polygon
    s=Settings(derive_traffic_paths=False,hydrography=False,traffic_speed_kmh=5,traffic_demand_vphpl=2000,duration_s=60,railways=[dict(rail(start_s=0,min_wagons=5,max_wagons=5),points=[{'x':40,'y':-15},{'x':40,'y':15}])])
    sim=TrafficSim(network(s),s,lambda *a:'carreta',duration=60);checks=0
    assert max(stop['warning_s'] for row in sim.transport.stops for stop in row)>20
    for t in np.arange(0,30,.2):
        trains=[Polygon(rectangle(part['p'],part['heading'],part['length'],part['width'])) for part in sim.transport.train_parts(float(t))]
        for p,h,vid,_,_ in sim.vehicles_ex(float(t)):
            length,width,*_=PROFILES[sim.info[vid][1]];body=Polygon(rectangle(p,h,length,width))
            for train in trains:assert body.intersection(train).area<1e-6;checks+=1
    assert checks>10 and sim.report()['rear_collisions']==0


def test_shared_rail_and_road_alignment_is_blocked_with_diagnostic():
    s=Settings(derive_traffic_paths=False,hydrography=False,railways=[dict(rail(start_s=0),points=[{'x':0,'y':0},{'x':300,'y':0}])]);n=network(s);c=Transport(s,n)
    assert c.report()['ambiguous_railway_conflicts']==1 and c.report()['warnings']
    assert not c.admission_allowed(0,0,4.5)
