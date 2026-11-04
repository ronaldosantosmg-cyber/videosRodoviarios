"""Confluência não pode comprimir a frota até a mera distância anti-colisão."""
import numpy as np
import pytest
from app.models import Settings
from app.simulation import TrafficSim
from app.traffic import tangent
from app.fleet_policy import require_export
from test_simulation_blocks import road


def merging_road():
    net=road(600.);x=np.linspace(0,600,601)
    for i,path in enumerate(net.paths):
        y=np.zeros_like(x) if i==0 else 20*np.clip(1-x/140,0,1)**2
        points=np.c_[x,y];d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))];join=d[140]
        path.update(p=points,d=d,t=tangent(points),length=float(d[-1]),links=[(('e',i),0.,join),(('e',2),join,float(d[-1]))])
    net.edges.append(dict(kind='main',level=0));return net


@pytest.mark.parametrize('seed',[1729,1,2,3])
def test_merge_reserves_free_spacing_before_moving(seed):
    cfg=Settings(duration_s=220 if seed==1729 else 80,traffic_density=4,traffic_speed_kmh=70,traffic_seed=seed,pedestrians=False)
    sim=TrafficSim(merging_road(),cfg,lambda *_:'car')
    assert sim.collisions==sim.side_collisions==0
    assert not sim.fleet_audit['violations']
    assert getattr(sim,'spacing_interventions',0)>0
    assert sum(sim.exited_by_path)>0
    require_export(sim,cfg)
