"""2.45: nível de serviço A–F — demanda por nível-alvo, classificação e medição na simulação."""
import pathlib,tempfile,types
import ezdxf
from app import nivel_servico as ns

def cfg(**k):return types.SimpleNamespace(**{'service_level_target':'manual','service_level_road':'pista_dupla','traffic_capacity_vphpl':1900.,'traffic_demand_vphpl':777.,'service_level_table':{},**k})
def test_manual_mantem_demanda_antiga():
    assert ns.demanda_efetiva(cfg())==777.
def test_demanda_cresce_de_A_a_F_e_cai_na_faixa_do_nivel():
    for tipo in ('pista_dupla','pista_simples'):
        d=[ns.demanda_efetiva(cfg(service_level_target=n,service_level_road=tipo)) for n in 'ABCDEF']
        assert d==sorted(d) and len(set(d))==6,(tipo,d)
        cap=min(1900.,ns.TABELAS[tipo]['capacidade_ref_vphpl'])
        for n,x in zip('ABCDE',d):
            lo,hi=ns.faixa_vc(tipo,n);assert lo<x/cap<=hi,(tipo,n)
        assert d[-1]>cap
def test_classificadores():
    assert ns.classificar_densidade('pista_dupla',5)=='A' and ns.classificar_densidade('pista_dupla',30)=='D' and ns.classificar_densidade('pista_dupla',60)=='F'
    assert ns.classificar_pelotao(20,95)=='A' and ns.classificar_pelotao(60,95)=='C' and ns.classificar_pelotao(20,65)=='D' and ns.classificar_pelotao(90,95)=='F'
    assert ns.classificar_vc('pista_dupla',.3)=='A' and ns.classificar_vc('pista_dupla',1.2)=='F'
    assert ns.pior('A','C',None)=='C'
def test_tabela_editavel():
    assert ns.classificar_densidade('pista_dupla',12,cfg(service_level_table={'pista_dupla':{'densidade_max':[20,30,40,50,60]}}))=='A'
def _sim(alvo):
    from test_v110 import S
    from app.render import Scene
    d=ezdxf.new();m=d.modelspace()
    for l in ['EIXO','PAVIMENTO']:d.layers.new(l)
    m.add_lwpolyline([(500000,7800000),(501500,7800000)],dxfattribs={'layer':'EIXO'})
    h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path([(500000,7799986),(501500,7799986),(501500,7800014),(500000,7800014)],is_closed=True)
    tmp=pathlib.Path(tempfile.mkdtemp());d.saveas(tmp/'input.dxf')
    sim=Scene(tmp,S(route_directions={'layer:EIXO':'forward'},traffic=True,service_level_target=alvo,service_level_road='pista_simples')).traffic()
    list(sim.vehicles_ex(240.));return sim.report()
def test_simulacao_nivel_alvo_ordena_o_nivel_medido():
    a=_sim('A')['level_of_service'];e=_sim('E')['level_of_service']
    assert a['disponivel'] and e['disponivel'],(a,e)
    assert ns.NIVEIS.index(a['nivel'])<=ns.NIVEIS.index(e['nivel']),(a['nivel'],e['nivel'])
    assert e['densidade_eq_km_faixa']>a['densidade_eq_km_faixa'] and e['pelotao_pct']>=a['pelotao_pct']
