/* Organiza os controles existentes; abrir/navegar na aba não inicia tarefas. */
(()=>{'use strict';
let organized=null,replaying=false,restoringSession=false;
function undoLayout(){if(!organized)return;for(const [node,mark] of organized.moves.reverse())if(mark.parentNode)mark.replaceWith(node);organized.first.hidden=organized.firstHidden;organized.grid.remove();organized=null}
function organize(){const section=$('secVista');if(!section||organized?.section===section)return;if(organized)undoLayout();
 const first=section.querySelector(':scope>.row:not(.timeline):not(.baseRow):not(.sessRow)');if(!first)return;
 const grid=document.createElement('div');grid.className='rsVistaGroups';const moves=[];organized={section,first,firstHidden:first.hidden,grid,moves};section.append(grid);
 const group=(name,id)=>{const f=document.createElement('fieldset');f.id=id;const legend=document.createElement('legend');legend.textContent=name;f.append(legend);grid.append(f);const row=document.createElement('div');row.className='row';f.append(row);return {f,row}};
 const move=(node,target)=>{if(!node)return;const mark=document.createComment('vista:'+node.id);node.before(mark);moves.push([node,mark]);target.append(node)};
 const nav=group('Navegação e enquadramento','rsVistaNavigation');for(const id of ['fitView','fullscreen','areaMaxBtn','toggleSide'])move($(id),nav.row);
 const preview=group('Prévia e instante','rsVistaPreview');const mode=document.createElement('label');mode.textContent='Enquadramento da prévia';preview.row.append(mode);move($('preview_mode'),mode);$('preview_mode').setAttribute('aria-label','Enquadramento da prévia');
 for(const id of ['preview','renderView'])move($(id),preview.row);move(section.querySelector('.timeline'),preview.f);
 const layers=group('Fundo e camadas da edição','rsVistaBackground');move(section.querySelector('.baseRow'),layers.f);layers.row.remove();
 const sessions=group('Sessões de trabalho','rsVistaSessions');move(section.querySelector('.sessRow'),sessions.f);sessions.row.remove();$('sessList').dataset.rsTransient='';
 const hint=document.createElement('p');hint.className='muted';hint.textContent='Uma sessão guarda vista, ferramenta e visibilidade. Não substitui Salvar projeto.';sessions.f.append(hint);
 const advanced=document.createElement('details');advanced.className='rsVistaAdvanced';advanced.innerHTML='<summary>Avançado: regeneração e fluxos</summary>';const extra=document.createElement('div');extra.className='row';advanced.append(extra);grid.append(advanced);for(const id of ['regenPreview','updFlows'])move($(id),extra);
 const names={fitView:'Enquadrar',preview:'Gerar prévia',renderView:'Detalhar vista atual',openAtTime:'Prévia neste instante',sessLoad:'Restaurar sessão',sessDel:'Apagar sessão'};
 for(const [id,label] of Object.entries(names))if($(id)){$(id).textContent=label;$(id).setAttribute('aria-label',label)}
 first.hidden=true;
 if(!section.dataset.rsSessionGuard){section.dataset.rsSessionGuard='1';section.addEventListener('click',e=>{const b=e.target.closest('#sessLoad');if(!b||replaying)return;e.preventDefault();e.stopImmediatePropagation();if(restoringSession)return;restoringSession=true;const project=pid,context=projectSession.context;
 void (async()=>{try{if(!await RodoviaPanels.close())return;if(pid!==project||projectSession.context!==context)throw Error('O projeto mudou. Escolha a sessão novamente.');replaying=true;try{b.click()}finally{replaying=false}}catch(error){msg(error.message,true)}finally{restoringSession=false}})();},true)}
}
function capture(){return {baseMode,tileAlpha,vecAlpha,vecOn:{...vecOn},sessionAuto:!!$('sessAuto')?.checked}}
function restore(s){baseMode=s.baseMode;tileAlpha=s.tileAlpha;vecAlpha=s.vecAlpha;Object.assign(vecOn,s.vecOn);if($('sessAuto'))$('sessAuto').checked=s.sessionAuto;try{localStorage.setItem('rodovia_sessauto',s.sessionAuto?'1':'0')}catch{}saveBasePrefs();baseUi();draw()}
const enter=pnEntrar,leave=pnSair;pnEntrar=function(...a){const r=enter(...a);organize();return r};pnSair=function(...a){undoLayout();return leave(...a)};
window.RodoviaViewPanel=Object.freeze({organize,capture,restore});queueMicrotask(()=>queueMicrotask(organize));
})();
