/* Uma entrada para distinguir circulação, simulação e enquadramento; nenhuma liberação cega. */
(()=>{'use strict';
const el=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e};
async function open(){
 requireProject();if(!await RodoviaPanels.close())return;await save();
 const project=pid,context=projectSession.context,d=el('dialog');d.className='winDlg rsTrafficHelp';d.setAttribute('aria-label','Diagnosticar veículos');d.append(el('h2','Por que os veículos não aparecem?'));
 const info=el('div'),error=el('p');error.setAttribute('role','alert');const row=el('div');row.className='row';d.append(info,error,row);document.body.append(d);
 const alive=()=>d.isConnected&&project===pid&&context===projectSession.context;
 let data=null,busy=false;
 async function read(){data=await api('/api/projects/'+project+'/traffic_status');if(!alive())return;info.replaceChildren(el('p','Veículos: '+(data.enabled?'ativados':'desativados')+' · itinerários válidos: '+(data.itineraries??'diagnóstico pendente')),
 el('p','Gerados na simulação: '+(data.simulated_vehicles??'ainda não medido')+' · ativos na prévia: '+(data.preview_active??'ainda não medido')+' · desenhados na prévia: '+(data.preview_drawn??'ainda não medido')));
 for(const note of data.notices)info.append(el('p',note));for(const s of data.segments.slice(0,12))info.append(el('p',(s.source||'Fluxo')+': '+s.technical_message));info.append(el('small',data.scope));focus.disabled=!data.editor_current||!data.itineraries}
 function button(text,fn){const b=el('button',text);b.type='button';b.onclick=guard(async()=>{if(busy)return;if(!alive())throw Error('O projeto mudou; reabra o diagnóstico.');busy=true;d.setAttribute('aria-busy','true');error.textContent='';try{await fn()}catch(e){if(d.isConnected)error.textContent=e.message;else msg(e.message,true)}finally{busy=false;d.setAttribute('aria-busy','false')}},text);row.append(b);return b}
 async function calculate(kind){busy=true;d.close();try{const result=await start(kind);if(!alive())return;if(!result||result.state!=='done')error.textContent=result?.error||result?.message||'A atualização não concluiu. Confira as orientações.';await read()}finally{busy=false;if(alive())d.showModal()}}
 button('Atualizar diagnóstico das rotas',()=>calculate('analyze'));
 const focus=button('Ativar veículos e gerar prévia de tráfego',async()=>{
  if(!data?.itineraries)return;const original=collect();
  $('traffic').checked=true;$('camera_mode').value='trafego';$('view_width_m').value='350';$('preview_mode').value='video';$('preview_time_s').value=String(Math.max(0,Math.min(Number($('duration_s').value)/2,5)));
  try{await save()}catch(e){fill(original);throw e}
  await calculate('preview');
 });
 button('Escolher eixo e configurar faixas',()=>{d.close();d.remove();return RodoviaSections.chooseAxis()});
 button('Corrigir problemas dos fluxos',()=>{d.close();d.remove();return RodoviaExecution.open()});
 button('Configuração do vídeo',()=>{d.close();d.remove();return psOpenHub('video')});
 const close=button('Fechar',()=>{d.close();d.remove()});d.oncancel=e=>{e.preventDefault();if(!busy)close.click()};d.showModal();try{await read()}catch(e){error.textContent=e.message}
}
window.RodoviaTrafficHelp=Object.freeze({open});comando(['DIAGNOSTICARVEICULOS'],open,'Confere rotas, simulação e enquadramento dos veículos');
queueMicrotask(()=>queueMicrotask(()=>{
 for(const title of ['Tráfego','Vídeo']){const panel=document.querySelector('[data-activity="'+title+'"]');if(!panel)continue;const b=el('button','Diagnosticar veículos');b.type='button';b.title='Conferir por que não há veículos e gerar uma prévia em detalhe';b.onclick=guard(open);panel.prepend(b)}
 // A câmera é um campo de câmera, mesmo quando vinha do perfil de aparência antigo.
 const camera=$('rsVideoPane_camera')?.querySelector('.rsVideoFields');if(camera&&$('camera_mode'))camera.prepend($('camera_mode').closest('label'));
}));
})();
