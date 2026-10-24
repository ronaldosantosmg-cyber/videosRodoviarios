// =====================================================================================================
// 1.27 — seleção e edição direta (grips destacados, arrastar, girar pela alça, mini-barra, setas),
// áreas do desenho (trocar textura, nome, tipo), caixas de chamada com linha ajustável, menu do botão
// direito só com os comandos da seleção (largura fixa), fluxos (ligações, velocidade, editar traçado),
// velocidade de avanço da apresentação, barra de menus e de status no estilo Windows, janela Sobre.
// =====================================================================================================
MARK_KEYS.push('connection_rules','advance_zones');
estender('emptyMarks',_em=>function(){return {..._em(),connection_rules:[],advance_zones:[]}},'velocidade de avanço da apresentação, barra de menus e de status no es');
for(const k of ['connection_rules','advance_zones'])if(!M[k])M[k]=[];
fields.push('advance_mode','advance_speed_kmh');numeric.push('advance_speed_kmh');checks.push('curve_speed');
OBJ_SPECS.push(['advance_zones','Velocidade de avanço','line',o=>[[o,'start'],[o,'end']]]);
OBJ_SPECS.push(['connection_rules','Regra de ligação','line',o=>[[o,'a'],[o,'b']]]);
ENUMS.action=ENUMS.action||{};ENUMS.action.connection_rules={deny:'Proibir o movimento',force:'Forçar a ligação'};
Object.assign(PROP_LABEL,{speed_pct:['Velocidade (% da normal)','50 = metade da velocidade (mais tempo neste trecho); 200 = o dobro.'],speed_kmh:['Velocidade (km/h)','Limite dos veículos neste fluxo; vazio = velocidade do vídeo.'],
 action:['Ação','Proibir: os veículos não fazem este movimento. Forçar: cria a ligação entre os dois trechos.'],direction:['Sentido','Auto, crescente, decrescente ou dois sentidos.'],level:['Nível','Nível do fluxo (viadutos: 1, 2…).'],texture:['Textura','']});
NULLABLE_NUM.add('speed_kmh');

// ---------- utilidades ----------
function selObjs(){return allSelected()}
function selGrips(){const L=selObjs();return L.flatMap(o=>o.grips.map(gripGet))}
function selBox(){if(typeof ready==='function'&&!ready())return null;const G=selGrips();if(!G.length)return null;const Q=G.map(p=>W2C(p));let x0=Infinity,y0=Infinity,x1=-Infinity,y1=-Infinity;for(const [x,y] of Q){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y)}
 let wx=0,wy=0;for(const p of G){wx+=p.x;wy+=p.y}return {x0,y0,x1,y1,c:{x:wx/G.length,y:wy/G.length},n:G.length}}
function rotHandle(){const b=selBox();if(!b||b.n<2)return null;const L=selObjs();if(L.length===1&&L[0].shape==='pt')return null;return {x:(b.x0+b.x1)/2,y:Math.max(14,b.y0-34),bx:(b.x0+b.x1)/2,by:b.y0,c:b.c}}
const LABEL_KEYS={highlights:o=>o.point,gantries:o=>({x:(o.a.x+o.b.x)/2,y:(o.a.y+o.b.y)/2})};
function labelAnchor(o){const f=LABEL_KEYS[o.key];return f?f(o.o):null}
function labelPos(o){const a=labelAnchor(o);if(!a)return null;if(o.o.label)return o.o.label;const k=1/Math.max(pxPerM(),1e-9);return {x:a.x+60*k,y:a.y+60*k}}
function leaderInfo(o){const a=labelAnchor(o),b=labelPos(o);if(!a||!b)return null;const d=Math.hypot(b.x-a.x,b.y-a.y),az=(Math.atan2(b.x-a.x,b.y-a.y)*180/Math.PI+360)%360;return {d,az}}
function segById(id){return editor?.segments?.find(x=>x.id===id)||null}
async function inputBox(title,labelText,value=''){return new Promise(res=>{const d=$('inputDlg');$('inputTitle').textContent=title;$('inputLabel').textContent=labelText;const i=$('inputValue');i.value=value;let done=false;
 const fin=v=>{if(done)return;done=true;d.close();res(v)};$('inputOk').onclick=()=>{const v=i.value.trim();if(!v){i.focus();return msg('O valor não pode ficar vazio.',true)}fin(v)};$('inputCancel').onclick=()=>fin(null);d.oncancel=e=>{e.preventDefault();fin(null)};
 i.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();e.stopPropagation();$('inputOk').click()}};d.showModal();setTimeout(()=>{i.focus();i.select()},0)})}

// ---------- desenho da seleção: grips destacados, alça de giro, linha de chamada e mini-barra ----------
let hotGrip=null,dxfSel=null,selLink=null,showAllLinks=false;
drawSelection=function(){const L=selObjs();if(!L.length)return;ctx.save();
 for(const o of L){const P=o.grips.map(g=>W2C(gripGet(g)));ctx.strokeStyle='#4fa3ff';ctx.lineWidth=2.5;ctx.setLineDash([7,4]);
  if(o.shape!=='pt'){ctx.beginPath();P.forEach(([x,y],k)=>k?ctx.lineTo(x,y):ctx.moveTo(x,y));if(o.shape==='area'){ctx.closePath();ctx.fillStyle='#4fa3ff22';ctx.fill()}ctx.shadowColor='#4fa3ff';ctx.shadowBlur=6;ctx.stroke();ctx.shadowBlur=0}
  ctx.setLineDash([]);
  o.grips.forEach((g,k)=>{const [x,y]=P[k];const hot=hotGrip&&hotGrip.o.key===o.key&&hotGrip.o.i===o.i&&hotGrip.k===k;const s=hot?8:6.5;ctx.fillStyle=drag?.type==='grip'&&hot?'#ff3b3b':hot?'#ff8a00':'#1f6fff';ctx.strokeStyle='#fff';ctx.lineWidth=2;ctx.shadowColor='#000a';ctx.shadowBlur=4;ctx.fillRect(x-s,y-s,2*s,2*s);ctx.shadowBlur=0;ctx.strokeRect(x-s,y-s,2*s,2*s)});
  const lp=labelPos(o);if(lp&&L.length===1){const [ax,ay]=W2C(labelAnchor(o)),[lx,ly]=W2C(lp);ctx.strokeStyle='#ffd66b';ctx.lineWidth=1.8;ctx.setLineDash([5,4]);ctx.beginPath();ctx.moveTo(ax,ay);ctx.lineTo(lx,ly);ctx.stroke();ctx.setLineDash([]);
   const hot=hotGrip&&hotGrip.label;ctx.fillStyle=hot?'#ff8a00':'#ffd66b';ctx.strokeStyle='#081623';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(lx,ly-9);ctx.lineTo(lx+9,ly);ctx.lineTo(lx,ly+9);ctx.lineTo(lx-9,ly);ctx.closePath();ctx.fill();ctx.stroke();
   const li=leaderInfo(o);ctx.font='11px system-ui';ctx.fillStyle='#ffe7a3';ctx.strokeStyle='#081623';ctx.lineWidth=3;const t=`caixa · linha ${li.d.toFixed(1)} m`;ctx.strokeText(t,lx+12,ly+4);ctx.fillText(t,lx+12,ly+4)}}
 const h=rotHandle();if(h){ctx.strokeStyle='#4fa3ff';ctx.lineWidth=1.5;ctx.beginPath();ctx.moveTo(h.bx,h.by);ctx.lineTo(h.x,h.y+8);ctx.stroke();ctx.beginPath();ctx.arc(h.x,h.y,8,0,7);ctx.fillStyle=hotGrip&&hotGrip.rot?'#ff8a00':'#fff';ctx.fill();ctx.stroke();
  ctx.strokeStyle='#1f6fff';ctx.lineWidth=1.6;ctx.beginPath();ctx.arc(h.x,h.y,4,-.3,4.2);ctx.stroke()}
 if(drag?.type==='rot'){const [cx,cy]=W2C(drag.c);ctx.strokeStyle='#ff8a00';ctx.setLineDash([4,4]);ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(drag.cur.cx,drag.cur.cy);ctx.stroke();ctx.setLineDash([]);ctx.font='bold 12px system-ui';ctx.fillStyle='#ffe7a3';ctx.fillText(`${drag.ang.toFixed(1)}°`,drag.cur.cx+12,drag.cur.cy-10)}
 ctx.restore()}
function drawDxfSel(){if(!dxfSel)return;const P=dxfSel.points.map(P_);ctx.save();poly(P,true);ctx.fillStyle='#38e1ff2e';ctx.fill();ctx.strokeStyle='#38e1ff';ctx.lineWidth=2.5;ctx.setLineDash([8,4]);ctx.stroke();ctx.setLineDash([]);
 const step=Math.max(1,Math.ceil(P.length/400));for(let i=0;i<P.length;i+=step){const [x,y]=W2C(P[i]);ctx.fillStyle='#081623';ctx.strokeStyle='#38e1ff';ctx.lineWidth=2;ctx.fillRect(x-4.5,y-4.5,9,9);ctx.strokeRect(x-4.5,y-4.5,9,9)}
 label(`Área do desenho · ${dxfSel.layer} · ${dxfSel.area_m2.toLocaleString('pt-BR')} m²`,P[0],'#bff4ff');ctx.restore()}
const P_=a=>Array.isArray(a)?{x:a[0],y:a[1]}:a;
function drawLinks(){if(!editor||!editor.connections||vecOn.flows===false)return;const sid=selSeg?selSeg.id:null;if(sid==null&&!showAllLinks&&!selLink)return;ctx.save();
 const one=(c,col,w,dash)=>{const pts=c.p.map(P);if(pts.length<2||polyLen(pts)<.1)return;poly(pts);ctx.strokeStyle=col;ctx.lineWidth=w;ctx.setLineDash(dash||[]);ctx.stroke();ctx.setLineDash([]);if(pts.length>1)arrowHead(pts[pts.length-2],pts[pts.length-1],10,col)};
 for(const c of editor.connections){const out=c.from===sid,inn=c.to===sid;if(!(showAllLinks||out||inn))continue;one(c,window.RodoviaFlowStudy?.stale?'#eab308':'#22c55e',out||inn?3.5:1.6)}
 for(const c of editor.denied||[]){if(!(showAllLinks||c.from===sid||c.to===sid))continue;one(c,'#ff4d4d',2.5,[5,4]);const m=P(c.p[Math.floor(c.p.length/2)]),[x,y]=W2C(m);ctx.strokeStyle='#ff4d4d';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(x-6,y-6);ctx.lineTo(x+6,y+6);ctx.moveTo(x+6,y-6);ctx.lineTo(x-6,y+6);ctx.stroke()}
 if(selLink){one(selLink,'#ffe14d',6);one(selLink,selLink.denied?'#ff4d4d':'#36f28a',2.5,selLink.denied?[5,4]:[])}ctx.restore()}
function drawAdvanceZones(){const ad=axisData();for(const z of M.advance_zones||[]){if(!z.start||!z.end)continue;let pts=[z.start,z.end];if(ad){const a=projectAxis(z.start),b=projectAxis(z.end);if(a&&b)pts=axisSub(a.s,b.s)}
  poly(pts);ctx.save();ctx.lineCap='butt';ctx.strokeStyle=z.enabled===false?'#9aa3a866':(z.speed_pct<100?'#ffb34799':'#5ad8ff99');ctx.lineWidth=Math.max(10,24);ctx.stroke();ctx.restore();label(`⏱ ${z.name} · ${Math.round(z.speed_pct)}%`,pts[0],z.speed_pct<100?'#ffd9a0':'#bfefff')}}
estender('draw',_d=>function(){_d();if(!ready())return;try{drawAdvanceZones();drawLinks();drawDxfSel();placeSelBar()}catch(err){}},'desenho da seleção: grips destacados, alça de giro, linha de chamada e');
function placeSelBar(){const bar=$('selBar');if(!bar)return;const L=selObjs();const b=selBox();if((!L.length&&!dxfSel)||drag||!b&&!dxfSel){bar.hidden=true;return}
 const r=canvas.getBoundingClientRect(),k=r.width/canvas.width;let x,y;if(b){x=b.x1*k+10;y=b.y0*k-6}else{const q=W2C(P_(dxfSel.points[0]));x=q[0]*k+10;y=q[1]*k-6}
 const isArea=L.length&&L.every(o=>o.key==='pavement_areas')||(!L.length&&dxfSel);const named=L.length===1&&('name' in L[0].o||'title' in L[0].o)||(!L.length&&dxfSel);
 bar.querySelectorAll('[data-sb]').forEach(btn=>{const a=btn.dataset.sb;btn.hidden=(a==='tex'&&!isArea)||(a==='name'&&!named)||(!L.length&&['move','rot','copy','del','props'].includes(a))||(L.length&&a==='edit')});
 bar.hidden=false;const w=bar.offsetWidth,h=bar.offsetHeight;bar.style.left=Math.max(4,Math.min(r.width-w-4,x))+'px';bar.style.top=Math.max(4,Math.min(r.height-h-4,y-h))+'px'}

// ---------- seleção e edição direta (tem prioridade: escuta na janela, fase de captura) ----------
function hitRot(c){const h=rotHandle();return h&&Math.hypot(c.cx-h.x,c.cy-h.y)<=11*DPR()?h:null}
function hitLabel(c){const L=selObjs();if(L.length!==1)return null;const lp=labelPos(L[0]);if(!lp)return null;const [x,y]=W2C(lp);return Math.hypot(c.cx-x,c.cy-y)<=11*DPR()?L[0]:null}
function hitAnyGrip(c){for(const o of selObjs())for(let k=0;k<o.grips.length;k++){const [x,y]=W2C(gripGet(o.grips[k]));if(Math.abs(x-c.cx)<=8*DPR()&&Math.abs(y-c.cy)<=8*DPR())return {o,k}}return null}
function linkAt(c){if(!editor?.connections)return null;const sid=selSeg?selSeg.id:null;let best=null;
 const test=(lk,den)=>{if(!(showAllLinks||lk.from===sid||lk.to===sid))return;const Q=lk.p.map(p=>W2C(P(p)));for(let i=0;i+1<Q.length;i++){const d=segDist(c.cx,c.cy,...Q[i],...Q[i+1]);if(d<=7*DPR()&&(!best||d<best.d))best={d,lk:{...lk,denied:den}}}};
 for(const lk of editor.connections)test(lk,false);for(const lk of editor.denied||[])test(lk,true);return best&&best.lk}
let sb=null;   // estado do arraste direto
window.addEventListener('pointerdown',e=>{if(e.target===canvas&&ctxState)closeMenu();if(e.target!==canvas||e.button!==0||!ready()||tool!=='pan'||cadCmd||spaceDown||e.ctrlKey)return;const c=canvasPt(e);
 const stop=()=>{e.stopImmediatePropagation();e.preventDefault();try{canvas.setPointerCapture(e.pointerId)}catch{};canvas.focus({preventScroll:true})};
 const r=hitRot(c);if(r){stop();checkpoint();const L=selObjs();drag={type:'rot',c:r.c,a0:Math.atan2(c.w.y-r.c.y,c.w.x-r.c.x),objs:L,base:L.map(o=>o.grips.map(gripGet)),ang:0,cur:c};return}
 const lo=hitLabel(c);if(lo){stop();checkpoint();drag={type:'label',o:lo};return}
 if(hitAnyGrip(c))return;   // grips: arraste do 1.22
 if(window.RodoviaFlowStudy?.isEditing?.()&&!e.shiftKey){
  const hit=hitObjects(c).find(h=>['route_alignments','traffic_paths'].includes(h.key));
  if(hit){stop();sel={key:hit.key,i:hit.i};selSet=[];dxfSel=null;selSeg=null;selLink=null;showProps();draw();return}
  const link=linkAt(c),segment=nearestSegment(c.w,6/Math.max(pxPerM(),1e-9));
  if(link||segment){stop();sel=null;selSet=[];dxfSel=null;if(link){selLink=link;selSeg=null;showLinkProps()}else{selSeg={id:segment.id};selLink=null;showSegProps()}draw();return}
 }
 let h=hitObject(c);
 // Dentro de uma área (sem tocar a borda), ligação ou trajetória perto do clique têm prioridade.
 if(h&&h.d>=7&&objOf(h)?.shape==='area'&&!e.shiftKey&&(linkAt(c)||(vecOn.flows!==false&&nearestSegment(c.w,6/Math.max(pxPerM(),1e-9)))))h=null;
 if(h){stop();dxfSel=null;selLink=null;const s={key:h.key,i:h.i};
  if(e.shiftKey){if(sel&&!inSet(sel))selSet.push(sel);if(inSet(s)){selSet=selSet.filter(x=>!(x.key===s.key&&x.i===s.i));sel=selSet[selSet.length-1]||null}else{selSet.push(s);sel=s}showProps();draw();return msg(`${selObjs().length} objeto(s) selecionado(s). Arraste para mover; alça redonda gira; botão direito: comandos.`)}
  const already=(sel&&sel.key===s.key&&sel.i===s.i)||inSet(s);if(!already){sel=s;selSet=[];selSeg=null;showProps()}
  checkpoint();const L=selObjs();drag={type:'mmove',w0:c.w,c0:c,objs:L,base:L.map(o=>o.grips.map(gripGet)),moved:false};
  if(!already){const o=objOf(sel);draw();msg(`Selecionado: ${o.label}${o.o.name?' “'+o.o.name+'”':''}. Arraste para mover · alça redonda gira · Delete apaga · setas deslocam · botão direito: comandos.`)}return}
 sb={c0:c,alt:e.altKey,hadSel:!!(sel||selSet.length||dxfSel||selLink)}},true);
window.addEventListener('pointermove',e=>{if(!drag||!['rot','label','mmove'].includes(drag.type))return;const c=canvasPt(e);if(!c.w)return;lastWorld=c.w;e.stopImmediatePropagation();
 if(drag.type==='mmove'){if(!drag.moved&&Math.hypot(c.cx-drag.c0.cx,c.cy-drag.c0.cy)<4)return;drag.moved=true;let dx=c.w.x-drag.w0.x,dy=c.w.y-drag.w0.y;if(e.shiftKey||$('orthoOn')?.checked){if(Math.abs(dx)>=Math.abs(dy))dy=0;else dx=0}drag.objs.forEach((o,k)=>o.grips.forEach((g,j)=>gripSet(g,{x:drag.base[k][j].x+dx,y:drag.base[k][j].y+dy})));drag.d=Math.hypot(dx,dy);$('cursor').textContent=`Movendo ${drag.objs.length} objeto(s): ${drag.d.toFixed(3)} m (ΔX ${dx.toFixed(3)} · ΔY ${dy.toFixed(3)}) · Shift: só na horizontal/vertical · Esc: desfaz o arraste`}
 else if(drag.type==='rot'){let a=(Math.atan2(c.w.y-drag.c.y,c.w.x-drag.c.x)-drag.a0)*180/Math.PI;if(e.shiftKey)a=Math.round(a/15)*15;a=((a+540)%360)-180;drag.ang=a;drag.cur=c;drag.moved=true;const r=a*Math.PI/180,co=Math.cos(r),si=Math.sin(r),C=drag.c;
  drag.objs.forEach((o,k)=>o.grips.forEach((g,j)=>{const p=drag.base[k][j];gripSet(g,{x:C.x+(p.x-C.x)*co-(p.y-C.y)*si,y:C.y+(p.x-C.x)*si+(p.y-C.y)*co})}));$('cursor').textContent=`Girando ${a.toFixed(1)}° (Shift: passos de 15°)`}
 else if(drag.type==='label'){drag.o.o.label={x:c.w.x,y:c.w.y};drag.moved=true;const li=leaderInfo(drag.o);$('cursor').textContent=`Caixa de chamada: linha ${li.d.toFixed(2)} m · direção ${li.az.toFixed(1)}°`}
 draw()},true);
window.addEventListener('pointerup',e=>{if(drag&&['rot','label','mmove'].includes(drag.type)){const d=drag;drag=null;e.stopImmediatePropagation();
  if(d.moved){if(d.objs)d.objs.forEach(o=>afterGeomEdit(o));changed(d.type==='rot'?`Girado ${d.ang.toFixed(1)}°.`:d.type==='label'?`Caixa de chamada reposicionada (linha ${leaderInfo(d.o).d.toFixed(1)} m).`:`${d.objs.length} objeto(s) movido(s) ${d.d.toFixed(3)} m.`);showProps();scheduleViewPreview()}else{undoStack.pop();updateUndo()}draw();return}
 if(!sb||e.target!==canvas&&!canvas.contains(e.target))return;const st=sb;sb=null;const c=canvasPt(e);if(!c.w||Math.hypot(c.cx-st.c0.cx,c.cy-st.c0.cy)>4||tool!=='pan'||e.button!==0)return;
 // Clique simples no vazio: ligação > trajetória > área do desenho (Alt: direto na área).
 const lk=st.alt?null:linkAt(c);if(lk){e.stopImmediatePropagation();selLink=lk;dxfSel=null;sel=null;selSet=[];showLinkProps();draw();return}
 const segNear=!st.alt&&vecOn.flows!==false&&nearestSegment(c.w,6/Math.max(pxPerM(),1e-9));if(segNear){selLink=null;dxfSel=null;return}
 if(sel||selSet.length){sel=null;selSet=[];showProps();if($('propPanel'))$('propPanel').hidden=true}
 selLink=null;selSeg=null;pickDxfArea(c.w)},true);
async function pickDxfArea(w){if(!pid||!useGeo())return;try{const r=await api(`/api/projects/${pid}/area?x=${w.x}&y=${w.y}`);dxfSel=r;showDxfProps();draw();msg(`Área do desenho selecionada (camada ${r.layer}, ${r.area_m2.toLocaleString('pt-BR')} m²). Botão direito: trocar textura, nome ou tipo. O DXF não é alterado.`)}
 catch(err){if(dxfSel){dxfSel=null;draw()}const box=$('propPanel');if(box&&!sel&&!selSet.length&&!selSeg)box.hidden=true}}
canvas.addEventListener('pointermove',e=>{if(drag||tool!=='pan'||!ready())return;const c=canvasPt(e);const r=hitRot(c),lo=hitLabel(c),g=hitAnyGrip(c);const nh=r?{rot:1}:lo?{label:1}:g?{o:g.o,k:g.k}:null;
 if(JSON.stringify(nh&&{r:nh.rot,l:nh.label,k:nh.k,o:nh.o&&nh.o.key+nh.o.i})!==JSON.stringify(hotGrip&&{r:hotGrip.rot,l:hotGrip.label,k:hotGrip.k,o:hotGrip.o&&hotGrip.o.key+hotGrip.o.i})){hotGrip=nh;draw()}
 canvas.style.cursor=r?'alias':lo||g?'move':hitObject(c)?'pointer':'grab'});
// Setas do teclado deslocam a seleção (0,10 m; Shift 1 m; Ctrl 0,01 m).
let nudgeT=null;canvas.addEventListener('keydown',e=>{if(!e.key.startsWith('Arrow')||tool!=='pan'||draft||cadCmd)return;const L=selObjs();if(!L.length)return;e.preventDefault();e.stopImmediatePropagation();
 const st=e.shiftKey?1:e.ctrlKey?.01:.1,dx=e.key==='ArrowRight'?st:e.key==='ArrowLeft'?-st:0,dy=e.key==='ArrowUp'?st:e.key==='ArrowDown'?-st:0;if(!nudgeT)checkpoint();clearTimeout(nudgeT);nudgeT=setTimeout(()=>{nudgeT=null;changed('Seleção deslocada pelas setas.');showProps()},600);
 L.forEach(o=>{o.grips.forEach(g=>{const p=gripGet(g);gripSet(g,{x:p.x+dx,y:p.y+dy})});afterGeomEdit(o)});draw()},true);
// Mini-barra junto da seleção.
document.addEventListener('click',guard(async e=>{const b=e.target.closest&&e.target.closest('#selBar [data-sb]');if(!b)return;const a=b.dataset.sb;canvas.focus({preventScroll:true});
 if(a==='move')runCommand('MOVER');else if(a==='rot')runCommand('GIRAR');else if(a==='copy')runCommand('COPIAR');else if(a==='del'){if(selObjs().length)deleteSel()}else if(a==='props'){showProps();$('propPanel')?.scrollIntoView({block:'nearest'})}
 else if(a==='tex')await openTexDialog();else if(a==='name')await renameSel();else if(a==='edit')await dxfToArea();draw()}));

// ---------- caixas de chamada: linha (comprimento e direção) nas propriedades ----------
estender('showProps',_sp=>function(){_sp();const box=$('propPanel');const L=selObjs();if(!box||box.hidden||L.length!==1)return;const o=L[0];const li=leaderInfo(o);
 if(li){box.querySelector('h4')?.insertAdjacentHTML('beforebegin',`<table><tr><td title="Distância entre o ponto e o centro da caixa de chamada">Linha de chamada (m)</td><td><input type="number" step="0.1" min="0" data-leader="d" value="${li.d.toFixed(2)}"></td></tr><tr><td title="Direção da caixa a partir do ponto (0° = norte, 90° = leste)">Direção da caixa (°)</td><td><input type="number" step="1" data-leader="az" value="${li.az.toFixed(1)}"></td></tr></table><p class="muted">Arraste o losango amarelo no editor para mudar a posição da caixa (a linha aumenta ou diminui).</p>`)}
 if(o.key==='pavement_areas'){const t=o.o.texture;box.querySelector('h4')?.insertAdjacentHTML('beforebegin',`<p class="ppInfo">Textura: ${t?`própria (grão ${t.grao}, tom ${t.tom}, remendos ${t.remendos}, fissuras ${t.fissuras}, brilho ${t.brilho})`:'a do tipo'}</p><div class="row"><button type="button" data-ppact="tex">Trocar textura…</button></div>`)}},'caixas de chamada: linha (comprimento e direção) nas propriedades');
document.addEventListener('keydown',e=>{const el=e.target;if(!el.dataset||!el.dataset.leader||e.key!=='Enter')return;e.preventDefault();e.stopPropagation();const o=objOf(sel);if(!o)return;const li=leaderInfo(o),a=labelAnchor(o);
 const d=el.dataset.leader==='d'?Number(String(el.value).replace(',','.')):li.d,az=el.dataset.leader==='az'?Number(String(el.value).replace(',','.')):li.az;if(!isFinite(d)||d<0||!isFinite(az))return msg('Valor inválido.',true);
 checkpoint();const r=az*Math.PI/180;o.o.label={x:a.x+d*Math.sin(r),y:a.y+d*Math.cos(r)};changed(`Caixa de chamada a ${d.toFixed(2)} m, direção ${az.toFixed(1)}°.`);showProps();scheduleViewPreview()},true);
document.addEventListener('click',guard(async e=>{const b=e.target.closest&&e.target.closest('#propPanel [data-ppact="tex"]');if(b)await openTexDialog()}));

// ---------- áreas do desenho: propriedades, tornar editável, trocar nome/tipo ----------
function dxfKind(){return ['pavement','existing_pavement','shoulder'].includes(dxfSel?.role)?dxfSel.role:'pavement'}
function showDxfProps(){const box=$('propPanel');if(!box||!dxfSel)return;box.hidden=false;
 box.innerHTML=`<h3>Área do desenho</h3><p class="ppInfo">camada ${esc(dxfSel.layer)} · ${esc(RLABEL[dxfSel.role]||dxfSel.role||'sem tipo')} · ${dxfSel.area_m2.toLocaleString('pt-BR')} m² · perímetro ${dxfSel.perimeter_m.toLocaleString('pt-BR')} m · ${dxfSel.points.length} vértices</p>
 <div class="row"><button type="button" data-dx="tex" class="primary">Trocar textura…</button><button type="button" data-dx="name">Trocar nome…</button><button type="button" data-dx="edit">Tornar editável (grips)</button><button type="button" data-dx="close">Desmarcar</button></div>
 <p class="muted">O DXF não é alterado: a troca cria uma “área de pista” com estes vértices exatos, que vale por cima do desenho.</p>`}
document.addEventListener('click',guard(async e=>{const b=e.target.closest&&e.target.closest('#propPanel [data-dx]');if(!b)return;const a=b.dataset.dx;if(a==='tex')await openTexDialog();else if(a==='name')await renameSel();else if(a==='edit')await dxfToArea();else{dxfSel=null;$('propPanel').hidden=true;draw()}}));
function dxfToArea(extra={}){if(!dxfSel)return null;checkpoint();const n=M.pavement_areas.length+1;const a={id:uid(),name:extra.name||`${PAV_LABEL[dxfKind()]} ${n} (${dxfSel.layer})`.slice(0,80),kind:extra.kind||dxfKind(),points:dxfSel.points.map(P_),source:'picked',material:extra.material||'auto',enabled:true,texture:extra.texture||null};
 M.pavement_areas.push(a);dxfSel=null;sel={key:'pavement_areas',i:M.pavement_areas.length-1};selSet=[];changed(`“${a.name}” criada com ${a.points.length} vértices exatos do desenho. Gere a prévia para ver no vídeo.`);showProps();scheduleViewPreview();return a}
async function renameSel(){const L=selObjs();
 if(!L.length&&dxfSel){const v=await inputBox('Trocar nome','Nome da área (aparece na lista e nos registros):',`${PAV_LABEL[dxfKind()]} (${dxfSel.layer})`);if(v)dxfToArea({name:v.slice(0,80)});return}
 if(L.length!==1)return msg('Selecione um objeto para trocar o nome.',true);const o=L[0],k='name' in o.o?'name':'title' in o.o?'title':null;if(!k)return msg('Este objeto não tem nome.',true);
 const v=await inputBox('Trocar nome',`Novo nome — ${o.label}:`,o.o[k]||'');if(!v)return;checkpoint();o.o[k]=v.slice(0,80);changed(`Nome alterado para “${o.o[k]}”.`);showProps();scheduleViewPreview()}

// ---------- diálogo de textura (área selecionada, área do desenho ou o tipo inteiro) ----------
const SURF_OF=(kind,mat)=>mat==='rigido'?'concreto':{pavement:'pista_nova',existing_pavement:'pista_existente',shoulder:'acostamento'}[kind]||'pista_nova';
let texTarget=null;
function tdVals(){const o={};for(const k of ['grao','tom','remendos','fissuras','brilho'])o[k]=Number($('td_'+k).value);return o}
function tdPreview(){const kind=$('td_kind').value,mat=$('td_mat').value,v=tdVals();const surf=SURF_OF(kind,mat==='auto'?(cfg[{pavement:'pavement_material',existing_pavement:'existing_material',shoulder:'shoulder_material'}[kind]]||'flexivel'):mat);
 const g=(cfg.texture_params||{})[surf]||{};const scopeType=$('td_scope').value==='tipo';const p=scopeType?v:{grao:(g.grao??1)*v.grao,tom:(g.tom??1)*v.tom,remendos:(g.remendos??1)*v.remendos,fissuras:(g.fissuras??1)*v.fissuras,brilho:Math.max(-.3,Math.min(.3,(g.brilho??0)+v.brilho))};
 for(const k of Object.keys(v))$('tdv_'+k).textContent=k==='brilho'?v[k].toFixed(2):v[k].toFixed(2)+'×';$('td_img').src=`/api/texture_preview.png?surface=${surf}&p=${encodeURIComponent(JSON.stringify(p))}&m_px=0.02`;$('td_surf').textContent=TEX_LABEL[surf]||surf;return surf}
async function openTexDialog(){const L=selObjs();let base={kind:'pavement',material:'auto',texture:null,name:''};
 if(L.length&&L.every(o=>o.key==='pavement_areas')){texTarget={areas:L};base=L[0].o}else if(!L.length&&dxfSel){texTarget={dxf:dxfSel};base={kind:dxfKind(),material:'auto',texture:null}}else return msg('Selecione uma área de pista (clique sobre ela) ou uma área do desenho para trocar a textura.',true);
 $('td_kind').value=base.kind||'pavement';$('td_mat').value=base.material||'auto';const t=base.texture||{};for(const [k,d] of [['grao',1],['tom',1],['remendos',1],['fissuras',1],['brilho',0]])$('td_'+k).value=t[k]??d;
 $('td_scope').value='area';$('td_title').textContent=texTarget.dxf?`Trocar textura — área do desenho (camada ${dxfSel.layer})`:L.length>1?`Trocar textura — ${L.length} áreas`:`Trocar textura — ${base.name}`;tdPreview();$('texDlg').showModal()}
function texApply(){const kind=$('td_kind').value,material=$('td_mat').value,v=tdVals(),neutral=v.grao===1&&v.tom===1&&v.remendos===1&&v.fissuras===1&&v.brilho===0;
 if($('td_scope').value==='tipo'){const surf=tdPreview();cfg.texture_params={...(cfg.texture_params||{}),[surf]:v};scheduleSave();try{texUi&&texUi()}catch{}$('texDlg').close();msg(`Textura de “${TEX_LABEL[surf]}” alterada para todas as áreas deste tipo. Gere a prévia para ver.`);scheduleViewPreview();return}
 if(texTarget?.dxf){dxfSel=texTarget.dxf;dxfToArea({kind,material,texture:neutral?null:v})}
 else if(texTarget?.areas){checkpoint();for(const o of texTarget.areas){o.o.kind=kind;o.o.material=material;o.o.texture=neutral?null:v}changed(`Textura aplicada a ${texTarget.areas.length} área(s). Gere a prévia para ver no vídeo.`);showProps();scheduleViewPreview()}
 $('texDlg').close()}
document.addEventListener('input',e=>{if(e.target.closest&&e.target.closest('#texDlg'))tdPreview()});
document.addEventListener('change',e=>{if(e.target.closest&&e.target.closest('#texDlg'))tdPreview()});
$('td_ok')?.addEventListener('click',texApply);$('td_cancel')?.addEventListener('click',()=>$('texDlg').close());
$('td_reset')?.addEventListener('click',()=>{for(const [k,d] of [['grao',1],['tom',1],['remendos',1],['fissuras',1],['brilho',0]])$('td_'+k).value=d;tdPreview()});
$('texDlg')?.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.target.matches('select')){e.preventDefault();e.stopPropagation();texApply()}});

