"""1.42.41: estabilidade do tráfego (perfis, cooldown, histerese, janela de brecha, merge forçado, seta)."""
import collections,math
import numpy as np
from shapely.geometry import box,Polygon
from app.models import Settings
from app.simulation import TrafficSim
from app import simulation
from app.traffic import TrafficNetwork


def _run(duration=100,length=1200,blocks=(),stab=True,speed=80,density=3,mp=None,**kw):
    if mp is not None:
        mp.setattr(simulation,'WARMUP',0)
    s=Settings(route_alignments=[dict(id='r',name='Via',points=[dict(x=0,y=0),dict(x=length,y=0)],type='dupla',lanes=2,lane_change='safe',taper_m=60)],derive_traffic_paths=False,hydrography=False,traffic_density=density,duration_s=duration,traffic_speed_kmh=speed,queue_capacity_model=False,traffic_stability=stab,lane_blocks=list(blocks),**kw)
    a=np.array([[0.,0.],[float(length),0.]]);net=TrafficNetwork([box(-30,-12,length+30,12)],[],[],a,np.array([0.,float(length)]),s)
    k=[0]
    def vt(kinds,identity):k[0]+=1;return 'truck18' if k[0]%5==0 else 'car'
    return TrafficSim(net,s,vt,duration=duration)


def test_perfis_70_15_15_estaticos():
    cont=collections.Counter(TrafficSim.vehicle_profile(i,'car')[0] for i in range(1,5001))
    assert abs(cont['convencional']/5000-.70)<.03 and abs(cont['lento']/5000-.15)<.03 and abs(cont['rapido']/5000-.15)<.03
    assert TrafficSim.vehicle_profile(7,'car')==TrafficSim.vehicle_profile(7,'car')
    assert TrafficSim.vehicle_profile(1,'truck')[0]=='lento'


def test_cooldown_entre_4_e_6_s():
    assert all(4.0<=TrafficSim.cooldown_for(i)<=6.0 for i in range(1,500))


def test_sem_zigue_zague_nem_colisao(monkeypatch):
    sim=_run(mp=monkeypatch);r=sim.report()
    assert r['rear_collisions']==0 and r['side_collisions']==0 and r['vehicles']>10
    last={}
    for e in sim.lane_events:
        if e['id'] in last:assert e['time']-last[e['id']]>=3.9+simulation.TrafficSim.LC_DURATION-0.01,(e,last[e['id']])
        last[e['id']]=e['time']
    assert sum(r['traffic_stability']['profiles'].values())==r['vehicles']


def test_estabilidade_reduz_trocas_em_relacao_ao_modo_antigo(monkeypatch):
    a=_run(stab=True,mp=monkeypatch).report();b=_run(stab=False,mp=monkeypatch).report()
    assert a['lane_changes']<=b['lane_changes'] and a['side_collisions']==0
    assert b['traffic_stability']['enabled'] is False


def test_interdicao_total_para_na_linha_sem_invadir(monkeypatch):
    blk=dict(name='Obra',points=[dict(x=700,y=-0.3),dict(x=760,y=-0.3),dict(x=760,y=-3.4),dict(x=700,y=-3.4)],mode='total',start_s=0,end_s=500)
    sim=_run(duration=100,blocks=[blk],mp=monkeypatch);r=sim.report()
    poly=Polygon([(p['x'],p['y']) for p in blk['points']]).buffer(-.3)
    from shapely.geometry import Point
    inside=0
    for t in np.arange(10,100,1.0):
        for vid,i,s,*_ in sim.state(float(t)):
            path=sim.paths[i];j=min(len(path['p'])-1,int(np.searchsorted(path['d'],s)))
            if poly.contains(Point(*path['p'][j])):inside+=1
    assert inside==0 and r['traffic_stability']['forced_merges']>=1 and r['rear_collisions']==0 and r['side_collisions']==0


def test_diagnostico_de_paradas_aponta_bloqueio(monkeypatch):
    blk=dict(name='Obra',points=[dict(x=700,y=-1.5),dict(x=760,y=-1.5),dict(x=760,y=-6),dict(x=700,y=-6)],mode='total',start_s=0,end_s=500)
    r=_run(duration=90,blocks=[blk],mp=monkeypatch).report()['stop_diagnostics']
    assert r['seconds_by_reason'].get('bloqueio',0)>0 and r['samples'] and r['samples'][0]['reason'] in ('bloqueio','lider')
    assert r['by_path'][0]['seconds']>0


def test_calibracao_idm_por_classe(monkeypatch):
    import pytest
    from app.models import Settings as St
    for bad in ({'x':{'T':1}},{'car':{'q':1}},{'car':{'T':99}}):
        with pytest.raises(Exception):St(traffic_calibration=bad)
    base=_run(duration=25,length=600,mp=monkeypatch);cal=_run(duration=25,length=600,traffic_calibration={'car':{'T':2.4,'s0':6.0}})
    assert base.dyn_of('car')['T']==1.35 and cal.dyn_of('car')['T']==2.4 and cal.dyn_of('car')['pcu']==1.0 and cal.dyn_of('truck')==base.dyn_of('truck')
    again=_run(duration=25,length=600)
    assert len(base.frames)==len(again.frames) and all(all(np.array_equal(x,y) for x,y in zip(a,b)) for a,b in zip(base.frames,again.frames))
