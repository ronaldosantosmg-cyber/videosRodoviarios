/* ---------- Vista: imagem <-> canvas <-> mundo ---------- */
let view={s:1,ox:0,oy:0};
let canvasResizeFrame=0;
function scheduleCanvasResize(){if(canvasResizeFrame)return;canvasResizeFrame=requestAnimationFrame(()=>{canvasResizeFrame=0;resizeCanvas()})}
function resizeCanvas(){const r=canvas.getBoundingClientRect(),d=window.devicePixelRatio||1;const w=Math.max(320,Math.round(r.width*d)),h=Math.max(180,Math.round(r.height*d));if(canvas.width!==w||canvas.height!==h){// 2.62: abrir/fechar painéis só recorta ou amplia a área visível; zoom e posição do mapa NÃO mudam (antes o mapa reescalava e deslizava, e o clique seguinte pegava outro objeto).
 // Só a densidade de pixels do monitor (devicePixelRatio) reescala, para o mapa manter o mesmo tamanho na tela.
 if(!canvas._rsOk){/* primeiro dimensionamento (tela ainda no tamanho padrão): mantém o comportamento original de centro fixo */canvas._rsOk=1;canvas._dprAnt=d;const k0=w/canvas.width,cx=(canvas.width/2-view.ox)/view.s,cy=(canvas.height/2-view.oy)/view.s;canvas.width=w;canvas.height=h;view.s*=k0;view.ox=w/2-cx*view.s;view.oy=h/2-cy*view.s;draw();return}
 const k=canvas._dprAnt?d/canvas._dprAnt:1;canvas._dprAnt=d;canvas.width=w;canvas.height=h;if(k!==1){view.s*=k;view.ox*=k;view.oy*=k}window.__rsAssentaAte=performance.now()+350}else{canvas._rsOk=1;canvas._dprAnt=canvas._dprAnt||d}draw()}
// O espaço de imagem pode mudar após recalcular rotas; conservar a vista em CRS.
function captureProjectView(){
 if(!ready())return null;
 try{const center=C2W(canvas.width/2,canvas.height/2),scale=pxPerM();
 return [center.x,center.y,scale].every(Number.isFinite)&&scale>0?{center,scale}:null}catch{return null}
}
function restoreProjectView(saved){
 if(!saved||!ready()||![saved.center?.x,saved.center?.y,saved.scale].every(Number.isFinite)||saved.scale<=0)return false;
 const [x,y]=worldToImg(saved.center),scale=saved.scale*mpp();
 if(![x,y,scale].every(Number.isFinite)||scale<=0)return false;
 view={s:scale,ox:canvas.width/2-x*scale,oy:canvas.height/2-y*scale};
 window.RodoviaLayers?.invalidate();draw();return true;
}
function fitView(){if(!ready()){draw();return}let x0=0,y0=0,x1,y1;[x1,y1]=imgSize();
 if(useGeo()&&analysis?.bounds){const [[a,b],[c,d]]=analysis.bounds;const q=[[a,b],[c,b],[a,d],[c,d]].map(([x,y])=>worldToImg({x,y}));x0=Math.min(...q.map(v=>v[0]));x1=Math.max(...q.map(v=>v[0]));y0=Math.min(...q.map(v=>v[1]));y1=Math.max(...q.map(v=>v[1]));const m=.06*Math.max(x1-x0,y1-y0);x0-=m;x1+=m;y0-=m;y1+=m}
 if(![x0,y0,x1,y1].every(Number.isFinite)||x1<=x0||y1<=y0)return msg('Não foi possível enquadrar: limites da geometria inválidos.',true);
 const s=Math.min(canvas.width/(x1-x0),canvas.height/(y1-y0));view={s,ox:(canvas.width-(x1-x0)*s)/2-x0*s,oy:(canvas.height-(y1-y0)*s)/2-y0*s};draw()}
const mpp=()=>useGeo()?geo.mpp_crs:meta.width_m/meta.screen_width; // metros (CRS) por pixel do espaço de imagem
function worldToImg(p){if(!p||(!useGeo()&&(typeof meta==='undefined'||!meta||!meta.camera)))return [0,0];if(useGeo()){const [mx,my]=toMerc(p.x,p.y);return [(mx-geo.m0x)/geo.R0,(geo.m0y-my)/geo.R0]}const dx=p.x-meta.camera[0],dy=p.y-meta.camera[1],m=mpp();return [(dx*meta.right[0]+dy*meta.right[1])/m+meta.screen_width/2,meta.screen_height/2-(dx*meta.up[0]+dy*meta.up[1])/m]}
function imgToWorld(x,y){if(useGeo()){const [X,Y]=toCrs(geo.m0x+x*geo.R0,geo.m0y-y*geo.R0);return {x:X,y:Y}}const m=mpp(),a=(x-meta.screen_width/2)*m,b=-(y-meta.screen_height/2)*m;return {x:meta.camera[0]+a*meta.right[0]+b*meta.up[0],y:meta.camera[1]+a*meta.right[1]+b*meta.up[1]}}
const W2C=p=>{const [x,y]=worldToImg(p);return [x*view.s+view.ox,y*view.s+view.oy]};
const C2W=(x,y)=>imgToWorld((x-view.ox)/view.s,(y-view.oy)/view.s);
const pxPerM=()=>view.s/mpp();
function evtCanvas(e){const r=canvas.getBoundingClientRect();return [(e.clientX-r.left)*canvas.width/r.width,(e.clientY-r.top)*canvas.height/r.height]}

/* ---------- 1.9: base de edição sobre imagem web (Esri) + vetores simplificados ---------- */
let localInfo=null,geo=null,vec=null,geoPid='',baseMode='map',vecPaths=null,tileState={ok:0,fail:0};
let directTiles=true;const ESRI_DIRECT=(z,y,x)=>`https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${z}/${y}/${x}`;
// Um único limite inclui rede e decodificação das duas bases.
const tilePipeline={active:0,queue:[],limit:6,enqueue(job){this.queue.push(job);this.pump()},pump(){while(this.active<this.limit&&this.queue.length){const job=this.queue.shift();if(!job.current())continue;this.active++;Promise.resolve().then(()=>job.current()?job.run():undefined).catch(()=>{}).finally(()=>{this.active--;this.pump()})}}};
class PixelTileCache extends Map{
 constructor(budget){super();this.budget=budget;this.bytes=0}
 get(k){const t=super.get(k);if(t){t.used=performance.now();super.delete(k);super.set(k,t)}return t}
 set(k,t){if(super.has(k))this.delete(k);t.bytes=t.bytes||256*256*4;super.set(k,t);this.bytes+=t.bytes;this.trim();return this}
 resize(k,t){if(super.get(k)!==t)return;this.bytes-=t.bytes;t.bytes=Math.max(1,t.img.naturalWidth||t.img.width)*Math.max(1,t.img.naturalHeight||t.img.height)*4;this.bytes+=t.bytes;this.trim()}
 trim(){while(this.bytes>this.budget&&this.size)this.delete(this.keys().next().value)}
 delete(k){const t=super.get(k);if(!t)return false;this.bytes-=t.bytes;t.cancelled=true;t.controller.abort();t.img.removeAttribute('src');return super.delete(k)}
 clear(){for(const k of [...this.keys()])this.delete(k)}
}
const tiles=new PixelTileCache(64*1024*1024),TILE_MAX_Z=19,MERC=20037508.342789244;
function tileEntry(){const img=new Image();img.decoding='async';return {img,ok:false,fail:false,empty:false,used:performance.now(),controller:new AbortController(),cancelled:false}}
async function decodeTileImage(t,url,current){
 if(!current())return false;
 await new Promise((resolve,reject)=>{const abort=()=>{t.img.removeAttribute('src');finish(Error('Imagem cancelada'))},finish=error=>{t.img.onload=t.img.onerror=null;t.controller.signal.removeEventListener('abort',abort);error?reject(error):resolve()};t.img.onload=()=>finish();t.img.onerror=()=>finish(Error('Imagem indisponível'));t.controller.signal.addEventListener('abort',abort,{once:true});t.img.src=url});
 if(!current())return false;
 if(typeof t.img.decode==='function')await t.img.decode();
 return current();
}
async function fetchTileImage(t,url,current){let objectUrl=null;try{const response=await fetch(url,{signal:t.controller.signal});if(!current())return false;if(response.status===204)return false;if(!response.ok)throw Error('Imagem HTTP '+response.status);const blob=await response.blob();if(!current())return false;objectUrl=URL.createObjectURL(blob);return await decodeTileImage(t,objectUrl,current)}finally{if(objectUrl)URL.revokeObjectURL(objectUrl)}}
const VSTYLE={water:['#4aa8ff',1.6,[],.25],edge_line:['#f4f2e2',1.2,[],0],cut:['#ff7a66',1.3,[],0],fill:['#86e08f',1.3,[],0],existing_pavement:['#d9d9d9',1.5,[],.10],pavement:['#ffffff',1.9,[],.14],shoulder:['#efe4b8',1.2,[],0],median:['#66e07a',1.5,[],.12],barrier:['#ffb347',1.7,[],0],oae:['#5ad8ff',2.2,[],.18],domain:['#ffe14d',1.4,[8,6],0],axis:['#ff4fd8',1.6,[10,6],0],overlay:['#c3b2ff',1.4,[],0],kmz:['#3fe0c5',2.2,[5,4],0]};
const VNAME={water:'Hidrografia (DXF)',edge_line:'Bordos (DXF)',pavement:'Pavimento',existing_pavement:'Pavimento existente',shoulder:'Acostamento',median:'Canteiro',barrier:'Barreira',oae:'OAE',cut:'Corte',fill:'Aterro',domain:'Faixa de domínio',axis:'Eixos',overlay:'DXF adicionais',kmz:'KMZ'};
const SIGN={signage:['Sinalização do vídeo','#f4f2e2'],arrows:['Setas de fluxo do vídeo','#ffffff'],flows:['Trajetórias e sentidos','#61e6d7']};
let vecOn={},vecAlpha=.9,tileAlpha=1;
try{const v=JSON.parse(localStorage.getItem('rodovia_base')||'{}');if(v.mode)baseMode=v.mode;if(v.on)vecOn=v.on;if(v.va!=null)vecAlpha=v.va;if(v.ta!=null)tileAlpha=v.ta}catch(_e){window.RodoviaErros&&RodoviaErros.avisar('vista_imagem_web',_e)}
function saveBasePrefs(){try{localStorage.setItem('rodovia_base',JSON.stringify({mode:baseMode,on:vecOn,va:vecAlpha,ta:tileAlpha}))}catch(_e){window.RodoviaErros&&RodoviaErros.avisar('vista_imagem_web',_e)}}
const useGeo=()=>!!geo&&(baseMode!=='preview'||!baseImage||!meta);
const ready=()=>useGeo()||!!(baseImage&&meta);
const imgSize=()=>useGeo()?[geo.img_w,geo.img_h]:[baseImage.width,baseImage.height];
function minScale(){if(!ready())return .05;const [w,h]=imgSize();return Math.min(.05,.25*Math.min(canvas.width/w,canvas.height/h))}
function T10(u,v){return [1,u,v,u*u,u*v,v*v,u*u*u,u*u*v,u*v*v,v*v*v]}
function dot10(t,c){let r=0;for(let i=0;i<10;i++)r+=t[i]*c[i];return r}
function toMerc(x,y){const t=T10((x-geo.c[0])/geo.s[0],(y-geo.c[1])/geo.s[1]);return [dot10(t,geo.fx),dot10(t,geo.fy)]}
function toCrs(mx,my){const t=T10((mx-geo.mc[0])/geo.ms[0],(my-geo.mc[1])/geo.ms[1]);return [dot10(t,geo.ix),dot10(t,geo.iy)]}
async function loadGeo(){const id=pid,context=projectSession.context,keep=geoPid===id&&geo,current=()=>pid===id&&projectSession.context===context;let nextGeo=null,nextVec=null,nextLocal=null;
 if(analysis){try{nextGeo=await api('/api/projects/'+id+'/geo')}catch(e){if(keep){nextGeo=geo;nextVec=vec;nextLocal=localInfo}if(current()&&$('baseInfo'))$('baseInfo').textContent='Imagem web indisponível: '+e.message}
 if(nextGeo){try{nextVec=await api('/api/projects/'+id+'/vectors.json')}catch{if(keep)nextVec=vec}}
 if(nextGeo&&cfg?.local_imagery?.image){try{nextLocal=await api(`/api/projects/${id}/local/info`)}catch(_e){window.RodoviaErros&&RodoviaErros.avisar('vista_imagem_web',_e)}}}
 if(!current())return;geo=nextGeo;vec=nextVec;vecPaths=null;axisCache=null;localInfo=nextLocal;localTiles.clear();if(geo)buildVectorPaths();
 try{await localUi()}catch(_e){window.RodoviaErros&&RodoviaErros.avisar('vista_imagem_web',_e)}if(!current())return;if(!keep&&geoPid!==id)tileState={ok:0,fail:0};geoPid=id}

function buildVectorPaths(){vecPaths={};if(!vec||!geo)return;const L=vec.layers||{};
 const part=(role,list,existing)=>{const path=new Path2D(),fill=new Path2D();let nf=0;
  for(const r of list){for(const stroke of (window.RodoviaTrimController?.records(r.hatch_outline?{...r,k:cfg.derived_contours?r.source_k:Array.from({length:r.p.length},(_,i)=>i)}:r)||[r])){const sk=stroke.k?new Set(stroke.k):null;stroke.p.forEach((q,i)=>{const [x,y]=worldToImg({x:q[0],y:q[1]});if(i&&!(sk&&sk.has(i-1)))path.lineTo(x,y);else path.moveTo(x,y)});if(stroke.c&&!(sk&&sk.has(stroke.p.length-1))){if(sk&&sk.size&&stroke.p.length>1){const [x0,y0]=worldToImg({x:stroke.p[0][0],y:stroke.p[0][1]});path.lineTo(x0,y0)}else path.closePath()}}   /* 3.2.1: closePath volta ao último moveTo (reinício após trecho oculto), não ao 1º vértice: gerava corda fantasma */if(r.c){r.p.forEach((q,i)=>{const [x,y]=worldToImg({x:q[0],y:q[1]});if(i)fill.lineTo(x,y);else{fill.moveTo(x,y);nf++}});fill.closePath()}}
  return {path,fill:nf?fill:null,n:list.length,color:role==='overlay'&&list[0]?.color?list[0].color:VSTYLE[role]?.[0],existing}};
 for(const [role,list] of Object.entries(L)){if(!list.length)continue;const v=part(role,list,null);v.phases=[true,false].map(existing=>part(role,list.filter(r=>(r.existing??(role==='existing_pavement'))===existing),existing));vecPaths[role]=v;if(vecOn[role]===undefined)vecOn[role]=true}
 buildSignage()}
function buildSignage(){if(!vecPaths||!geo)return;delete vecPaths.signage;delete vecPaths.signage_y;delete vecPaths.arrows;if(!editor)return;
 const w={signage:new Path2D(),signage_y:new Path2D()};let n=0;
 for(const m of editor.markings||[]){const a=worldToImg({x:m[0],y:m[1]}),b=worldToImg({x:m[2],y:m[3]});const P=m[4]?w.signage_y:w.signage;P.moveTo(a[0],a[1]);P.lineTo(b[0],b[1]);n++}
 const ar=new Path2D();for(const a of editor.arrows||[]){const p={x:a[0],y:a[1]},t={x:a[2],y:a[3]},nn={x:-t.y,y:t.x};const pts=[[-2.4,0],[2.4,0],[.6,.9],[2.4,0],[.6,-.9]].map(([u,v])=>worldToImg({x:p.x+t.x*u+nn.x*v,y:p.y+t.y*u+nn.y*v}));ar.moveTo(...pts[0]);ar.lineTo(...pts[1]);ar.moveTo(...pts[2]);ar.lineTo(...pts[3]);ar.lineTo(...pts[4])}
 const pw=new Path2D(),py=new Path2D();for(const [yl,rings] of editor.paint||[]){const P=yl?py:pw;for(const r of rings){r.forEach((q,i)=>{const [x,y]=worldToImg({x:q[0],y:q[1]});i?P.lineTo(x,y):P.moveTo(x,y)});P.closePath()}}
 vecPaths.signage={path:w.signage,yellow:w.signage_y,paint:pw,paintY:py,n:n+(editor.paint||[]).length,color:'#f4f2e2'};vecPaths.arrows={path:ar,n:(editor.arrows||[]).length,color:'#ffffff'};
 for(const k of ['signage','arrows','flows'])if(vecOn[k]===undefined)vecOn[k]=true}
function tileKey(z,x,y){return (webSrc()==='esri'?'public':pid)+'|'+webKey()+':'+z+'/'+x+'/'+y}
// 1.19: fonte web do projeto (Esri atual, Wayback por data, XYZ ou WMS).
const webSrc=()=>cfg?.web_imagery?.source||'esri';
const webKey=()=>{const w=cfg?.web_imagery||{};return w.source&&w.source!=='esri'?[w.source,w.wayback_release||'',w.url||'',w.wms_layers||'',w.wms_version||'',w.wms_format||''].join('|'):'esri'};
const tileMaxZ=()=>webSrc()==='esri'?TILE_MAX_Z:Math.min(22,cfg.web_imagery.max_zoom||19);
let tileDrawPending=false;function tileRedraw(){if(tileDrawPending)return;tileDrawPending=true;requestAnimationFrame(()=>{tileDrawPending=false;draw()})}
function tilePlaceholder(img){try{const c=document.createElement('canvas');c.width=c.height=16;const g=c.getContext('2d',{willReadFrequently:true});g.drawImage(img,0,0,16,16);const d=g.getImageData(0,0,16,16).data;let r=0,gg=0,b=0,n=d.length/4;for(let i=0;i<d.length;i+=4){r+=d[i];gg+=d[i+1];b+=d[i+2]}r/=n;gg/=n;b/=n;
  if(Math.abs(r-gg)>4||Math.abs(gg-b)>4||r<190||r>215)return false;let v=0;for(let i=0;i<d.length;i+=4)v+=(d[i]-r)**2;return Math.sqrt(v/n)<12}catch{return false}}
function getTile(z,x,y){const k=tileKey(z,x,y),project=pid,context=projectSession.context,source=webKey();let t=tiles.get(k);
 if(t&&(t.project!==project||t.context!==context)){tiles.delete(k);t=null}
 if(t&&t.fail&&performance.now()-t.failAt>30000){tiles.delete(k);t=null}if(t)return t;
 t=tileEntry();t.project=project;t.context=context;tiles.set(k,t);
 const current=()=>!t.cancelled&&pid===project&&projectSession.context===context&&webKey()===source&&tiles.get(k)===t;
 const url=webSrc()==='esri'?`/tiles/esri/${z}/${y}/${x}`:`/api/projects/${project}/web_tiles/${z}/${y}/${x}?k=${encodeURIComponent(source)}`,esri=webSrc()==='esri';
 tilePipeline.enqueue({current,run:async()=>{try{
  let loaded=false;try{loaded=await fetchTileImage(t,url,current)}catch(error){if(!current())return;if(!esri||directTiles===false)throw error;t.direct=true;loaded=await decodeTileImage(t,ESRI_DIRECT(z,y,x),current)}
  if(!loaded||!current())return;tiles.resize(k,t);if(!current())return;
  if(tilePlaceholder(t.img)){t.placeholder=true;if(z>8)getTile(z-1,x>>1,y>>1);tileRedraw();return}
  t.ok=true;tileState.ok++;if(t.direct)tileState.direct=(tileState.direct||0)+1;tileRedraw();
 }catch(error){if(!current())return;t.fail=true;t.failAt=performance.now();tileState.fail++;tileRedraw()}}});return t}
/* Imagem local usa a mesma fila e um orçamento próprio de pixels decodificados. */
const localTiles=new PixelTileCache(32*1024*1024);
function localTileKey(z,x,y){return pid+'|'+(localInfo?.key||'')+'|'+z+'/'+x+'/'+y}
function getLocalTile(z,x,y){const project=pid,context=projectSession.context,source=localInfo?.key,k=localTileKey(z,x,y);let t=localTiles.get(k);
 if(t&&t.context!==context){localTiles.delete(k);t=null}
 if(t&&t.fail&&performance.now()-t.failAt>30000){localTiles.delete(k);t=null}if(t)return t;
 t=tileEntry();t.context=context;localTiles.set(k,t);
 const current=()=>!t.cancelled&&pid===project&&projectSession.context===context&&localInfo?.key===source&&localTiles.get(k)===t;
 tilePipeline.enqueue({current,run:async()=>{try{const loaded=await fetchTileImage(t,`/api/projects/${project}/local_tiles/${z}/${y}/${x}.png?k=${encodeURIComponent(source||'')}`,current);if(!current())return;if(!loaded){t.empty=true;tileRedraw();return}localTiles.resize(k,t);if(!current())return;t.ok=true;tileRedraw()}catch(error){if(!current())return;t.empty=true;t.fail=true;t.failAt=performance.now();tileRedraw()}}});return t}
function drawLocalTiles(){if(!localInfo||!localInfo.sources?.length||localInfo.editor===false||!geo)return;
 const res=geo.R0/view.s;const z=Math.max(10,Math.min(localInfo.max_zoom,Math.ceil(Math.log2(2*MERC/256/res)-.25))),n=2**z,size=2*MERC/n;
 const corners=[[0,0],[canvas.width,0],[0,canvas.height],[canvas.width,canvas.height]].map(([cx,cy])=>[geo.m0x+(cx-view.ox)/view.s*geo.R0,geo.m0y-(cy-view.oy)/view.s*geo.R0]);
 let mx0=Math.min(...corners.map(c=>c[0])),mx1=Math.max(...corners.map(c=>c[0])),my0=Math.min(...corners.map(c=>c[1])),my1=Math.max(...corners.map(c=>c[1]));
 const B=localInfo.sources.reduce((b,s)=>[Math.min(b[0],s.merc[0]),Math.min(b[1],s.merc[1]),Math.max(b[2],s.merc[2]),Math.max(b[3],s.merc[3])],[Infinity,Infinity,-Infinity,-Infinity]);
 mx0=Math.max(mx0,B[0]);my0=Math.max(my0,B[1]);mx1=Math.min(mx1,B[2]);my1=Math.min(my1,B[3]);if(mx1<=mx0||my1<=my0)return;
 const tx0=Math.floor((mx0+MERC)/size),tx1=Math.floor((mx1+MERC)/size),ty0=Math.floor((MERC-my1)/size),ty1=Math.floor((MERC-my0)/size);if((tx1-tx0+1)*(ty1-ty0+1)>300)return;
 ctx.save();ctx.setTransform(view.s,0,0,view.s,view.ox,view.oy);ctx.globalAlpha=tileAlpha;const px=size/geo.R0,pad=.6/view.s;
 for(let ty=ty0;ty<=ty1;ty++)for(let tx=tx0;tx<=tx1;tx++){const t=getLocalTile(z,tx,ty),ix=(-MERC+tx*size-geo.m0x)/geo.R0,iy=(geo.m0y-(MERC-ty*size))/geo.R0;
  if(t.ok){ctx.drawImage(t.img,ix,iy,px+pad,px+pad);continue}
  let retained=false;for(let k=1;k<=6&&z-k>=0;k++){const parent=localTiles.get(localTileKey(z-k,tx>>k,ty>>k));if(!parent?.ok)continue;const sub=parent.img.width/2**k,sx=(tx-((tx>>k)<<k))*sub,sy=(ty-((ty>>k)<<k))*sub;ctx.drawImage(parent.img,sx,sy,sub,sub,ix,iy,px+pad,px+pad);retained=true;break}
  if(!retained)for(let cy=0;cy<2;cy++)for(let cx=0;cx<2;cx++){const child=localTiles.get(localTileKey(z+1,tx*2+cx,ty*2+cy));if(child?.ok)ctx.drawImage(child.img,ix+cx*px/2,iy+cy*px/2,px/2+pad,px/2+pad)}
 }
 ctx.restore()}
function peekTile(z,x,y){const t=tiles.get(tileKey(z,x,y));if(t&&t.ok){t.used=performance.now();return t}return null}
function tileZoom(){const res=geo.R0/view.s;return Math.max(0,Math.min(tileMaxZ(),Math.ceil(Math.log2(2*MERC/256/res)-.25)))}
function drawTiles(){const z=tileZoom(),n=2**z,size=2*MERC/n;
 const corners=[[0,0],[canvas.width,0],[0,canvas.height],[canvas.width,canvas.height]].map(([cx,cy])=>[geo.m0x+(cx-view.ox)/view.s*geo.R0,geo.m0y-(cy-view.oy)/view.s*geo.R0]);
 const mx0=Math.min(...corners.map(c=>c[0])),mx1=Math.max(...corners.map(c=>c[0])),my0=Math.min(...corners.map(c=>c[1])),my1=Math.max(...corners.map(c=>c[1]));
 const tx0=Math.max(0,Math.floor((mx0+MERC)/size)),tx1=Math.min(n-1,Math.floor((mx1+MERC)/size)),ty0=Math.max(0,Math.floor((MERC-my1)/size)),ty1=Math.min(n-1,Math.floor((MERC-my0)/size));
 if((tx1-tx0+1)*(ty1-ty0+1)>400)return;
 ctx.save();ctx.setTransform(view.s,0,0,view.s,view.ox,view.oy);ctx.globalAlpha=tileAlpha;ctx.imageSmoothingEnabled=true;const px=size/geo.R0,pad=.6/view.s;
 for(let ty=ty0;ty<=ty1;ty++)for(let tx=tx0;tx<=tx1;tx++){const ix=(-MERC+tx*size-geo.m0x)/geo.R0,iy=(geo.m0y-(MERC-ty*size))/geo.R0;const t=getTile(z,tx,ty);
  if(t.ok){ctx.drawImage(t.img,ix,iy,px+pad,px+pad);continue}
  if(z>5)getTile(z-3,tx>>3,ty>>3);let retained=false;for(let k=1;k<=12&&z-k>=0;k++){const p=peekTile(z-k,tx>>k,ty>>k);if(!p)continue;const sub=p.img.width/2**k,sx=(tx-((tx>>k)<<k))*sub,sy=(ty-((ty>>k)<<k))*sub;ctx.drawImage(p.img,sx,sy,sub,sub,ix,iy,px+pad,px+pad);retained=true;break}
  if(!retained)for(let cy=0;cy<2;cy++)for(let cx=0;cx<2;cx++){const child=peekTile(z+1,tx*2+cx,ty*2+cy);if(child)ctx.drawImage(child.img,ix+cx*px/2,iy+cy*px/2,px/2+pad,px/2+pad)}
 }
 ctx.restore()}
function drawVectors(){if(!vecPaths)return;ctx.save();ctx.setTransform(view.s,0,0,view.s,view.ox,view.oy);ctx.lineJoin='round';ctx.lineCap='round';ctx.globalAlpha=vecAlpha;const k=1/view.s;
 for(const phase of [true,false])for(const role of Object.keys(VSTYLE)){const base=vecPaths[role],v=base?.phases?.find(p=>p.existing===phase)||(phase===false?base:null);if(!v||!v.n||vecOn[role]===false)continue;const st=VSTYLE[role];
  if(v.fill&&st[3]){ctx.fillStyle=v.color+Math.round(st[3]*255).toString(16).padStart(2,'0');ctx.fill(v.fill,'evenodd')}
  try{window.RodoviaTexturasVivas?.pintarRole?.(ctx,role,v)}catch(e){window.RodoviaErros?.avisar('textura 2D',e)}
  ctx.setLineDash([]);ctx.strokeStyle='#05101a';ctx.globalAlpha=vecAlpha*.55;ctx.lineWidth=(st[1]+2)*k;ctx.stroke(v.path);ctx.globalAlpha=vecAlpha;
  ctx.setLineDash(st[2].map(d=>d*k));ctx.strokeStyle=v.color;ctx.lineWidth=st[1]*k;ctx.stroke(v.path)}
 ctx.setLineDash([]);const mpx=geo.R0/geo.k;// metros por pixel do espaço de imagem
 // Sinalização e setas como no vídeo: largura real (0,15 m / 0,16 m) com mínimo de 1 px na tela.
 if(vecPaths.signage&&vecOn.signage!==false){ctx.globalAlpha=Math.min(1,vecAlpha+.1);ctx.lineWidth=Math.max(.15/mpx,1*k);ctx.strokeStyle='#f4f2e2';ctx.stroke(vecPaths.signage.path);ctx.strokeStyle='#f4c846';ctx.stroke(vecPaths.signage.yellow);ctx.fillStyle='#f4f2e2';ctx.fill(vecPaths.signage.paint,'evenodd');ctx.fillStyle='#f4c846';ctx.fill(vecPaths.signage.paintY,'evenodd')}
 if(vecPaths.arrows&&vecOn.arrows!==false&&editor?.signage_detail!=='full'){ctx.globalAlpha=1;ctx.lineWidth=Math.max(.35/mpx,2*k);ctx.strokeStyle='#05101a';ctx.stroke(vecPaths.arrows.path);ctx.lineWidth=Math.max(.18/mpx,1.2*k);ctx.strokeStyle='#ffffff';ctx.stroke(vecPaths.arrows.path)}
 ctx.restore();if(editor&&vecOn.signage!==false)for(const g of editor.signs||[])if(g.source!=='manual')drawSignIcon({x:g.x,y:g.y},g.code,g.text,false)}
function setBase(mode){if(mode==='preview'&&!(baseImage&&meta))return msg('Gere uma prévia para usar a imagem renderizada como fundo.',true);if(mode!=='preview'&&!geo)return msg('Analise os arquivos (seção 1) para usar a imagem web.',true);
 let c=null,ppm=null;if(ready()){c=C2W(canvas.width/2,canvas.height/2);ppm=pxPerM()}baseMode=mode;saveBasePrefs();
 if(c){const [x,y]=worldToImg(c);view.s=ppm*mpp();view.ox=canvas.width/2-x*view.s;view.oy=canvas.height/2-y*view.s}baseUi();draw()}
function baseUi(){const sel=$('baseMode');if(!sel)return;sel.value=useGeo()?(baseMode==='none'?'none':'map'):'preview';
 sel.querySelector('option[value=preview]').disabled=!(baseImage&&meta);for(const v of ['map','none'])sel.querySelector(`option[value=${v}]`).disabled=!geo;
 $('vecAlpha').value=vecAlpha;$('tileAlpha').value=tileAlpha;
 const roles=vecPaths?Object.keys(VSTYLE).filter(r=>vecPaths[r]).concat(['signage','arrows'].filter(r=>vecPaths[r])):[];if(editor)roles.push('flows');$('vecLayers').innerHTML=roles.length?roles.map(r=>`<label class="vl"><input type="checkbox" data-vrole="${r}" ${vecOn[r]!==false?'checked':''}><span style="background:${(vecPaths?.[r]||{color:SIGN[r]?.[1]}).color}"></span>${VNAME[r]||SIGN[r]?.[0]||r} <small>(${r==='flows'?editor.segments.length:vecPaths[r].n})</small></label>`).join(''):'<span class="muted">Sem vetores: clique “Analisar arquivos”.</span>';
 $('baseInfo').textContent=geo?`Conversão CRS ↔ imagem web: erro máx. ${(Math.max(geo.err_fwd_m,geo.err_inv_m)*1000).toFixed(1)} mm`+(vec?` · ${vec.points} vértices simplificados (tolerância 0,25 m)`:' · vetores ainda não gerados: clique “Analisar arquivos”')+(useGeo()?'':' · editando sobre a prévia renderizada'):(analysis?'':'Analise os arquivos para abrir a imagem web.')}

