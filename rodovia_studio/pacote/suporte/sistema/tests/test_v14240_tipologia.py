"""1.42.40: tipologia do eixo, retorno à faixa, pavimento ausente sem erro e linhas transversais ignoradas."""
import hashlib,sys
import numpy as np
import pytest
from shapely.geometry import box,LineString
from app.models import Settings
from app.native_axes import native_paths,axis_fingerprint,ROLE_KIND
from app.routes import cap_lane_change
from app.flow_fit import physical_obstacles,crosses_transversally


def test_modelo_aceita_tipologias_e_recusa_invalida():
    assert Settings(axis_types={'axis:x':'pista_dupla'}).axis_types=={'axis:x':'pista_dupla'}
    for t in ('auto','pista_simples','pista_dupla','acesso','retorno','dispositivo'):Settings(axis_types={'axis:x':t})
    with pytest.raises(Exception):Settings(axis_types={'axis:x':'qualquer'})


def test_tipologia_so_restringe_ultrapassagem():
    assert cap_lane_change('safe','acesso')=='off' and cap_lane_change('marked','dispositivo')=='off'
    assert cap_lane_change('safe','pista_simples')=='marked' and cap_lane_change('off','pista_simples')=='off'
    assert cap_lane_change('safe','pista_dupla')=='safe' and cap_lane_change('safe','auto')=='safe' and cap_lane_change('marked','retorno')=='off'


def _axes():
    p=np.array([[0.,0.],[300.,0.]]);return [dict(points=p,layer='EIXO',level=0)],axis_fingerprint(p,'EIXO',0)


def test_eixo_nativo_leva_tipologia_e_papel_no_fluxo():
    axes,fp=_axes()
    for tipo in ('pista_simples','acesso','retorno','dispositivo'):
        s=Settings(layers={'axis':['EIXO']},axis_types={'axis:'+fp:tipo})
        rows,_=native_paths(axes,s,box(-10,-10,310,10))
        assert rows[0]['axis_type']==tipo
        assert (rows[0].get('flow_role')==tipo) if tipo in ROLE_KIND else 'flow_role' not in rows[0]
    rows,_=native_paths(axes,Settings(layers={'axis':['EIXO']}),box(-10,-10,310,10));assert rows[0]['axis_type']=='auto'


def test_alinhamento_vinculado_ao_eixo_recebe_o_limite():
    from app.routes import raw_paths
    axes,fp=_axes()
    def paths(tipo):
        s=Settings(axis_types={'axis:'+fp:tipo} if tipo else {},route_alignments=[dict(id='r',name='R',points=[dict(x=0,y=0),dict(x=300,y=0)],type='dupla',lanes=2,lane_change='safe',source_axis_fingerprint=fp)])
        return raw_paths(s)
    assert {p['lane_change'] for p in paths(None)}=={'safe'}
    assert {p['lane_change'] for p in paths('acesso')}=={'off'} and {p['axis_type'] for p in paths('acesso')}=={'acesso'}
    assert {p['lane_change'] for p in paths('pista_simples')}=={'marked'}


def test_linhas_transversais_ignoradas_exceto_canteiro():
    eixo=[dict(points=np.array([[0.,0.],[300.,0.]]))]
    transv=dict(points=[[100,-8],[100,8]],closed=False,role='barrier')
    paralela=dict(points=[[0,5],[300,5]],closed=False,role='barrier')
    canteiro=dict(points=[[100,-1],[200,-1],[200,1],[100,1]],closed=True,role='median')
    assert physical_obstacles([transv],eixo)==[]
    assert len(physical_obstacles([paralela],eixo))==1 and len(physical_obstacles([canteiro,transv,paralela],eixo))==2
    assert len(physical_obstacles([transv]))==1            # sem eixo conhecido: comportamento anterior
    assert crosses_transversally(LineString([[100,-8],[100,8]]),eixo) and not crosses_transversally(LineString([[0,5],[300,5]]),eixo)


def test_sem_pavimento_nao_gera_erro_nem_veiculos():
    from app.traffic import TrafficNetwork
    from app.simulation import TrafficSim
    from tests.test_v14212_traffic_safety import configuration
    cfg=configuration(duration_s=20);p=np.array([[0.,0.],[600.,0.]])
    for roads in ([],[box(0,0,0,0)]):
        net=TrafficNetwork(roads,[],[dict(points=p)],p,np.array([0.,600.]),cfg)
        sim=TrafficSim(net,cfg,lambda *a:'car',duration=20)
        assert sim.report()['vehicles']==0 and sim.state(5.)==[] and sim.vehicle_body_state(5.)==[]


def test_ultrapassa_e_volta_a_faixa_sem_colisao(monkeypatch):
    sys.path.insert(0,'/tmp');import importlib
    from app import simulation
    from app.traffic import TrafficNetwork
    def run(mode):
        monkeypatch.setattr(simulation,'WARMUP',0);orig=np.random.default_rng
        class A:
            def __init__(s,*a,**k):s.r=orig(*a,**k)
            def exponential(s,*a,**k):return 12.
            def __getattr__(s,n):return getattr(s.r,n)
        monkeypatch.setattr(simulation.np.random,'default_rng',A);monkeypatch.setitem(simulation.SPEED_FACTOR,'truck18',.35)
        try:
            s=Settings(route_alignments=[dict(id='r',name='Via',points=[dict(x=0,y=0),dict(x=1500,y=0)],type='dupla',lanes=2,lane_change='safe',taper_m=60)],derive_traffic_paths=False,hydrography=False,traffic_density=3,duration_s=120,traffic_speed_kmh=80,queue_capacity_model=False,**mode)
            a=np.array([[0.,0.],[1500.,0.]]);net=TrafficNetwork([box(-30,-12,1530,12)],[],[],a,np.array([0.,1500.]),s);k=[0]
            def vt(kinds,identity):k[0]+=1;return 'truck18' if k[0]%4==0 else 'car'
            return simulation.TrafficSim(net,s,vt,duration=120).report()
        finally:pass
    r=run({});assert r['lane_changes']>0 and r['lane_returns']>0 and r['rear_collisions']==0 and r['side_collisions']==0


def _rede(roads,edge_lines=(),**kw):
    from app.traffic import TrafficNetwork
    from tests.test_v14212_traffic_safety import configuration
    cfg=configuration(duration_s=40,**kw);p=np.array([[0.,0.],[600.,0.]])
    return cfg,TrafficNetwork(roads,[],[dict(points=p)],p,np.array([0.,600.]),cfg,edge_lines=edge_lines)


def test_junta_de_hachura_nao_interrompe_o_fluxo():
    from app.simulation import TrafficSim
    from app.flow_fit import close_seams
    from shapely.ops import unary_union
    roads=[box(-30,-6,300,6),box(300.3,-6,630,6)]                       # fresta de 0,3 m entre duas hachuras
    assert not unary_union(roads).contains(box(299,-1,302,1)) and close_seams(unary_union(roads)).contains(box(299,-1,302,1))
    cfg,net=_rede(roads);sim=TrafficSim(net,cfg,lambda *a:'car',duration=40)
    r=sim.report();assert r['vehicles']>0 and r['motion_blocked_vehicles']==0 and r['rear_collisions']==0 and r['side_collisions']==0


def test_vazio_largo_e_canteiro_continuam_sendo_impedimento():
    from app.flow_fit import close_seams
    from shapely.ops import unary_union
    g=close_seams(unary_union([box(0,-6,300,-1.5),box(0,1.5,300,6)]))     # canteiro de 3 m
    assert not g.contains(box(100,-.5,110,.5))


def test_linha_de_bordo_conduz_e_transversal_e_ignorada():
    from app.flow_fit import edge_guide
    eixo=[dict(points=np.array([[0.,0.],[600.,0.]]))]
    g=edge_guide([np.array([[0.,5.],[600.,5.]]),np.array([[300.,-6.],[300.,6.]])],eixo)
    assert g.intersects(box(100,4.9,110,5.1)) and not g.intersects(box(299.5,-1,300.5,1))
    cfg,net=_rede([box(-30,-8,630,8)],edge_lines=[np.array([[0.,5.],[600.,5.]])])
    assert not net.allowed.contains(box(100,4.95,110,5.05)) and net.allowed.contains(box(100,-1,110,1))
    cfg,net=_rede([box(-30,-8,630,8)],edge_lines=[np.array([[0.,5.],[600.,5.]])],edge_line_guide=False)
    assert net.allowed.contains(box(100,4.95,110,5.05))
