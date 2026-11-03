"""Fila de semáforo: descarga no ritmo de saturação (vários veículos por verde) e fila que se dissolve; sem comboio em trecho livre."""
import functools,numpy as np
from types import SimpleNamespace
from shapely.geometry import box
from app.simulation import TrafficSim
from app.models import Settings
from app.transport_models import TrafficSignal
from app import visual

def _net(L):
    x=np.linspace(0,L,int(L)+1);p=np.c_[x,np.zeros(len(x))]
    path=dict(p=p,d=x.copy(),length=float(L),kinds=['main'],route='r',route_dir='f',route_lane=0,lane_change='marked',route_start_m=0.,route_end_m=float(L),links=[(('e',0),0.,float(L))])
    return SimpleNamespace(paths=[path],edges=[dict(kind='main',level=0)],allowed=box(-30,-8,L+30,12))

def test_fila_do_semaforo_descarrega_varios_veiculos_por_verde_e_cruzam_em_movimento():
    L,X,dur=2400.,1200.,300.;sig=TrafficSignal(id='s1',point={'x':X,'y':0.},heading_deg=0,lanes_a=2,lanes_b=2)
    s=Settings(traffic_density=6.0,traffic_speed_kmh=70,duration_s=dur,vehicle_mix='variado',traffic_signals=[sig])
    # Com semeadura já espaçada, demanda 6 mantém uma fila real em todos os verdes.
    sim=TrafficSim(_net(L),s,functools.partial(visual.vehicle_type,mix='variado'),duration=dur)
    assert sim.collisions==sim.side_collisions==0
    assert not sim.fleet_audit['violations']
    sg=sim.transport.signals[0];dt=.2
    from app.transport import timings
    verde=timings(sg)[0][0];assert verde>=20
    cross=[];prev={}
    for k,(ids,ss,ps,to,al) in enumerate(sim.frames):
        for i,s_ in zip(ids,ss):
            if i in prev and prev[i]<X<=s_:cross.append(k*dt)
        prev={i:s_ for i,s_ in zip(ids,ss)}
    st=[sim.transport.signal_state(sg,k*dt)[0] for k in range(len(sim.frames))]
    inicios=[k*dt for k in range(1,len(st)) if st[k]=='green' and st[k-1]!='green']
    assert len(inicios)>=2
    por_verde=[sum(1 for c in cross if a<=c<a+verde+sg.amber_s) for a in inicios[:-1]]
    assert min(por_verde)>=4,por_verde      # antes: 1 a 3 veículos por verde (fila crescia sem parar)
