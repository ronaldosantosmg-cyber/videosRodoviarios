from types import SimpleNamespace as S
import math
import numpy as np
import pytest
from shapely.geometry import box
from app.models import Settings
from app.simulation import TrafficSim, DT
from app.transport import Transport


def road(length=1500):
    x=np.linspace(0,length,151);p=np.c_[x,np.zeros(len(x))]
    path=dict(p=p,d=x,length=float(length),kinds=['main'],route='r',route_dir='f',route_lane=0,
              lane_change='marked',route_start_m=0.,route_end_m=float(length),links=[(('e',0),0.,float(length))])
    return S(paths=[path],edges=[dict(kind='main',level=0)],allowed=box(-30,-8,length+30,12))


@pytest.mark.parametrize('warmup',[0.,.1,.5])
def test_population_starts_without_negative_saved_time(warmup):
    settings=Settings(duration_s=3,traffic_warmup_s=warmup)
    sim=TrafficSim(road(),settings,lambda *a:'car',duration=3)
    assert abs(sim.t_first)<1e-9
    assert sim.warmup_seconds==pytest.approx(math.ceil(warmup/DT)*DT)
    assert sim.semeados>0 and len(sim.frames[0][0])>0
    assert sim.collisions==sim.side_collisions==0
    assert not sim.fleet_audit['violations']


def test_initial_speed_accounts_for_shared_leader_distance():
    sim=TrafficSim(road(),Settings(duration_s=3),lambda *a:'car',duration=3)
    rear=dict(id=100,p=0,s=100.,v=0.,v0=25.,L=4.6,lc=None)
    front=dict(id=101,p=0,s=120.,v=0.,v0=25.,L=4.6,lc=None)
    sim.initialize_speeds([rear,front],0.)
    assert rear['v']<front['v']
    assert rear['v']<=(20.-4.6-2.5)/3.+1e-9
    rear.update(s=0.,v0=12.)
    sim.initialize_speeds([rear,front],0.)
    assert rear['v']==12.  # A inicialização não eleva um limite desejado menor.


def test_transport_distinguishes_red_box_and_rail():
    control=Transport.__new__(Transport);control.s=S(traffic_respect_signals=True)
    signal=S(lanes_a=2,lanes_b=2,lane_width_m=3.5)
    vehicle=dict(p=0,s=0.,L=4.,v=0.)
    control.stops=[[dict(kind='signal',s=20.,signal=signal,axis=0)]]
    control.signal_state=lambda *a:('red','green',False)
    assert control.stop_gap(vehicle,0)==18.
    assert vehicle['_transport_kind']=='semaforo'
    control.signal_state=lambda *a:('green','red',False)
    assert control.stop_gap(vehicle,0,leader_gap=1.,leader_v=0.)==18.
    assert vehicle['_transport_kind']=='caixa_cruzamento'
    control.stops=[[dict(kind='rail',s=20.,cross=30.)]]
    control.rail_stop_closed=lambda *a:True
    assert control.stop_gap(vehicle,0)==18.
    assert vehicle['_transport_kind']=='ferrovia'
