/* Diagnóstico visual separado da apresentação; campos originais, sem cópias. */
(()=>{'use strict';
const element=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e};
const point=p=>Array.isArray(p)&&p.length===2&&p.every(v=>typeof v==='number'&&Number.isFinite(v)&&Math.abs(v)<=1e9);
let overlay=null,frame=0;const nodes=new Map();
function locate(issue){setTool('pan');vecOn.flows=true;selSeg={id:issue.segment};zoomTo(P(issue.point));draw()}
function showIssue(issue){
 const d=element('dialog');d.className='winDlg rsFlowIssue';d.setAttribute('aria-label','Como corrigir este fluxo');
 d.append(element('h2','Como corrigir este fluxo'),element('p',issue.message),element('p',issue.exact?'Ponto informado pelo motor.':'Referência do trecho; o motor não informou a posição exata do defeito.'));
 const segment=(editor?.segments||[]).find(s=>s.id===issue.segment),guide=segment?.technical_assistant;
 if(guide){d.append(element('h3',guide.title));const list=element('ol');for(const step of guide.steps||[])list.append(element('li',step.instruction));d.append(list)}
 if(window.RodoviaFlowStudy?.stale)d.append(element('p','Diagnóstico anterior: há alterações pendentes. Atualize os fluxos antes de considerar o problema resolvido.'));
 const context=projectSession.context,project=pid,revision=editor?.engine_revision;
 const row=element('div');row.className='row';
 for(const [label,fn] of [['Localizar no desenho',()=>locate(issue)],['Analisar correção com IA',()=>window.RodoviaExecution.open({segment:issue.segment})],['Editar trecho',()=>{selSeg={id:issue.segment};showSegProps()}]]){
  const b=element('button',label);b.type='button';b.onclick=guard(async()=>{if(project!==pid||context!==projectSession.context||revision!==editor?.engine_revision)throw Error('O diagnóstico mudou. Localize novamente o problema atualizado.');d.close();d.remove();if(await RodoviaPanels.close())await fn()},label);row.append(b)
 }
 const close=element('button','Fechar');close.type='button';close.onclick=()=>{d.close();d.remove()};row.append(close);d.append(row);d.oncancel=e=>{e.preventDefault();close.click()};document.body.append(d);d.showModal();
}
function sync(){
 frame=0;const host=canvas.closest('.canvasWrap');if(!host)return;
 if(!overlay){overlay=element('div');overlay.id='rsFlowProblemOverlay';overlay.setAttribute('aria-label','Pontos de problemas do estudo técnico; não aparecem no vídeo');host.append(overlay)}
 const rect=canvas.getBoundingClientRect(),parent=host.getBoundingClientRect();
 const active=!!pid&&ready()&&vecOn.flows!==false&&!canvas.hidden&&rect.width>0&&rect.height>0;
 overlay.hidden=!active;if(!active){nodes.clear();overlay.replaceChildren();return}
 const visible=new Set();let count=0;
 function add(issue){if(count>=200||!point(issue.point))return;const p=W2C(P(issue.point));if(!p.every(Number.isFinite))return;const x=p[0]*rect.width/canvas.width+rect.left-parent.left,y=p[1]*rect.height/canvas.height+rect.top-parent.top;
  if(x<0||y<0||x>parent.width||y>parent.height)return;
  const key=JSON.stringify([pid,projectSession.context,editor?.engine_revision,issue.segment,issue.point]);if(visible.has(key))return;visible.add(key);count++;
  let b=nodes.get(key);if(!b){b=element('button');b.type='button';b.className='rsFlowProblemPoint';b.dataset.segment=String(issue.segment);nodes.set(key,b);overlay.append(b)}
  b.title=(issue.exact?'Problema do fluxo: ':'Referência do fluxo: ')+issue.message+' · Clique para orientação';b.setAttribute('aria-label',b.title);b.style.left=x+'px';b.style.top=y+'px';b.onclick=()=>showIssue(issue);
 }
 for(const segment of (editor?.segments||[]).slice(0,10000)){
  if(segment.technical_status==='ok'||segment.disabled||segment.technical_exclusion==='length_limit')continue;
  const points=(segment.technical_points||[]).filter(p=>point(p.point));
  for(const p of points)add({segment:segment.id,point:p.point,message:segment.technical_message||p.reason||'Confira o diagnóstico do fluxo.',exact:true});
  if(!points.length&&point(segment.mid))add({segment:segment.id,point:segment.mid,message:segment.technical_message||'Confira a continuidade deste trecho.',exact:false});
  if(count>=200)break;
 }
 const conflict=window.RodoviaFlowEditConflict;
 if(conflict&&conflict.project===pid&&conflict.revision===editor?.engine_revision){const p=Array.isArray(conflict.point)?conflict.point:[conflict.point?.x,conflict.point?.y];add({segment:selSeg?.id,point:p,message:'Ligação ou edição recusada. Confira sentido, nível e geometria; a rota válida deve ser preservada.',exact:true})}
 for(const [key,node] of nodes)if(!visible.has(key)){node.remove();nodes.delete(key)}
}
function schedule(){if(!frame)frame=requestAnimationFrame(sync)}
const oldDraw=draw;draw=function(...args){const r=oldDraw(...args);schedule();return r};
window.addEventListener('rodovia:project-state',schedule);window.addEventListener('resize',schedule);
window.RodoviaFlowMarkers=Object.freeze({sync:schedule,get count(){return nodes.size}});

function organizeVideo(){
 const section=pnItens.find(i=>/Exportar vídeo/i.test(i.t))?.el;if(!section||section.dataset.videoOrganized)return;section.dataset.videoOrganized='true';section.classList.add('rsVideoSettings');
 const definitions=[['saida','Exportação','Resolução, duração e qualidade do arquivo.'],['camera','Câmera','Enquadramento, pontos-chave e vista da cabine.'],['traffic','Veículos e fluxo','Demanda, velocidade e comportamento. A seção típica define as faixas.'],['look','Aparência','Iluminação, água, sinalização e materiais de apresentação.'],['advanced','Avançado','Mosaico, encoder, paralelismo e comparação de resultados.']];
 const nav=element('nav');nav.className='rsVideoTabs';nav.setAttribute('role','tablist');nav.setAttribute('aria-label','Configuração do vídeo');const panes=new Map(),buttons=[];
 for(const [id,title,hint] of definitions){const panel=element('div');panel.id='rsVideoPane_'+id;panel.className='rsVideoPane';panel.setAttribute('role','tabpanel');panel.setAttribute('aria-label',title);panel.append(element('p',hint));const grid=element('div');grid.className='rsVideoFields';panel.append(grid);panes.set(id,{panel,grid});const b=element('button',title);b.type='button';b.id='rsVideoTab_'+id;b.setAttribute('role','tab');b.setAttribute('aria-controls',panel.id);panel.setAttribute('aria-labelledby',b.id);b.onclick=()=>activate(id);buttons.push(b);nav.append(b)}
 function activate(id,focus=false){for(const [key,{panel}] of panes)panel.hidden=key!==id;for(const b of buttons){const on=b.id==='rsVideoTab_'+id;b.setAttribute('aria-selected',String(on));b.tabIndex=on?0:-1;if(on&&focus)b.focus()}}
 nav.onkeydown=e=>{const i=buttons.indexOf(document.activeElement);if(i<0)return;let n=i;if(e.key==='ArrowRight')n=(i+1)%buttons.length;else if(e.key==='ArrowLeft')n=(i+buttons.length-1)%buttons.length;else if(e.key==='Home')n=0;else if(e.key==='End')n=buttons.length-1;else return;e.preventDefault();activate(definitions[n][0],true)};
 const put=(id,node)=>panes.get(id).grid.append(node);
 for(const d of [...section.querySelectorAll('details')].filter(d=>!d.parentElement.closest('details'))){let id='look';if(d.id==='ambienteBox'||d.querySelector('#cabinEnabled'))id='camera';else if(d.querySelector('#traffic_density'))id='traffic';else if(d.classList.contains('retirada'))id='advanced';d.open=id==='traffic';put(id,d)}
 const basic=new Set(['width','fps','duration_s','video_quality','render_profile']),camera=new Set(['view_width_m','short_video_mode']),traffic=new Set(['traffic','traffic_speed_kmh']);
 for(const control of [...section.querySelectorAll('input,select,textarea')]){
  if(control.closest('details')||control.closest('.rsVideoPane'))continue;
  const label=control.closest('label');if(!label)continue;
  const id=basic.has(control.id)?'saida':camera.has(control.id)?'camera':traffic.has(control.id)?'traffic':['encoder','cpu_preset','imagery_pixels','render_workers'].includes(control.id)?'advanced':'look';put(id,label);
 }
 const heading=section.querySelector(':scope>h2'),render=$('render');
 for(const child of [...section.children]){if(child===heading||child===render)continue;if(child.matches('p')||child.querySelector('input,select,textarea,button,[id]'))put('advanced',child);else child.remove()}
 section.append(nav,...[...panes.values()].map(p=>p.panel));
 if(render){const row=element('div');row.className='rsVideoGenerate';row.append(element('span','Salvar e fechar confirma as configurações. Gerar vídeo usa os valores confirmados.'),render);section.append(row)}
 activate('saida');
}
queueMicrotask(()=>queueMicrotask(()=>{organizeVideo();schedule()}));
})();
