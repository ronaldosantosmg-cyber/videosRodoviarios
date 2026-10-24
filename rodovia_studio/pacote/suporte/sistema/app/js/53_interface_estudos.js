// 1.42.1: menus em cascata, comandos encaixados e diagnóstico técnico do editor.
(()=>{
'use strict';
const state={menus:[],top:-1,focus:null};
const study={stale:false,editing:false};
window.RodoviaFlowStudy=study;
const call=f=>{try{const r=f?.();if(r?.catch)r.catch(e=>msg(e.message,true))}catch(e){msg(e.message,true)}};
const leaf=(t,f,k)=>({t,f,k});
const toolItem=id=>{const t=TOOLS.find(t=>Array.isArray(t)&&t[0]===id);return t?leaf(toolLabel(t).replace(/^[^\p{L}\p{N}]+/u,''),()=>setTool(id)):null};
function modelGroups(){
 const known=new Set();
 const groups=[
  ['Traçado e referências',['align','route','chain','chainend','pair','imgadjust']],
  ['Pavimento e superfícies',['pavarea','pavpick','shoulder','hatch','cleanarea','exvert','exlasso','exedit']],
  ['Tráfego e ligações',['flowadd','flowrev','flowoff','linkforce','noconn','noconnarea','dir','arrowrot','lanes','lanerange','block','crossok','crossno']],
  ['Sinalização e estruturas',['sign','crosswalk','gantry','oae','oaepoly','access']],
  ['Apresentação e ambiente',['highlight','poi','city','advzone','veg','pedpath']]
 ].map(([t,ids])=>({t,sub:ids.map(id=>{known.add(id);return toolItem(id)}).filter(Boolean)}));
 const rest=TOOLS.filter(t=>Array.isArray(t)&&!known.has(t[0])&&!['pan','move','mmove','inspect','grip','rot'].includes(t[0])).map(t=>toolItem(t[0]));
 if(rest.length)groups.push({t:'Outras ferramentas',sub:rest});
 return groups.filter(g=>g.sub.length);
}
function menuDefinitions(){
 const project=(MENUBAR[0]?.[1]||[]).map(i=>i?leaf(i[0],i.at(-1),typeof i[1]==='string'?i[1]:null):{sep:true});
 return [{t:'Arquivo',sub:project},...RIBBON.map(([t,groups])=>({t:t==='Layers'?'Camadas':t,sub:t==='Modelar'?modelGroups():(groups||[]).map(([label,items])=>({t:label,sub:items.map(i=>leaf(i[0].replace(/layers/ig,'camadas'),i[2]))}))}))];
}
function closeMenus(restore=false){
 state.menus.forEach(m=>m.el.remove());state.menus=[];state.top=-1;
 document.querySelectorAll('[data-rs-menu]').forEach(b=>{b.classList.remove('on');b.setAttribute('aria-expanded','false')});
 if(restore)state.focus?.focus();
}
function trimMenus(depth){while(state.menus.length>depth)state.menus.pop().el.remove()}
function invoke(item){if(item.dis)return;closeMenus();call(item.f)}
function popup(items,anchor,depth=0,point=null){
 trimMenus(depth);
 const el=document.createElement('div');el.className='rsCascade';el.setAttribute('role','menu');el.setAttribute('aria-label',anchor?.textContent?.trim()||'Menu de contexto');
 const rows=[];
 for(const item of items){
  if(item.sep){const d=document.createElement('div');d.className='rsSeparator';d.setAttribute('role','separator');el.appendChild(d);continue}
  if(item.hd){const d=document.createElement('div');d.className='rsMenuHeading';d.textContent=item.hd;el.appendChild(d);continue}
  const b=document.createElement('button');b.type='button';b.setAttribute('role','menuitem');b.tabIndex=-1;b.disabled=!!item.dis;b.setAttribute('aria-label',item.t);
  b.innerHTML=`<span class="rsMenuIcon">${typeof icoPara==='function'?icoPara(item.t):''}</span><span>${esc(item.t)}</span><span class="rsMenuKey">${esc(item.k||'')}${item.sub?' ›':''}</span>`;
  if(item.sub){b.setAttribute('aria-haspopup','menu');b.setAttribute('aria-expanded','false')}
  b.title=item.h||item.t;
  const open=()=>{if(!item.dis&&item.sub){b.setAttribute('aria-expanded','true');popup(item.sub,b,depth+1)}};
  b.addEventListener('pointerenter',()=>{rows.forEach(r=>r.b.setAttribute('aria-expanded','false'));trimMenus(depth+1);if(item.sub)open()});
  b.onclick=e=>{e.stopPropagation();item.sub?open():invoke(item)};
  b.onkeydown=e=>{
   const available=rows.filter(r=>!r.b.disabled);let index=available.findIndex(r=>r.b===b);
   if(['ArrowDown','ArrowUp','Home','End','ArrowRight','ArrowLeft','Escape','Enter',' '].includes(e.key)){e.preventDefault();e.stopPropagation()}
   if(e.key==='ArrowDown'||e.key==='ArrowUp'){index=(index+(e.key==='ArrowDown'?1:-1)+available.length)%available.length;available[index]?.b.focus()}
   else if(e.key==='Home')available[0]?.b.focus();else if(e.key==='End')available.at(-1)?.b.focus();
   else if(e.key==='ArrowRight'&&item.sub){open();state.menus.at(-1)?.rows.find(r=>!r.b.disabled)?.b.focus()}
   else if(e.key==='ArrowLeft'||e.key==='Escape'){if(depth){trimMenus(depth);anchor?.setAttribute('aria-expanded','false');anchor?.focus()}else closeMenus(true)}
   else if(e.key==='Enter'||e.key===' '){if(item.sub){open();state.menus.at(-1)?.rows.find(r=>!r.b.disabled)?.b.focus()}else invoke(item)}
  };
  el.appendChild(b);rows.push({b,item});
 }
 document.body.appendChild(el);state.menus.push({el,rows});
 const r=anchor?.getBoundingClientRect(),box=el.getBoundingClientRect();
 let x=point?.x??(depth?anchor.closest('.rsCascade').getBoundingClientRect().right-2:r.left),y=point?.y??(depth?r.top:r.bottom);
 if(depth&&x+box.width>innerWidth-6)x=r.left-box.width+2;
 el.style.left=Math.max(4,Math.min(x,innerWidth-box.width-4))+'px';el.style.top=Math.max(4,Math.min(y,innerHeight-box.height-4))+'px';
 return el;
}
function topMenu(index,button){
 const definitions=menuDefinitions();
 if(state.top===index){closeMenus(true);return}
 closeMenus();state.focus=button;state.top=index;
 button.classList.add('on');button.setAttribute('aria-expanded','true');popup(definitions[index].sub,button);
}
function buildMenus(){
 const old=$('menuBar');if(!old)return;const bar=old.cloneNode(false);old.replaceWith(bar);
 bar.setAttribute('role','menubar');bar.setAttribute('aria-label','Menu principal');bar.classList.add('rsMenuBar');
 menuDefinitions().forEach((menu,i)=>{
  const b=document.createElement('button');b.type='button';b.className='mb';b.textContent=menu.t;b.dataset.rsMenu=i;b.setAttribute('role','menuitem');b.setAttribute('aria-haspopup','menu');b.setAttribute('aria-expanded','false');
  b.onclick=()=>topMenu(i,b);b.onpointerenter=()=>{if(state.top>=0&&state.top!==i)topMenu(i,b)};
  b.onkeydown=e=>{const buttons=[...bar.querySelectorAll('[data-rs-menu]')];
   if(['ArrowLeft','ArrowRight','ArrowDown','Enter',' ','Escape'].includes(e.key)){e.preventDefault();e.stopPropagation()}
   if(e.key==='ArrowLeft'||e.key==='ArrowRight'){const n=(i+(e.key==='ArrowRight'?1:-1)+buttons.length)%buttons.length;buttons[n].focus();if(state.top>=0)topMenu(n,buttons[n])}
   else if(['ArrowDown','Enter',' '].includes(e.key)){if(state.top!==i)topMenu(i,b);state.menus[0]?.rows.find(r=>!r.b.disabled)?.b.focus()}
   else if(e.key==='Escape')closeMenus(true);
  };bar.appendChild(b);
 });
}
// Um único renderizador dos menus substitui o ribbon; o catálogo de ações permanece o mesmo.
buildRibbon=buildMenus;
function contextItems(w){
 if(draft||cadCmd)return [{hd:'Comando em andamento'},leaf('Concluir',()=>draft?finishDraft():runCommand(''),'Enter'),leaf('Desfazer último ponto',()=>canvas.dispatchEvent(new KeyboardEvent('keydown',{key:'Backspace',bubbles:true})),'Backspace'),leaf('Cancelar',()=>escapeCommand(),'Esc')];
 const original=ctxItems(w); // mantém as ações específicas de fluxo, camada e seleção.
 if(selSeg||selLink)return original;
 const selected=allSelected().length||dxfSel;
 if(selected)return original.filter(i=>i.t!=='Inserir'&&i.t!=='Sessão');
 return [{t:'Modelar',sub:modelGroups()},...original.filter(i=>!i.hd&&['Desfazer','Refazer','Enquadrar tudo','Centralizar aqui','Regenerar tela','Comandos e ajuda'].includes(i.t))];
}
openCanvasMenu=function(x,y,w){closeMenu();closeMenus();state.focus=canvas;popup(contextItems(w),null,0,{x,y})};
const flowTools=new Set(['flowadd','flowrev','flowoff','linkforce','noconn','noconnarea','route','routesec','dir','arrowrot','lanes','lanerange','block','crossok','crossno']);
function flowEditing(){return study.editing||flowTools.has(tool)}
study.isEditing=flowEditing;
function quickTools(rail){
 if($('rsQuickTools'))return;
 const bar=document.createElement('div');bar.id='rsQuickTools';bar.setAttribute('role','toolbar');bar.setAttribute('aria-label','Acesso rápido');rail.prepend(bar);
 const groups=[
  ['Projeto',[
   ['new','Novo',()=>$('new')?.click()],['open','Abrir',()=>openProjectDialog()],['save','Salvar',()=>$('saveProject')?.click()]]],
  ['Editar',[
   ['properties','Propriedades',()=>psOpenHub('props')]]],
  ['Vista',[
   ['select','Selecionar',()=>setTool('pan')],['fit','Enquadrar',()=>fitView()]]],
  ['Fluxos',[
   ['flows','Editar fluxos',()=>{study.editing=!study.editing;vecOn.flows=true;if(!study.editing&&flowTools.has(tool))setTool('pan');sync();draw()}],
   ['route','Nova rota',()=>setTool('route')],['update-flows','Atualizar fluxos',()=>$('updFlows')?.click()]]],
  ['Vídeo',[
   ['preview','Prévia',()=>$('openAtTime')?.click()],['render','Gerar vídeo',()=>typeof gerarVideo==='function'?gerarVideo():$('render')?.click()]]]
 ];
 for(const [label,items] of groups){
  const group=document.createElement('div');group.className='rsQuickGroup';group.setAttribute('role','group');group.setAttribute('aria-label',label);
  for(const [id,text,fn] of items){const btn=document.createElement('button');btn.type='button';btn.dataset.rsQuick=id;btn.title=text;btn.setAttribute('aria-label',text);btn.innerHTML=`${icoPara(text)}<span>${esc(text)}</span>`;btn.onclick=()=>call(fn);group.appendChild(btn)}
  if(label==='Editar')for(const id of ['redo','undo']){const button=$(id);if(button)group.prepend(button)}
  bar.appendChild(group);
 }
}
function dockCommands(){
 const title=document.querySelector('.dwTitleBar');if(title)$('menuBar').before(title);
 let rail=$('rsCommandRail');if(!rail){rail=document.createElement('div');rail.id='rsCommandRail';rail.setAttribute('aria-label','Acesso rápido e opções da ferramenta');$('menuBar').after(rail)}
 quickTools(rail);
 for(const el of [$('toolOptions'),$('selBar')])if(el&&el.parentNode!==rail)rail.appendChild(el);
 const tb=$('toolbar');if(tb)tb.hidden=true;
 let footer=$('rsStudyFooter');if(!footer){footer=document.createElement('div');footer.id='rsStudyFooter';footer.setAttribute('aria-label','Comando, coordenadas e diagnóstico de fluxos');$('bottomBar').before(footer)}
 if(!$('rsActiveTool')){const head=document.createElement('div');head.id='rsActiveTool';head.setAttribute('role','status');footer.appendChild(head)}
 for(const el of [document.querySelector('.dwCursor'),$('dwCommandDrawer')])if(el&&el.parentNode!==footer)footer.appendChild(el);
 if(!$('rsFlowLegend')){const legend=document.createElement('div');legend.id='rsFlowLegend';legend.innerHTML='<span class="flow-ok">● Fluxo OK</span><span class="flow-problem">● Problema</span><span class="flow-adjustment">● Ajuste necessário</span><span>Estudo técnico · não aparece no vídeo</span>';footer.appendChild(legend)}
}
function foregroundFlows(){
 if(!ready()||!flowEditing()||vecOn.flows===false)return;
 ctx.save();ctx.setTransform(1,0,0,1,0,0);ctx.globalAlpha=1;ctx.lineJoin='round';ctx.lineCap='round';
 const line=(points,status,forward=true,both=false,dashed=false)=>{
  const pts=(points||[]).map(p=>Array.isArray(p)?P(p):p).filter(p=>Number.isFinite(p.x)&&Number.isFinite(p.y));if(pts.length<2)return;
  const color=flowStudyColor(status);poly(pts);ctx.setLineDash([]);ctx.strokeStyle='#081623';ctx.lineWidth=7;ctx.stroke();
  ctx.setLineDash(dashed?[7,4]:[]);ctx.strokeStyle=color;ctx.lineWidth=4;ctx.stroke();ctx.setLineDash([]);arrowsAlong(pts,forward,both,color,85);
 };
 for(const seg of editor?.segments||[])line(seg.points,seg,seg.forward,seg.both,seg.disabled);
 for(const route of M.traffic_paths||[])line(route.points,route.enabled===false?{disabled:true}:(editor?.segments||[]).find(s=>s.source===route.name),true,false,route.enabled===false);
 for(const route of M.route_alignments||[]){
  const calculated=(editor?.segments||[]).filter(s=>s.route===route.id);const status=route.enabled===false?{disabled:true}:calculated.find(s=>s.technical_status==='problem')||calculated.find(s=>s.technical_status==='adjustment')||calculated[0];
  line(route.points,status,true,false,true);
 }
 for(const lane of routeLanes||[]){const route=M.route_alignments?.[lane.route];const calculated=(editor?.segments||[]).find(s=>s.route===route?.id);line(lane.points,lane.enabled===false?{disabled:true}:calculated,true,false)}
 for(const link of editor?.connections||[])line(link.p,{technical_status:'ok'},true,false,!!link.forced);
 for(const link of editor?.denied||[])line(link.p,{disabled:true},true,false,true);
 // Preserva os grips de uma rota selecionada acima do próprio realce.
 if(sel&&['route_alignments','traffic_paths'].includes(sel.key)){
  const obj=objOf(sel);for(const grip of obj?.grips||[]){const [x,y]=W2C(gripGet(grip));ctx.fillStyle='#fff';ctx.strokeStyle='#1f2937';ctx.lineWidth=1.5;ctx.fillRect(x-4,y-4,8,8);ctx.strokeRect(x-4,y-4,8,8)}
 }
 ctx.restore();
}
function sync(){
 const quick=$('rsQuickTools')?.querySelector('[data-rs-quick="flows"]');if(quick){quick.setAttribute('aria-pressed',String(flowEditing()));quick.classList.toggle('on',flowEditing())}
 const active=TOOLS.find(t=>Array.isArray(t)&&t[0]===tool);
 if($('rsActiveTool'))$('rsActiveTool').textContent='Comando: '+(active?toolLabel(active).replace(/^[^\p{L}\p{N}]+/u,''):'Selecionar')+' · Enter conclui · Esc cancela';
 const b=document.querySelector('[data-pshub="props"]');if(b){b.setAttribute('aria-expanded',String(!dockState.recolhida&&dockState.aba==='prop'));b.classList.toggle('on',!dockState.recolhida&&dockState.aba==='prop')}
 const legend=$('rsFlowLegend');if(legend)legend.hidden=vecOn.flows===false;
}
function init(){
 document.body.classList.add('studio142');buildMenus();dockCommands();sync();
 const oldPlace=placeSelBar;placeSelBar=function(){oldPlace();const b=$('selBar');if(b){b.style.left='';b.style.top=''}};
 const oldTool=setTool;setTool=function(...args){if(flowTools.has(args[0]))vecOn.flows=true;const r=oldTool(...args);sync();return r};
 const oldDraw=draw;draw=function(...args){const r=oldDraw(...args);foregroundFlows();return r};
 const oldDock=aplicarDock;aplicarDock=function(...args){const r=oldDock(...args);sync();return r};
 const oldChanged=changed;changed=function(...args){study.stale=true;const r=oldChanged(...args);sync();return r};
 const oldLoad=load;load=async function(...args){const r=await oldLoad(...args);study.stale=!!(task||savePending);draw();sync();return r};
 const oldShow=showSegProps;showSegProps=function(...args){const r=oldShow(...args);const seg=segById(selSeg?.id);if(seg&&$('propPanel')&&!$('propPanel').hidden){const p=document.createElement('p');p.className='rsFlowDiagnostic';p.textContent=study.stale?'Ajuste necessário: recalcule os fluxos após a alteração.':seg.technical_message||'Diagnóstico pendente: atualize os fluxos.';$('propPanel').appendChild(p)}return r};
 document.addEventListener('pointerdown',e=>{if(!e.target.closest('.rsCascade,#menuBar'))closeMenus()},true);
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&state.menus.length&&!e.target.closest('.rsCascade')){e.preventDefault();closeMenus(true)}},true);
 window.addEventListener('resize',()=>closeMenus());
 // API de leitura para conferência e testes de interação, sem dados no modelo do vídeo.
 window.RodoviaMenus=Object.freeze({close:closeMenus,modelGroups,contextItems});
}
queueMicrotask(init);
})();
