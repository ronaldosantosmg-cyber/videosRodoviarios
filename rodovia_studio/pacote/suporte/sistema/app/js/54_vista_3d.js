// Vista WebGL local: compartilha o projeto e o motor, preservando o editor CAD 2D.
(()=>{
'use strict';
let viewer=null,active=false,pending=false,currentPid='',token=0,selection=null,stale=false;
const state={context:'ready'};let exporting=null;
const q=id=>document.getElementById(id);
function say(text,error=false){q('rs3dState').textContent=text;msg(text,error)}
function button(id,name,help,action){const b=document.createElement('button');b.type='button';b.dataset.rs3d=id;b.setAttribute('aria-label',name);b.title=name+' — '+help;b.setAttribute('aria-describedby','rsToolHelp');const show=()=>{const tip=q('rsToolHelp');tip.textContent=b.title;tip.hidden=false;const r=b.getBoundingClientRect();tip.style.left=Math.max(5,Math.min(innerWidth-tip.offsetWidth-5,r.left))+'px';tip.style.top=(r.bottom+5)+'px'};b.addEventListener('pointerenter',show);b.addEventListener('focus',show);for(const event of ['pointerleave','blur','click'])b.addEventListener(event,()=>q('rsToolHelp').hidden=true);b.innerHTML=RodoviaInfraRail.forTool(id)||RodoviaIcons[id]||RodoviaIcons.view3d;b.onclick=guard(action,name);return b}
function sync(){document.querySelectorAll('[data-rs3d=view3d]').forEach(b=>{b.classList.toggle('on',active);b.setAttribute('aria-pressed',String(active))});q('rs3dControls').hidden=!active;q('rs3dTime').disabled=!viewer||stale||!!exporting;document.querySelectorAll('#rs3dControls button').forEach(b=>b.disabled=!!exporting||pending||(state.context==='lost'&&b.dataset.rs3d!=='view2d')||(!viewer&&b.dataset.rs3d!=='rebuild3d'));}
function close(){if(exporting){exporting.cancelled=true;void cancelExport(exporting)}token++;pending=false;if(viewer){viewer.dispose();viewer=null}active=false;currentPid='';q('rsViewport3D').hidden=true;canvas.hidden=false;if(selection){sel=selection.sel;selSet=selection.selSet;dxfSel=selection.dxfSel;selection=null;showProps()}resizeCanvas();q('rs3dState').textContent='';sync()}
async function open(force=false){
 requireProject();if(pending)return;
 if(active&&!force){close();return}
 const request=++token,project=pid;pending=true;sync();say('Preparando a vista 3D…');
 try{
  await save();let data;
  if(!force)try{data=await api(`/api/projects/${project}/scene3d.json`)}catch(e){if(!/404|409|Construa|desatualizada|Cena inválida/.test(e.message))throw e}
  if(!data){if(task)throw Error('Aguarde ou cancele a operação atual antes de construir o 3D.');await start('scene3d');data=await api(`/api/projects/${project}/scene3d.json`)}
  if(request!==token||project!==pid)return;
  const {RoadViewer}=await import('/webgl/viewer.mjs');
  if(request!==token||project!==pid)return;
  if(viewer)viewer.dispose();else selection={sel,selSet:[...selSet],dxfSel};
  currentPid=project;canvas.hidden=true;q('rsViewport3D').hidden=false;
  viewer=new RoadViewer(q('rsViewport3D'),{onStatus:text=>{q('rs3dState').textContent=text;if(viewer)q('rs3dTime').value=String(viewer.time)},onContext:kind=>{state.context=kind;sync();if(kind==='lost'&&exporting){exporting.cancelled=true;void cancelExport(exporting)}if(kind==='lost')reportClient('Contexto WebGL perdido','','visualização 3D');},onPick:inspect});
  viewer.load(data);active=true;state.context='ready';stale=false;q('rs3dTime').max=String(data.duration_s);q('rs3dTime').value='0';say(`3D · ${data.terrain.label} · ${data.vehicles.length} veículos · prévia de ${data.duration_s.toFixed(0)} s${data.coordinates_confirmed?'':' · CRS não confirmado'}`);
  viewer.canvas.addEventListener('contextmenu',e=>{e.preventDefault();RodoviaMenus.open([{t:'Enquadrar 3D',f:()=>viewer?.fit()},{t:'Vista de planta 3D',f:()=>viewer?.fit(true)},{t:'Capturar imagem PNG',f:capture},{t:'Voltar ao editor 2D',f:close}],{x:e.clientX,y:e.clientY})});
 }catch(e){if(request===token){if(viewer){viewer.dispose();viewer=null}active=false;q('rsViewport3D').hidden=true;canvas.hidden=false;resizeCanvas();say('Não foi possível abrir o 3D: '+e.message,true)}}
 finally{if(request===token){pending=false;sync()}}
}
function inspect(info){const world=info.world.map(n=>Number(n).toFixed(3));q('rs3dState').textContent=`${info.name||'Objeto'} · X ${world[0]} · Y ${world[1]} · Z ${world[2]} m`;const panel=q('propPanel');if(!panel)return;psOpenHub('props');panel.hidden=false;panel.innerHTML='<h3>Inspeção 3D</h3><p>'+esc(info.name||'Objeto')+'</p><p>'+esc(info.layer||info.role||'')+'</p><p>X: '+world[0]+' m<br>Y: '+world[1]+' m<br>Z: '+world[2]+' m</p><p class="muted">Use o editor 2D para modificar a geometria original.</p>'}
async function capture(){if(!viewer||stale)throw Error('Reconstrua a cena 3D antes de capturar.');const blob=await viewer.png(),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='RodoviaStudio_vista_3D.png';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);say('Imagem 3D capturada sem os diagnósticos técnicos.')}
async function cancelExport(session){try{await api(session.url+'/cancel',{method:'POST',headers:session.headers})}catch(e){reportClient(e.message,'','cancelar exportação 3D')}}
function exportDialog(){
 if(!viewer||stale)throw Error('Reconstrua a cena antes de exportar.');
 let dialog=q('rs3dExport');if(!dialog){dialog=document.createElement('dialog');dialog.id='rs3dExport';dialog.innerHTML='<form method="dialog"><h2>Exportar prévia 3D MP4</h2><p>Usa a câmera atual e o tráfego validado. Os fluxos técnicos ficam fora do vídeo.</p><label>Resolução <select id="rs3dWidth"><option value="1280">HD — 1280 × 720</option><option value="1920">Full HD — 1920 × 1080</option><option value="2560">QHD — 2560 × 1440</option><option value="3840">4K — 3840 × 2160</option></select></label><label>Quadros por segundo <select id="rs3dFps"><option>24</option><option>30</option></select></label><label>Duração da prévia (s) <input id="rs3dDuration" type="number" min="3" step="1" required></label><p id="rs3dExportInfo"></p><button value="cancel">Fechar</button><button id="rs3dExportStart" type="button">Exportar MP4</button><button id="rs3dExportCancel" type="button" hidden>Cancelar exportação</button></form>';document.body.appendChild(dialog);q('rs3dExportStart').onclick=guard(exportVideo,'Exportar prévia 3D');q('rs3dExportCancel').onclick=()=>{if(exporting){exporting.cancelled=true;void cancelExport(exporting)}};dialog.addEventListener('cancel',e=>{if(exporting){e.preventDefault();q('rs3dExportCancel').click()}});dialog.addEventListener('close',()=>{if(exporting){exporting.cancelled=true;void cancelExport(exporting)}})}
 q('rs3dDuration').max=String(viewer.data.duration_s);q('rs3dDuration').value=String(Math.min(10,Math.floor(viewer.data.duration_s)));q('rs3dExportInfo').textContent='Prévia disponível: até '+viewer.data.duration_s+' s. A exportação é local e pode ser cancelada.';dialog.showModal();
}
async function exportVideo(){
 if(exporting||!viewer||stale||task)throw Error('Aguarde a tarefa atual ou reconstrua a cena.');
 const local=viewer,project=pid,duration=Number(q('rs3dDuration').value),width=Number(q('rs3dWidth').value),fps=Number(q('rs3dFps').value);
 if(!Number.isFinite(duration)||duration<3||duration>local.data.duration_s)throw Error('Duração inválida para esta prévia.');
 const session={cancelled:false,url:null,headers:null,id:null};exporting=session;sync();q('rs3dExportStart').disabled=true;q('rs3dExportCancel').hidden=false;let restore;
 try{
  const response=await api(`/api/projects/${project}/scene3d/capture`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:local.data.revision,width,fps,duration_s:duration,camera:local.cameraState()})});
  session.id=response.id;session.url=`/api/projects/${project}/scene3d/capture/${response.id}`;session.headers={'X-Rodovia-Capture':response.token};task=response.id;
  const check=()=>{if(session.cancelled||viewer!==local||pid!==project||local.lost||stale)throw Error('Exportação 3D cancelada ou cena alterada.')};
  for(;;){check();const state=await api(session.url,{headers:session.headers});if(state.ended)throw Error(state.job.message);if(state.ready)break;await new Promise(resolve=>setTimeout(resolve,200))}
  restore=local.captureSize(response.width,response.height);
  for(let i=0;i<response.frames;i++){check();local.setTime(i/response.fps);const blob=await local.png();check();await api(session.url+'/frame?index='+i,{method:'POST',headers:session.headers,body:blob});q('rs3dExportInfo').textContent=`Exportando quadro ${i+1} de ${response.frames}…`}
  check();const result=await api(session.url+'/finish',{method:'POST',headers:session.headers});q('rs3dExportInfo').textContent='Vídeo 3D conferido e guardado na pasta de vídeos. ';if(result.arquivo){const link=document.createElement('a');link.textContent='Baixar MP4';link.href=`/api/projects/${project}/videos/${encodeURIComponent(result.arquivo)}?baixar=1`;q('rs3dExportInfo').appendChild(link)}say('Vídeo 3D conferido e guardado.');
 }catch(e){if(session.url)await cancelExport(session);q('rs3dExportInfo').textContent=e.message;say(e.message,true)}
 finally{if(restore)restore();if(task===session.id)task=null;exporting=null;q('rs3dExportStart').disabled=false;q('rs3dExportCancel').hidden=true;sync()}
}
function init(){
 const viewport=document.createElement('div');viewport.id='rsViewport3D';viewport.hidden=true;canvas.parentElement.appendChild(viewport);
 const status=document.createElement('span');status.id='rs3dState';q('rsStudyFooter').appendChild(status);
 const controls=document.createElement('div');controls.id='rs3dControls';controls.hidden=true;controls.setAttribute('role','toolbar');controls.setAttribute('aria-label','Controles da cena 3D');
 const specs=[['play3d','Reproduzir tráfego','Reproduz a simulação validada.',()=>{if(stale)throw Error('Reconstrua a cena após alterar o projeto.');viewer?.play()}],['pause3d','Pausar tráfego','Pausa no tempo atual.',()=>viewer?.pause()],['scene3d','Seguir veículo','Acompanha um veículo da simulação validada.',()=>viewer?.follow()],['fit3d','Enquadrar 3D','Mostra o projeto em perspectiva.',()=>viewer?.fit()],['top3d','Planta 3D','Mostra o projeto de cima.',()=>viewer?.fit(true)],['light3d','Iluminação','Alterna dia, entardecer e noite; faróis dos trens acendem à noite.',()=>{if(!viewer)return;viewer.setLight(({dia:'entardecer',entardecer:'noite',noite:'dia'})[viewer.lightMode]||'dia');q('rs3dControls').querySelector('[data-rs3d=light3d]').innerHTML=RodoviaInfraRail.icon(viewer.lightMode==='noite'?'night-mode':'day-mode')}],['flows3d','Diagnósticos técnicos','Mostra ou oculta os fluxos de estudo; não saem na captura.',()=>viewer?.setDiagnostics(!viewer.technical.visible)],['rebuild3d','Reconstruir 3D','Atualiza a geometria e a simulação do projeto.',()=>open(true)],['png3d','Capturar imagem 3D','Salva a vista em PNG sem diagnósticos.',capture],['video3d','Exportar prévia 3D MP4','Gera vídeo local da câmera atual, sem fluxos técnicos.',exportDialog],['view2d','Voltar ao editor 2D','Retoma os comandos de edição.',close]];
 for(const spec of specs)controls.appendChild(button(...spec));
 const label=document.createElement('label');label.textContent='Tempo da prévia';const time=document.createElement('input');time.id='rs3dTime';time.type='range';time.min='0';time.max='60';time.step='.1';time.value='0';time.oninput=()=>{if(viewer&&!stale){viewer.pause();viewer.setTime(Number(time.value));q('rs3dState').textContent=`Prévia 3D · ${viewer.time.toFixed(1)} s`}};label.appendChild(time);controls.appendChild(label);q('rsTechnicalOptions').appendChild(controls);
 const mode=button('view3d','Vista 3D','Abre ou fecha o visualizador WebGL local.',()=>open());q('rsToolPanel0').querySelector('[data-rs-group="Navegação"]').prepend(mode);
 itemFaixa('Exibir','Vista 3D',["Vista 3D / editor 2D",'⬡',()=>open()]);buildRibbon();
 const originalTool=setTool;setTool=function(...args){if(active)close();return originalTool(...args)};
 const originalResize=resizeCanvas;resizeCanvas=function(...args){if(!active)return originalResize(...args)};
 const originalLoad=load;load=async function(id,...args){if((active||pending)&&id!==pid)close();return originalLoad(id,...args)};
 const originalChanged=changed;changed=function(...args){const result=originalChanged(...args);if(active&&viewer){stale=true;viewer.pause();say('Projeto alterado. Reconstrua a cena 3D para atualizar a visualização.');sync()}return result};
 window.addEventListener('rodovia:project-state',e=>{if(!active||!viewer||e.detail.project!==currentPid)return;const key=e.detail.revisions?.scene3d;if(key){stale=savePending||viewer.data.revision!==key;if(stale){viewer.pause();say('Cena 3D desatualizada. Reconstrua para usar os resultados atuais.')}else say('Cena 3D sincronizada com o projeto.');sync()}});
 sync();window.Rodovia3D=Object.freeze({open,close,stats:()=>viewer?{...viewer.stats(),stale,project:currentPid,context:state.context}:{ready:false,pending},setTime:t=>viewer?.setTime(t),setDiagnostics:b=>viewer?.setDiagnostics(b)});
}
queueMicrotask(init);
})();
