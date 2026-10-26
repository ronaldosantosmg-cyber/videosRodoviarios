// Confirmações opcionais; abrir, salvar projeto e exportar sempre atualizam o modelo.
(()=>{'use strict';
let mode='manual',timer=null,waiting=null,suppress=0;
try{mode=localStorage.getItem('rodovia_update_mode')==='automatic'?'automatic':'manual'}catch{}
const current=(project,context)=>pid===project&&projectSession.context===context;
function cancelWaiting(){clearTimeout(timer);timer=null;waiting=null}
async function hasInputs(project){const data=await api('/api/projects/'+project);return !!(data.files?.dxf||data.files?.kmz||data.config?.route_alignments?.some(r=>r.enabled&&r.points?.length>1)||data.config?.custom_axis?.points?.length>1)}
async function refresh(reason='Atualizar',automatic=false){
 requireProject();const project=pid,context=projectSession.context;cancelWaiting();
 suppress++;let resolved;try{resolved=!window.RodoviaPanels||await RodoviaPanels.close()}finally{suppress--}
 if(!resolved||!current(project,context))return false;
 if(!await hasInputs(project)){if(current(project,context))msg('Dados preservados. Importe DXF/KMZ ou cadastre um eixo para calcular o projeto.');return {state:'no_input'}}
 if(!current(project,context))return false;
 if(automatic&&window.RodoviaPanels?.opened)return false;
 if(window.Rodovia3D?.stats().ready)return Rodovia3D.open(true,{policyAuto:automatic});
 return start('refresh',undefined,{policy:true,policyAuto:automatic});
}
function defer(project,context,automatic=true){
 clearTimeout(timer);waiting={project,context,automatic};
 const run=()=>{const item=waiting;if(!item)return;if(!current(item.project,item.context)||item.automatic&&mode!=='automatic'){cancelWaiting();return}
  if(suppress||fileMutationPending||task||taskRequestPending||window.RodoviaPanels?.opened){timer=setTimeout(run,200);return}
  waiting=null;timer=null;void refresh(item.automatic?'Confirmação de formulário':'Abertura do projeto',item.automatic).catch(e=>msg('Dados preservados. Atualização não concluída: '+e.message,true));
 };timer=setTimeout(run,350);
}
function committed(detail={}){if(suppress)return;const project=detail.project||pid,context=detail.context??projectSession.context;if(!project||!current(project,context))return;window.dispatchEvent(new CustomEvent('rodovia:update-state'));if(mode==='automatic')defer(project,context,true)}
function setMode(value){mode=value==='automatic'?'automatic':'manual';try{localStorage.setItem('rodovia_update_mode',mode)}catch{}if(mode==='manual'&&waiting?.automatic)cancelWaiting();if($('rsUpdateMode'))$('rsUpdateMode').value=mode;msg(mode==='automatic'?'Automático: confirmar um formulário inicia a atualização completa.':'Manual: confirmações deixam atualização pendente. Abrir, Salvar projeto, Prévia e Vídeo sempre recalculam.')}
async function saveProject(){requireProject();const project=pid,context=projectSession.context;cancelWaiting();suppress++;try{if(window.RodoviaPanels&&!await RodoviaPanels.close())return false;await save()}finally{suppress--}let result;try{result=await refresh('Salvar projeto')}catch(error){throw Error('Projeto salvo. Atualização não concluída: '+error.message)}if(!current(project,context))return false;if(result!==false)msg(result?.state==='no_input'?'Projeto salvo; importe os arquivos para calcular.':'Projeto salvo e atualizado.');return result}
async function saveAs(){requireProject();cancelWaiting();const project=pid,context=projectSession.context;let held=true;suppress++;try{
 if(window.RodoviaPanels&&!await RodoviaPanels.close())return false;
 await save();if(task||taskRequestPending||fileMutationPending)throw Error('Aguarde ou cancele o processamento antes de Salvar como.');
 const name=await inputBox('Salvar como','Nome da cópia do projeto:',((cfg.name||'Projeto')+' (cópia)').slice(0,80));if(!name||!current(project,context))return false;
 const result=await api('/api/projects/'+project+'/save_as',json('POST',{name}));await list();suppress--;held=false;await load(result.id);return true;
 }finally{if(held)suppress--}}
window.RodoviaUpdatePolicy=Object.freeze({refresh,committed,setMode,saveProject,saveAs,consumePending:cancelWaiting,snapshot:()=>({mode,waiting:!!waiting})});
window.addEventListener('rodovia:form-committed',e=>committed(e.detail));
const originalLoad=load;load=async function(id,options={}){const value=await originalLoad(id,options);if(value===false||pid!==id||options.resultsOnly)return value;const context=projectSession.context;
 let resume=false;try{const jid=localStorage.getItem('rodovia_job');if(jid){const job=await api('/api/jobs/'+jid);resume=job.project===id&&['queued','running','cancel_requested'].includes(job.state)}}catch{}
 if(resume||task||taskRequestPending||fileMutationPending||window.RodoviaPanels?.opened){defer(id,context,false);return value}
 await refresh('Abrir projeto');return value;
};
queueMicrotask(()=>queueMicrotask(()=>{
 const label=document.createElement('label');label.className='rsUpdateModeChoice';label.innerHTML='Atualização <select id="rsUpdateMode" aria-label="Modo de atualização"><option value="manual">Manual</option><option value="automatic">Automático</option></select>';
 label.title='Automático recalcula ao confirmar formulários. Abrir/reabrir, Salvar projeto, Salvar como, Prévia e Vídeo sempre atualizam o modelo.';
 $('rsUpdateProject').after(label);$('rsUpdateMode').value=mode;$('rsUpdateMode').title=label.title;$('rsUpdateMode').setAttribute('aria-description',label.title);$('rsUpdateMode').onchange=e=>setMode(e.target.value);
 for(const [id,fn] of [['saveProject',saveProject],['save',saveProject],['saveAsProject',saveAs]]){const old=$(id);if(!old)continue;const button=old.cloneNode(true);old.replaceWith(button);button.onclick=guard(fn,id==='saveAsProject'?'Salvar como':'Salvar projeto')}
}));
})();
