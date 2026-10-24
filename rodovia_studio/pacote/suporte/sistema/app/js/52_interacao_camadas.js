// =====================================================================================================
// Rodovia Studio 1.40.3 — Interação, pilha visual e estabilidade de viewport
// • Preserva centro/escala/seleção e o ponto sob o cursor em reload, resize e regeneração.
// • Alt+clique e Tab percorrem objetos sobrepostos; tolerância adaptativa sem seleção grosseira.
// • Expõe uma API pequena para o Gerenciador de Ordem Visual.
// =====================================================================================================
(()=>{
'use strict';
const $id=id=>document.getElementById(id);
const S={client:null,inside:false,lastHits:[],hitIndex:-1,restoring:false};
function safeObj(s){try{return s&&typeof objOf==='function'&&objOf(s)?{key:s.key,i:s.i}:null}catch{return null}}
function capture(){
  const st={pid:typeof pid==='string'?pid:null,sel:safeObj(typeof sel!=='undefined'?sel:null),selSet:[],center:null,ppm:null,pointer:null};
  try{if(Array.isArray(selSet))st.selSet=selSet.map(safeObj).filter(Boolean)}catch{}
  try{if(typeof ready==='function'&&ready()&&canvas){st.center=C2W(canvas.width/2,canvas.height/2);st.ppm=pxPerM()}}
  catch{}
  try{if(S.inside&&S.client&&canvas&&typeof canvasPt==='function'){
    const r=canvas.getBoundingClientRect();const ev={clientX:S.client.x,clientY:S.client.y};
    const c=canvasPt(ev);if(c?.w)st.pointer={world:{x:c.w.x,y:c.w.y},nx:(S.client.x-r.left)/Math.max(1,r.width),ny:(S.client.y-r.top)/Math.max(1,r.height)};
  }}catch{}
  return st;
}
function restore(st,{selection=true,anchor=true}={}){
  if(!st||S.restoring)return;S.restoring=true;
  try{
    if(typeof ready==='function'&&ready()&&canvas&&st.ppm&&st.center){
      const p=worldToImg(st.center);view.s=st.ppm*mpp();view.ox=canvas.width/2-p[0]*view.s;view.oy=canvas.height/2-p[1]*view.s;
      if(anchor&&st.pointer?.world&&S.inside){
        const r=canvas.getBoundingClientRect();const cx=st.pointer.nx*canvas.width,cy=st.pointer.ny*canvas.height;
        const ip=worldToImg(st.pointer.world);view.ox=cx-ip[0]*view.s;view.oy=cy-ip[1]*view.s;
      }
    }
    if(selection){
      const ok=s=>safeObj(s);
      if(st.sel&&ok(st.sel))sel={...st.sel};
      else if(typeof sel!=='undefined')sel=null;
      if(typeof selSet!=='undefined')selSet=(st.selSet||[]).filter(ok).map(x=>({...x}));
      try{showProps()}catch{}
    }
    try{draw()}catch{}
  }finally{S.restoring=false}
}
function trackPointer(){
  if(!window.canvas)return;
  canvas.addEventListener('pointerenter',e=>{S.inside=true;S.client={x:e.clientX,y:e.clientY}},{passive:true});
  canvas.addEventListener('pointermove',e=>{S.inside=true;S.client={x:e.clientX,y:e.clientY}},{passive:true});
  canvas.addEventListener('pointerleave',()=>{S.inside=false},{passive:true});
}
function wrapAsyncReload(){
  if(typeof load==='function'&&!load.__rs1403){const prev=load;const fn=async function(id){const st=capture(),same=st.pid&&String(st.pid)===String(id);const r=await prev(id);if(same)requestAnimationFrame(()=>restore(st));return r};fn.__rs1403=true;load=fn}
  if(typeof regenScreen==='function'&&!regenScreen.__rs1403){const prev=regenScreen;const fn=function(...a){const st=capture();const r=prev(...a);requestAnimationFrame(()=>restore(st,{selection:true,anchor:true}));return r};fn.__rs1403=true;regenScreen=fn}
  if(typeof resizeCanvas==='function'&&!resizeCanvas.__rs1403){const prev=resizeCanvas;const fn=function(...a){const st=capture();const r=prev(...a);requestAnimationFrame(()=>restore(st,{selection:true,anchor:true}));return r};fn.__rs1403=true;resizeCanvas=fn}
}
function hitListAtEvent(e){try{return typeof hitObjects==='function'?hitObjects(canvasPt(e)):[]}catch{return []}}
function chooseHit(h,why='Selecionado'){
  if(!h)return false;
  try{sel={key:h.key,i:h.i};selSet=[];if(typeof dxfSel!=='undefined')dxfSel=null;if(typeof selLink!=='undefined')selLink=null;if(typeof selSeg!=='undefined')selSeg=null;showProps();draw();const o=objOf(sel);msg(`${why}: ${o?.label||'objeto'}${o?.o?.name?' “'+o.o.name+'”':''}.`);return true}catch{return false}
}
function installOverlapSelection(){
  if(!window.canvas)return;
  canvas.addEventListener('pointerdown',e=>{
    if(e.button!==0||!e.altKey||e.shiftKey||typeof tool==='undefined'||tool!=='pan'||typeof ready!=='function'||!ready())return;
    const L=hitListAtEvent(e);if(L.length<2)return;
    e.preventDefault();e.stopImmediatePropagation();
    const cur=typeof sel!=='undefined'&&sel?L.findIndex(h=>h.key===sel.key&&h.i===sel.i):-1;const k=(cur+1+L.length)%L.length;
    S.lastHits=L;S.hitIndex=k;chooseHit(L[k],`Objeto abaixo (${k+1}/${L.length})`);
  },true);
  document.addEventListener('keydown',e=>{
    if(e.key!=='Tab'||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey||!S.inside||!S.client)return;
    if(e.target?.matches?.('input,textarea,select,[contenteditable=true]'))return;
    try{const L=hitListAtEvent({clientX:S.client.x,clientY:S.client.y});if(L.length<2)return;e.preventDefault();const cur=sel?L.findIndex(h=>h.key===sel.key&&h.i===sel.i):-1;const k=(cur+1+L.length)%L.length;S.lastHits=L;S.hitIndex=k;chooseHit(L[k],`Sobreposição (${k+1}/${L.length})`)}catch{}
  },true);
}
function installSelectionPersistence(){
  // Seleção só é limpa por Esc/Desmarcar/apagar; terminar uma edição preserva o contexto do usuário.
  try{window.RodoviaSelectionPolicy=Object.freeze({preserveAfterCommand:true,overlap:'Alt+clique ou Tab'})}catch{}
}
function init(){trackPointer();wrapAsyncReload();installOverlapSelection();installSelectionPersistence();
  window.addEventListener('rodovia:workspace-resize',()=>{const st=capture();requestAnimationFrame(()=>restore(st,{selection:true,anchor:true}))});
  window.RodoviaViewport=Object.freeze({capture,restore});
}
queueMicrotask(init);
})();
