"""Verifica o sampler real e o pool de agentes sem exigir GPU/browser."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[1]
viewer=(root/'suporte/sistema/app/webgl/viewer.mjs').read_text()
agents=(root/'suporte/sistema/app/webgl/agents.mjs').read_text()
sampler=viewer.split(' sample(track,time,out){',1)[1].split('\n setTime(',1)[0]
js=r'''
const assert=require('node:assert/strict');
const sample=new Function('track','time','out',SAMPLER);
const receiver={reveal:null,sample};
const track={id:1,samples:[[0,0,1,0,1,0,0],[1,10,1,4,1,0,0],[2,20,1,8,0,0,1]]};
function original(track,time){const a=track.samples;if(!a.length||time<a[0][0]||time>a.at(-1)[0])return null;let lo=0,hi=a.length-1;while(lo+1<hi){const mid=(lo+hi)>>1;if(a[mid][0]<=time)lo=mid;else hi=mid}const p=a[lo],q=a[hi],f=q[0]>p[0]?(time-p[0])/(q[0]-p[0]):0;return p.map((v,i)=>i?v+(q[i]-v)*f:time)}
const out=[],future=[];
for(const time of [-1,0,.1,.5,1,1.5,2,3])assert.deepEqual(sample.call(receiver,track,time,out),original(track,time));
const first=sample.call(receiver,track,.4);sample.call(receiver,track,.8);assert.deepEqual(first,original(track,.4));
assert.equal(sample.call(receiver,track,.2,out),out);const retained=out.slice();sample.call(receiver,track,.7,future);assert.deepEqual(out,retained);assert.notEqual(out,future);
const wide={samples:[[0,1,2,3,4,5,6,7,8],[1,2,3,4,5,6,7,8,9]]};sample.call(receiver,wide,.5,out);assert.equal(out.length,9);sample.call(receiver,track,.5,out);assert.equal(out.length,7);
let allocations=0;
class MathObject{constructor(){allocations++}set(){return this}normalize(){return this}setFromUnitVectors(){return this}compose(){return this}makeScale(){return this}setPosition(){return this}multiplyMatrices(){return this}makeTranslation(){return this}makeRotationZ(){return this}scale(){return this}}
class Geometry{constructor(){allocations++}}
class Mesh{constructor(){this.instanceMatrix={setUsage(){}};this.userData={}}setMatrixAt(){}setColorAt(){}}
const THREE={Matrix4:MathObject,Quaternion:MathObject,Vector3:MathObject,Color:MathObject,BoxGeometry:Geometry,SphereGeometry:Geometry,CylinderGeometry:Geometry,MeshStandardMaterial:Geometry,InstancedMesh:Mesh};
const SceneAgents=new Function('THREE',AGENTS+';return SceneAgents')(THREE);
const view={...receiver,geometries:new Set(),materials:new Set(),scene:{add(){}},pickables:[]};
const people=new SceneAgents(view,{pedestrians:[track],vehicles:[],duration_s:2});
const before=allocations,current=people.scratch.current,next=people.scratch.future;
for(let i=0;i<100;i++)people.update((i%20)/10);
assert.equal(allocations,before,'repeated agent updates must allocate no math/geometry objects');assert.equal(people.scratch.current,current);assert.equal(people.scratch.future,next);assert.notEqual(current,next);people.dispose();assert.equal(people.scratch,null);
console.log('Pooling 3D: equivalência, independência, tamanhos variáveis, 100 atualizações sem novas geometrias/matemática e descarte OK.');
'''
import json
js=js.replace('SAMPLER',json.dumps(sampler.rsplit('}',1)[0])).replace('AGENTS',json.dumps(agents.split('\n',1)[1].replace('export ','')))
subprocess.run(['node','-e',js],check=True,cwd=root)
