"""1.42.39: barreira final anti-conflito (app.conflict_guard) ligada ao TrafficSim."""
import math
import numpy as np
import pytest
from shapely.geometry import Polygon
from app.simulation import TrafficSim
from app.vehicle_safety import PolygonSafety
from tests.test_v14212_traffic_safety import network,configuration


def _sim(duration=40,guard=True,**kw):
    cfg=configuration(traffic_conflict_guard=guard,duration_s=duration,**kw)
    return TrafficSim(network(cfg),cfg,lambda *a:'car',duration=duration)


def _min_clear(sim,duration):
    worst=1e9
    for t in np.arange(0,duration,.5):
        polys=[Polygon(s['polygon']) for s in sim.vehicle_body_state(float(t))]
        for i,p in enumerate(polys):
            for q in polys[i+1:]:worst=min(worst,p.distance(q) if not p.intersects(q) else -p.intersection(q).area)
    return worst


def test_sem_conflito_resultado_identico_com_e_sem_guarda():
    a=_sim(guard=True);b=_sim(guard=False)
    assert len(a.frames)==len(b.frames)>50
    for fa,fb in zip(a.frames,b.frames):
        assert all(np.array_equal(x,y) for x,y in zip(fa,fb))
    assert a.conflict_guard.interventions==0 and a.report()['conflict_guard']['unresolved']==0


def test_guarda_resolve_sobreposicao_quando_as_outras_barreiras_falham(monkeypatch):
    monkeypatch.setattr(PolygonSafety,'resolve',lambda self,V,planned,vehicle_check=True:planned)
    monkeypatch.setattr(TrafficSim,'enforce_hard_separation',lambda self,V:None)
    monkeypatch.setattr(TrafficSim,'leader_state',lambda self,v,occ,look=150.,path_i=None,s=None:(math.inf,0.,None))
    monkeypatch.setattr(TrafficSim,'check',lambda self,V:None)
    # O cenário de falha exige velocidades distintas, sem a semeadura uniforme da 3.5.
    sem=_sim(60,guard=False,traffic_density=6,traffic_sem_comboio=False,traffic_semear=False)
    assert _min_clear(sem,60)<0,'o cenário precisa produzir sobreposição sem a guarda'
    com=_sim(60,guard=True,traffic_density=6,traffic_sem_comboio=False,traffic_semear=False)
    assert com.conflict_guard.interventions>0 and com.conflict_guard.unresolved==0
    assert _min_clear(com,60)>=-1e-6


def test_guarda_respeita_chave_de_desligar():
    assert _sim(20,guard=False).report()['conflict_guard']['interventions']==0
