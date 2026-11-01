"""2.28: sentido por layer de eixo (EIXO_OESTE) e diagnóstico de escolhas que não chegam ao motor."""
import numpy as np
from shapely.geometry import box
from app.models import Settings
from app.native_axes import native_paths,axis_fingerprint,direction_for,direction_diagnostics

def axis(layer,y,n=60):
    return dict(layer=layer,level=0,points=np.column_stack([np.linspace(0,600,n),np.full(n,y)]),role='axis')

def S(**kw):return Settings(layers={'axis':['EIXO_LESTE','EIXO_OESTE']},**kw)

def dirs(settings,axes):
    rows,_=native_paths(axes,settings,box(-10,-30,610,30))
    return {r['native_id']:r['native_direction'] for r in rows},rows

def test_layer_reverse_vale_para_todos_os_eixos_do_layer():
    axes=[axis('EIXO_LESTE',0),axis('EIXO_OESTE',9)]
    d,rows=dirs(S(route_directions={'layer:EIXO_OESTE':'reverse'}),axes)
    por_layer={r['layer'] if 'layer' in r else None:r['native_direction'] for r in rows}
    assert sorted(r['native_direction'] for r in rows)==['auto','reverse']

def test_escolha_do_eixo_vence_a_do_layer():
    a=[axis('EIXO_OESTE',9)];fp=axis_fingerprint(a[0]['points'],'EIXO_OESTE',0)
    d,rows=dirs(S(route_directions={'layer:EIXO_OESTE':'reverse','axis:'+fp:'forward'}),a)
    assert rows[0]['native_direction']=='forward'

def test_chave_antiga_nao_bloqueia_o_layer():
    a=[axis('EIXO_OESTE',9)]
    # chave de um DXF anterior (não casa com nada) deixa a análise em modo "revisão"; o layer resolve mesmo assim
    d,rows=dirs(S(route_directions={'axis:'+'0'*64:'forward','layer:EIXO_OESTE':'reverse'}),a)
    assert len(rows)==1 and rows[0]['native_direction']=='reverse'

def test_diagnostico_aponta_chaves_orfas_e_layers_sem_escolha():
    a=[axis('EIXO_LESTE',0),axis('EIXO_OESTE',9)]
    dd=direction_diagnostics(a,S(route_directions={'axis:'+'1'*64:'reverse','layer:EIXO_LESTE':'forward'}))
    assert dd['orphan_keys']==1 and dd['axes_without_choice']==['EIXO_OESTE']
    assert direction_for({'layer:X':'reverse'},'axis:abc','X')=='reverse' and direction_for({},'k','X')=='auto'

import shutil,subprocess
from pathlib import Path
import pytest
JS=Path(__file__).resolve().parents[1]/'app'/'js'/'94_sentido_eixo.js';NODE=shutil.which('node')

@pytest.mark.skipif(NODE is None,reason='node ausente')
def test_js_compat_aplicar_layer_sem_apagar_o_que_nao_conhece():
    s=r'''global.window=global;global.COMANDOS=new Map();global.comando=(n,f)=>n.forEach(x=>COMANDOS.set(x,f));global.analysis={routes:[{layer:'EIXO_OESTE',direction_key:'axis:aa',length_exact_m:9000},{layer:'EIXO_OESTE',direction_key:'axis:bb',length_exact_m:900}]};
global.cfg={layers:{axis:['EIXO_LESTE','EIXO_OESTE']},route_directions:{'axis:aa':'forward','axis:bb':'forward','axis:zz':'reverse'}};
eval(require('fs').readFileSync(process.argv[2],'utf8'));eval(require('fs').readFileSync(process.argv[1],'utf8'));const A=RodoviaSentidoEixo;
A.aplicar(cfg,'EIXO_OESTE','reverse',true);
console.log(JSON.stringify([cfg.route_directions,A.camadas(),COMANDOS.has('SENTIDOEIXO')]))'''
    r=subprocess.run([NODE,'-e',s,str(JS),str(JS.with_name('00_glossario.js'))],capture_output=True,text=True,timeout=60);assert r.returncode==0,r.stderr
    assert r.stdout.strip()=='[{"axis:aa":"forward","axis:bb":"forward","axis:zz":"reverse","layer:EIXO_OESTE":"reverse"},[],true]'


from app.direction_policy import resolver_eixo,relatorio
from app.models import RouteAlignment
from app.routes import inherited_sense

def test_politica_unica_explica_origem_e_sobrescritos():
    a=axis('EIXO_OESTE',9);fp=axis_fingerprint(a['points'],'EIXO_OESTE',0)
    # só layer
    r=resolver_eixo(S(route_directions={'layer:EIXO_OESTE':'reverse'}),a)
    assert (r['efetivo'],r['origem'],r['conflitos'])==('reverse','layer',[])
    # eixo vence layer e o layer aparece como sobrescrito
    r=resolver_eixo(S(route_directions={'layer:EIXO_OESTE':'reverse','axis:'+fp:'forward'}),a)
    assert (r['efetivo'],r['origem'])==('forward','eixo') and len(r['conflitos'])==1
    # rota explícita vence os dois
    rota=RouteAlignment(id='r',name='Seção OESTE',points=[dict(x=0,y=9),dict(x=600,y=9)],flow_direction='decrescente',source_axis_fingerprint=fp)
    r=resolver_eixo(S(route_directions={'layer:EIXO_OESTE':'forward','axis:'+fp:'forward'},route_alignments=[rota]),a)
    assert (r['efetivo'],r['origem'])==('reverse','rota') and len(r['conflitos'])==2

def test_relatorio_avisa_orfas_setas_e_inversao_do_eixo():
    rel=relatorio([axis('EIXO_OESTE',9)],S(route_directions={'axis:'+'2'*64:'reverse'},reverse_axis=True))
    assert rel['orfas']==['axis:'+'2'*64] and any('Inverter eixo' in x for x in rel['avisos']) and rel['ordem'][0]=='seta desenhada'

def test_rota_herda_sentido_do_layer_quando_nao_tem_escolha_propria():
    a=axis('EIXO_OESTE',9);fp=axis_fingerprint(a['points'],'EIXO_OESTE',0)
    rota=RouteAlignment(id='r',name='Faixas',points=[dict(x=0,y=9),dict(x=600,y=9)],source_axis_fingerprint=fp,source_axis_layer='EIXO_OESTE')
    assert inherited_sense(rota,S(route_directions={'layer:EIXO_OESTE':'reverse'}))==-1
    assert inherited_sense(rota,S(route_directions={'layer:EIXO_OESTE':'reverse','axis:'+fp:'forward'}))==1
