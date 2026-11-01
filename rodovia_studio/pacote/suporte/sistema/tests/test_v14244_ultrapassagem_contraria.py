from types import SimpleNamespace
import numpy as np
from shapely.geometry import box
from app.models import Settings
from app.shoulder_probe import ShoulderProbe,envelope
from app.vehicle_motion import prepare_points
from app.vehicle_safety import PolygonSafety
from app import passing_zones as PZ


def straight(length=1200.):
    return np.array([[x,0.] for x in np.arange(0,length+1,10.)])


def curve():
    t=np.linspace(0,np.pi/2,200);R=80.
    return np.column_stack([R*np.sin(t)+0,R*(1-np.cos(t))])*3  # raio ~240 m... curva fechada o bastante para testar o desvio da corda


def test_zonas_de_ultrapassagem_so_em_reta_visivel_e_longe_das_pontas():
    z=PZ.zones(straight(1200))
    assert z and z[0][0]>=PZ.END_MARGIN_M-1 and z[-1][1]<=1200-PZ.END_MARGIN_M+1
    sharp=np.column_stack([60*np.sin(np.linspace(0,np.pi,200)),60*(1-np.cos(np.linspace(0,np.pi,200)))])  # raio 60 m
    assert PZ.zones(sharp)==[]
    assert not PZ.window_allowed(straight(1200),0,100)            # perto da ponta
    assert not PZ.window_allowed(straight(1200),300,500,deny=[(400,450)])


def scenario(oncoming_s=None,width=(-6.,6.)):
    fwd=np.array([[x,-1.8] for x in np.arange(0,1200.1,5.)]);back=np.array([[x,1.8] for x in np.arange(1200,-0.1,-5.)])
    paved=box(-30,width[0],1230,width[1])
    sim=SimpleNamespace(s=Settings(opposite_overtake=True,opposite_overtake_share=1.0),paths=[dict(p=fwd,length=1200),dict(p=back,length=1200)],
        motion_points=[prepare_points(fwd),prepare_points(back)],net=SimpleNamespace(allowed=paved,operational_pavement=paved,shoulder_envelope=envelope(paved,[])),blocks=[],time=0,
        route_station=lambda i,s:s,_sec_value=lambda sec,k,d=None:sec.get(k,d))
    sim.polygon_safety=PolygonSafety(sim);sim.shoulder_probe=ShoulderProbe(sim)
    v=dict(id=1,p=0,s=300.,v=16.,v0=20.,t='car6',L=4.5,lc=None,prof='convencional')
    w=dict(id=2,p=0,s=325.,v=7.,v0=7.,t='car6',L=4.5,lc=None)
    veh=[v,w]
    if oncoming_s is not None:veh.append(dict(id=3,p=1,s=oncoming_s,v=18.,v0=18.,t='car6',L=4.5,lc=None))
    return sim,v,w,veh


def test_ultrapassa_pela_pista_contraria_quando_livre_e_retorna_sem_sobreposicao():
    sim,v,w,veh=scenario();probe=sim.shoulder_probe
    assert probe.try_pass_oncoming(v,w,veh),dict(probe.counts)
    e=probe.events[(1,0)][0];assert e['kind']=='ultrapassagem_contraria' and e['offset']<0
    assert probe.offset(e,e['stations'][0])==probe.offset(e,e['stations'][-1])==0
    assert any(abs(probe.offset(e,s))>2 for s in np.linspace(e['stations'][1],e['stations'][2],10))   # entra na pista oposta (y>0)
    for s in np.linspace(e['stations'][0],e['stations'][-1],201):
        ws=w['s']+(s-v['s'])/16*7
        assert not probe.geometry(v,s,e).intersection(probe.geometry({**w,'s':ws},ws)).area>1e-7


def test_recusa_com_veiculo_oposto_trecho_proibido_sem_pista_contraria_e_canteiro():
    sim,v,w,veh=scenario(oncoming_s=900.);assert not sim.shoulder_probe.try_pass_oncoming(v,w,veh)
    assert sim.shoulder_probe.counts['ultrapassagens_com_veiculo_oposto']==1
    sim,v,w,veh=scenario();sim.paths[0]['lane_change_sections']=[dict(mode='deny',start_m=250,end_m=700)]
    assert not sim.shoulder_probe.try_pass_oncoming(v,w,veh)
    sim,v,w,veh=scenario();sim.paths[0]['lane_change']='off';assert not sim.shoulder_probe.try_pass_oncoming(v,w,veh)
    sim,v,w,veh=scenario();sim.motion_points.pop();sim.paths.pop();assert not sim.shoulder_probe.try_pass_oncoming(v,w,veh[:2])
    sim,v,w,veh=scenario(width=(-6.,0.));assert not sim.shoulder_probe.try_pass_oncoming(v,w,veh)    # sem pavimento na pista contrária
    sim,v,w,veh=scenario();sim.s.opposite_overtake=False;assert not sim.shoulder_probe.try_pass_oncoming(v,w,veh)
    sim,v,w,veh=scenario();sim.s.opposite_overtake_share=0.;assert not sim.shoulder_probe.try_pass_oncoming(v,w,veh)


def test_pista_com_faixa_contraria_e_exposta_ao_editor():
    a=np.array([[x,-1.8] for x in np.arange(0,1200.1,5.)]);b=np.array([[x,1.8] for x in np.arange(1200,-0.1,-5.)]);c=np.array([[x,-1.8] for x in np.arange(0,1200.1,5.)])
    assert PZ.has_oncoming(a,[b]) and not PZ.has_oncoming(a,[c])
    from app.render import passing_zone_rows
    net=SimpleNamespace(paths=[dict(p=a),dict(p=b)]);rows=passing_zone_rows(net)
    assert rows and {r['path'] for r in rows}=={0,1} and all(len(r['p'])>=4 for r in rows)
    assert passing_zone_rows(SimpleNamespace(paths=[dict(p=a)]))==[]


def test_divisorias_geradas_partem_exatamente_do_eixo_do_dxf():
    from app.models import Settings
    from app.traffic import TrafficNetwork
    axis=np.array([[0.,0.],[400.,0.]])
    # eixo na borda esquerda (0,4 m) de um pavimento que se estende 10 m à direita (y negativo): 2 faixas de 3,5 m
    s=Settings(derive_traffic_paths=False,hydrography=False,layers={'axis':['EIXO']},signage_detail='full',lanes_per_direction=2,lane_width_m=3.5)
    n=TrafficNetwork([box(-20,-10,420,.4)],[],[dict(points=axis,layer='EIXO')],axis,np.array([0.,400.]),s,edge_lines=[])
    white=[(a,b) for a,b,c in n.markings if tuple(c)==(244,242,226)]
    ys=np.array([[a[1],b[1]] for a,b in white]).ravel()
    div=ys[(ys<-3.)&(ys>-4.)]
    assert len(div)>10 and np.allclose(div,-3.5,atol=.05),(len(div),ys.min(),ys.max())


def test_contorno_do_hatch_sem_juntas_internas_nem_linhas_perpendiculares():
    from app.webmap import vectors
    def blk(x0,x1,role='pavement'):return dict(role=role,layer='H',closed=True,points=np.array([[x0,-6.],[x1,-6.],[x1,6.],[x0,6.]]),holes=[])
    items=[blk(0,50),blk(50,100),blk(100,150),blk(20,80,'existing_pavement')]   # 3 blocos em série + um sobreposto
    axis=np.array([[0.,0.],[150.,0.]]);out=vectors(items,axis)['layers']
    kept=[]
    for role in ('pavement','existing_pavement'):
        for rec in out[role]:
            q=np.asarray(rec['p']);skip=set(rec.get('k',[]));n=len(q)
            for i in range(n if rec['c'] and not np.allclose(q[0],q[-1]) else n-1):
                a,b=q[i],q[(i+1)%n]
                if i not in skip:kept.append((a,b))
    long=[(a,b) for a,b in kept if abs(b[0]-a[0])>1]            # segmentos longitudinais
    assert all(abs(a[1])>=5.9 and abs(b[1])>=5.9 for a,b in long)       # só os bordos externos
    assert not [(a,b) for a,b in kept if abs(b[0]-a[0])<1e-6]          # nenhuma junta transversal traçada


def test_borda_gerada_cede_ao_contorno_do_dxf():
    from app.models import Settings
    from app.traffic import TrafficNetwork
    axis=np.array([[0.,0.],[400.,0.]])
    s=Settings(derive_traffic_paths=False,hydrography=False,layers={'axis':['EIXO']},signage_detail='full',lanes_per_direction=2,lane_width_m=3.5)
    n=TrafficNetwork([box(-20,-7.5,420,.4)],[],[dict(points=axis,layer='EIXO')],axis,np.array([0.,400.]),s,edge_lines=[])
    assert n.near_authoritative(np.array([[100.,-7.2],[100.,-3.5]]),1.2).tolist()==[True,False]
    assert n.perpendicular_to_axis(np.array([200.,-6.]),np.array([200.,0.])) and not n.perpendicular_to_axis(np.array([200.,-6.]),np.array([206.,-6.]))
