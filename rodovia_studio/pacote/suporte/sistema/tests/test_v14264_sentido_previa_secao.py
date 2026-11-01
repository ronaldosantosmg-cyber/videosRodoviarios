"""2.37: a prévia das faixas de uma seção aplicada obedece ao sentido do eixo/layer e se refaz quando ele muda."""
from pathlib import Path
from fastapi.testclient import TestClient
from app.native_axes import axis_fingerprint
JS=Path(__file__).resolve().parents[1]/'app'/'js'

def rota(fp,left_dir):
    pts=[{'x':0.,'y':0.},{'x':100.,'y':0.},{'x':200.,'y':20.}]
    sec={'id':'s1','name':'S','start_m':0,'end_m':200,'type':'simples','median_m':0,'left':[{'kind':'pista','width_m':3.6,'traffic_enabled':True}],'right':[{'kind':'pista','width_m':3.6,'traffic_enabled':True}],'left_dir':left_dir,'right_dir':'mesmo'}
    return {'id':'r1','name':'Seção','points':pts,'enabled':True,'type':'simples','lanes':1,'lane_width_m':3.6,'source':'eixo_dxf','source_axis_fingerprint':fp,'source_axis_layer':'EIXO_LESTE','sections_only':True,'section_surface':True,'cross_sections':[sec]}

def previa(c,fp,rd,left_dir):
    r=c.post('/api/rotas_previa',json={'route_alignments':[rota(fp,left_dir)],'route_directions':rd});assert r.status_code==200,r.text
    return sorted({l['dir'] for l in r.json()['lanes']})

def test_previa_segue_sentido_do_eixo_e_do_layer():
    from app.server import app
    c=TestClient(app);fp=axis_fingerprint([(0.,0.),(100.,0.),(200.,20.)],'EIXO_LESTE',0)
    for left in ('mesmo','contrario'):
        base=previa(c,fp,{},left)
        assert previa(c,fp,{'axis:'+fp:'reverse'},left)==['r'],left
        assert previa(c,fp,{'layer:EIXO_LESTE':'reverse'},left)==['r'],left
        assert previa(c,fp,{'axis:'+fp:'forward'},left)==['f'] if left=='contrario' else previa(c,fp,{'axis:'+fp:'forward'},left)==['f']
    assert previa(c,fp,{},'mesmo')==['f']

def test_front_envia_e_observa_sentido():
    t=(JS/'32_rotas.js').read_text(encoding='utf-8')
    assert 'FLUXO.todos()' in t.split('function routeSignature')[1].split('\n')[0]
    assert 'route_directions:FLUXO.todos()' in t
