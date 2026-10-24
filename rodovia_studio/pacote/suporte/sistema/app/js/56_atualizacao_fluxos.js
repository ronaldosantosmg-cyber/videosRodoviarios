// Recalcula somente o editor, uma tentativa por revisão; nunca inicia vídeo sozinho.
(()=>{'use strict';const attempted=new Set();let timer=null;
function schedule(info){const id=info.project,key=info.revisions?.editor||info.config_revision||id;
 if(id!==pid||!analysis||editor||task||savePending||attempted.has(key))return;
 clearTimeout(timer);timer=setTimeout(guard(async()=>{if(pid!==id||task||savePending||editor)return;attempted.add(key);msg('Atualizando automaticamente os fluxos para a revisão atual…');await start('analyze')}),300);
}
window.addEventListener('rodovia:project-state',e=>{const info=e.detail;if(info.project!==pid)return;if(window.RodoviaFlowStudy&&info.artifacts?.editor?.state==='ready')RodoviaFlowStudy.stale=savePending;const status=info.artifacts?.editor?.state;if(['stale','failed','processing'].includes(status))editor=null;schedule(info)});
const previous=load;load=async function(id,...args){const r=await previous(id,...args);if(r!==false&&pid===id)schedule({project:id,config_revision:projectSession.revision});return r};
})();
