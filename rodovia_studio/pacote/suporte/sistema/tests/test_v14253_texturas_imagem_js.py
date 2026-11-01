"""2.26: texturas ao vivo, captura de imagem aérea robusta e sintaxe de todos os JS."""
import io,shutil,subprocess
from pathlib import Path
import numpy as np
import pytest
from PIL import Image

JSDIR=Path(__file__).resolve().parents[1]/'app'/'js'
NODE=shutil.which('node')

@pytest.mark.skipif(NODE is None,reason='node ausente')
def test_todos_os_js_tem_sintaxe_valida():
    ruins=[]
    for f in sorted(JSDIR.glob('*.js')):
        r=subprocess.run([NODE,'--check',str(f)],capture_output=True,text=True)
        if r.returncode:ruins.append((f.name,r.stderr[:200]))
    assert not ruins,ruins

@pytest.mark.skipif(NODE is None,reason='node ausente')
def test_textura_viva_e_deterministica_e_reage_aos_parametros():
    s=r'''global.document=undefined;eval(require('fs').readFileSync(process.argv[1],'utf8'));
const T=RodoviaTexturasVivas,h=a=>Buffer.from(a).toString('base64');
const a=h(T.gerar('pista_nova',{},24)),b=h(T.gerar('pista_nova',{},24)),c=h(T.gerar('pista_nova',{grao:2},24)),d=h(T.gerar('canteiro',{},24));
console.log(JSON.stringify([a===b,a!==c,a!==d,Object.keys(T.SUP).length]))'''
    r=subprocess.run([NODE,'-e',s,str(JSDIR/'94_texturas_vivas.js')],capture_output=True,text=True,timeout=60);assert r.returncode==0,r.stderr
    assert r.stdout.strip()=='[true,true,true,7]'

def test_baixar_bloco_repete_ate_receber_imagem_valida():
    from app import imagery
    def png(ruido):
        b=io.BytesIO();Image.fromarray(np.random.RandomState(1).randint(0,255,(64,64,3),np.uint8) if ruido else np.full((64,64,3),255,np.uint8)).save(b,'PNG');return b.getvalue()
    seq=[b'lixo',png(False),png(True)];n=[0]
    def f(u):
        r=seq[n[0]];n[0]+=1;return r
    assert imagery.baixar_bloco('x',abrir=f,espera=0)==seq[2] and n[0]==3

def test_ampliar_mantem_proporcao():
    from app import imagery
    assert imagery.ampliar(np.zeros((10,12,3),np.uint8),2).shape==(20,24,3)

@pytest.mark.skipif(NODE is None,reason='node ausente')
def test_paleta_filtra_comandos():
    s=r'''global.CMD_HELP=[['LINHA / L','Desenha linha'],['ZOOM / Z','Aproxima']];global.COMANDOS=new Map([['LINHA',1],['L',1],['ZOOM',1],['Z',1],['SEMAJUDA',1]]);
eval(require('fs').readFileSync(process.argv[1],'utf8'));const P=RodoviaPaleta,l=P.itens();
console.log(JSON.stringify([l.length,P.filtrar(l,'l')[0].nome,P.filtrar(l,'aprox')[0].nome,P.filtrar(l,'semaj').length]))'''
    r=subprocess.run([NODE,'-e',s,str(JSDIR/'94_paleta_comandos.js')],capture_output=True,text=True,timeout=60);assert r.returncode==0,r.stderr
    assert r.stdout.strip()=='[3,"LINHA","ZOOM",1]'

@pytest.mark.skipif(NODE is None,reason='node ausente')
def test_registro_de_erros_trata_sem_quebrar():
    s=r'''const regs=[];global.COMANDOS=new Map();global.comando=(n,f)=>{n.forEach(x=>COMANDOS.set(x,f))};global.msg=()=>{};global.reportClient=(m)=>regs.push(m);
eval(require('fs').readFileSync(process.argv[1],'utf8'));const E=RodoviaErros;
E.avisar('a',new Error('x'));E.avisar('a',new Error('x'));E.avisar('b','texto');
const f=E.seguro('c',()=>{throw new Error('boom')},7);
console.log(JSON.stringify([f(),E.resumo().total,regs.length,COMANDOS.has('DIAGNOSTICOJS')]))'''
    r=subprocess.run([NODE,'-e',s,str(JSDIR/'94_registro_erros.js')],capture_output=True,text=True,timeout=60);assert r.returncode==0,r.stderr
    assert r.stdout.strip().splitlines()[-1]=='[7,4,3,true]'

@pytest.mark.skipif(NODE is None,reason='node ausente')
def test_estilos_de_mapa_e_minimapa_sem_dom():
    s=r'''const calls=[];global.tileAlpha=1;global.vecAlpha=.9;global.COMANDOS=new Map();global.comando=(n,f)=>n.forEach(x=>COMANDOS.set(x,f));global.msg=()=>{};global.draw=()=>{};global.saveBasePrefs=()=>{};
global.ctx={canvas:{width:800,height:600},save(){},restore(){},setTransform(){},fillRect(){calls.push('r')},strokeRect(){calls.push('s')},beginPath(){},moveTo(){},lineTo(){calls.push('l')},stroke(){},fillText(){},arc(){},fill(){},closePath(){}};
global.editor={paths:[{p:[[0,0],[100,50],[300,80]]}]};global.C2W=(x,y)=>[x/2,y/2];global.geo={R0:1,k:1};global.view={s:1,ox:0,oy:0};
global.localStorage={getItem(){return null},setItem(){}};global.window={};global.document={getElementById(){return null},addEventListener(){}};
eval(require('fs').readFileSync(process.argv[1],'utf8'));const M=RodoviaMapa2D;
M.aplicarEstilo('tecnico',true);const a=[tileAlpha,vecAlpha];M.minimapa();
console.log(JSON.stringify([a,calls.includes('l'),calls.includes('s'),COMANDOS.has('ESTILOMAPA'),COMANDOS.has('MINIMAPA')]))'''
    r=subprocess.run([NODE,'-e',s,str(JSDIR/'94_mapa_2d.js')],capture_output=True,text=True,timeout=60);assert r.returncode==0,r.stderr
    assert r.stdout.strip().splitlines()[-1]=='[[0.38,1],true,true,true,true]'
