"""Motor de microssimulação (app.microsim): IDM, MOBIL, setas, transição suave, OBB/SAT e anti-sobreposição.
Determinístico, sem navegador. Executa em poucos segundos."""
import math,random,time
import numpy as np
from app.microsim import (Simulation,Vehicle,Phase,RoadNetwork,Lane,TrafficSignal,StopLine,LaneClosure,BoundaryKind as B,
    LayerRules,parallel_lanes,OBB,SpatialHash,separation,idm_accel,EngineParams,IDMParams,VehicleParams)
from app.microsim.params import MobilParams


def reta(n=1,comp=2000.,between=None,v0=16.7,outer=B.EDGE):
    net=RoadNetwork()
    for l in parallel_lanes('f',[[0,0],[comp,0]],n,3.5,v0,between,outer,outer):net.add_lane(l)
    return net


def test_obb_sat_e_grelha():
    a=OBB(0,0,0,4.5,1.8);b=OBB(4.0,0,0,4.5,1.8);c=OBB(5.0,0,0,4.5,1.8)
    assert separation(a,b)<0 and separation(a,c)>0
    d=OBB(0,3,math.radians(45),4.5,1.8);assert separation(a,d)>-1e9
    h=SpatialHash(10.)
    for k,o in enumerate([a,b,c,OBB(500,500,0,4,2)]):h.insert(k,o)
    ps=set(h.pairs());assert (0,1) in ps and (1,2) in ps and not any(3 in p for p in ps)


def test_idm_limites_de_seguranca():
    p=IDMParams(s0=0.5,T=0.1);assert p.s0>=2.0 and p.T>=1.2
    assert idm_accel(0,16,None,0,p)>1.0
    assert idm_accel(15,16,1.0,15,p)<=-p.b_max+1e-9      # lacuna < s0 e fechando → frenagem máxima
    assert idm_accel(20,16,200,0,p)<0                    # acima de v0


def test_via_livre_atinge_velocidade_desejada():
    net=reta(comp=3000.);s=Simulation(net);s.add_vehicle(Vehicle('a','f0',0.));s.run(60)
    assert abs(s.vehicles['a'].v-16.7)<1.0


def test_semaforo_vermelho_para_e_verde_libera():
    net=reta(comp=600.);net.add_signal(TrafficSignal('S',phases=[('red',40.),('green',100.)]))
    net.add_stop_line(StopLine('f0',300.,'S'));s=Simulation(net);s.add_vehicle(Vehicle('a','f0',100.,v=14.))
    for _ in range(300):
        s.step();v=s.vehicles['a'];assert v.s+v.length/2<=300.+.05
    assert s.vehicles['a'].v<.3 and 300-s.vehicles['a'].s-2.25<4.5
    s.run(40);assert 'a' not in s.vehicles or s.vehicles['a'].s>300


def test_seguidor_mantem_folga_minima_e_frenagem_de_emergencia():
    net=reta(comp=3000.);s=Simulation(net)
    s.add_vehicle(Vehicle('l','f0',200.,v=15.));s.add_vehicle(Vehicle('f','f0',150.,v=15.))
    mn=1e9
    for k in range(900):
        if k==300:s.vehicles['l'].params.idm.b_max=9.;s.net.lanes['f0'].v0=0.1     # líder passa a querer parar
        if k==400:s.vehicles['l'].v=0.;s.vehicles['l'].a=0.
        s.step();l,f=s.vehicles['l'],s.vehicles['f'];gap=l.s-f.s-4.5;mn=min(mn,gap)
        assert not s.overlaps()
    assert mn>=-1e-6 and s.vehicles['f'].v<.5


def test_ultrapassagem_seta_antecede_e_transicao_suave():
    net=reta(2,comp=3000.,between=[B.OPEN]);s=Simulation(net)
    s.add_vehicle(Vehicle('lento','f0',300.,v=8.,params=VehicleParams(v0_factor=.45)))
    s.add_vehicle(Vehicle('rapido','f0',200.,v=14.))
    t_on=t_move=None;lats=[];ind=[];heads=[]
    for _ in range(1200):
        s.step();v=s.vehicles['rapido'];ind.append(v.indicator)
        if v.indicator!='off' and t_on is None:t_on=s.t
        if t_move is None and v.phase is Phase.CHANGING:t_move=s.t
        if v.phase is Phase.CHANGING:
            lats.append(v.lat)
            if v.indicator=='off':raise AssertionError('seta apagada durante a transição')
        assert not s.overlaps()
    assert t_on is not None and t_move is not None and t_move-t_on>=1.0-1e-6
    ev=[e for e in s.events if e['id']=='rapido']
    kinds=[(e['kind'],e.get('side')) for e in ev]
    assert ('indicator_on','left') in kinds and ('indicator_on','right') in kinds     # esquerda para sair, direita para voltar
    assert s.vehicles['rapido'].lane_id=='f0' and s.vehicles['rapido'].s>s.vehicles['lento'].s
    assert ind[-1]=='off' and s.vehicles['rapido'].lat==0.


def test_transicao_lateral_monotona_e_rumo_tangente():
    net=reta(2,comp=3000.,between=[B.OPEN]);s=Simulation(net);v=Vehicle('a','f0',100.,v=14.);s.add_vehicle(v)
    s._index();s._pose(v);v.indicator='left';v.lc=__import__('app.microsim.vehicle',fromlist=['x']).LaneChange(side=1,to_lane='f1',from_lane='f0',reason='t')
    s._commit(v,v.s);lat=[];hd=[]
    for _ in range(80):
        s.step()
        if v.phase is Phase.CHANGING:lat.append(v.lat);hd.append(v.heading)
    assert all(abs(b)<=abs(a)+1e-9 for a,b in zip(lat,lat[1:])) and abs(lat[0])>1.0
    assert max(abs(h) for h in hd)<math.radians(10) and max(abs(h) for h in hd)>0          # esterçamento suave, sem salto


def test_limites_das_layers_bloqueiam_troca():
    for kind in (B.SOLID_LINE,B.MEDIAN,B.BARRIER,B.EDGE):
        net=reta(2,comp=3000.,between=[kind]);s=Simulation(net)
        s.add_vehicle(Vehicle('lento','f0',300.,v=8.,params=VehicleParams(v0_factor=.45)));s.add_vehicle(Vehicle('r','f0',250.,v=14.))
        s.run(60);assert s.stats['lane_changes']==0,kind
        assert all(v.lane_id=='f0' for v in s.vehicles.values())


def test_novo_seguidor_inseguro_bloqueia_troca():
    net=reta(2,comp=3000.,between=[B.OPEN]);s=Simulation(net)
    s.add_vehicle(Vehicle('lento','f0',300.,v=8.,params=VehicleParams(v0_factor=.45)));s.add_vehicle(Vehicle('r','f0',270.,v=8.))
    s.add_vehicle(Vehicle('x','f1',262.,v=25.,params=VehicleParams(v0_factor=1.6)))       # veloz colado na faixa vizinha
    n0=s.stats['lane_changes']
    for _ in range(20):
        s.step()
        assert not (s.vehicles['r'].phase is Phase.CHANGING and s.vehicles['x'].s-s.vehicles['r'].s<0 and s.vehicles['r'].s-s.vehicles['x'].s<12 and s.vehicles['r'].v<s.vehicles['x'].v-8)


def test_interdicao_zipper_ninguem_entra_no_trecho_fechado():
    net=reta(2,comp=1500.,between=[B.OPEN]);net.add_closure(LaneClosure('f0',700.,900.));s=Simulation(net)
    for i in range(5):s.add_vehicle(Vehicle(f'c{i}','f0',50.+i*40,v=14.))
    for i in range(4):s.add_vehicle(Vehicle(f'd{i}','f1',70.+i*45,v=14.))
    for _ in range(1200):
        s.step();assert not s.overlaps()
        for v in s.vehicles.values():
            if v.lane_id=='f0' and v.phase is not Phase.CHANGING:assert not(700.<v.s<900.),(v.id,v.s)
    assert s.stats['lane_changes']>=1


def test_classificacao_de_layers():
    r=LayerRules()
    assert r.classify('BARREIRA_NEWJERSEY') is B.BARRIER and r.classify('Canteiro central') is B.MEDIAN
    assert r.classify('BORDO_PISTA') is B.EDGE and r.classify('LINHA_TRACEJADA') is B.OPEN
    assert r.classify('qualquer coisa') is B.SOLID_LINE


def test_faixas_paralelas_lado_correto_e_validacao():
    net=reta(3,between=[B.OPEN,B.MEDIAN]);assert net.validate()==[]
    ys=[net.lanes[f'f{i}'].center[0][1] for i in range(3)];assert ys[0]<ys[1]<ys[2]          # f0 = direita (y menor)
    assert net.lanes['f1'].boundary(1) is B.MEDIAN and net.lanes['f2'].boundary(-1) is B.MEDIAN


def test_failsafe_impede_sobreposicao_mesmo_com_idm_sabotado(monkeypatch):
    import app.microsim.engine as eng
    monkeypatch.setattr(eng,'idm_accel',lambda v,v0,gap,dv,p:1.5)       # acelera sempre, ignora o líder
    net=reta(comp=3000.);s=Simulation(net)
    s.add_vehicle(Vehicle('l','f0',60.,v=3.));s.add_vehicle(Vehicle('f','f0',20.,v=15.))
    for _ in range(300):
        s.step();assert not s.overlaps()
    assert s.stats['frozen']>0


def test_denso_aleatorio_sem_sobreposicao_e_desempenho():
    random.seed(7);net=reta(3,comp=3000.,between=[B.OPEN,B.OPEN]);s=Simulation(net);k=0
    for lane in ('f0','f1','f2'):
        for i in range(25):
            try:s.add_vehicle(Vehicle(f'{lane}-{i}',lane,10+i*28+random.uniform(0,6),v=random.uniform(5,16),params=VehicleParams(v0_factor=random.uniform(.5,1.2))));k+=1
            except ValueError:pass
    assert k>=60;t0=time.time()
    for _ in range(600):
        s.step();assert not s.overlaps()
    dt=time.time()-t0;assert dt<40,dt
    assert s.stats['lane_changes']>0
