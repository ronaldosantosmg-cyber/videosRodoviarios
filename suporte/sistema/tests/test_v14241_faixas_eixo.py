"""1.42.41: faixas à esquerda/direita do eixo e acostamentos geram alinhamento ligado ao eixo (zero = sobre o eixo)."""
import json,re,shutil,subprocess
import pytest
from app.models import Settings
from app.native_axes import axis_fingerprint
from app.routes import raw_paths
import numpy as np

JS='app/js/87_circulacao_simples.js'

def _gerar(values,axis_type='auto',prev=None):
    if not shutil.which('node'):pytest.skip('node ausente')
    src=open(JS,encoding='utf-8').read()
    a=src.index('const axisPoint');b=src.index('async function directions')
    fp=axis_fingerprint(np.array([[0.,0.],[300.,0.]]),'EIXO',0)
    prog="const uid=()=>'sec-'+Math.random().toString(36).slice(2);"+src[a:b]+f"const axis={{name:'Eixo',points:[[0,0],[300,0]],level:0,fingerprint:'{fp}',length_m:300,length_exact_m:300}};console.log(JSON.stringify(axisLanesRoute(axis,{json.dumps(values)},{json.dumps(prev)},'{axis_type}')))"
    out=subprocess.run(['node','-e',prog],capture_output=True,text=True,check=True).stdout
    return json.loads(out),fp

def _paths(route):
    return raw_paths(Settings(route_alignments=[route]))

def test_duas_faixas_a_direita_so_sentido_do_desenho():
    r,_=_gerar(dict(left=0,right=2,shoulderLeft=0,shoulderRight=2.5))
    p=_paths(r);assert {x['route_dir'] for x in p}=={'f'} and len(p)==2
    assert sorted(round(float(x['points'][0][1]),2) for x in p)==[-5.25,-1.75] or sorted(round(abs(float(x['points'][0][1])),2) for x in p)==[1.75,5.25]

def test_uma_faixa_de_cada_lado_e_tipologia_dupla_libera_ultrapassagem():
    r,fp=_gerar(dict(left=1,right=1,shoulderLeft=0,shoulderRight=0),'pista_dupla')
    p=_paths(r);assert {x['route_dir'] for x in p}=={'f','r'} and r['lane_change']=='safe' and r['source_axis_fingerprint']==fp

def test_lado_zero_nao_gera_trafego_e_atualizacao_preserva_id():
    r,_=_gerar(dict(left=0,right=1,shoulderLeft=0,shoulderRight=0))
    assert [x['route_dir'] for x in _paths(r)]==['f']
    r2,_=_gerar(dict(left=2,right=1,shoulderLeft=1,shoulderRight=0),prev=r)
    assert r2['id']==r['id'] and len(_paths(r2))==3
