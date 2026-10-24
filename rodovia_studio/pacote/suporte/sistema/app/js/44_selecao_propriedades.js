// =====================================================================================================
// 1.35: seleção mais precisa e propriedades que não perdem o que foi digitado.
//  • Tolerâncias em pixels da tela (escala do Windows 125 %/150 % incluída): DPR().
//  • Prioridade: ponto > linha > borda de área > interior de área (a menor área primeiro).
//  • Clique de novo no mesmo lugar alterna entre os objetos sobrepostos (como no CAD).
//  • Ao passar o mouse, o objeto que será selecionado fica realçado.
//  • Propriedades: o que foi digitado num campo vale ao sair dele (Windows); trocar uma lista (ex.: categoria)
//    grava antes os outros campos alterados — o nome digitado não some mais.
// =====================================================================================================
function DPR(){return Math.max(1,window.devicePixelRatio||1)}
function areaPx(P){let a=0;for(let i=0,j=P.length-1;i<P.length;j=i++)a+=(P[j][0]+P[i][0])*(P[j][1]-P[i][1]);return Math.abs(a/2)}
function dentro(P,x,y){let inside=false;for(let i=0,j=P.length-1;i<P.length;j=i++){const [xi,yi]=P[i],[xj,yj]=P[j];if(((yi>y)!==(yj>y))&&x<(xj-xi)*(y-yi)/(yj-yi)+xi)inside=!inside}return inside}
// Todos os objetos sob o cursor, do mais provável ao menos provável.
function hitObjects(c){const T=10*DPR(),out=[];
 for(const o of objList()){const P=o.grips.map(g=>W2C(gripGet(g)));let d=Infinity,score=Infinity;
  if(o.shape==='pt'){d=Math.min(...P.map(([x,y])=>Math.hypot(x-c.cx,y-c.cy)));score=d}
  else{for(let k=0;k+1<P.length;k++)d=Math.min(d,segDist(c.cx,c.cy,...P[k],...P[k+1]));
   if(o.shape==='area'&&P.length>2){d=Math.min(d,segDist(c.cx,c.cy,...P[P.length-1],...P[0]));score=d+2*DPR();
    if(d>T&&dentro(P,c.cx,c.cy)){d=T*.9;score=T+Math.min(T,Math.sqrt(areaPx(P))/40)}}
   else score=d+1*DPR()}
  if(d<=T)out.push({key:o.key,i:o.i,d,score})}
 return out.sort((a,b)=>a.score-b.score)}
let ultimaEscolha=null;
let escolhaEvento=null;
estender('hitObject',()=>function(c){const ev=window.event;if(ev&&escolhaEvento&&escolhaEvento.ev===ev)return escolhaEvento.r;   // mesma escolha para todos os que tratam este clique
 const L=hitObjects(c);if(!L.length)return null;
 if(ev&&ev.type==='pointerdown'&&ev.button===0&&!ev.shiftKey&&L.length>1){
  const u=ultimaEscolha,mesmo=u&&Math.hypot(u.cx-c.cx,u.cy-c.cy)<=5*DPR()&&u.chave===L.map(h=>h.key+h.i).join('|');
  const atual=sel&&L.findIndex(h=>h.key===sel.key&&h.i===sel.i);
  const k=mesmo&&atual>=0&&Date.now()-u.t<4000?(atual+1)%L.length:0;ultimaEscolha={cx:c.cx,cy:c.cy,chave:L.map(h=>h.key+h.i).join('|'),t:Date.now()};
  if(k>0||L.length>1)setTimeout(()=>msg(`${L.length} objetos neste ponto (${k+1} de ${L.length}). Clique de novo no mesmo lugar para alternar.`),0);
  escolhaEvento={ev,r:L[k]};return L[k]}
 return L[0]},'seleção precisa: prioridade e alternância entre objetos sobrepostos');
// Realce ao passar o mouse (pré-seleção).
let sobMouse=null,sobRaf=0;
canvas.addEventListener('pointermove',e=>{if(sobRaf)return;sobRaf=requestAnimationFrame(()=>{sobRaf=0;if(!ready()||tool!=='pan'||drag||cadCmd&&!cadCmd.proximo){if(sobMouse){sobMouse=null;draw()}return}
 const c=canvasPt(e);const h=hitObjects(c)[0]||null;const k=h&&h.key+':'+h.i,ka=sobMouse&&sobMouse.key+':'+sobMouse.i;if(k!==ka){sobMouse=h;draw()}})});
canvas.addEventListener('pointerleave',()=>{if(sobMouse){sobMouse=null;draw()}});
estender('draw',anterior=>function(){anterior();if(!sobMouse||!ready())return;if(sel&&sel.key===sobMouse.key&&sel.i===sobMouse.i)return;const o=objOf(sobMouse);if(!o)return;
 const P=o.grips.map(g=>W2C(gripGet(g)));ctx.save();ctx.strokeStyle='#ffd400';ctx.lineWidth=3*DPR();ctx.globalAlpha=.85;ctx.shadowColor='#000';ctx.shadowBlur=4;
 if(o.shape==='pt'){const [x,y]=P[0];ctx.beginPath();ctx.arc(x,y,11*DPR(),0,2*Math.PI);ctx.stroke()}
 else{ctx.beginPath();P.forEach(([x,y],k)=>k?ctx.lineTo(x,y):ctx.moveTo(x,y));if(o.shape==='area')ctx.closePath();ctx.stroke()}
 const lab=o.label+(o.o.name?` · ${o.o.name}`:'');ctx.font=`${12*DPR()}px "Segoe UI",system-ui`;const [x,y]=P[0];ctx.shadowBlur=0;ctx.globalAlpha=1;
 const tw=ctx.measureText(lab).width;ctx.fillStyle='#fffbe6';ctx.fillRect(x+12*DPR(),y+10*DPR(),tw+10*DPR(),18*DPR());ctx.strokeStyle='#767676';ctx.lineWidth=1;ctx.strokeRect(x+12*DPR(),y+10*DPR(),tw+10*DPR(),18*DPR());
 ctx.fillStyle='#1b1b1b';ctx.fillText(lab,x+17*DPR(),y+23*DPR());ctx.restore()},'seleção: realce ao passar o mouse');

// ---------- propriedades ----------
// Grava (sem redesenhar o painel) os campos de texto/número alterados, exceto o informado.
function propPendentes(exceto){const o=objOf(sel);if(!o)return 0;let n=0;
 document.querySelectorAll('#propPanel input[data-pp]:not([type=checkbox])').forEach(el=>{if(el===exceto)return;const k=el.dataset.pp,old=o.o[k];if(!(k in o.o))return;
  let v=el.type==='number'?Number(String(el.value).replace(',','.')):el.value;if(el.type==='number'&&String(el.value).trim()==='')return;
  if(typeof old==='number'&&!isFinite(v))return;if(['name','title','description'].includes(k)&&typeof old==='string'&&old.trim()!==''&&String(v).trim()==='')return;
  if(String(old??'')!==String(v)){o.o[k]=v;n++}});return n}
estender('commitProp',anterior=>function(el){if(!el||el.dataset.grip!==undefined||!objOf(sel))return anterior(el);
 const antes=JSON.stringify(M),n0=undoStack.length,n=propPendentes(el);const r=anterior(el);
 // Os campos pendentes entram no mesmo passo de desfazer da alteração atual.
 if(n){if(undoStack.length===n0+1)undoStack[n0]=antes;else if(undoStack.length===n0){undoStack.push(antes);updateUndo();changed('Propriedades alteradas.');showProps()}}
 return r},'propriedades: o nome digitado não some ao trocar outra opção');
// Sair de um campo alterado grava o valor (como no Windows); Esc continua desfazendo a digitação.
document.addEventListener('focusout',e=>{const el=e.target;if(!el.matches||!el.matches('#propPanel input[data-pp]:not([type=checkbox]),#propPanel input[data-grip]'))return;
 setTimeout(()=>{if(!el.isConnected)return;const o=objOf(sel);if(!o)return;
  if(el.dataset.grip!==undefined){const p=gripGet(o.grips[Number(el.dataset.grip)]);if(Math.abs(Number(String(el.value).replace(',','.'))-p[el.dataset.ax])>1e-9)commitProp(el);return}
  const old=o.o[el.dataset.pp];if(String(old??'')!==String(el.type==='number'?Number(String(el.value).replace(',','.')):el.value))commitProp(el)},0)});
// Clique de novo sobre o objeto já selecionado (que agora é um grip): se houver outros objetos no mesmo ponto,
// alterna para o próximo em vez de arrastar o grip.
window.addEventListener('pointerdown',e=>{if(e.target!==canvas||e.button!==0||e.shiftKey||e.ctrlKey||tool!=='pan'||cadCmd||!ready()||!sel)return;const c=canvasPt(e);const u=ultimaEscolha;
 if(!u||Math.hypot(u.cx-c.cx,u.cy-c.cy)>5*DPR()||Date.now()-u.t>4000)return;const L=hitObjects(c);if(L.length<2||u.chave!==L.map(h=>h.key+h.i).join('|'))return;
 const atual=L.findIndex(h=>h.key===sel.key&&h.i===sel.i);if(atual<0)return;const k=(atual+1)%L.length;e.stopImmediatePropagation();e.preventDefault();
 sel={key:L[k].key,i:L[k].i};selSet=[];dxfSel=null;selLink=null;showProps();draw();u.t=Date.now();
 const o=objOf(sel);msg(`${L.length} objetos neste ponto (${k+1} de ${L.length}): ${o?.label||''}${o?.o?.name?' “'+o.o.name+'”':''}. Clique de novo para alternar.`)},true);
