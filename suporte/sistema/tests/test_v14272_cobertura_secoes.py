"""2.43: (a) a seção só autoriza circulação fora da hachura onde o usuário mandou (por seção); (b) faixa de seção sem pavimento/obstáculo é DIAGNOSTICADA com intervalo e motivo;
(c) duas faixas no mesmo sentido circulam as duas quando há pavimento para as duas."""
import collections,pathlib,tempfile
import numpy as np,ezdxf
from app.models import RouteAlignment
from test_v110 import S
from app.render import Scene
P=lambda w=3.5:{'kind':'pista','width_m':w,'traffic_enabled':True}
def dxf(largura,comp=600,tunel=None):
    d=ezdxf.new();m=d.modelspace()
    for l in ['EIXO','PAVIMENTO']:d.layers.new(l)
    m.add_lwpolyline([(500000,7800000),(500000+comp,7800000)],dxfattribs={'layer':'EIXO'})
    trechos=[(0,comp)] if not tunel else [(0,tunel[0]),(tunel[1],comp)]
    for a,b in trechos:
        h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path([(500000+a,7800000-largura),(500000+b,7800000-largura),(500000+b,7800000+2),(500000+a,7800000+2)],is_closed=True)
    tmp=pathlib.Path(tempfile.mkdtemp());d.saveas(tmp/'input.dxf');return tmp
def rota(secs,comp=600):
    return RouteAlignment.model_validate({'id':'r1','name':'Eixo','points':[{'x':500000,'y':7800000},{'x':500000+comp,'y':7800000}],'enabled':True,'type':'simples','lanes':1,'lane_width_m':3.5,'source':'eixo_dxf','sections_only':True,'cross_sections':secs})
def sec(i,a,b,**k):
    base={'id':i,'name':'S'+i,'start_m':a,'end_m':b,'type':'simples','median_m':0,'left':[],'right':[P(),P()],'left_dir':'contrario','right_dir':'mesmo'};base.update(k);return base
def veiculos_por_y(sc,ate=60,passo=2.):
    sim=sc.traffic();c=collections.Counter()
    for t in np.arange(0,ate,passo):
        for v in sim.vehicles_ex(t):c[round(float(v[0][1])-7800000,0)]+=1
    return c
def test_duas_faixas_mesmo_sentido_circulam_as_duas():
    tmp=dxf(9)    # pavimento cobre as duas faixas (3,5 + 3,5 m à direita do eixo)
    sc=Scene(tmp,S(route_alignments=[rota([sec('a',0,600)])],traffic=True,traffic_density=1.0,traffic_demand_vphpl=1800))
    c=veiculos_por_y(sc);faixas=[y for y,n in c.items() if n>20]
    assert len(faixas)==2,c
def test_sem_autorizacao_nao_ha_veiculo_onde_nao_ha_hachura_e_o_trecho_e_diagnosticado():
    tmp=dxf(9,tunel=(200,400))    # 200–400 m: sem hachura (túnel existente)
    secs=[sec('a',0,600,authorize_surface=False)]
    sc=Scene(tmp,S(route_alignments=[rota(secs)],traffic=True,traffic_density=1.0,traffic_demand_vphpl=1800))
    xs=[float(v[0][0])-500000 for t in np.arange(0,80,2.) for v in sc.traffic().vehicles_ex(t)]
    assert xs and not [x for x in xs if 215<x<385],'veículo sobre área sem pavimento'
    gaps=[g for c in sc.network.lane_coverage for g in c['gaps']]
    assert gaps and any(g['reason']=='sem hachura de pavimento' and g['start_m']<230 and g['end_m']>370 for g in gaps),gaps
    assert any('sem circulação' in w for w in sc.network.coverage_warnings())
def test_com_autorizacao_a_secao_circula_fora_da_hachura_e_avisa():
    tmp=dxf(9,tunel=(200,400))
    sc=Scene(tmp,S(route_alignments=[rota([sec('a',0,600,authorize_surface=True)])],traffic=True,traffic_density=1.0,traffic_demand_vphpl=1800))
    xs=[float(v[0][0])-500000 for t in np.arange(0,80,2.) for v in sc.traffic().vehicles_ex(t)]
    assert [x for x in xs if 230<x<370]
    assert any('FORA da hachura' in w for w in sc.network.coverage_warnings())
def test_autorizacao_por_secao_so_vale_no_trecho():
    tmp=dxf(9,tunel=(200,400))
    secs=[sec('a',0,300,authorize_surface=False),sec('b',300,600,authorize_surface=True)]
    sc=Scene(tmp,S(route_alignments=[rota(secs)],traffic=True,traffic_density=1.0,traffic_demand_vphpl=1800))
    xs=[float(v[0][0])-500000 for t in np.arange(0,120,2.) for v in sc.traffic().vehicles_ex(t)]
    assert not [x for x in xs if 215<x<290],'trecho sem autorização'      # 200–300: sem hachura e sem autorização
    assert [x for x in xs if 310<x<390],'trecho autorizado (300–400) deveria circular'
