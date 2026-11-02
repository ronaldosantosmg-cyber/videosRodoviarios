from test_v110 import junction  # noqa: F401
import numpy as np
from app.models import RouteAlignment
from app.road_sections import CrossSection,SectionBand
from app.transicao_secoes import transicoes,required_taper,eixo_amarelo,eixo_transicao
from app.routes import build_lanes

def B(k,w=3.5,t=True):return SectionBand(kind=k,width_m=w,traffic_enabled=t)
def simples(a,b,acost=2.5):
    L=[B('pista')]+([B('acostamento',acost,False)] if acost else []);return CrossSection(id=f's{a}',name='Pista simples',start_m=a,end_m=b,type='simples',left=L,right=[x.model_copy() for x in L],left_dir='contrario',right_dir='mesmo')
def dupla(a,b,med=3.):
    L=[B('pista'),B('pista'),B('acostamento',2.5,False)];return CrossSection(id=f'd{a}',name='Pista dupla',start_m=a,end_m=b,type='dupla',median_m=med,left=L,right=[x.model_copy() for x in L],left_dir='contrario',right_dir='mesmo')
def rota(secs,taper=40,n=2001,L=2000):
    pts=[dict(x=500000+i*L/(n-1),y=7800000) for i in range(n)]
    return RouteAlignment(name='R',points=pts,sections_only=True,taper_m=taper,cross_sections=secs)

def test_transicao_simples_dupla_detectada_e_dimensionada():
    r=rota([simples(0,900),dupla(900,2000)],taper=10)
    t=transicoes(r);assert len(t)==1 and t[0]['kind']=='pista simples → pista dupla'
    assert t[0]['shift_m']>1 and not t[0]['sufficient'] and t[0]['required_m']>=20*t[0]['shift_m']-1e-6
    assert required_taper(r)>10

def test_sem_mudanca_sem_transicao():
    assert transicoes(rota([simples(0,1000),simples(1000,2000)]))==[]
    assert required_taper(rota([simples(0,1000),simples(1000,2000)],taper=33))==33

def test_faixas_sem_salto_lateral_e_sentidos_opostos_nao_se_cruzam():
    r=rota([simples(0,900),dupla(900,2000)],taper=10);lanes=build_lanes(r)
    assert lanes
    for ln in lanes:
        P=np.asarray(ln['points']);dy=np.abs(np.diff(P[:,1]));ds=np.maximum(np.linalg.norm(np.diff(P,axis=0),axis=1),1e-9)
        assert (dy/ds).max()<=1/20+.01                     # inclinação lateral ≤ 1:20 (tolerância numérica)
    # faixas de sentidos opostos: sempre separadas lateralmente em cada x (nunca se cruzam)
    f=[np.asarray(l['points']) for l in lanes if l['dir']=='f'];rv=[np.asarray(l['points']) for l in lanes if l['dir']=='r']
    xs=np.arange(500010,501990,20.)
    for x in xs:
        yf=[np.interp(x,p[np.argsort(p[:,0]),0],p[np.argsort(p[:,0]),1]) for p in f if p[:,0].min()<=x<=p[:,0].max()]
        yr=[np.interp(x,p[np.argsort(p[:,0]),0],p[np.argsort(p[:,0]),1]) for p in rv if p[:,0].min()<=x<=p[:,0].max()]
        if yf and yr:assert min(yr)-max(yf)>=2.9          # sentidos opostos separados (f à direita do eixo, r à esquerda): nunca se cruzam

def test_eixo_amarelo_duplo_so_na_pista_simples_de_dois_sentidos():
    r=rota([simples(0,900),dupla(900,2000)])
    seg=eixo_amarelo(r);assert seg
    xs=np.array([a[0] for a,b in seg]);assert xs.max()<=900+500000+2 and xs.min()>=500000-1
    ys=sorted({round(float(a[1])-7800000,2) for a,b in seg});assert ys==[-.12,.12]
    assert eixo_amarelo(rota([dupla(0,2000)]))==[]

def test_eixo_de_transicao_tem_pontos_na_janela():
    e=eixo_transicao(rota([simples(0,900),dupla(900,2000)],taper=10));assert len(e)==1 and len(e[0]['points'])>=3

def test_eixo_amarelo_aparece_na_sinalizacao_da_pista_simples(junction):
    from app.render import Scene
    from app.signage import YELLOW
    from test_v132 import S
    r=RouteAlignment(name='R',points=[dict(x=500000+i*10,y=7800000) for i in range(41)],sections_only=False,cross_sections=[simples(0,400)])
    com=Scene(junction,S(route_alignments=[r]));sem=Scene(junction,S())
    amar=lambda n:sum(1 for m in n.markings if tuple(m[2])==tuple(YELLOW))
    assert sum(1 for k in com.network.mark_src if k==-7)>0 and amar(com.network)>amar(sem.network)   # eixo amarelo só existe com a seção cadastrada
