from pathlib import Path
from app.models import RouteAlignment
from app.routes import _build_lanes
from app.flow_nodes import orient_offsets
PTS=[{'x':i*100.,'y':0.} for i in range(101)]
P={'kind':'pista'}
D=dict(id='d',name='dupla',start_m=0,end_m=10000,type='dupla',median_m=3,left=[P,P],right=[P,P])
S=dict(id='s',name='simples',start_m=3000,end_m=5000,type='simples',left=[P],right=[P])
def rota(secs,**k):
    return RouteAlignment.model_validate({'id':'r','name':'r','points':PTS,'sections_only':True,'cross_sections':secs,**k})
def test_secao_nova_recorta_a_anterior():
    r=rota([D,S]);iv=[(s.start_m,s.end_m) for s in r.cross_sections]
    assert iv==[(0,3000),(3000,5000),(5000,10000)]
    assert len({s.id for s in r.cross_sections})==3
def test_simples_no_meio_da_dupla_gera_faixas():
    L=_build_lanes(rota([D,S]))
    assert {(l['dir'],l['lane']) for l in L}=={('f',0),('f',1),('r',0),('r',1)}
def test_sentido_explicito_filtra_e_misto_preserva_pista_dupla_sentido():
    o=[{('f',0):1.75,('r',0):-1.75}]
    r2=rota([S|dict(start_m=0,end_m=10000)],flow_direction='crescente')
    assert orient_offsets(r2,o,0)==[{('f',0):1.75}]
    um=dict(id='u',name='um',start_m=0,end_m=1000,type='simples',left=[P],right=[P],left_dir='mesmo',right_dir='mesmo')
    r3=rota([um,S|dict(start_m=2000,end_m=4000)],flow_direction='crescente')
    assert orient_offsets(r3,[{('f',0):-1.75,('f',1):1.75},o[0]],0)[1]==o[0]
def test_js_recorta_em_vez_de_bloquear():
    t=(Path(__file__).resolve().parents[1]/'app/js/65_secoes_pare_siga.js').read_text(encoding='utf-8')
    assert 'function recortar' in t and 'sobrepõe outra seção' not in t
