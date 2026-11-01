"""2.23: presets de via montam alinhamentos válidos e faixas coerentes."""
import numpy as np,pytest
from app.via_presets import PRESETS,montar,catalogo
from app.models import RouteAlignment,Settings
from app.routes import _build_lanes

EIXO={'name':'EIXO_LESTE','points':[{'x':0,'y':0},{'x':300,'y':0},{'x':600,'y':50}],'fingerprint':'e'*64,'level':0}

def lanes(preset,**p):
    r=RouteAlignment.model_validate(montar(preset,EIXO,p));return r,_build_lanes(r)

def test_todo_preset_gera_rota_valida_e_faixas():
    for k in PRESETS:
        r,L=lanes(k) if k!='rotatoria' else (None,[1])
        assert L,k

def test_pista_simples_dois_sentidos():
    _,L=lanes('pista_simples');assert {l['dir'] for l in L}=={'f','r'} and len(L)==2

def test_duplicada_com_canteiro_editavel():
    r,L=lanes('duplicada_canteiro',faixas=2,canteiro=6)
    assert len(L)==4 and r.cross_sections[0].median_m==6
    ys=sorted(float(np.mean(l['points'][:,1])) for l in L if l['dir']=='f');assert ys[0]>3     # faixas à direita do canteiro

def test_um_sentido_meio_sem_canteiro_e_todas_no_mesmo_sentido():
    r,L=lanes('um_sentido_meio',faixas=2);assert {l['dir'] for l in L}=={'f'} and len(L)==2 and r.cross_sections[0].median_m==0

def test_um_sentido_bordo_so_um_lado():
    _,L=lanes('um_sentido_bordo',faixas=3);ys=[float(np.mean(l['points'][:,1])) for l in L]
    assert len(L)==3 and min(ys)>0

def test_sentido_decrescente_espelha():
    _,L=lanes('um_sentido_meio',faixas=2,sentido='decrescente');assert {l['dir'] for l in L}=={'r'}

def test_ramal_e_rotatoria():
    r=RouteAlignment.model_validate(montar('ramal',EIXO));assert r.type=='unico' and r.lane_change=='off'
    r=RouteAlignment.model_validate(montar('rotatoria',{**EIXO}));assert r.flow_role=='rotatoria'

def test_reaplicar_preserva_identidade():
    a=montar('pista_simples',EIXO);b=montar('duplicada_canteiro',EIXO,anterior=a)
    assert a['id']==b['id'] and a['cross_sections'][0]['id']==b['cross_sections'][0]['id']

def test_parametros_invalidos():
    with pytest.raises(ValueError):montar('pista_simples',EIXO,{'faixas':9})
    with pytest.raises(ValueError):montar('pista_simples',EIXO,{'largura':1})
    with pytest.raises(ValueError):montar('nao_existe',EIXO)

def test_semente_no_modelo():
    assert Settings.model_fields['traffic_seed'].default==1729


def test_painel_via_comandos_unicos_e_sintaxe():
    import re,shutil,subprocess
    from pathlib import Path
    js=Path(__file__).resolve().parents[1]/'app'/'js'
    nomes={}
    for f in sorted(js.glob('*.js')):
        for m in re.finditer(r"comando\(\[([^\]]*)\]",f.read_text(encoding='utf-8')):
            for n in re.findall(r"'([^']+)'",m.group(1)):nomes.setdefault(n,[]).append(f.name)
    assert {'VIA','GERARTRAFEGO'}<=set(nomes)
    # nenhum nome de comando pode repetir (comando() lança erro em duplicidade)
    dup={n:v for n,v in nomes.items() if len(v)>1 and n in ('VIA','TIPOVIA','GERARTRAFEGO','TRAFEGO')}
    assert dup=={},dup
    node=shutil.which('node')
    if node:assert subprocess.run([node,'--check',str(js/'97_via_painel.js')],capture_output=True).returncode==0


def test_resumo_do_trafego_conta_faixas_cortes_e_ligacoes():
    import json,shutil,subprocess
    from pathlib import Path
    node=shutil.which('node')
    if not node:return
    js=Path(__file__).resolve().parents[1]/'app'/'js'/'97_via_painel.js'
    script=r'''
const fs=require('fs'),vm=require('vm');
const g={editor:{paths:[{kinds:['main']},{kinds:['main']},{kinds:['return']}],segments:[{technical_status:'ok'},{technical_status:'cortado'},{disabled:true,technical_status:'ok'}],connections:[1,2],denied:[],passing_zones:[1],ghost_zones:[],warnings:[1,2,3]},
 comando(){},queueMicrotask(){},document:{querySelectorAll(){return[]}},window:{}};g.globalThis=g;vm.createContext(g);
vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),g);console.log(JSON.stringify(g.window.RodoviaResumoTrafego.dados()));'''
    r=subprocess.run([node,'-e',script,str(js)],capture_output=True,text=True,timeout=60);assert r.returncode==0,r.stderr
    o=json.loads(r.stdout.strip().splitlines()[-1])
    assert o['faixas']==3 and o['porTipo']=={'main':2,'return':1} and o['cortes']==1 and o['desativados']==1 and o['ligacoes']==2 and o['ultrapassagem']==1 and o['alertas']==3
