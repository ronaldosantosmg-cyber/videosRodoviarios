// Resultados anteriores permanecem utilizáveis; salvar não inicia cálculos.
(()=>{'use strict';
window.addEventListener('rodovia:project-state',e=>{if(e.detail.project!==pid)return;const status=e.detail.artifacts?.editor?.state;if(window.RodoviaFlowStudy){const stale=savePending||status!=='ready';if(RodoviaFlowStudy.stale!==stale){RodoviaFlowStudy.stale=stale;draw()}}window.dispatchEvent(new CustomEvent('rodovia:update-state'))});
})();
