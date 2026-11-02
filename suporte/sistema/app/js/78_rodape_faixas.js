// Mesmos comandos e coordenadas CRS, com uma única linha de estado.
(()=>{'use strict';
let frame=0,point=null;
const before=statusBar;statusBar=function(){before();const spans=$('statusBar')?.children;if(!spans?.length)return;
 spans[0].title='Comando ativo · Enter conclui · Esc cancela';spans[0].classList.add('rsStatusCommand');
 spans[1].hidden=spans[1].textContent==='nada selecionado';
 const coordinate=spans[4],w=lastWorld;coordinate.id='rsLiveCoordinates';coordinate.textContent=w&&Number.isFinite(w.x)&&Number.isFinite(w.y)?`X ${w.x.toFixed(3)} · Y ${w.y.toFixed(3)}`:'';
 coordinate.title=$('cursor')?.textContent||'';coordinate.tabIndex=0;coordinate.setAttribute('aria-label',coordinate.title||'Coordenadas do projeto');
 for(let i=5;i<spans.length;i++)spans[i].hidden=true;
 $('statusBar').title=[$('saveState')?.textContent,'Versão '+(window.APP_VERSION||'')].filter(Boolean).join(' · ');
};
window.addEventListener('pointermove',e=>{if(e.target!==canvas||!ready())return;point={clientX:e.clientX,clientY:e.clientY};if(frame)return;frame=requestAnimationFrame(()=>{frame=0;const c=canvasPt(point);if(!c.w||!Number.isFinite(c.w.x)||!Number.isFinite(c.w.y))return;lastWorld=c.w;cursorInfo(c.w);statusBar()})},{capture:true,passive:true});
function init(){
 const bar=$('bottomBar');if(!bar||$('rsStatusActions'))return;document.body.classList.add('rsFooter24');
 const actions=document.createElement('div');actions.id='rsStatusActions';bar.appendChild(actions);
 for(const el of [$('rsUpdateProject'),document.querySelector('.rsUpdateModeChoice'),$('rsUpdateState')])if(el)actions.appendChild(el);
 if($('progCard'))bar.appendChild($('progCard'));
 for(const d of document.querySelectorAll('.rsConsolidatedPanel>.rsAdvancedTools')){
  if(d.closest('[data-activity="Vídeo"]')&&!d.querySelector('button')){
   for(const [name,fn] of [['Vídeos gerados',openVideos],['Registros da exportação',()=>openLogs('execucao')],['Prompt de reprodução',promptIA]]){const b=document.createElement('button');b.type='button';b.textContent=name;b.onclick=guard(fn,name);d.appendChild(b)}
  }
  d.classList.add(d.contains($('rsTechnicalOptions'))?'rsPresentationExpansion':'rsInlineExpansion');
  const body=document.createElement('div');body.className='rsExpandedTools';for(const child of [...d.children])if(child.tagName!=='SUMMARY')body.appendChild(child);d.appendChild(body);
  const close=document.createElement('button');close.type='button';close.className='rsRetractTools';close.textContent='‹';close.title='Recolher ferramentas';close.setAttribute('aria-label','Recolher ferramentas');close.onclick=()=>{d.open=false;d.querySelector('summary').focus();requestAnimationFrame(scheduleCanvasResize)};body.appendChild(close);
  d.addEventListener('toggle',()=>{d.querySelector('summary').setAttribute('aria-expanded',String(d.open));requestAnimationFrame(scheduleCanvasResize)});
 }
 statusBar();requestAnimationFrame(scheduleCanvasResize);
}
queueMicrotask(()=>queueMicrotask(init));
})();
