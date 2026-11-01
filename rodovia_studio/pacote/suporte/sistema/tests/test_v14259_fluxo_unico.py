"""2.33: sentido por eixo com fonte única. Cada eixo é independente (motor e telas)."""
import re,shutil,subprocess,json
from pathlib import Path
import pytest
JS=Path(__file__).resolve().parents[1]/'app'/'js';NODE=shutil.which('node')
def fluxo_src():
    t=(JS/'01_estado_configuracao.js').read_text(encoding='utf-8');m=re.search(r'const FLUXO=\(\(\)=>\{.*?\n\}\)\(\);',t,re.S);assert m;return m.group(0)
def rodar(corpo):
    s='global.document=undefined;global.cfg={route_directions:{}};'+fluxo_src()+';'+corpo
    r=subprocess.run([NODE,'-e',s],capture_output=True,text=True,timeout=60);assert r.returncode==0,r.stderr;return json.loads(r.stdout)
@pytest.mark.skipif(NODE is None,reason='node ausente')
def test_definir_muda_so_a_chave_pedida():
    r=rodar("FLUXO.definir('axis:a','reverse');FLUXO.definir('axis:b','forward');FLUXO.definir('axis:a','auto');console.log(JSON.stringify(cfg.route_directions))")
    assert r=={'axis:b':'forward'}
@pytest.mark.skipif(NODE is None,reason='node ausente')
def test_obter_prefere_eixo_a_layer_e_orfas_sao_removidas():
    r=rodar("cfg.route_directions={'layer:X':'reverse','axis:a':'forward','axis:velha':'reverse'};const a=[FLUXO.obter('axis:a','X'),FLUXO.obter('axis:b','X'),FLUXO.obter('axis:c','Y')];const n=FLUXO.limparOrfas(new Set(['axis:a','axis:b']));console.log(JSON.stringify([a,n,cfg.route_directions]))")
    assert r==[['forward','reverse','auto'],1,{'layer:X':'reverse','axis:a':'forward'}]
def test_salvar_nao_le_mais_os_seletores_da_tela():
    t=(JS/'01_estado_configuracao.js').read_text(encoding='utf-8')
    assert "querySelectorAll('#routes select').forEach(el=>{if(el.value!=='pending')s.route_directions" not in t
    assert 's.route_directions=FLUXO.todos()' in t
def test_telas_gravam_pela_fonte_unica():
    assert 'FLUXO.todos()' in (JS/'87_circulacao_simples.js').read_text(encoding='utf-8')
    assert 'FLUXO.definir' in (JS/'94_sentido_eixo.js').read_text(encoding='utf-8')
    assert 'FLUXO.sync' in (JS/'94_central.js').read_text(encoding='utf-8')

import itertools
import numpy as np
from shapely.geometry import box
from app.models import Settings
from app.native_axes import native_paths,axis_fingerprint
def _ax(layer,y):
    return dict(layer=layer,level=0,points=np.column_stack([np.linspace(0,600,60),np.full(60,y)]),role='axis')
def test_cada_eixo_tem_fluxo_proprio_em_todas_as_combinacoes():
    """Quatro eixos (dois no mesmo layer): qualquer combinação de escolhas individuais chega a cada um sem vazar."""
    axes=[_ax('A',0),_ax('B',9),_ax('C',18),_ax('C',27)];fps=[axis_fingerprint(a['points'],a['layer'],0) for a in axes]
    for combo in itertools.product(['auto','forward','reverse','off'],repeat=4):
        rd={'axis:'+fp:v for fp,v in zip(fps,combo) if v!='auto'}
        s=Settings(layers={'axis':['A','B','C']},route_directions=rd)
        rows,_=native_paths(axes,s,box(-10,-40,610,40))
        got={fps.index(r['fingerprints'][0] if 'fingerprints' in r else None) if False else r['native_id']:r['native_direction'] for r in rows}
        for i,v in enumerate(combo):
            if v=='off':assert str(i) not in got
            else:assert got[str(i)]==v,(combo,i,got)

@pytest.mark.skipif(NODE is None,reason='node ausente')
def test_chave_do_trecho_e_estavel_quando_os_ids_mudam():
    r=rodar("const a={id:3,origin_key:'abc',points:[[100.2,50.4],[1,1]]},b={id:1,origin_key:'abc',points:[[100.4,49.6],[1,1]]},c={id:2,origin_key:'xyz',points:[[100.2,50.4],[1,1]]};console.log(JSON.stringify([FLUXO.chaveTrecho(a)===FLUXO.chaveTrecho(b),FLUXO.chaveTrecho(a)===FLUXO.chaveTrecho(c)]))")
    assert r==[True,False]
def test_selecao_de_trecho_segue_identidade_estavel():
    t=(JS/'01_estado_configuracao.js').read_text(encoding='utf-8')
    assert 'FLUXO.chaveTrecho(x)===_chaveAntes' in t and 'FLUXO.sync()}' in t

@pytest.mark.skipif(NODE is None,reason='node ausente')
def test_rumo_fisico_mostra_para_onde_circula():
    src=(JS/'94_sentido_eixo.js').read_text(encoding='utf-8')
    s='''global.window=global;global.COMANDOS=new Map();global.comando=()=>{};global.cfg={route_directions:{}};
global.editor={segments:[{source:'Eixo DXF · 1',forward:false,points:[[0,0],[1000,0]]},{source:'Eixo DXF · 2',forward:true,points:[[0,0],[1000,0]]},{source:'Eixo DXF · 3',forward:true,points:[[0,0],[0,500]],disabled:true}]};
eval(require('fs').readFileSync(process.argv[2],'utf8'));eval(require('fs').readFileSync(process.argv[1],'utf8'));
console.log(JSON.stringify([RodoviaSentidoEixo.rumo(1),RodoviaSentidoEixo.rumo(2),RodoviaSentidoEixo.rumo(3)]))'''
    r=subprocess.run([NODE,'-e',s,src and str(JS/'94_sentido_eixo.js'),str(JS/'00_glossario.js')],capture_output=True,text=True,timeout=60)
    assert r.returncode==0,r.stderr
    assert json.loads(r.stdout)==['Oeste','Leste','']
def test_inverter_eixo_avisa_que_vale_para_todos():
    t=(JS/'94_sentido_eixo.js').read_text(encoding='utf-8');assert 'TODOS os eixos de uma vez' in t
    assert 'TODOS os eixos' in (JS/'10_ajuda_dicas.js').read_text(encoding='utf-8')
