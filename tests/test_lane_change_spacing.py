"""A troca acompanha o destino e preserva a regra de espaçamento."""
import math
from app.simulation import TrafficSim
from test_signal_queue_origin import fixture


def test_instantaneous_return_gap_is_not_enough_when_closing_on_leader():
    sim=TrafficSim.__new__(TrafficSim)
    assert not sim.lane_change_clearance(15.6,35.,12.,math.inf,0.)
    assert sim.lane_change_clearance(15.6,65.,12.,math.inf,0.)
    assert not sim.lane_change_clearance(15.6,65.,12.,35.,20.)


def test_acceleration_follows_target_leader_before_lane_change_finishes():
    sim,v=fixture();sim.transport.red=False
    v.update(v=15.,s=200.,lc=None)
    sim.leader_state=lambda *a,**kw:(math.inf,0.,None)
    free=sim.accel(v,None,0.)
    target=dict(id=3,p=1,s=230.,v=5.,L=4.5)
    sim.map_s=lambda source,target,station:station
    sim.leader_state=lambda *a,**kw:(25.,5.,target) if kw.get('path_i')==1 else (math.inf,0.,None)
    v['lc']={'to':1,'elapsed':0.,'duration':4.}
    braking=sim.accel(v,None,0.)
    assert free>0 and braking<0
    assert v['_why']=='lider'


def test_uncontrolled_stop_does_not_seek_a_gap_below_twelve_metres():
    sim,v=fixture();sim.transport.red=False
    v.update(v=0.,s=200.);sim.lead['v']=0.;sim.gap=11.
    assert sim.accel(v,None,0.)<=0
    sim.gap=15.
    assert sim.accel(v,None,0.)>0
