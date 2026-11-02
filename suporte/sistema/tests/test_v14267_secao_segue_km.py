"""2.39: Crescente (km) vale para SEÇÕES como para eixos. Se o km cresce contra a ordem do desenho (início/fim, “inverter eixo”,
estaqueamento manual), a seção cadastrada sobre o eixo circula no sentido do KM, e muda quando o km é invertido."""
import numpy as np
from fastapi.testclient import TestClient
from test_v14265_uniformidade_sentido import S,eixos,rota,dirs_por_rota
from app import routes
from app.native_axes import axis_fingerprint

MAIN=np.array([[0.,0.],[300.,0.]]);DS=np.array([0.,300.])
def dirs(rd,axis_order,km_dir=1,mode='meio'):
    A=eixos();rotas=[rota(a,mode) for a in A]
    st=S(rd,rotas);chain=routes.make_chain(axis_order,DS,km_dir)
    with routes.km_context(chain):
        return {r.name:v for r,v in zip(rotas,[dirs_por_rota(st,routes.raw_paths(st)).get(r.id) for r in rotas])},A,rotas
def todos(rd,axis_order,km_dir=1,mode='meio'):
    d,A,_=dirs(rd,axis_order,km_dir,mode);return set(map(frozenset,d.values()))

def test_km_crescente_no_desenho_secao_vai_no_sentido_do_desenho():
    A=eixos();rd={'axis:'+a['fp']:'forward' for a in A}
    assert todos(rd,MAIN)=={frozenset({'f'})}
def test_inverter_eixo_inverte_a_secao_porque_o_km_inverteu():
    A=eixos();rd={'axis:'+a['fp']:'forward' for a in A}
    assert todos(rd,MAIN[::-1].copy())=={frozenset({'r'})}          # eixo principal invertido: km cresce contra o desenho
    rd2={'axis:'+a['fp']:'reverse' for a in A}
    assert todos(rd2,MAIN[::-1].copy())=={frozenset({'f'})}
def test_estaqueamento_manual_invertido_tambem_vale():
    A=eixos();rd={'axis:'+a['fp']:'forward' for a in A}
    assert todos(rd,MAIN,km_dir=-1)=={frozenset({'r'})}
def test_dois_sentidos_forward_mantem_so_a_faixa_do_km():
    A=eixos();rd={'axis:'+a['fp']:'forward' for a in A}
    assert todos(rd,MAIN[::-1].copy(),mode='dois')=={frozenset({'r'})}
    assert todos(rd,MAIN,mode='dois')=={frozenset({'f'})}
def test_sem_contexto_de_km_nada_muda_compatibilidade():
    A=eixos();rotas=[rota(a,'meio') for a in A];rd={'axis:'+a['fp']:'forward' for a in A};st=S(rd,rotas)
    assert set(map(frozenset,dirs_por_rota(st,routes.raw_paths(st)).values()))=={frozenset({'f'})}
def test_previa_usa_km_signs_da_tela():
    from app.server import app
    c=TestClient(app);A=eixos();a=A[0];r=rota(a,'meio');fp=a['fp']
    body=lambda k:{'route_alignments':[r.model_dump()],'route_directions':{'axis:'+fp:'forward'},'km_signs':{r.id:k}}
    d=lambda k:sorted({l['dir'] for l in c.post('/api/rotas_previa',json=body(k)).json()['lanes']})
    assert d(1)==['f'] and d(-1)==['r']
def test_front_envia_sinal_do_km_e_observa_inverter_eixo():
    from pathlib import Path
    t=(Path(__file__).resolve().parents[1]/'app'/'js'/'32_rotas.js').read_text(encoding='utf-8')
    assert 'km_signs:routeKmSigns()' in t and 'reverseAxisPendente()' in t.split('function routeSignature')[1].split('\n')[0]
