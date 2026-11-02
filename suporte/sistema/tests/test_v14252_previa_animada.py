"""2.24: prévia animada determinística (semente) e segura sem rede/DOM."""
import json,shutil,subprocess
from pathlib import Path
import pytest

JS=Path(__file__).resolve().parents[1]/'app'/'js'/'98_previa_animada.js'
NODE=shutil.which('node')

SCRIPT=r'''
const fs=require('fs'),vm=require('vm');
function run(seed,dens){
 const calls=[];
 const ctx={canvas:{width:800,height:600},save(){},restore(){},beginPath(){},ellipse(){calls.push(1)},fill(){},stroke(){}};
 const g={editor:{engine_revision:'r',paths:[{kinds:['main'],p:[[0,0],[500,0],[1000,100]]},{kinds:['return'],p:[[0,10],[300,10]]}]},cfg:{traffic_seed:seed,traffic_density:dens},
  W2C:p=>[p.x*.5+100,300-p.y*.5],ctx,draw(){},comando(){},msg(){},document:{addEventListener(){},querySelectorAll(){return[]},hidden:false},performance:{now:()=>0},
  requestAnimationFrame(){return 1},cancelAnimationFrame(){},queueMicrotask(f){},window:{}};
 g.globalThis=g;vm.createContext(g);vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),g);
 const P=g.window.RodoviaPreviaAnimada.preparar();
 return P.map(x=>x.cars.map(c=>[+c.off.toFixed(3),+c.v.toFixed(3)]));
}
console.log(JSON.stringify({a:run(7,1),b:run(7,1),c:run(8,1),d:run(7,3)}));
'''

@pytest.mark.skipif(NODE is None,reason='node ausente')
def test_mesma_semente_mesma_animacao_e_densidade_muda_quantidade():
    r=subprocess.run([NODE,'-e',SCRIPT,str(JS)],capture_output=True,text=True,timeout=60);assert r.returncode==0,r.stderr
    o=json.loads(r.stdout.strip().splitlines()[-1])
    assert o['a']==o['b'] and o['a']!=o['c']
    assert sum(len(x) for x in o['d'])>sum(len(x) for x in o['a'])
    assert all(len(x)>=1 for x in o['a'])
