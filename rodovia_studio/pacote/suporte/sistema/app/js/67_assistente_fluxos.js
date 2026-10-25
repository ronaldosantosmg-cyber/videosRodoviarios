// Sistema especialista local: só ações de navegação e cálculo explicitamente solicitadas.
(()=>{'use strict';
const previous=showSegProps;
showSegProps=function(...args){const result=previous(...args),seg=segById(selSeg?.id),guide=seg?.technical_assistant;
 if(!seg||!guide||seg.technical_status==='ok'||$('propPanel').hidden)return result;
 const details=document.createElement('details');details.className='rsFlowAssistant';details.dataset.flowAssistant=String(seg.id);
 const summary=document.createElement('summary');summary.textContent='Como corrigir este fluxo · assistente local';details.appendChild(summary);
 const title=document.createElement('h4');title.textContent=guide.title;details.appendChild(title);
 const list=document.createElement('ol');
 for(const step of Array.isArray(guide.steps)?guide.steps:[]){if(!step||typeof step!=='object')continue;const item=document.createElement('li'),text=document.createElement('p');text.textContent=step.instruction||'';item.appendChild(text);
  const why=document.createElement('small');why.textContent=step.why;item.appendChild(why);
  const action={layers:['Abrir camadas',()=>psOpenHub('layers')],recalculate:['Recalcular fluxos',()=>start('analyze')],locate:['Localizar ponto',async()=>{const p=guide.point;if(!Array.isArray(p)||p.length!==2||!p.every(Number.isFinite))throw Error('Recalcule para localizar o ponto.');if(await RodoviaPanels.close()){setTool('pan');zoomTo({x:p[0],y:p[1]});draw()}}]}[step.action];
  if(action){const button=document.createElement('button');button.type='button';button.textContent=action[0];button.dataset.assistantAction=step.action;button.onclick=guard(action[1]);if(step.action==='locate'&&!guide.point)button.disabled=true;item.appendChild(button)}list.appendChild(item)
 }details.appendChild(list);const note=document.createElement('p');note.className='muted';note.textContent=guide.limitations;details.appendChild(note);$('propPanel').appendChild(details);return result;
};
})();
