"""2.39: a APRESENTAÇÃO (arestas da rede, setas de sinalização, nós) de uma seção acompanha o km: inverter o eixo inverte tudo junto."""
import numpy as np
from test_v130 import S,Y
from test_v110 import junction  # noqa: F401
from test_workflow import settings  # noqa: F401
FP='a'*64
def secao():
    sec={'id':'s1','name':'S','start_m':0,'end_m':360,'type':'simples','median_m':0,'left':[{'kind':'pista','width_m':3.6,'traffic_enabled':True}],'right':[{'kind':'pista','width_m':3.6,'traffic_enabled':True}],'left_dir':'mesmo','right_dir':'mesmo'}
    return {'id':'r1','name':'Rota A','points':[{'x':500020,'y':Y},{'x':500380,'y':Y}],'type':'simples','lanes':1,'source':'eixo_dxf','source_axis_fingerprint':FP,'source_axis_layer':'EIXO','sections_only':True,'section_surface':True,'cross_sections':[sec]}
def cena(junction,reverse,sentido):
    from app.render import Scene
    return Scene.light(junction,S(derive_traffic_paths=False,reverse_axis=reverse,route_directions={'axis:'+FP:sentido},route_alignments=[secao()]))
def leitura(sc):
    E=[e for e in sc.network.edges if e['source'].startswith('Rota A') and not e['disabled']]
    dx=sorted({int(np.sign(e['p'][-1][0]-e['p'][0][0])) for e in E})
    tx=[float(np.sign(e['t'][len(e['t'])//2][0])) for e in E]
    A=[t for p,t in sc.network.arrows if abs(p[1]-Y)<8 and 500020<=p[0]<=500380]
    return E,dx,tx,sorted({int(np.sign(t[0])) for t in A})
def rumo_veiculos(sc):
    """Rumo (x) dos veículos da simulação — é o que o vídeo e o 3D desenham."""
    sim=sc.traffic();out=set()
    for t in (4.,8.,12.):
        for v in sim.vehicles_ex(t):
            if abs(v[0][1]-Y)<8 and 500020<=v[0][0]<=500380:out.add(int(np.sign(v[1][0])))
    return sorted(out)
def test_apresentacao_acompanha_o_km_ao_inverter_eixo(junction):
    r={}
    for rev in (False,True):
        for sent in ('forward','reverse'):
            sc=cena(junction,rev,sent);E,dx,tx,ax=leitura(sc);assert E,(rev,sent)
            r[(rev,sent)]=(dx,sorted(set(tx)),ax,rumo_veiculos(sc))
    # sem inverter: Crescente = x crescente (km cresce para leste no DXF de teste)
    km_leste=r[(False,'forward')][0]
    assert len(km_leste)==1
    # inverter o eixo troca o sentido físico de Crescente; Decrescente com inversão == Crescente sem inversão
    assert r[(True,'forward')][0]==r[(False,'reverse')][0]!=km_leste
    assert r[(True,'reverse')][0]==km_leste
    # setas de sinalização e tangentes das arestas concordam com as arestas (mesma apresentação)
    for k,(dx,tx,ax,vx) in r.items():
        assert tx==[float(dx[0])],(k,dx,tx)
        assert not ax or ax==dx,(k,dx,ax)
        assert vx==dx,('veículos (vídeo/3D) divergem das arestas',k,dx,vx)   # vídeo e 3D leem a mesma simulação
