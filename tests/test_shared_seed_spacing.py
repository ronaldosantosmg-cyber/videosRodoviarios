import copy
import numpy as np
import pytest
from app.models import Settings
from app.simulation import TrafficSim
from app.fleet_policy import require_export
from test_simulation_blocks import road


def shared_network():
    net=road(700.);net.paths[1]=copy.deepcopy(net.paths[0]);net.paths[1]['route']='other_itinerary'
    return net


def config(seed=1729):return Settings(duration_s=5,traffic_density=6,traffic_speed_kmh=70,traffic_seed=seed,pedestrians=False)


@pytest.mark.parametrize('seed',[1729,1,2,3,4])
def test_shared_itineraries_are_valid_from_first_frame(seed):
    sim=TrafficSim(shared_network(),config(seed),lambda *_:'car')
    assert sim.semeados>0 and sim.seed_shared_spacing_rejected>0
    assert not sim.fleet_audit['violations']
    assert sim.collisions==sim.side_collisions==0
    require_export(sim,sim.s)


def test_seeding_does_not_rebuild_full_occupancy_for_each_candidate(monkeypatch):
    original=TrafficSim.semear_percurso
    def checked(self,*args,**kwargs):
        saved=self.occupancy
        self.occupancy=lambda *_:(_ for _ in ()).throw(AssertionError('Ocupação global reconstruída durante a semeadura'))
        try:return original(self,*args,**kwargs)
        finally:self.occupancy=saved
    monkeypatch.setattr(TrafficSim,'semear_percurso',checked)
    sim=TrafficSim(shared_network(),config(),lambda *_:'car')
    assert not sim.fleet_audit['violations']


def test_seed_gap_looks_through_an_internal_link_and_checks_reverse_order():
    net=shared_network();net.paths[0]['links']=[(('e',0),0.,100.),(('e',1),100.,700.)]
    net.paths[1]['links']=[(('e',1),0.,700.)]
    sim=TrafficSim(net,config(),lambda *_:'car',defer=True)
    a=dict(p=0,s=95.,L=4.5);b=dict(p=1,s=2.,L=4.5)
    assert sim.seed_forward_gap(a,b,100.)==pytest.approx(2.5)
    assert sim.seed_forward_gap(b,a,100.)==float('inf')


def test_parallel_independent_lanes_are_not_treated_as_one_link():
    sim=TrafficSim(road(700.),config(),lambda *_:'car')
    assert sim.seed_shared_spacing_rejected==0
    assert not sim.fleet_audit['violations']


def test_continuous_low_speed_admission_respects_the_twelve_metre_floor():
    settings=Settings(duration_s=45,traffic_semear=False,traffic_speed_kmh=5,traffic_demand_vphpl=3000,pedestrians=False)
    sim=TrafficSim(road(200.),settings,lambda *_:'car')
    assert sim.spawned>2
    assert not sim.fleet_audit['violations']
    require_export(sim,settings)
