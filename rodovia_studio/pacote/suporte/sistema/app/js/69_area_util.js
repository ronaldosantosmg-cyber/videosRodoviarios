// Mesmos controles e eventos; faixa única e painéis laterais recolhíveis.
(()=>{'use strict';
function init(){
 document.body.classList.add('rsCompactWorkspace');
 const ribbon=$('rsToolRibbon'),options=$('rsTechnicalOptions');if(ribbon&&options)ribbon.appendChild(options);
 const nav=$('atividades');if(!nav||$('rsSidebarToggle'))return;
 const toggle=document.createElement('button');toggle.type='button';toggle.id='rsSidebarToggle';toggle.title='Recolher / expandir os painéis laterais';toggle.setAttribute('aria-label',toggle.title);toggle.textContent='❮';
 toggle.onclick=()=>{const small=document.body.classList.toggle('rsSidebarCollapsed');toggle.textContent=small?'❯':'❮';toggle.setAttribute('aria-expanded',String(!small));requestAnimationFrame(()=>resizeCanvas())};toggle.setAttribute('aria-expanded','true');nav.prepend(toggle);
}
const previous=psSyncActivities;psSyncActivities=function(...args){const result=previous(...args);init();return result};
queueMicrotask(()=>queueMicrotask(init));
})();
