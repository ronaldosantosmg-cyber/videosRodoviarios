"""1.42.38: regiões de fundo (textura) não roubam o clique do eixo/objeto específico. Roda o hitObjects real em Node."""
import json,shutil,subprocess
from pathlib import Path
import pytest

JS=Path(__file__).resolve().parents[1]/'app/js/44_selecao_propriedades.js'
RUNNER='''
const fs=require('fs'),vm=require('vm');
const OBJS=%s;
const ctx={window:{devicePixelRatio:1,event:null},document:{},console,setTimeout,Math,Date,
 canvas:{addEventListener(){}},requestAnimationFrame(){},estender(){},msg(){},
 W2C:p=>[p.x,p.y],gripGet:g=>g[0][g[1]],objList:()=>OBJS.map(o=>({...o,grips:o.pts.map((_,i)=>[o.pts,i])})),
 sel:null,segDist:(px,py,ax,ay,bx,by)=>{const dx=bx-ax,dy=by-ay,L=dx*dx+dy*dy;let t=L?((px-ax)*dx+(py-ay)*dy)/L:0;t=Math.max(0,Math.min(1,t));return Math.hypot(px-ax-t*dx,py-ay-t*dy)}};
vm.createContext(ctx);const src=fs.readFileSync(process.argv[process.argv.length-1],'utf8');const a=src.indexOf('function DPR'),b=src.indexOf('let ultimaEscolha');
vm.runInContext(src.slice(a,b)+';this.hitObjects=hitObjects;',ctx);
const out=[];for(const t of %s){ctx.window.event=t.alt?{altKey:true}:null;ctx.sel=t.sel||null;out.push(ctx.hitObjects({cx:t.x,cy:t.y}).map(h=>h.key));}
console.log(JSON.stringify(out));
'''
TEX=dict(key='texture_areas',i=0,shape='area',pts=[{'x':0,'y':0},{'x':400,'y':0},{'x':400,'y':100},{'x':0,'y':100}])
EIXO=dict(key='route_alignments',i=0,shape='poly',pts=[{'x':0,'y':50},{'x':400,'y':50}])
ZEB=dict(key='hatch_areas',i=0,shape='area',pts=[{'x':100,'y':20},{'x':200,'y':20},{'x':200,'y':80},{'x':100,'y':80}])

@pytest.mark.skipif(not shutil.which('node'),reason='Node é necessário')
def test_textura_nao_rouba_clique_do_eixo_nem_de_area_especifica():
    casos=[dict(x=300,y=50),dict(x=300,y=45),dict(x=150,y=50),dict(x=300,y=70),dict(x=300,y=70,alt=True),dict(x=300,y=70,sel=dict(key='texture_areas',i=0)),dict(x=0,y=70)]
    r=subprocess.run(['node','-e',RUNNER%(json.dumps([TEX,EIXO,ZEB]),json.dumps(casos)),str(JS)],capture_output=True,text=True,timeout=60)
    assert r.returncode==0,r.stderr
    o=json.loads(r.stdout)
    assert o[0]==['route_alignments'] and o[1]==['route_alignments']        # sobre o eixo: só o eixo
    assert o[2][0]=='route_alignments' and 'hatch_areas' in o[2]            # dentro do zebrado: eixo primeiro, zebrado depois, nunca a textura
    assert 'texture_areas' not in o[2]
    assert o[3]==[]                                                        # interior da textura sozinho: não seleciona
    assert o[4]==['texture_areas'] and o[5]==['texture_areas']              # Alt+clique ou já selecionada: seleciona
    assert 'texture_areas' in o[6]                                         # a borda continua selecionável
