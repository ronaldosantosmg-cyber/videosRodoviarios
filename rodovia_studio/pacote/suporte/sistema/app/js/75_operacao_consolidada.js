// Uma entrada por atividade, tarefas explícitas e fila local sem execução duplicada.
(()=>{'use strict';
const pending=[],requests=new Map();let running=null,serial=0,draining=false;
const oldStart=start;
function queueState(){const waiting=pending.length+(running?.phase==='waiting'?1:0);if($('pcQueue'))$('pcQueue').textContent=waiting?waiting+' na fila':'';if($('rsClearQueue'))$('rsClearQueue').hidden=!waiting;window.dispatchEvent(new CustomEvent('rodovia:update-state'))}
async function drain(){if(draining)return;draining=true;try{while(pending.length){const row=pending.shift();running=row;row.phase='waiting';queueState();try{
 if(row.project!==pid||row.context!==projectSession.context){row.resolve(false);continue}
 const deadline=Date.now()+120000;
 while(!row.cancelled&&(task||taskRequestPending||fileMutationPending)){if(pid!==row.project||projectSession.context!==row.context)break;if(Date.now()>deadline)throw Error('A operação atual continua. Solicite a atualização novamente após concluir ou cancelar.');await new Promise(r=>setTimeout(r,150))}
 if(row.cancelled||row.project!==pid||row.context!==projectSession.context){row.resolve(false);continue}
 row.phase='running';queueState();row.resolve(await oldStart(row.kind,row.payload,row.options));
 }catch(error){row.reject(error)}finally{requests.delete(row.key);running=null;queueState()}}}finally{draining=false}}
start=function(kind,payload,options={}){
 if(options.automatic)return Promise.resolve(false);
 requireProject();const signature=JSON.stringify(collect()),key=JSON.stringify([pid,projectSession.context,kind,payload,signature]);
 if(requests.has(key))return requests.get(key).promise;
 if(pending.length>=8)return Promise.reject(Error('A fila já tem oito operações. Aguarde a conclusão.'));
 let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b});const row={id:++serial,key,promise,resolve,reject,kind,payload,options,project:pid,context:projectSession.context};requests.set(key,row);pending.push(row);queueState();void drain();return promise;
};
function updateState(){const b=$('rsUpdateProject');if(!b)return;const three=window.Rodovia3D?.stats(),artifact=projectSession.artifacts?.[three?.ready?'scene3d':'preview'];const stale=!!pid&&(savePending||previewStale||artifact?.state!=='ready');b.classList.toggle('rsPending',stale);b.title=stale?'Atualização pendente. Salvar preserva os dados sem iniciar cálculos.':'Atualizar a apresentação do projeto';$('rsUpdateState').textContent=stale?'Atualização pendente':'Resultados atuais'}
async function update(){requireProject();const three=window.Rodovia3D?.stats(),stable=!savePending&&!window.RodoviaPanels?.opened;
 if(three?.ready){if(stable&&!three.stale&&projectSession.artifacts?.scene3d?.state==='ready'){msg('Cena 3D atual; nenhum recálculo necessário.');return true}return Rodovia3D.open(true)}
 if(stable&&!previewStale&&projectSession.artifacts?.preview?.state==='ready'&&baseImage){draw();msg('Prévia atual; nenhum recálculo necessário.');return true}
 return start('preview')}
window.RodoviaUpdates=Object.freeze({update,snapshot:()=>({running:running?.kind||null,queued:pending.map(r=>r.kind),requests:requests.size}),clearQueue(){if(running?.phase==='waiting')running.cancelled=true;for(const row of pending.splice(0)){requests.delete(row.key);row.resolve(false)}queueState()}});
window.addEventListener('rodovia:project-state',updateState);window.addEventListener('rodovia:update-state',updateState);
const previousSchedule=scheduleSave;scheduleSave=function(...args){const result=previousSchedule(...args);updateState();return result};
const quickIcons={'zoom-in':'M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14M15 15l6 6M10 7v6M7 10h6','zoom-out':'M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14M15 15l6 6M7 10h6',fit:'M3 9V3h6M15 3h6v6M21 15v6h-6M9 21H3v-6',undo:'M9 5 3 11l6 6M3 11h10a7 7 0 0 1 7 7',redo:'m15 5 6 6-6 6M21 11H11a7 7 0 0 0-7 7'};
const action=(text,fn,icon='inspect')=>{const b=document.createElement('button');b.type='button';b.className='rsPrimaryAction';b.innerHTML=(quickIcons[icon]?'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="'+quickIcons[icon]+'"/></svg>':RodoviaIcons[icon]||toolIcon(icon)||'')+'<span>'+esc(text)+'</span>';b.title=text;b.setAttribute('aria-label',text);b.onclick=guard(fn,text);return b};
function materials(){
 const section=document.createElement('section');section.id='rsMaterialsSection';section.innerHTML='<h2>Materiais e apresentação</h2><p>Selecione a área no desenho para ajustar seu material. Os controles são os mesmos usados na geração do vídeo.</p>';
 const profile=document.createElement('label');profile.innerHTML='Perfil de apresentação<select id="rsPresentationProfile"><option value="custom">Personalizado</option><option value="technical">Técnico</option><option value="artistic">Maquete artística</option></select>';section.appendChild(profile);
 profile.querySelector('select').onchange=e=>{if(e.target.value==='artistic')$('rsArtisticPreset').click();else if(e.target.value==='technical'){$('style_profile').value='tecnico';$('natural_materials_only').checked=false;$('earthwork_look').value='hatch';scheduleSave()}else{$('style_profile').value='padrao';$('natural_materials_only').checked=false;scheduleSave()}};
 const row=document.createElement('div');row.className='row';row.append(action('Material da área selecionada',async()=>{if(!await RodoviaPanels.close())return;if(dxfSel&&['pavement','existing_pavement','shoulder'].includes(dxfSel.role))return openTexDialog();if(dxfSel&&SURF_MODE[dxfSel.role])return openSurfDialog('tex',{ring:dxfSel.points,layer:dxfSel.layer,surface:SURF_MODE[dxfSel.role]});const o=objOf(sel);if(o?.key==='texture_areas')return openSurfDialog('tex',{area:o.o,surface:o.o.surface});if(o?.key==='pavement_areas')return openTexDialog();msg('Selecione uma área de pavimento, textura ou uma hachura do desenho.',true)},'brush'),action('Catálogo e nomes CAD',async()=>{if(await RodoviaPanels.close())await RodoviaAssetCatalog.open()},'hatch'));section.appendChild(row);
 const controls=document.createElement('div');controls.className='grid';section.appendChild(controls);
 for(const id of ['style_profile','pavement_material','existing_material','shoulder_material','joint_spacing_m','texture_style','earthwork_look','natural_materials_only'])if($(id))controls.appendChild($(id).closest('label'));
 if($('rsArtisticPreset'))section.appendChild($('rsArtisticPreset'));
 for(const id of ['texEditor','pavStyles'])if($(id))section.appendChild($(id));
 const parent=pnItens[0]?.el.parentNode||document.querySelector('main');parent.appendChild(section);pnItens.push({id:section.id,t:'Materiais e apresentação',el:section});section.classList.add('pnOculta');
 const fillPrevious=fill;fill=function(...args){const value=fillPrevious(...args);$('rsPresentationProfile').value=$('style_profile').value==='tecnico'?'technical':$('natural_materials_only').checked?'artistic':'custom';return value};
 window.RodoviaMaterialsHub=Object.freeze({open:async()=>{if(await RodoviaPanels.close())openSection('Materiais e apresentação')}});
}
function zoomAtCenter(deltaY){const r=canvas.getBoundingClientRect();canvas.dispatchEvent(new WheelEvent('wheel',{deltaY,clientX:r.left+r.width/2,clientY:r.top+r.height/2,bubbles:true,cancelable:true}))}
function init(){
 materials();const ribbon=$('rsToolRibbon');let tabs=$('rsToolTabs');if(!ribbon||!tabs)return;
 const sources=[...ribbon.querySelectorAll('.rsAllGroups [data-rs-group]')];const definitions=[['Projeto',new Set(['Calibração e cabine'])],['Editar',new Set(['Edição','Cálculos','Estaqueamento e obras','Outras ferramentas'])],['Tráfego',new Set(['Fluxos de tráfego','Tráfego e acessos','Ferrovia e semáforos'])],['Cena',new Set(['Áreas e sinalização','Paisagem','Navegação'])],['Vídeo',new Set()]];
 const nav=document.createElement('div');nav.id='rsQuickNavigation';nav.setAttribute('role','toolbar');nav.setAttribute('aria-label','Navegação e histórico');ribbon.before(nav);
 const pan=sources.flatMap(g=>[...g.querySelectorAll('[data-rs-tool=pan]')])[0];if(pan)nav.appendChild(pan);
 for(const [text,fn,id] of [['Aproximar',()=>zoomAtCenter(-150),'zoom-in'],['Afastar',()=>zoomAtCenter(150),'zoom-out'],['Enquadrar',fitView,'fit'],['Desfazer',undo,'undo'],['Refazer',redo,'redo']]){const b=action(text,fn,id);b.classList.remove('rsPrimaryAction');b.dataset.quick=id;nav.appendChild(b)}
 const updateButton=action('Atualizar',update);updateButton.id='rsUpdateProject';nav.appendChild(updateButton);const state=document.createElement('span');state.id='rsUpdateState';nav.appendChild(state);
 const panels=[];tabs.replaceChildren();const originals=[...ribbon.querySelectorAll(':scope>.rsToolPanel')];
 definitions.forEach(([name,groups],i)=>{const tab=document.createElement('button');tab.type='button';tab.id='rsToolTab'+i;tab.textContent=name;tab.setAttribute('role','tab');tab.setAttribute('aria-controls','rsToolPanel'+i);tabs.appendChild(tab);
 const panel=document.createElement('div');panel.id='rsToolPanel'+i;panel.className='rsToolPanel rsConsolidatedPanel';panel.setAttribute('role','tabpanel');panel.setAttribute('aria-labelledby',tab.id);panel.dataset.activity=name;panels.push(panel);
 const advanced=document.createElement('details');advanced.className='rsAdvancedTools';advanced.innerHTML='<summary>Mais ferramentas</summary>';panel.appendChild(advanced);
 for(const group of sources)if(groups.has(group.dataset.rsGroup)){if(name==='Cena'){const three=group.querySelector('[data-rs3d=view3d]');if(three)panel.prepend(three)}advanced.appendChild(group)}
 tab.onclick=()=>activate(i);ribbon.appendChild(panel);
 });
 function activate(index){panels.forEach((p,i)=>{p.hidden=i!==index;tabs.children[i].setAttribute('aria-selected',String(i===index));tabs.children[i].tabIndex=i===index?0:-1});$('rsToolHelp').hidden=true;requestAnimationFrame(scheduleCanvasResize)}
 tabs.onkeydown=e=>{const i=[...tabs.children].indexOf(document.activeElement);if(i<0)return;let n=i;if(e.key==='ArrowRight')n=(i+1)%5;else if(e.key==='ArrowLeft')n=(i+4)%5;else if(e.key==='Home')n=0;else if(e.key==='End')n=4;else return;e.stopImmediatePropagation();e.preventDefault();activate(n);tabs.children[n].focus()};
 // O listener antigo referia-se às abas removidas; substitui a própria lista mantendo o ID público.
 const cleanTabs=tabs.cloneNode(false);while(tabs.firstChild)cleanTabs.appendChild(tabs.firstChild);cleanTabs.onkeydown=tabs.onkeydown;tabs.replaceWith(cleanTabs);tabs=cleanTabs;
 const header=document.createElement('div');header.className='rsToolHeader';ribbon.prepend(header);header.append(tabs,nav);
 // activate usa a lista nova; os botões permanecem as mesmas instâncias.
 
 for(const old of originals)old.remove();
 panels[0].prepend(action('Arquivos do projeto',()=>psOpenHub('project')),action('Camadas e imagens',()=>psOpenHub('layers')));
 panels[2].prepend(action('Escolher eixo',()=>RodoviaSections.chooseAxis(),'route'),action('Configurar faixas',()=>RodoviaSections.open(),'lanes'),action('Gerar e visualizar',update),action('Corrigir problemas',()=>RodoviaFlowRepair.open(),'flowcut'));
 panels[3].prepend(action('Materiais e texturas',()=>RodoviaMaterialsHub.open(),'brush'));
 panels[4].prepend(action('Configurar vídeo',()=>psOpenHub('video')),action('Gerar prévia',()=>start('preview')),action('Gerar vídeo',()=>start('render')));
 const controls=$('rs3dControls');if(controls)panels[3].appendChild(controls);
 const results=document.createElement('details');results.innerHTML='<summary>Resultado do vídeo</summary>';for(const id of ['download','video'])if($(id))results.appendChild($(id));panels[4].appendChild(results);
 const options=$('rsTechnicalOptions');if(options){const details=document.createElement('details');details.className='rsAdvancedTools';details.innerHTML='<summary>Parâmetros de apresentação</summary>';details.appendChild(options);panels[0].appendChild(details)}
 const footer=$('rsStudyFooter');if(footer)footer.prepend(progQuadro());const clear=document.createElement('button');clear.type='button';clear.id='rsClearQueue';clear.textContent='Limpar fila';clear.hidden=true;clear.onclick=()=>RodoviaUpdates.clearQueue();$('progCard').appendChild(clear);if($('logs'))$('progCard').appendChild($('logs'));if($('cancel'))$('cancel').hidden=true;
 const source=$('cancel')?.closest('section');if(source&&!source.contains($('video')))source.hidden=true;
 if($('toolHint'))$('toolHint').hidden=true;document.body.classList.add('rsSimplified21');activate(0);updateState();
 const undoPrevious=updateUndo;updateUndo=function(...args){const result=undoPrevious(...args);nav.querySelector('[data-quick=undo]').disabled=!undoStack.length;nav.querySelector('[data-quick=redo]').disabled=!redoStack.length;return result};updateUndo();
 }
queueMicrotask(()=>queueMicrotask(init));
})();
