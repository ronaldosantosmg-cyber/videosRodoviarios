"""Saídas abertas retiram a frota pelo portal sem criar estacionamento terminal."""
import numpy as np
from app.models import Settings
from app.simulation import TrafficSim
from app.vehicle_motion import PROFILES
from test_simulation_blocks import road


def settings():
    return Settings(duration_s=35,traffic_density=2,traffic_speed_kmh=40,
                    traffic_warmup_s=0,pedestrians=False)


def test_front_reaches_sink_and_no_body_remains_beyond_terminal():
    sim=TrafficSim(road(240.),settings(),lambda *_:'truck')
    assert sum(sim.exited_by_path)>0
    for ids,stations,paths,_,_ in sim.frames:
        for vid,station,path in zip(ids,stations,paths):
            assert station+PROFILES[sim.info[int(vid)][1]][0]/2<sim.paths[int(path)]['length']+1e-6
    assert sim.collisions==sim.side_collisions==0


def test_exit_is_end_of_whole_itinerary_not_an_internal_link():
    net=road(240.)
    for i,p in enumerate(net.paths):p['links']=[(('e',i),0.,120.),(('c',i,i),120.,125.),(('e',i+2),125.,240.)]
    net.edges.extend([{'kind':'main','level':0},{'kind':'main','level':0}])
    sim=TrafficSim(net,settings(),lambda *_:'truck')
    assert any(np.any((f[1]>125.)&(f[1]<230.)) for f in sim.frames)
    assert sum(sim.exited_by_path)>0


def test_existing_total_block_before_exit_is_not_bypassed():
    from app.models import LaneBlock
    cfg=settings().model_copy(update={'lane_blocks':[LaneBlock(id='b',points=[{'x':210.,'y':-7.},{'x':220.,'y':-7.},{'x':220.,'y':7.},{'x':210.,'y':7.}],mode='total')]})
    sim=TrafficSim(road(240.),cfg,lambda *_:'truck')
    # Veículos que já nasceram a jusante podem sair; nenhum veículo a montante
    # atravessa a obra só por estar próximo ao fim do itinerário.
    initial={int(v):float(s) for v,s,p,_,_ in sim.state(0) if p==0 and s<200.}
    for ids,stations,paths,_,_ in sim.frames:
        for vid,station,path in zip(ids,stations,paths):
            if int(path)==0 and int(vid) in initial:assert station<210.
