"""2.44: frota “Rodovia brasileira realista” — classes com dimensões reais em todas as tabelas, mistura estável, cores ponderadas, motoristas com
comportamento contínuo e simulação sem colisão com todas as classes ao mesmo tempo."""
import collections,pathlib,tempfile
import numpy as np,cv2,ezdxf
from app import visual
from app.visual import TYPES,vehicle_type,vehicle_color,FROTA_BR,MIX_BR_RODOVIA,MIX_BR_RAMO
from app.vehicle_motion import PROFILES
from app import simulation as sm
NOVAS=[x[0] for x in FROTA_BR]

def test_novas_classes_estao_em_todas_as_tabelas():
    for k in NOVAS:
        assert k in TYPES and k in PROFILES and k in sm.TYPE_DYN and k in sm.SPEED_FACTOR and k in sm._LEN,k
        L,B=TYPES[k]['L'],TYPES[k]['B'];assert PROFILES[k][0]==L and PROFILES[k][1]==B,(k,L,B,PROFILES[k])
        assert TYPES[k]['view'] in ('car','truck','bus','carreta')
def test_mistura_rodovia_segue_a_tabela_e_nao_cicla():
    n=20000;c=collections.Counter(vehicle_type({'main'},(3,v,0),'rodovia_br') for v in range(n))
    assert set(c)=={k for k,_ in MIX_BR_RODOVIA}
    assert sum(p for _,p in MIX_BR_RODOVIA)==100==sum(p for _,p in MIX_BR_RAMO)
    for k,pct in MIX_BR_RODOVIA:assert abs(100*c[k]/n-pct)<2.0,(k,100*c[k]/n,pct)
    # sem ciclo de 100: as 100 primeiras e as 100 seguintes não são iguais
    a=[vehicle_type({'main'},(3,v,0),'rodovia_br') for v in range(100)];b=[vehicle_type({'main'},(3,v,0),'rodovia_br') for v in range(100,200)]
    assert a!=b
def test_ramos_tem_menos_pesados():
    n=5000;pesados={'carreta','bitrem','toco','cacamba','truck','onibus13','bus'}
    r=sum(vehicle_type({'access'},(1,v,0),'rodovia_br') in pesados for v in range(n))/n;m=sum(vehicle_type({'main'},(1,v,0),'rodovia_br') in pesados for v in range(n))/n
    assert r<.08 and m>.2 and m>3*r
def test_cores_ponderadas_e_validas():
    c=collections.Counter(vehicle_color((2,v,0),'sedan') for v in range(5000))
    assert all(len(x)==3 and all(0<=u<=255 for u in x) for x in c)
    claras=sum(n for x,n in c.items() if x in [(236,236,232),(196,199,200),(58,60,64),(118,122,126)])/5000
    assert .7<claras<.9,claras
    assert len({vehicle_color((2,v,0),'onibus13') for v in range(500)})>=6
def test_todas_as_classes_desenham_sem_erro():
    for k in ['car','moto','pickup','van','truck','bus','carreta']+NOVAS:
        im=np.full((120,300,3),90,np.uint8);T=TYPES[k]
        screen=lambda P:np.asarray(P,float)*8+np.array([150.,60.])
        visual.draw_vehicle(im,np.array([0.,0.]),np.array([1.,0.]),k,vehicle_color((1,2,0),k),screen,1/8.)
        assert (im!=90).any(),k
def test_motoristas_variam_de_forma_continua_e_pesados_menos():
    leves=[];pesados=[]
    for vid in range(2000):
        for vt,dest in (('sedan',leves),('carreta',pesados)):
            v={'v0':25.};sm.TrafficSim.driver_variety(v,vid,vt);dest.append((v['v0'],v['T_k'],v['acc_k']))
    L=np.array(leves);H=np.array(pesados)
    assert L[:,0].std()>.8 and L[:,1].min()<.85 and L[:,1].max()>1.15
    assert H[:,0].std()<L[:,0].std() and len({round(x,3) for x in L[:,0]})>500
def test_simulacao_com_todas_as_classes_sem_colisao():
    from test_v110 import S
    from app.render import Scene
    d=ezdxf.new();m=d.modelspace()
    for l in ['EIXO','PAVIMENTO']:d.layers.new(l)
    m.add_lwpolyline([(500000,7800000),(500900,7800000)],dxfattribs={'layer':'EIXO'})
    h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path([(500000,7799986),(500900,7799986),(500900,7800014),(500000,7800014)],is_closed=True)
    tmp=pathlib.Path(tempfile.mkdtemp());d.saveas(tmp/'input.dxf')
    sc=Scene(tmp,S(vehicle_mix='rodovia_br',route_directions={'layer:EIXO':'forward'},traffic=True,traffic_density=1.0,traffic_demand_vphpl=1500));sim=sc.traffic()
    list(sim.vehicles_ex(10.))
    tipos={vt for (_,vt,_) in sim.info.values()}
    assert len(tipos)>=9,tipos
    rep=sim.report();assert rep.get('collisions',0)==0 and rep.get('side_collisions',0)==0,rep
