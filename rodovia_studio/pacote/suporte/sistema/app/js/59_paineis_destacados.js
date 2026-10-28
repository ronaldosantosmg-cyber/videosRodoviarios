// Janelas amplas para os mesmos campos do painel; alterações ficam pendentes até confirmar.
(()=>{'use strict';
let active=null,committing=false,closing=false,decision=null,closePending=null,resultsLoading=0;
const clone=x=>JSON.parse(JSON.stringify(x));
const originalSave=save,originalSchedule=scheduleSave,originalStart=start,originalLoad=load;
function surface(){return active?.surface||dialog()}
function panelStatus(text){const el=surface().querySelector('[data-rs-edit-status]')||$('rsPanelStatus');if(el)el.textContent=text}
function controls(root=document){return [...root.querySelectorAll('input,select,textarea')].filter(e=>e.type!=='file'&&!e.matches('[data-rs-transient]')).map(e=>({el:e,value:e.value,checked:e.checked}))}
function fingerprint(root=active?.node||document){let data;try{data=collect()}catch{data=null}const values=(root?.dataset?.rsConfigOnly==='true'?[]:controls(root)).map(c=>JSON.stringify([c.el.id||c.el.name||JSON.stringify(c.el.dataset),c.el.type,c.value,c.checked])).sort();return JSON.stringify([data,values])}
function differs(){return !!active&&(fingerprint()!==active.fingerprint||projectSession.epoch!==active.epoch)}
function state(node){const signature=fingerprint(node);return {cfg:clone(cfg),marks:clone(M),undo:undoStack.slice(),redo:redoStack.slice(),controls:controls(node),pending:savePending,studyStale:!!window.RodoviaFlowStudy?.stale,previewStale:typeof previewStale==='undefined'?false:previewStale,epoch:projectSession.epoch,fingerprint:signature}}
function pauseTimers(){clearTimeout(saveTimer);if(typeof prevTimer!=='undefined')clearTimeout(prevTimer);if(typeof flowTimer!=='undefined')clearTimeout(flowTimer)}
function restore(base){
 cfg=base.cfg;M=base.marks;undoStack=base.undo;redoStack=base.redo;
 for(const c of base.controls)if(c.el.isConnected){c.el.value=c.value;c.el.checked=c.checked}
 projectSession.epoch=base.epoch;savePending=base.pending;if(window.RodoviaFlowStudy)RodoviaFlowStudy.stale=base.studyStale;if(typeof previewStale!=='undefined')previewStale=base.previewStale;axisCache=null;snapIndex=null;exactSnap=null;
 refreshLists();updateUndo();showProps();if(analysis)showLayers();if(typeof refreshRouteLanes==='function')refreshRouteLanes(true);draw();
 $('saveState').textContent=savePending?'alterações anteriores aguardam gravação…':'alterações da janela descartadas';syncImagery();
}
function dialog(){
 let d=$('rsPanelPopup');if(d)return d;
 d=document.createElement('dialog');d.id='rsPanelPopup';d.setAttribute('aria-labelledby','rsPanelTitle');
 d.innerHTML='<header><h2 id="rsPanelTitle"></h2><button type="button" id="rsPanelClose" aria-label="Fechar janela">×</button></header><div id="rsPanelBody"></div><footer><span id="rsPanelStatus" data-rs-edit-status role="status">Alterações de configuração serão confirmadas ao salvar.</span><button type="button" id="rsPanelCancel">Cancelar</button><button type="button" id="rsPanelDiscard">Descartar alterações</button><button type="button" id="rsPanelSave" class="primary">Salvar e fechar</button></footer>';
 document.body.appendChild(d);$('rsPanelClose').onclick=()=>void requestClose();$('rsPanelCancel').onclick=()=>void requestClose();$('rsPanelSave').onclick=()=>void commitClose();$('rsPanelDiscard').onclick=discardClose;
 d.addEventListener('cancel',e=>{e.preventDefault();void requestClose()});
 d.addEventListener('input',()=>{scheduleSave();panelStatus('Alterações pendentes — salve ou descarte antes de fechar.')});return d;
}
function open(node,title,key){
 if(!node||closing)return;
 if(active){if(active.key===key){dialog().focus();return}void requestClose().then(ok=>{if(ok)open(node,title,key)});return}
 pauseTimers();const base=state(node),placeholder=document.createComment('painel destacado');node.before(placeholder);
 active={...base,node,parent:placeholder.parentNode,placeholder,key,title,classes:node.className,hidden:node.hidden,project:pid};
 node.classList.remove('pnOculta','vazia');node.hidden=false;$('rsPanelBody')||dialog();$('rsPanelBody').appendChild(node);$('rsPanelTitle').textContent=title;
 panelStatus('Alterações de configuração serão confirmadas ao salvar.');
 dialog().show();document.body.classList.add('rsPanelOpen');
}
function finish(discard){
 if(!active)return;const base=active;closing=true;active=null;
 let refreshError=null;
 try{if(discard)restore(base)}catch(e){refreshError=e}
 finally{
  try{base.node.className=base.classes;base.node.hidden=base.hidden;if(!base.standalone){if(base.placeholder.isConnected)base.placeholder.replaceWith(base.node);else if(base.parent?.isConnected)base.parent.appendChild(base.node)}if(discard)base.onRestore?.()}catch(e){refreshError??=e}
  // O fechamento não pode depender de uma atualização de lista/propriedades.
  (base.surface||dialog()).close();document.body.classList.remove('rsPanelOpen');
  try{if(!base.standalone){if(base.key.startsWith('dock:'))recolherDock(true);else pnAbrir(null)}}catch(e){refreshError??=e}
  finally{closing=false}
 }
 try{syncImagery()}catch(e){refreshError??=e}
 if(refreshError)msg((discard?'Alterações descartadas. ':'Alterações salvas. ')+'A janela foi fechada; não foi possível atualizar uma parte do painel: '+refreshError.message,true);
 const refresh=()=>{if(active||pid!==base.project)return;window.dispatchEvent(new CustomEvent('rodovia:update-state'))};
 if(discard&&base.project&&!savePending)void oldApi('/api/projects/'+base.project).then(r=>{if(pid===base.project&&!savePending&&projectSession.revision===r.config_revision)window.dispatchEvent(new CustomEvent('rodovia:project-state',{detail:{project:base.project,...r}}))}).catch(()=>{});
 if(savePending){clearTimeout(saveTimer);saveTimer=setTimeout(async()=>{try{await originalSave();refresh()}catch(e){msg(e.message,true)}},900)}else setTimeout(refresh,350)
}
async function commitClose(){
 if(!active||committing)return false;
 const pane=active;
 if(pane.project!==pid){msg('O projeto mudou. Feche e reabra esta janela.',true);return false}
 if(!pid){msg('Crie ou abra um projeto antes de salvar.',true);return false}
 committing=true;
 try{flushPropertyInputs(pane.node);surface().querySelectorAll('button,input,select,textarea').forEach(e=>{e.dataset.rsWasDisabled=String(e.disabled);e.disabled=true});if(!String($('name')?.value||'').trim())throw Error('Informe o nome do projeto antes de salvar.');await originalSave();if(savePending)throw Error('Há novas alterações pendentes. Revise e salve novamente.');finish(false);window.dispatchEvent(new CustomEvent('rodovia:form-committed',{detail:{project:pane.project,context:projectSession.context}}));return true}
 catch(e){panelStatus('Não foi salvo: '+e.message);msg(e.message,true);return false}
 finally{document.querySelectorAll('[data-rs-was-disabled]').forEach(e=>{e.disabled=e.dataset.rsWasDisabled==='true';delete e.dataset.rsWasDisabled});committing=false}
}
function discardClose(){
 if(!active||committing)return false;
 if(active.project!==pid){msg('O projeto mudou. Feche e reabra esta janela.',true);return false}
 finish(differs());return true;
}
async function openDialog(node,title,key,{onRestore}={}){
 if(!node||closing)return false;
 if(active){if(active.surface===node){node.focus();return true}if(!await requestClose())return false}
 pauseTimers();const base=state(node);
 active={...base,node,key,title,classes:node.className,hidden:node.hidden,project:pid,surface:node,standalone:true,onRestore};
 node.classList.add('rsTransactionalDialog');node.hidden=false;
 panelStatus('Alterações de configuração serão confirmadas ao salvar.');
 if(!node.open)node.showModal();document.body.classList.add('rsPanelOpen');return true;
}
function choose(){
 if(decision)return decision.promise;
 let resolve;const promise=new Promise(r=>resolve=r),d=document.createElement('dialog');d.id='rsPanelDecision';d.setAttribute('aria-labelledby','rsPanelDecisionTitle');
 d.innerHTML='<h2 id="rsPanelDecisionTitle">Salvar alterações?</h2><p>Os dados desta janela foram alterados. Salve a configuração ou descarte as alterações feitas desde a abertura.</p><div class="row"><button type="button" data-choice="continue">Continuar editando</button><button type="button" data-choice="discard">Descartar alterações</button><button type="button" data-choice="save" class="primary">Salvar</button></div>';
 const done=value=>{d.close();d.remove();decision=null;resolve(value)};d.onclick=e=>{const value=e.target.closest('[data-choice]')?.dataset.choice;if(value)done(value)};d.oncancel=e=>{e.preventDefault();done('continue')};
 document.body.appendChild(d);decision={promise};d.showModal();return promise;
}
function requestClose(){
 if(closePending)return closePending;
 if(!active)return Promise.resolve(true);if(committing)return Promise.resolve(false);
 const pane=active;
 closePending=(async()=>{
  if(!differs()){finish(false);return true}
  const answer=await choose();if(answer==='continue')return false;
  if(active!==pane)return !active;
  if(answer==='discard'){finish(true);return true}return commitClose();
 })().finally(()=>{closePending=null});return closePending;
}
scheduleSave=function(...args){if(!active||committing)return originalSchedule(...args);projectSession.epoch++;savePending=true;pauseTimers();$('saveState').textContent='alterações pendentes na janela';panelStatus('Alterações pendentes — salve ou descarte antes de fechar.')};
save=async function(...args){if(active&&!committing){pauseTimers();if(!await requestClose())throw Error('Gravação cancelada; a janela continua em edição.')}return originalSave(...args)};
const oldSchedulePreview=scheduleViewPreview,oldViewPreview=runViewPreview;
scheduleViewPreview=function(...args){if(active){previewStale=true;pauseTimers();return}return oldSchedulePreview(...args)};
runViewPreview=async function(...args){if(active){previewStale=true;pauseTimers();return false}return oldViewPreview(...args)};
start=async function(...args){const project=pid,context=projectSession.context;if(args[2]?.automatic&&document.querySelector('dialog[open]'))return false;if(args[2]?.policyAuto&&active)return false;if(active&&!committing){pauseTimers();if(!await requestClose())return false}if(pid!==project||projectSession.context!==context)return false;if(['refresh','preview','render','scene3d'].includes(args[0]))window.RodoviaUpdatePolicy?.consumePending();return originalStart(...args)};
load=async function(...args){if(active&&!committing&&!args[1]?.resultsOnly){if(!await requestClose()){$('projects').value=pid;return false}}const resultsOnly=!!args[1]?.resultsOnly;if(resultsOnly)resultsLoading++;try{return await originalLoad(...args)}finally{if(resultsOnly)resultsLoading--}};
const oldDock=abrirAba;abrirAba=function(id,click){
 // Receber um resultado atualiza campos e seleção, sem abrir outra janela.
 if(resultsLoading&&!click)return;
 if(closing)return oldDock(id,click);
 const key='dock:'+id;
 if(active){if(active.key===key){if(click)void requestClose();return}void requestClose().then(ok=>{if(ok)abrirAba(id,click)});return}
 const result=oldDock(id,false);
 if(!dockState.recolhida&&(click||id==='prop'&&!$('propPanel').hidden)){const item=document.querySelector(`.dockItem[data-dock="${id}"]`);open(item,DOCK_ITENS.find(i=>i.id===id)?.t||'Propriedades',key)}return result;
};
const oldHub=psOpenHub;psOpenHub=function(id){
 if(active){if((id==='props'&&active.key==='dock:prop')||active.key==='hub:'+id){void requestClose();return}void requestClose().then(ok=>{if(ok)psOpenHub(id)});return}
 const result=oldHub(id);if(id==='props'||active)return result;
 const item=pnItens.find(i=>i.id===pnEstado.aberto);if(item)open(item.el,item.t,'hub:'+id);return result;
};
destacar=function(id){const item=document.querySelector(`.dockItem[data-dock="${id}"]`);open(item,DOCK_ITENS.find(i=>i.id===id)?.t||'Propriedades','dock:'+id)};
const oldSection=openSection;openSection=function(title){if(active){void requestClose().then(ok=>{if(ok)openSection(title)});return}const result=oldSection(title);const item=pnItens.find(i=>i.id===pnEstado.aberto);if(item)open(item.el,item.t,'section:'+item.id);return result};
// Uma operação que grava arquivos fecha primeiro a edição pendente; os originais não fazem parte de Descartar.
const oldApi=api;api=async function(url,options={}){
 const mutating=options.method&&!['GET','HEAD'].includes(options.method.toUpperCase());
 if(active&&!committing&&mutating&&/^\/api\/projects\/[^/]+\/(analyze|preview|refresh|render|scene3d|frames|export)(\/|$)/.test(url)){if(!await requestClose())throw Error('Processamento cancelado; a janela continua em edição.');}
 if(active&&!committing&&/\/config$/.test(url)&&options.headers?.['If-Match'])return oldApi(url,options);
 if(active&&!committing&&mutating&&/^\/api\/projects\/[^/]+\//.test(url)&&!/^\/api\/projects\/[^/]+\/(validate_path|sessoes|client_error|client_log)(\/|$)/.test(url)){if(!await requestClose())throw Error('Operação cancelada; a janela continua em edição.')}
 return oldApi(url,options);
};
document.addEventListener('click',e=>{const button=e.target.closest('[data-pspn]');if(!button)return;e.preventDefault();e.stopImmediatePropagation();const show=()=>{const id=button.dataset.pspn;pnAbrir(id);if($('psMore'))$('psMore').hidden=true;PS.extraOpen=false;const item=pnItens.find(i=>i.id===id);if(item)open(item.el,item.t,'more:'+id);psUpdateHubState()};if(active)void requestClose().then(ok=>{if(ok)show()});else show()},true);
// Os cliques fora da janela precisam resolver a edição antes de voltar ao desenho.
document.addEventListener('pointerdown',e=>{if(!active||e.target.closest('#rsPanelPopup,#rsPanelDecision,#atividades,.dockHead'))return;if(e.target.closest('dialog,button,a,[role=button]'))return;e.preventDefault();e.stopImmediatePropagation();void requestClose()},true);
// Resolva a edição e execute o botão original uma única vez, já com os dados gravados.
document.addEventListener('click',e=>{
 if(!active||committing||e.target.closest('#rsPanelPopup,#rsPanelDecision,#atividades,.dockHead,dialog'))return;
 const button=e.target.closest('button,a,[role=button]');if(!button||button.disabled)return;
 e.preventDefault();e.stopImmediatePropagation();const project=pid;
 void requestClose().then(ok=>{if(ok&&pid===project&&button.isConnected&&!button.disabled)button.click()}).catch(err=>msg(err.message,true));
},true);
document.addEventListener('keydown',e=>{if(active&&!decision&&e.key==='Tab'){const items=[...surface().querySelectorAll('button,input,select,textarea,a[href]')].filter(el=>!el.disabled&&el.getClientRects().length);if(items.length){const first=items[0],last=items[items.length-1];if(e.shiftKey&&(e.target===first||!surface().contains(e.target))){e.preventDefault();last.focus()}else if(!e.shiftKey&&(e.target===last||!surface().contains(e.target))){e.preventDefault();first.focus()}}}if(active&&(e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();e.stopImmediatePropagation();void (async()=>{if(await commitClose()&&window.RodoviaUpdatePolicy)await RodoviaUpdatePolicy.saveProject()})().catch(e=>msg(e.message,true));return}if(active&&e.key==='Escape'&&!decision){e.preventDefault();e.stopImmediatePropagation();void requestClose()}},true);
window.addEventListener('beforeunload',e=>{if(active&&differs()){e.preventDefault();e.returnValue=''}});
function currentImagery(){const image=$('imagery')?.value||cfg.imagery;if(image==='esri')return cfg.local_imagery?.image&&cfg.local_imagery.detail!==false&&($('imagery_detail')?.value||cfg.imagery_detail)!=='off'?'mixed':'map';return image||'map'}
function syncImagery(){const select=$('rsPresentationBase');if(select){const mode=currentImagery();select.value=mode;const legacy=select.querySelector('option[value=cache]');if(legacy){legacy.hidden=mode!=='cache';legacy.disabled=mode!=='cache'}}}
function installImagery(){
 const bar=$('rsTechnicalOptions');if(!bar||$('rsPresentationBase'))return;
 const label=document.createElement('label');label.className='rsPresentationChoice';label.innerHTML='Imagem da apresentação <select id="rsPresentationBase"><option value="map">Mapa georreferenciado</option><option value="mixed">Imagem local + mapa georreferenciado</option><option value="local">Somente imagem local</option><option value="neutral">Fundo neutro</option><option value="cache">Cache legado (conferir cobertura)</option></select>';
 bar.appendChild(label);const button=document.createElement('button');button.id='rsPresentationImages';button.type='button';button.textContent='Configurar imagens…';button.onclick=()=>psOpenHub('layers');bar.appendChild(button);
 $('rsPresentationBase').onchange=guard(async()=>{
  if(active&&!await requestClose()){syncImagery();return}requireProject();const mode=$('rsPresentationBase').value;
  if(['local','mixed'].includes(mode)&&!cfg.local_imagery?.image){syncImagery();throw Error('Envie primeiro uma imagem local georreferenciada em Configurar imagens.')}
  const imagery=mode==='mixed'||mode==='map'?'esri':mode,useLocal=['local','mixed'].includes(mode);
  cfg.imagery=imagery;$('imagery').value=imagery;cfg.local_imagery={...(cfg.local_imagery||{}),detail:useLocal,editor:useLocal};
  if(useLocal){cfg.imagery_detail='auto';$('imagery_detail').value='auto'}
  if($('liDetail'))$('liDetail').checked=useLocal;if($('liEditor'))$('liEditor').checked=useLocal;if(localInfo)localInfo.editor=useLocal;
  baseMode=mode==='local'||mode==='neutral'?'none':'map';saveBasePrefs();localTiles.clear();tiles.clear();scheduleSave();draw();
  msg(mode==='mixed'?'Imagem local nos detalhes; mapa georreferenciado completa a cobertura. Gere a prévia para conferir.':'Base da apresentação alterada. Gere a prévia para conferir.');
 });syncImagery();
}
window.addEventListener('rodovia:project-state',syncImagery);queueMicrotask(()=>{for(const w of document.querySelectorAll('.floatWin[data-dock]'))encaixar(w.dataset.dock);installImagery()});
window.RodoviaPanels=Object.freeze({openDock:id=>abrirAba(id,false),openDialog,saveAndClose:commitClose,discard:discardClose,close:requestClose,get pending(){return differs()},get opened(){return active?.key||null}});
})();
