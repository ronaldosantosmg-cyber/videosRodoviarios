"""2.19: pista dupla com faixas no mesmo sentido; eixo no meio da pista (sem canteiro) ou no bordo."""
import numpy as np,pytest
from app.road_sections import CrossSection,SectionBand,band_layout,section_offsets,section_lane_widths
from app.routes import lane_offsets,_build_lanes
from app.models import RouteAlignment

def band(w=3.5,k='pista',on=True):return SectionBand(kind=k,width_m=w,traffic_enabled=on)
def sec(**k):return CrossSection(**{'id':'s','start_m':0,'end_m':1000,**k})

def test_padrao_dois_sentidos_inalterado():
    s=sec(type='dupla',median_m=6,left=[band(),band()],right=[band(),band()])
    L=band_layout(s)
    assert L[('f',0)][0]==6/2+1.75 and L[('f',1)][0]==3+3.5+1.75
    assert L[('r',0)][0]==-(3+1.75) and L[('r',1)][0]==-(3+3.5+1.75)

def test_eixo_no_meio_da_pista_duas_faixas_mesmo_sentido():
    s=sec(left=[band()],right=[band()],left_dir='mesmo',right_dir='mesmo')
    L=band_layout(s)
    assert set(L)=={('f',0),('f',1)}
    assert L[('f',0)][0]==-1.75 and L[('f',1)][0]==1.75   # 0 = faixa mais à esquerda da marcha

def test_canteiro_so_com_pista_dos_dois_lados():
    with pytest.raises(ValueError):sec(type='dupla',median_m=3,left=[band(2.5,'acostamento',False)],right=[band()],left_dir='mesmo',right_dir='mesmo')

def test_duas_pistas_mesmo_sentido_com_canteiro_editavel():
    s=sec(type='dupla',median_m=4,left=[band(),band()],right=[band(),band()],left_dir='mesmo',right_dir='mesmo')
    L=band_layout(s)
    assert set(L)=={('f',0),('f',1),('f',2),('f',3)}
    offs=[L[('f',k)][0] for k in range(4)]
    assert offs==sorted(offs) and offs[2]-offs[1]==pytest.approx(4+3.5)   # canteiro de 4 m entre as pistas

def test_eixo_no_bordo_so_um_lado():
    s=sec(left=[band(2.5,'acostamento',False)],right=[band(),band()])
    L=band_layout(s)
    assert set(L)=={('f',0),('f',1)} and L[('f',0)][0]==1.75 and L[('f',1)][0]==5.25

def test_dois_sentidos_exigem_pista_nos_dois_lados():
    s=sec(left=[band()],right=[band()],left_dir='contrario',right_dir='contrario')   # tudo no sentido contrário
    assert set(band_layout(s))=={('r',0),('r',1)}

def test_sem_pista_e_erro():
    with pytest.raises(ValueError):sec(left=[band(2.5,'acostamento',False)],right=[])

def test_faixa_desabilitada_mantem_numeracao():
    s=sec(left=[band()],right=[band(on=False)],left_dir='mesmo',right_dir='mesmo')
    assert set(section_offsets(RouteAlignment(id='r',points=[{'x':0,'y':0},{'x':1000,'y':0}],cross_sections=[s]),np.array([10.]),[{}])[0])=={('f',0)}

def test_larguras_por_faixa():
    s=sec(left=[band(3.0)],right=[band(3.6)],left_dir='mesmo',right_dir='mesmo')
    assert section_lane_widths(s)=={('f',0):3.0,('f',1):3.6}

def test_rota_unico_centro_e_bordos():
    o=lane_offsets(['unico'],[2],[0],3.5,['centro'])[0];assert o=={('f',0):-1.75,('f',1):1.75}
    o=lane_offsets(['unico'],[2],[0],3.5,['bordo_esquerdo'])[0];assert o=={('f',0):1.75,('f',1):5.25}
    o=lane_offsets(['unico'],[2],[0],3.5,['bordo_direito'])[0];assert o=={('f',0):-5.25,('f',1):-1.75}

def test_geracao_de_faixas_reais_mesmo_sentido():
    r=RouteAlignment(id='r',name='x',points=[{'x':0,'y':0},{'x':400,'y':0}],sections_only=True,cross_sections=[sec(end_m=400,left=[band()],right=[band()],left_dir='mesmo',right_dir='mesmo')])
    lanes=_build_lanes(r)
    assert {l['dir'] for l in lanes}=={'f'} and len(lanes)==2
    ys=sorted(float(np.mean(l['points'][:,1])) for l in lanes)
    assert abs(ys[1]-ys[0])==pytest.approx(3.5,abs=.05)
    assert all(l['points'][-1][0]>l['points'][0][0] for l in lanes)    # no sentido do eixo, sem canteiro entre elas


def test_sentido_unico_por_secao_percorrido_ao_contrario_e_espelhado():
    r=RouteAlignment(id='r',name='x',points=[{'x':0,'y':0},{'x':400,'y':0}],flow_role='principal',flow_start='saida',flow_end='entrada',sections_only=True,
        cross_sections=[sec(end_m=400,left=[band()],right=[band()],left_dir='mesmo',right_dir='mesmo')])
    lanes=_build_lanes(r)
    assert {l['dir'] for l in lanes}=={'r'} and len(lanes)==2
    assert all(l['points'][-1][0]<l['points'][0][0] for l in lanes)   # percorre do fim para o início


from types import SimpleNamespace

def _rota(fp='a'*64,**k):
    base=dict(id='r',name='x',points=[{'x':0,'y':0},{'x':400,'y':0}],sections_only=True,source_axis_fingerprint=fp,
              cross_sections=[sec(end_m=400,left=[band()],right=[band()])])
    base.update(k);return RouteAlignment(**base)

def test_sentido_do_eixo_vale_para_secao_cadastrada():
    fp='b'*64
    for valor,esperado in (('forward','f'),('reverse','r')):
        st=SimpleNamespace(route_directions={'axis:'+fp:valor},alternating_zones=[])
        lanes=_build_lanes(_rota(fp),st)
        assert {l['dir'] for l in lanes}=={esperado}
    st=SimpleNamespace(route_directions={},alternating_zones=[])
    assert {l['dir'] for l in _build_lanes(_rota(fp),st)}=={'f','r'}

def test_sentido_proprio_da_rota_vence_o_do_eixo():
    fp='c'*64;st=SimpleNamespace(route_directions={'axis:'+fp:'reverse'},alternating_zones=[])
    lanes=_build_lanes(_rota(fp,flow_direction='crescente'),st)
    assert {l['dir'] for l in lanes}=={'f'}

def test_secao_de_um_sentido_segue_decrescente_do_eixo():
    fp='d'*64;st=SimpleNamespace(route_directions={'axis:'+fp:'reverse'},alternating_zones=[])
    r=_rota(fp,cross_sections=[sec(end_m=400,left=[band()],right=[band()],left_dir='mesmo',right_dir='mesmo')])
    lanes=_build_lanes(r,st)
    assert len(lanes)==2 and {l['dir'] for l in lanes}=={'r'} and all(l['points'][-1][0]<l['points'][0][0] for l in lanes)

