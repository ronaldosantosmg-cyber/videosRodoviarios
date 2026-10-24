import * as THREE from '/vendor/three/build/three.module.js';
import {RoundedBoxGeometry} from '/vendor/three/examples/jsm/geometries/RoundedBoxGeometry.js';
import {OrbitControls} from '/vendor/three/examples/jsm/controls/OrbitControls.js';

const PALETTE={pavement:0x667079,existing_pavement:0x899195,shoulder:0x8e948d,median:0x73906a,oae:0x8a9299,water:0x4e899d,cut:0x9a765b,fill:0x8a8762,rail_ballast:0x8d877c,crosswalk:0xf4f3e6};
const finiteArray=(a,stride)=>Array.isArray(a)&&a.length%stride===0&&a.every(Number.isFinite);
export function validateScene(data){
 if(data?.format!=='rodovia-scene3d-1'||!finiteArray(data.origin_crs,3)||data.origin_crs.length!==3||!Number.isFinite(data.span_m)||data.span_m<=0||data.span_m>200000)throw Error('Origem ou escala 3D inválida.');
 if(!Array.isArray(data.meshes)||data.meshes.length>10000||!Array.isArray(data.vehicles)||data.vehicles.length>20000)throw Error('Cena 3D fora dos limites de segurança.');
 let count=0;
 for(const mesh of data.meshes){if(!finiteArray(mesh.positions,9))throw Error('Superfície 3D com coordenadas inválidas.');count+=mesh.positions.length/3;}
 if(count>600000||!finiteArray(data.terrain?.positions,3)||data.terrain.positions.length>150000||!Array.isArray(data.terrain.indices)||!data.terrain.indices.every(i=>Number.isSafeInteger(i)&&i>=0&&i<data.terrain.positions.length/3))throw Error('Geometria 3D excede o orçamento.');
 if(!Number.isFinite(data.duration_s)||data.duration_s<0||data.duration_s>60)throw Error('Duração da prévia 3D inválida.');
 let samples=0;
 for(const v of data.vehicles){if(!Number.isFinite(v.length)||v.length<=0||v.length>30||!Number.isFinite(v.width)||v.width<=0||v.width>5||!Array.isArray(v.samples))throw Error('Dimensões de veículo inválidas.');let last=-Infinity;for(const s of v.samples){if(!finiteArray(s,7)||s.length!==7||s[0]<last||s[0]<0||s[0]>data.duration_s+.001)throw Error('Animação 3D inválida.');last=s[0];samples++;}}
 if(samples>120000)throw Error('Animação 3D excede o orçamento.');
 for(const line of [...(data.markings||[]),...(data.diagnostics||[])])if(!finiteArray(line.p,3))throw Error('Linha 3D inválida.');
 if(data.transport){const t=data.transport;if(!Array.isArray(t.heads)||t.heads.length>1000||!Array.isArray(t.lines)||!Array.isArray(t.states)||t.states.length>10000||!Array.isArray(t.signal_ids)||t.signal_ids.length>100)throw Error('Controles 3D fora dos limites.');let vertices=0;for(const line of t.lines){if(!finiteArray(line.p,3)||!['rail','sleeper','stop'].includes(line.kind))throw Error('Ferrovia 3D inválida.');vertices+=line.p.length/3;}if(vertices>600000)throw Error('Detalhe ferroviário excede o orçamento.');for(const head of t.heads)if(!finiteArray(head.p,3)||head.p.length!==3||!['signal','rail'].includes(head.kind))throw Error('Sinal 3D inválido.');let previous=-Infinity;for(const state of t.states){if(!Array.isArray(state)||state.length!==3||!Number.isFinite(state[0])||state[0]<previous||state[0]<0||state[0]>data.duration_s+.001||!Array.isArray(state[1])||state[1].length!==t.signal_ids.length*3||!state[1].every(v=>Number.isInteger(v)&&v>=-1&&v<=2)||!Array.isArray(state[2])||!state[2].every(v=>typeof v==='boolean'))throw Error('Relógio semafórico inválido.');previous=state[0];}}
 return data;
}

export class RoadViewer {
 constructor(container,{onStatus=()=>{},onPick=()=>{},onContext=()=>{}}={}){
  this.container=container;this.onStatus=onStatus;this.onPick=onPick;this.onContext=onContext;this.time=0;this.playing=false;this.disposed=false;this.lost=false;this.raf=0;this.materials=new Set();this.geometries=new Set();this.textures=new Set();
  this.scene=new THREE.Scene();this.scene.background=new THREE.Color(0xcbd7df);
  try{this.renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:false,logarithmicDepthBuffer:true,powerPreference:'high-performance'});}catch{throw Error('WebGL2 indisponível. O editor 2D continua disponível.');}
  this.renderer.outputColorSpace=THREE.SRGBColorSpace;this.renderer.toneMapping=THREE.ACESFilmicToneMapping;this.renderer.toneMappingExposure=1.15;this.renderer.shadowMap.enabled=true;this.renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  this.canvas=this.renderer.domElement;this.canvas.tabIndex=0;this.canvas.setAttribute('aria-label','Vista 3D do projeto');container.appendChild(this.canvas);
  this.camera=new THREE.PerspectiveCamera(45,1,.05,100000);this.controls=new OrbitControls(this.camera,this.canvas);this.controls.enableDamping=false;this.controls.maxPolarAngle=Math.PI*.49;this.controls.minDistance=2;this.controls.addEventListener('change',()=>this.render());
  const hemi=new THREE.HemisphereLight(0xe7f2ff,0x697554,2.2);this.scene.add(hemi);
  this.sun=new THREE.DirectionalLight(0xfff2da,3.);this.sun.castShadow=true;this.sun.shadow.mapSize.set(1024,1024);this.sun.shadow.bias=-.00015;this.sun.shadow.normalBias=.05;this.scene.add(this.sun);this.scene.add(this.sun.target);
  this.ray=new THREE.Raycaster();this.pointer=new THREE.Vector2();this.pickables=[];this.vehicleBatches=[];this.followId=null;this.controls.addEventListener('start',()=>{this.followId=null});this.technical=new THREE.Group();this.technical.visible=false;this.scene.add(this.technical);this.lightMode='dia';
  this.lostHandler=e=>{e.preventDefault();this.lost=true;this.pause();onContext('lost');onStatus('Contexto gráfico perdido. Aguarde a recuperação ou volte ao 2D.');};
  this.restoreHandler=()=>{if(this.disposed)return;this.lost=false;onContext('restored');onStatus('Contexto gráfico recuperado.');this.render();};
  this.canvas.addEventListener('webglcontextlost',this.lostHandler);this.canvas.addEventListener('webglcontextrestored',this.restoreHandler);
  this.down=e=>{this.pointerStart={x:e.clientX,y:e.clientY};};this.up=e=>{if(!this.pointerStart||Math.hypot(e.clientX-this.pointerStart.x,e.clientY-this.pointerStart.y)>4||e.button!==0)return;this.pick(e);};
  this.canvas.addEventListener('pointerdown',this.down);this.canvas.addEventListener('pointerup',this.up);
  this.resizeObserver=new ResizeObserver(()=>this.resize());this.resizeObserver.observe(container);
  this.visibility=()=>{if(document.hidden)this.pause();};document.addEventListener('visibilitychange',this.visibility);this.resize();
 }
 geometry(positions,indices=null){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));if(indices)g.setIndex(indices);if(indices||positions.length%9===0)g.computeVertexNormals();this.geometries.add(g);return g;}
 texture(kind){const n=64,bytes=new Uint8Array(n*n*4);let seed=kind==='asphalt'?257:1729;for(let i=0;i<n*n;i++){seed=(Math.imul(seed,1664525)+1013904223)>>>0;const noise=kind==='asphalt'?185+(seed%60):205+(seed%48);bytes[i*4]=noise;bytes[i*4+1]=noise;bytes[i*4+2]=noise;bytes[i*4+3]=255;}const t=new THREE.DataTexture(bytes,n,n,THREE.RGBAFormat);t.colorSpace=THREE.SRGBColorSpace;t.generateMipmaps=true;t.minFilter=THREE.LinearMipmapLinearFilter;t.magFilter=THREE.LinearFilter;t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=Math.min(8,this.renderer.capabilities.getMaxAnisotropy());t.needsUpdate=true;this.textures.add(t);return t;}
 texturedGeometry(positions,indices=null){const g=this.geometry(positions,indices),uv=[];for(let i=0;i<positions.length;i+=3)uv.push(positions[i]/8,positions[i+2]/8);g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));return g;}
 material(options){const m=new THREE.MeshStandardMaterial({roughness:.9,metalness:0,side:THREE.DoubleSide,...options});this.materials.add(m);return m;}
 load(data){
  validateScene(data);if(this.data)throw Error('Crie uma nova vista ao reconstruir a cena.');this.data=data;
  const span=data.span_m;this.camera.near=Math.max(.03,span/200000);this.camera.far=Math.max(2000,span*12);this.camera.updateProjectionMatrix();this.controls.maxDistance=Math.max(500,span*5);
  this.scene.fog=new THREE.Fog(0xcbd7df,span*3,span*10);this.sun.position.set(span*.4,span*.7,span*.3);const sc=Math.max(100,span*.6);Object.assign(this.sun.shadow.camera,{left:-sc,right:sc,top:sc,bottom:-sc,near:.1,far:span*4+100});this.sun.shadow.camera.updateProjectionMatrix();
  const asphalt=this.texture('asphalt'),grass=this.texture('grass'),ballast=this.texture('asphalt');ballast.repeat.set(8,8);
  const ground=new THREE.Mesh(this.texturedGeometry(data.terrain.positions,data.terrain.indices),this.material({color:0x809478,map:grass}));ground.receiveShadow=true;ground.userData={name:data.terrain.label,role:'terrain'};this.scene.add(ground);this.pickables.push(ground);
  for(const record of data.meshes){const mesh=new THREE.Mesh(this.texturedGeometry(record.positions),this.material({map:record.role==='rail_ballast'?ballast:['pavement','existing_pavement','shoulder'].includes(record.role)?asphalt:['median','fill'].includes(record.role)?grass:null,color:PALETTE[record.role]??0x7d8589,roughness:record.role==='water'?.35:.94,metalness:record.role==='water'?.15:0,polygonOffset:true,polygonOffsetFactor:-1,polygonOffsetUnits:-1}));mesh.receiveShadow=true;mesh.castShadow=false;mesh.userData=record;this.scene.add(mesh);this.pickables.push(mesh);}
  const white=[],yellow=[];for(const m of data.markings||[])(m.yellow?yellow:white).push(...m.p);
  for(const [p,color] of [[white,0xf4f2e2],[yellow,0xf4c846]]){const g=this.geometry(p);const material=new THREE.LineBasicMaterial({color});this.materials.add(material);this.scene.add(new THREE.LineSegments(g,material));}
  const paths={ok:[],problem:[],adjustment:[]};for(const line of data.diagnostics||[]){const out=paths[line.status]||paths.adjustment;for(let i=3;i<line.p.length;i+=3)out.push(...line.p.slice(i-3,i+3));}
  for(const [status,color] of [['ok',0x22c55e],['problem',0xef4444],['adjustment',0xeab308]]){const g=this.geometry(paths[status]);const m=new THREE.LineBasicMaterial({color,depthTest:false});this.materials.add(m);const line=new THREE.LineSegments(g,m);line.renderOrder=100;this.technical.add(line);}
  this.createTransport(data.transport);this.createVehicles(data.vehicles);this.setTime(0);this.fit();this.render();
 }
 createTransport(data){
  this.transportData=data;this.signalLights=[];this.railLights=[];this.trainLights=[];if(!data)return;
  const groups={rail:[],sleeper:[],stop:[]};for(const line of data.lines||[]){for(let i=3;i<line.p.length;i+=3)(groups[line.kind]||groups.stop).push(...line.p.slice(i-3,i+3));}
  for(const [kind,color] of [['rail',0xcdd3d8],['sleeper',0x4a3d33],['stop',0xf4f3e6]]){const mat=new THREE.LineBasicMaterial({color});this.materials.add(mat);this.scene.add(new THREE.LineSegments(this.geometry(groups[kind]),mat));}
  const pole=new THREE.CylinderGeometry(.08,.1,4,8),box=new THREE.BoxGeometry(.55,1.7,.45),lens=new THREE.SphereGeometry(.18,10,8);for(const g of [pole,box,lens])this.geometries.add(g);
  for(const head of data.heads||[]){const group=new THREE.Group();group.position.fromArray(head.p);this.scene.add(group);const p=new THREE.Mesh(pole,this.material({color:0x555f65,metalness:.7}));p.position.y=2;group.add(p);const body=new THREE.Mesh(box,this.material({color:0x18212a}));body.position.y=4.5;group.add(body);const lights=[];
   for(let i=0;i<(head.kind==='rail'?2:3);i++){const m=this.material({color:0x282828,emissive:0x000000}),light=new THREE.Mesh(lens,m);light.position.set(head.kind==='rail'?(i-.5)*.5:0,head.kind==='rail'?4.6:5-i*.5,.3);group.add(light);lights.push(m)}
   group.userData={name:head.kind==='rail'?'Passagem em nível':'Semáforo',role:'traffic_control'};this.pickables.push(body);(head.kind==='rail'?this.railLights:this.signalLights).push({head,lights});
  }
  for(const vehicle of this.data.vehicles.filter(v=>v.type==='rail_locomotive')){const group=new THREE.Group();const geometry=new THREE.SphereGeometry(.16,8,6);this.geometries.add(geometry);for(const side of [-1,1]){const material=this.material({color:0xfff4c1,emissive:0xffed9d,emissiveIntensity:3});const lamp=new THREE.Mesh(geometry,material);lamp.position.set(vehicle.length/2,1.8,side);group.add(lamp);if(this.trainLights.length<4){const light=new THREE.PointLight(0xfff3b5,15,18,2);light.position.copy(lamp.position);group.add(light)}}this.scene.add(group);this.trainLights.push({vehicle,group});}
 }
 updateTransport(){const data=this.transportData;if(!data)return;let state=data.states?.[0];for(const candidate of data.states||[]){if(candidate[0]>this.time+1e-7)break;state=candidate}const colors=[0xff3030,0xffbf32,0x25ee65];
  for(const {head,lights} of this.signalLights){const index=data.signal_ids.indexOf(head.signal),active=state?.[1]?.[index*3+head.axis]??-1;lights.forEach((m,i)=>{m.color.setHex(i===active?colors[i]:0x292b29);m.emissive.setHex(i===active?colors[i]:0);m.emissiveIntensity=i===active?2.8:0})}
  for(const {head,lights} of this.railLights){const closed=state?.[2]?.[head.rail_index];lights.forEach((m,i)=>{const on=closed&&Math.floor(this.time*2)%2===i;m.color.setHex(on?0xff2929:0x352828);m.emissive.setHex(on?0xff2020:0);m.emissiveIntensity=on?3:0})}
  for(const {vehicle,group} of this.trainLights){const s=this.sample(vehicle,this.time);group.visible=!!s;if(s){group.position.set(s[1],s[2],s[3]);group.quaternion.setFromUnitVectors(new THREE.Vector3(1,0,0),new THREE.Vector3(s[4],s[5],s[6]).normalize())}}
 }
 createVehicles(vehicles){
  const groups=new Map();for(const v of vehicles){if(!groups.has(v.type))groups.set(v.type,[]);groups.get(v.type).push(v);}
  const box=new RoundedBoxGeometry(1,1,1,2,.08),wheel=new THREE.CylinderGeometry(1,1,1,10);wheel.rotateX(Math.PI/2);this.geometries.add(box);this.geometries.add(wheel);
  for(const [type,tracks] of groups){
   const body=new THREE.InstancedMesh(box,this.material({color:0xffffff,roughness:.42,metalness:.28}),tracks.length);
   const glass=new THREE.InstancedMesh(box,this.material({color:0x233947,roughness:.2,metalness:.35}),tracks.length);
   const tires=new THREE.InstancedMesh(wheel,this.material({color:0x182127,roughness:1}),tracks.length*4);
   for(const m of [body,glass,tires]){m.instanceMatrix.setUsage(THREE.DynamicDrawUsage);m.castShadow=true;m.receiveShadow=true;m.frustumCulled=false;this.scene.add(m);}body.userData={name:'Veículo',type};this.pickables.push(body);
   tracks.forEach((v,i)=>body.setColorAt(i,new THREE.Color(/^#[0-9a-f]{6}$/i.test(v.color)?v.color:'#7890a0')));
   const cab=new THREE.InstancedMesh(box,this.material({color:0xffffff,roughness:.45,metalness:.25}),tracks.length);cab.frustumCulled=false;cab.castShadow=true;tracks.forEach((v,i)=>cab.setColorAt(i,new THREE.Color(/^#[0-9a-f]{6}$/i.test(v.color)?v.color:'#7890a0')));this.scene.add(cab);
   this.vehicleBatches.push({tracks,body,glass,tires,cab});
  }
 }
 sample(track,time){const a=track.samples;if(!a.length||time<a[0][0]||time>a.at(-1)[0])return null;let lo=0,hi=a.length-1;while(lo+1<hi){const mid=(lo+hi)>>1;if(a[mid][0]<=time)lo=mid;else hi=mid;}const p=a[lo],q=a[hi],f=q[0]>p[0]?(time-p[0])/(q[0]-p[0]):0;return p.map((v,i)=>i?v+(q[i]-v)*f:time);}
 setTime(value){if(!this.data||!Number.isFinite(value))return;this.time=Math.max(0,Math.min(this.data.duration_s,value));const root=new THREE.Matrix4(),m=new THREE.Matrix4(),part=new THREE.Matrix4(),rot=new THREE.Quaternion(),dir=new THREE.Vector3(),up=new THREE.Vector3(1,0,0);
  for(const batch of this.vehicleBatches){batch.tracks.forEach((v,i)=>{const s=this.sample(v,this.time);if(!s){m.makeScale(0,0,0);batch.body.setMatrixAt(i,m);batch.glass.setMatrixAt(i,m);batch.cab.setMatrixAt(i,m);for(let w=0;w<4;w++)batch.tires.setMatrixAt(i*4+w,m);return;}
   dir.set(s[4],s[5],s[6]);if(dir.lengthSq()<1e-8)dir.set(1,0,0);dir.normalize();rot.setFromUnitVectors(up,dir);root.compose(new THREE.Vector3(s[1],s[2],s[3]),rot,new THREE.Vector3(1,1,1));
   const heavy=['truck','bus','carreta','rail_locomotive','rail_wagon'].includes(v.type),height=heavy?2.6:v.type==='moto'?.9:1.25;
   const cargo=['truck','carreta'].includes(v.type);part.makeScale(v.length*(cargo?.76:1),height*(cargo?.9:.62),v.width);part.setPosition(cargo?-v.length*.12:0,height*.48,0);m.multiplyMatrices(root,part);batch.body.setMatrixAt(i,m);
   part.makeScale(v.length*(cargo?.16:heavy?.84:.48),height*.4,v.width*.86);part.setPosition(cargo?v.length*.4:0,height*(cargo?.72:.98),0);m.multiplyMatrices(root,part);batch.glass.setMatrixAt(i,m);
   if(cargo){part.makeScale(v.length*.2,height*.7,v.width*.92);part.setPosition(v.length*.4,height*.35,0);m.multiplyMatrices(root,part);}else m.makeScale(0,0,0);batch.cab.setMatrixAt(i,m);
   const radius=heavy?.48:.3;for(let w=0;w<4;w++){part.makeScale(radius,radius,v.width*.12);part.setPosition((w<2?-1:1)*Math.min(v.wheelbase,v.length*.8)/2,radius,(w%2?1:-1)*v.width*.48);m.multiplyMatrices(root,part);batch.tires.setMatrixAt(i*4+w,m);}
  });batch.body.instanceMatrix.needsUpdate=true;batch.glass.instanceMatrix.needsUpdate=true;batch.tires.instanceMatrix.needsUpdate=true;batch.cab.instanceMatrix.needsUpdate=true;}
  if(this.followId!=null){const v=this.data.vehicles.find(v=>v.id===this.followId),s=v&&this.sample(v,this.time);if(s){const direction=new THREE.Vector3(s[4],s[5],s[6]).normalize(),position=new THREE.Vector3(s[1],s[2],s[3]);this.camera.position.copy(position).addScaledVector(direction,-Math.max(18,v.length*1.5));this.camera.position.y+=Math.max(7,v.length*.45);this.controls.target.copy(position).addScaledVector(direction,7);this.controls.target.y+=1;this.camera.lookAt(this.controls.target);}}
  this.updateTransport();this.render();
 }
 follow(){const v=this.data?.vehicles.find(v=>this.sample(v,this.time));if(!v)throw Error('Não há veículo ativo neste instante. Avance o tempo da prévia.');this.followId=v.id;this.setTime(this.time);}
 play(){if(!this.data||this.playing||this.lost||this.disposed)return;if(this.time>=this.data.duration_s)this.setTime(0);this.playing=true;let previous=performance.now();const tick=now=>{if(!this.playing||this.disposed)return;const dt=Math.min(.1,(now-previous)/1000);previous=now;this.setTime(this.time+dt);this.onStatus(`Prévia 3D · ${this.time.toFixed(1)} / ${this.data.duration_s.toFixed(1)} s`);if(this.time>=this.data.duration_s){this.pause();return;}this.raf=requestAnimationFrame(tick);};this.raf=requestAnimationFrame(tick);}
 pause(){this.playing=false;cancelAnimationFrame(this.raf);}
 setDiagnostics(show){this.technical.visible=!!show;this.render();}
 setLight(mode){this.lightMode=mode;this.sun.color.set(mode==='entardecer'?0xffbf83:0xfff2da);this.sun.intensity=mode==='entardecer'?1.7:3.;this.sun.position.y=this.data?.span_m*(mode==='entardecer'?.2:.7)||100;this.render();}
 fit(top=false){if(!this.data)return;this.followId=null;const s=Math.max(this.data.span_m,60);this.controls.target.set(0,0,0);this.camera.position.set(top?0:s*.7,top?s*1.2:s*.7,top?.001:s*.85);this.controls.update();this.render();}
 pick(event){if(!this.data||this.lost)return;const r=this.canvas.getBoundingClientRect();if(!r.width||!r.height)return;this.pointer.set((event.clientX-r.left)/r.width*2-1,-(event.clientY-r.top)/r.height*2+1);this.ray.setFromCamera(this.pointer,this.camera);const hit=this.ray.intersectObjects(this.pickables,false)[0];if(!hit)return;let info=hit.object.userData;const batch=this.vehicleBatches.find(b=>b.body===hit.object);if(batch&&hit.instanceId!=null){const v=batch.tracks[hit.instanceId];info={name:`Veículo ${v.id}`,role:v.type,length:v.length,width:v.width};}const p=hit.point;this.onPick({...info,world:[p.x+this.data.origin_crs[0],-p.z+this.data.origin_crs[1],p.y+this.data.origin_crs[2]]});}
 captureSize(width,height){const previous={ratio:this.renderer.getPixelRatio(),size:this.renderer.getSize(new THREE.Vector2()),aspect:this.camera.aspect,enabled:this.controls.enabled,time:this.time,playing:this.playing};this.pause();this.capturing=true;this.controls.enabled=false;this.renderer.setPixelRatio(1);this.renderer.setSize(width,height,false);this.camera.aspect=width/height;this.camera.updateProjectionMatrix();return ()=>{if(this.disposed)return;this.capturing=false;this.renderer.setPixelRatio(previous.ratio);this.renderer.setSize(previous.size.x,previous.size.y,false);this.camera.aspect=previous.aspect;this.camera.updateProjectionMatrix();this.controls.enabled=previous.enabled;this.setTime(previous.time);if(previous.playing)this.play()};}
 cameraState(){return {position:this.camera.position.toArray(),target:this.controls.target.toArray(),follow_id:this.followId,light:this.lightMode};}
 resize(){if(this.disposed||this.capturing)return;const r=this.container.getBoundingClientRect();if(r.width<2||r.height<2)return;const ratio=Math.min(devicePixelRatio||1,2,Math.sqrt(4000000/(r.width*r.height)));this.renderer.setPixelRatio(Math.max(.5,ratio));this.renderer.setSize(r.width,r.height);this.camera.aspect=r.width/r.height;this.camera.updateProjectionMatrix();this.render();}
 render(){if(!this.disposed&&!this.lost)this.renderer.render(this.scene,this.camera);}
 async png(){if(this.disposed||!this.data||this.lost)throw Error('A vista 3D ainda não está disponível.');const wasPlaying=this.playing;this.pause();const visible=this.technical.visible;this.technical.visible=false;this.renderer.render(this.scene,this.camera);try{return await new Promise((resolve,reject)=>this.canvas.toBlob(b=>b?resolve(b):reject(Error('Falha ao capturar a vista 3D.')),'image/png'));}finally{this.technical.visible=visible;this.render();if(wasPlaying&&!this.disposed)this.play();}}
 stats(){return {ready:!!this.data,lost:this.lost,time:this.time,playing:this.playing,triangles:this.renderer.info.render.triangles,drawCalls:this.renderer.info.render.calls,geometries:this.renderer.info.memory.geometries,vehicles:this.data?.vehicles.length||0,diagnostics:this.technical.visible,trafficLights:this.signalLights?.length||0,railLights:this.railLights?.length||0,trainHeadlights:this.trainLights?.length||0,light:this.lightMode,followId:this.followId};}
 dispose(){if(this.disposed)return;this.pause();this.disposed=true;this.resizeObserver.disconnect();this.controls.dispose();this.canvas.removeEventListener('webglcontextlost',this.lostHandler);this.canvas.removeEventListener('webglcontextrestored',this.restoreHandler);this.canvas.removeEventListener('pointerdown',this.down);this.canvas.removeEventListener('pointerup',this.up);document.removeEventListener('visibilitychange',this.visibility);this.geometries.forEach(g=>g.dispose());this.materials.forEach(m=>m.dispose());this.textures.forEach(t=>t.dispose());this.renderer.dispose();this.renderer.forceContextLoss();this.canvas.remove();this.scene.clear();}
}
