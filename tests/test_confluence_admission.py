"""Retenção local antes da entrada, sem varredura global nem aquecimento extra."""
import copy
import numpy as np
import pytest
from app.models import Settings
from app.simulation import TrafficSim
from app.traffic import tangent
from app.fleet_policy import require_export
from test_simulation_blocks import road


def network():
    net=road(300.);x=np.arange(301,dtype=float)
    for i,path in enumerate(net.paths):
        y=20*np.clip(1-x/40,0,1)**2 if i else np.zeros_like(x)
        p=np.c_[x,y];d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        path.update(p=p,d=d,t=tangent(p),length=float(d[-1]),links=[(('e',i),0.,float(d[40])),(('e',2),float(d[40]),float(d[-1]))])
    net.edges.append(dict(kind='main',level=0));return net


def simulator(**kwargs):
    return TrafficSim(network(),Settings(duration_s=80,pedestrians=False,**kwargs),lambda *_:'car',defer=True)


def entrant():return {'id':100,'p':0,'s':5.,'v':10.,'L':4.5}


def vehicle(path,station,speed=0.,identity=1):
    return {'id':identity,'p':path,'s':station,'v':speed,'L':4.5,'li':0,'lc':None}


def test_closed_receiving_space_holds_then_releases_without_moving_existing_vehicle():
    sim=simulator();join=sim.link_of[1][1][1];other=vehicle(1,join+3);before=copy.deepcopy(other)
    occ=sim.occupancy([other]);physical=copy.deepcopy(other)
    assert not sim.entry_confluence_ready(entrant(),occ,0.)
    assert other==physical and other['s']==before['s']
    assert sim.entry_retry_at[0]==pytest.approx(.6)
    assert sim.entry_confluence_ready(entrant(),{},.6)
    assert 0 not in sim.entry_retry_at and sim.entry_gate_holds==1


def test_approaching_vehicle_gets_reserved_time_without_fake_control_cause():
    sim=simulator();join=sim.link_of[1][1][1]
    other=vehicle(1,join-30,10.);occ=sim.occupancy([other])
    assert not sim.entry_confluence_ready(entrant(),occ,0.)
    assert '_control_cause' not in other


def test_no_confluence_does_not_probe_unrelated_fleet():
    sim=TrafficSim(road(),Settings(duration_s=3),lambda *_:'car',defer=True)
    class NoLookup(dict):
        def get(self,*args):raise AssertionError('Trecho sem confluência não deve consultar ocupação')
    assert sim.entry_confluence_ready(entrant(),NoLookup(),0.)
    assert sim.entry_gate_checks==sim.entry_gate_probes==0


def test_stopped_vehicle_on_other_approach_keeps_rear_clearance():
    sim=simulator();join=sim.link_of[1][1][1]
    other=vehicle(1,join-16.,0.)
    assert not sim.entry_confluence_ready(entrant(),sim.occupancy([other]),0.)


def test_receiving_lookup_checks_neighbors_not_the_entire_queue():
    sim=simulator();other=vehicle(1,sim.link_of[1][1][1]+3)
    rows=[(float(i*10+3),other,1,0.) for i in range(10000)]
    assert not sim.entry_confluence_ready(entrant(),{('e',2):rows},0.)
    assert sim.entry_gate_probes<=2


@pytest.mark.parametrize('seed',[1729,1,2])
@pytest.mark.parametrize('warmup',[0,10])
def test_full_simulation_keeps_rule_and_discharges_held_entries(seed,warmup):
    sim=simulator(traffic_density=4,traffic_seed=seed,traffic_warmup_s=warmup);sim.run()
    require_export(sim,sim.s)
    assert sim.collisions==sim.side_collisions==0
    assert not sim.fleet_audit['violations']
    assert sim.entry_gate_holds>0 and sum(sim.exited_by_path)>0
    assert sim.spawned==sum(sim.exited_by_path)+sim.active_end
    assert sim.report()['confluence_admission']['extra_warmup_s']==0
