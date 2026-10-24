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
function quickPopup(id,items){closeMenus();const anchor=document.querySelector(`[data-rs-quick="${id}"]`);state.focus=anchor;popup(items,anchor)}
function zoomStep(factor){if(!ready())return msg('Analise ou abra um projeto antes de ajustar o zoom.');const r=canvas.getBoundingClientRect();canvas.dispatchEvent(new WheelEvent('wheel',{clientX:r.left+r.width/2,clientY:r.top+r.height/2,deltaY:-Math.log(factor)/.0015,cancelable:true}))}
function allToolGroups(){let g=0;const groups=[{t:TOOL_GROUPS[0],sub:[]}];for(const t of TOOLS){if(t==='|'){g++;groups.push({t:TOOL_GROUPS[g]||'Outras ferramentas',sub:[]})}else groups.at(-1).sub.push(toolItem(t[0]))}return groups.filter(g=>g.sub.length)}
function registerControlTool(){
 if(FERRAMENTAS.insertcontrol)return;
 ferramenta('insertcontrol',{rotulo:'Inserir vértice',dica:'Selecione uma linha ou área editável e clique no trecho onde inserir um ponto de controle. Esc encerra.',clique(w){
  const obj=objOf(sel);const points=Array.isArray(obj?.o)?obj.o:obj?.o?.points||obj?.o?.polygon;
  if(!obj||!Array.isArray(points)||points.length<2)return msg('Selecione uma rota, alinhamento ou área editável antes de inserir vértices.',true);
  if(!w||!Number.isFinite(w.x)||!Number.isFinite(w.y)||points.length>=20000)return msg('Ponto inválido ou limite de vértices atingido.',true);
  const closed=obj.shape==='area';let best=null;
  for(let i=0;i<points.length-(closed?0:1);i++){
   const a=points[i],b=points[(i+1)%points.length],dx=b.x-a.x,dy=b.y-a.y,D=dx*dx+dy*dy;if(D<1e-10)continue;
   const t=Math.max(0,Math.min(1,((w.x-a.x)*dx+(w.y-a.y)*dy)/D));const q={x:a.x+t*dx,y:a.y+t*dy};const dist=Math.hypot(w.x-q.x,w.y-q.y);
   if(!best||dist<best.dist)best={i,q,dist};
  }
  if(!best||best.dist*pxPerM()>12)return msg('Clique sobre um trecho da geometria selecionada.',true);
  if(points.some(p=>Math.hypot(p.x-best.q.x,p.y-best.q.y)<.01))return msg('Já existe um vértice nesse ponto.',true);
  checkpoint();points.splice(best.i+1,0,best.q);axisCache=null;afterGeomEdit(obj);changed('Vértice inserido. Arraste o grip para ajustar o traçado.');showProps();draw();
 }});
 if(!COMANDOS.has('REDRAW'))comando(['REDRAW'],()=>regenScreen(),'Redesenha a tela, preservando vista e seleção');
}
function quickTools(rail){
 if($('rsQuickTools'))return;
 const bar=document.createElement('div');bar.id='rsQuickTools';bar.setAttribute('role','toolbar');bar.setAttribute('aria-label','Acesso rápido');rail.prepend(bar);
 const groups=[
  ['Projeto',[
   ['new','Novo',()=>$('new')?.click()],['open','Abrir',()=>openProjectDialog()],['save','Salvar',()=>$('saveProject')?.click()]]],
  ['Editar',[
   ['properties','Propriedades',()=>psOpenHub('props')],
   ['modify','Modificar ▾',()=>quickPopup('modify',['MOVER','GIRAR','COPIAR','ESCALA','ESPELHAR','OFFSET'].map(c=>leaf(({MOVER:'Mover',GIRAR:'Girar',COPIAR:'Copiar',ESCALA:'Escala',ESPELHAR:'Espelhar',OFFSET:'Paralela'})[c],()=>runCommand(c))))],
   ['points','Pontos ▾',()=>quickPopup('points',[leaf('Mover ponto / grip',()=>setTool('move')),leaf('Inserir vértice',()=>setTool('insertcontrol')),leaf('Editar vértices de área',()=>setTool('exedit')),leaf('Par de controle DXF × imagem',()=>setTool('pair')),leaf('Inspecionar coordenadas',()=>setTool('inspect'))])]]],
  ['Vista',[
   ['select','Pan / selecionar',()=>setTool('pan')],['zoom-in','Zoom +',()=>zoomStep(1.25)],['zoom-out','Zoom −',()=>zoomStep(.8)],['fit','Enquadrar',()=>fitView()],['redraw','Redesenhar',()=>regenScreen()]]],
  ['Fluxos',[
   ['flows','Editar fluxos',()=>{study.editing=!study.editing;vecOn.flows=true;if(!study.editing&&flowTools.has(tool))setTool('pan');sync();draw()}],
   ['route','Nova rota',()=>setTool('route')],['update-flows','Atualizar fluxos',()=>$('updFlows')?.click()]]],
  ['Vídeo',[
   ['preview','Prévia',()=>$('openAtTime')?.click()],['render','Gerar vídeo',()=>typeof gerarVideo==='function'?gerarVideo():$('render')?.click()]]],
  ['Ferramentas',[['all-tools','Ferramentas ▾',()=>quickPopup('all-tools',allToolGroups())]]]
 ];
 for(const [label,items] of groups){
  const group=document.createElement('div');group.className='rsQuickGroup';group.setAttribute('role','group');group.setAttribute('aria-label',label);
  for(const [id,text,fn] of items){const btn=document.createElement('button');btn.type='button';btn.dataset.rsQuick=id;btn.title=text;btn.setAttribute('aria-label',text);btn.innerHTML=`${icoPara(text)}<span>${esc(text)}</span>`;btn.onclick=()=>call(fn);group.appendChild(btn)}
  if(label==='Editar')for(const id of ['redo','undo']){const button=$(id);if(button)group.prepend(button)}
  if(label==='Fluxos'){const control=$('min_route_segment_m')?.closest('label');if(control){control.classList.add('rsFlowLimit');group.appendChild(control)}}
  bar.appendChild(group);
 }
}
// Acesso visível às ferramentas, separado do menu completo em cascata.
function commandRibbon(rail){
 if($('rsToolRibbon'))return;
 const ribbon=document.createElement('div');ribbon.id='rsToolRibbon';ribbon.setAttribute('aria-label','Ferramentas de edição');
 const tabs=document.createElement('div');tabs.id='rsToolTabs';tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label','Grupos de comandos');ribbon.appendChild(tabs);
 const groups=[{label:'Todas',tools:[],commands:[]},{label:'Edição',tools:['move','insertcontrol','exedit','inspect'],commands:['MOVER','GIRAR','COPIAR','ESCALA','ESPELHAR','OFFSET','APAGAR','DIST']}];
 let g=0;for(const t of TOOLS){if(t==='|'){g++;continue}let group=groups[g+2];if(!group){group={label:TOOL_GROUPS[g]||'Outras ferramentas',tools:[],commands:[]};groups[g+2]=group}group.tools.push(t[0])}
 const panels=[];
 const activate=(n,focus=false)=>{groups.forEach((group,i)=>{const tab=tabs.children[i];tab.setAttribute('aria-selected',String(i===n));tab.tabIndex=i===n?0:-1;panels[i].hidden=i!==n});if(focus){tabs.children[n].focus();tabs.children[n].scrollIntoView({block:'nearest',inline:'nearest'})}};
 groups.forEach((group,i)=>{
  const tab=document.createElement('button');tab.type='button';tab.id='rsToolTab'+i;tab.textContent=group.label;tab.setAttribute('role','tab');tab.setAttribute('aria-controls','rsToolPanel'+i);tab.onclick=()=>activate(i);tabs.appendChild(tab);
  const panel=document.createElement('div');panel.id='rsToolPanel'+i;panel.className='rsToolPanel';panel.setAttribute('role','tabpanel');panel.setAttribute('aria-labelledby',tab.id);panel.tabIndex=0;panels.push(panel);ribbon.appendChild(panel);
  for(const command of group.commands){const b=document.createElement('button');b.type='button';b.dataset.rsCommand=command;const name=({OFFSET:'Paralela',DIST:'Medir distância'})[command]||command.charAt(0)+command.slice(1).toLowerCase();b.innerHTML=(icoPara(name)||toolIcon('chain'))+'<span>'+esc(name)+'</span>';b.setAttribute('aria-label',name);b.title=name+' — '+command;b.onclick=()=>call(()=>runCommand(command));panel.appendChild(b)}
  for(const id of group.tools){const toolDef=TOOLS.find(t=>Array.isArray(t)&&t[0]===id);if(!toolDef)continue;const b=document.createElement('button');b.type='button';b.dataset.rsTool=id;b.title=toolLabel(toolDef)+' — '+toolDef[2];b.setAttribute('aria-label',toolLabel(toolDef));b.innerHTML=(toolIcon(id)||icoPara(toolLabel(toolDef))||icoSvg('grips'))+'<span>'+esc(toolLabel(toolDef))+'</span>';b.onclick=()=>call(()=>setTool(id));panel.appendChild(b)}
 });
 const all=document.createElement('div');all.className='rsAllGroups';panels[0].appendChild(all);
 for(let i=1;i<panels.length;i++){const group=document.createElement('div');group.className='rsAllGroup';group.setAttribute('role','group');group.setAttribute('aria-label',groups[i].label);for(const original of panels[i].querySelectorAll('button')){const copy=original.cloneNode(true);copy.onclick=original.onclick;group.appendChild(copy)}all.appendChild(group)}
 ribbon.classList.add('rsIconMode');
 const help=document.createElement('div');help.id='rsToolHelp';help.setAttribute('role','tooltip');help.hidden=true;document.body.appendChild(help);
 const hideHelp=()=>{help.hidden=true};
 for(const b of ribbon.querySelectorAll('[data-rs-tool],[data-rs-command]')){
  const text=b.title;b.dataset.rsHelp=text;b.removeAttribute('title');b.setAttribute('aria-describedby',help.id);
  const show=()=>{help.textContent=text;help.hidden=false;const r=b.getBoundingClientRect();const w=help.offsetWidth,h=help.offsetHeight;help.style.left=Math.max(6,Math.min(innerWidth-w-6,r.left))+'px';help.style.top=(r.bottom+h+8<innerHeight?r.bottom+6:Math.max(6,r.top-h-6))+'px'};
  b.addEventListener('pointerenter',show);b.addEventListener('pointerleave',hideHelp);b.addEventListener('focus',show);b.addEventListener('blur',hideHelp);
 }
 ribbon.addEventListener('click',hideHelp);ribbon.addEventListener('keydown',e=>{if(e.key==='Escape')hideHelp()});window.addEventListener('resize',hideHelp);window.addEventListener('scroll',hideHelp,true);
 tabs.addEventListener('keydown',e=>{const current=[...tabs.children].indexOf(document.activeElement);if(current<0)return;let n=current;if(e.key==='ArrowRight')n=(current+1)%groups.length;else if(e.key==='ArrowLeft')n=(current+groups.length-1)%groups.length;else if(e.key==='Home')n=0;else if(e.key==='End')n=groups.length-1;else return;e.preventDefault();activate(n,true)});
 rail.prepend(ribbon);activate(0);
}
function dockCommands(){
 const title=document.querySelector('.dwTitleBar');if(title)$('menuBar').before(title);
 let rail=$('rsCommandRail');if(!rail){rail=document.createElement('div');rail.id='rsCommandRail';rail.setAttribute('aria-label','Acesso rápido e opções da ferramenta');$('menuBar').after(rail)}
 quickTools(rail);commandRibbon(rail);
 for(const el of [$('toolOptions'),$('selBar')])if(el&&el.parentNode!==rail)rail.appendChild(el);
 const tb=$('toolbar');if(tb){tb.hidden=true;$('toolLabels')?.remove()}
 let footer=$('rsStudyFooter');if(!footer){footer=document.createElement('div');footer.id='rsStudyFooter';footer.setAttribute('aria-label','Comando, coordenadas e diagnóstico de fluxos');$('bottomBar').before(footer)}
 if(!$('rsActiveTool')){const head=document.createElement('div');head.id='rsActiveTool';head.setAttribute('role','status');footer.appendChild(head)}
 for(const el of [document.querySelector('.dwCursor'),$('dwCommandDrawer')])if(el&&el.parentNode!==footer)footer.appendChild(el);
 if(!$('rsFlowLegend')){const legend=document.createElement('div');legend.id='rsFlowLegend';legend.innerHTML='<span class="flow-ok">● Fluxo OK</span><span class="flow-problem">● Problema</span><span class="flow-adjustment">● Ajuste necessário</span><span>Estudo técnico · não aparece no vídeo</span>';footer.appendChild(legend)}
}
function foregroundFlows(){
 if(!ready()||!flowEditing()||vecOn.flows===false)return;
 ctx.save();ctx.setTransform(1,0,0,1,0,0);ctx.globalAlpha=1;ctx.lineJoin='round';ctx.lineCap='round';
 const line=(points,status,forward=true,both=false,dashed=false)=>{
  const pts=(points||[]).map(p=>Array.isArray(p)?P(p):p).filter(p=>Number.isFinite(p.x)&&Number.isFinite(p.y));if(pts.length<2||polyLen(pts)<.1)return;
  const color=flowStudyColor(status);poly(pts);ctx.setLineDash([]);ctx.strokeStyle='#081623';ctx.lineWidth=7;ctx.stroke();
  ctx.setLineDash(dashed?[7,4]:[]);ctx.strokeStyle=color;ctx.lineWidth=4;ctx.stroke();ctx.setLineDash([]);arrowsAlong(pts,forward,both,color,85);
 };
 for(const seg of editor?.segments||[])line(seg.points,seg,seg.forward,seg.both,seg.disabled);
 for(const route of M.traffic_paths||[])line(route.points,route.enabled===false?{disabled:true}:(editor?.segments||[]).find(s=>s.source===route.name),true,false,route.enabled===false);
 for(const route of M.route_alignments||[]){
  const calculated=(editor?.segments||[]).filter(s=>s.route===route.id);const status=route.enabled===false?{disabled:true}:polyLen(route.points)<minFlowLength()?{technical_status:'adjustment'}:calculated.find(s=>s.technical_status==='problem')||calculated.find(s=>s.technical_status==='adjustment')||calculated[0];
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
 document.querySelectorAll('[data-rs-tool]').forEach(b=>{const on=b.dataset.rsTool===tool;b.setAttribute('aria-pressed',String(on));b.classList.toggle('on',on)});
 const quick=$('rsQuickTools')?.querySelector('[data-rs-quick="flows"]');if(quick){quick.setAttribute('aria-pressed',String(flowEditing()));quick.classList.toggle('on',flowEditing())}
 const active=TOOLS.find(t=>Array.isArray(t)&&t[0]===tool);
 if($('rsActiveTool'))$('rsActiveTool').textContent='Comando: '+(active?toolLabel(active).replace(/^[^\p{L}\p{N}]+/u,''):'Selecionar')+' · Enter conclui · Esc cancela';
 const b=document.querySelector('[data-pshub="props"]');if(b){b.setAttribute('aria-expanded',String(!dockState.recolhida&&dockState.aba==='prop'));b.classList.toggle('on',!dockState.recolhida&&dockState.aba==='prop')}
 const legend=$('rsFlowLegend');if(legend)legend.hidden=vecOn.flows===false;
}
function init(){
 registerControlTool();document.body.classList.add('studio142');buildMenus();dockCommands();sync();
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
