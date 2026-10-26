/* Proposta local/online revisável: nenhuma resposta executa código. */
(()=>{'use strict';
const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n};
async function open(phase='general',segment=null){
 requireProject();if(!await RodoviaPanels.close())return;await save();
 const project=pid,context=projectSession.context,d=el('dialog');d.className='winDlg rsSmallAI';d.setAttribute('aria-label','IA local 3B e mini prompts');
 d.append(el('h2','IA local 3B e mini prompts'));
 const state=el('p','Conferindo disponibilidade…'),choice=el('select'),provider=el('select'),taskInput=el('textarea'),preview=el('pre'),output=el('section'),actions=el('div');
 choice.setAttribute('aria-label','Etapa da assistência');provider.setAttribute('aria-label','Provedor IA');taskInput.setAttribute('aria-label','Pedido para a IA');taskInput.maxLength=500;taskInput.rows=3;taskInput.placeholder='Descreva o problema ou a melhoria desejada. A proposta será conferida pelo motor antes de aplicar.';
 for(const [key,label] of [['general','Diagnóstico geral'],['files','Arquivos'],['flow','Fluxo selecionado'],['chainage','Esquerda/direita e estaqueamento'],['textures','Texturas'],['video','Apresentação do vídeo']])choice.append(new Option(label,key));choice.value=phase;
 provider.append(new Option('Modelo local 3B','local'),new Option('API online opcional','online'));
 const prepare=el('button','Preparar mini prompt'),run=el('button','Consultar IA'),cancel=el('button','Cancelar consulta'),close=el('button','Fechar');for(const b of [prepare,run,cancel,close])b.type='button';run.disabled=true;cancel.hidden=true;
 const layersInput=el('textarea');layersInput.rows=2;layersInput.maxLength=2400;layersInput.setAttribute('aria-label','Camadas para consultar');layersInput.placeholder='Até 8 nomes de layers, um por linha. Em branco: até 3 camadas por consulta.';layersInput.value=dxfSel?.layer||'';layersInput.hidden=phase!=='textures';
 const agree=el('label'),checkbox=el('input');checkbox.type='checkbox';agree.append(checkbox,document.createTextNode(' Autorizo enviar somente o mini prompt exibido à API online configurada.'));agree.hidden=true;
 const previewBox=el('details');previewBox.append(el('summary','Conferir mini prompt e dados compartilhados'),preview);
 preview.className='rsMiniPrompt';preview.setAttribute('aria-label','Mini prompt que será enviado');actions.className='row';actions.append(prepare,run,cancel,close);d.append(state,choice,provider,taskInput,layersInput,agree,previewBox,output,actions);document.body.append(d);d.showModal();
 let prompt=null,busy=false,capabilities=null,cancelled=false;
 const alive=()=>pid===project&&projectSession.context===context&&d.isConnected;
 function reset(){prompt=null;run.disabled=true;checkbox.checked=false;preview.textContent='Prepare um novo mini prompt após alterar o pedido ou a etapa.';output.replaceChildren()}
 taskInput.oninput=reset;layersInput.oninput=reset;choice.onchange=()=>{layersInput.hidden=choice.value!=='textures';reset()};provider.onchange=()=>{agree.hidden=provider.value!=='online';checkbox.checked=false};
 const guarded=fn=>guard(async()=>{if(!alive())throw Error('O projeto mudou. Reabra a assistência.');return fn()});
 prepare.onclick=guarded(async()=>{if(busy)return;prompt=await api('/api/projects/'+project+'/assistencia/mini_prompt',json('POST',{phase:choice.value,task:taskInput.value,segment:segment??selSeg?.id??null,layers:choice.value==='textures'?layersInput.value.split('\n').map(s=>s.trim()).filter(Boolean):[]}));if(!alive())return;preview.textContent=JSON.stringify(prompt.messages,null,2);output.replaceChildren(el('p',prompt.notice));run.disabled=false});
 cancel.onclick=guarded(async()=>{cancelled=true;await api('/api/projects/'+project+'/assistencia/modelo/cancelar',json('POST',{}));state.textContent='Cancelamento solicitado; aguardando encerramento do provedor.'});
 function finish(){if(busy){state.textContent='Cancele a consulta e aguarde o encerramento antes de fechar.';return}d.close();d.remove()}
 close.onclick=finish;d.oncancel=e=>{e.preventDefault();finish()};
 run.onclick=guarded(async()=>{if(!prompt||busy)return;if(provider.value==='online'&&!checkbox.checked)throw Error('Revise o mini prompt e marque a autorização de envio online.');
  if(provider.value==='local'&&!capabilities?.installed){state.textContent='Pacote do modelo ainda não instalado. A integração está disponível, mas não há inferência local habilitada.';return}
  busy=true;cancelled=false;run.disabled=prepare.disabled=provider.disabled=choice.disabled=taskInput.disabled=layersInput.disabled=checkbox.disabled=true;cancel.hidden=false;const progress='mini:'+project+Date.now();
  progMostrar({id:progress,titulo:'Consultando IA '+(provider.value==='local'?'local 3B':'online'),valor:null,info:'Preparando proposta. Nenhuma alteração aplicada.',cancelar:()=>cancel.click()});
  try{const result=await api('/api/projects/'+project+'/assistencia/modelo',json('POST',{prompt_id:prompt.prompt_id,provider:provider.value,consent_online:provider.value==='online'&&checkbox.checked}));if(!alive()){progFim(progress,'Resultado descartado: projeto alterado.');return}
   output.replaceChildren(el('h3',result.reply.summary));const list=el('ol');for(const step of result.reply.steps)list.append(el('li',step));output.append(list,el('p',result.notice));
   const review=el('button','Revisar nas ferramentas do motor');review.type='button';review.onclick=guarded(async()=>{d.close();d.remove();const action=result.reply.action;
    if(action==='flow_repair')return RodoviaExecution.open({segment:result.query.segment});
    if(action==='textures'&&result.review.layers.length)return RodoviaIA.accept(result.review);
    if(action==='textures')return RodoviaMaterialsHub.open();
    if(action==='video')return psOpenHub('video');
    if(action==='files')return RodoviaProtection.open();
    if(action==='chainage')return openSection('2. Configuração');
    return RodoviaIA.open('logs');
   });output.append(review);state.textContent='Proposta pronta em '+result.seconds+' s. Confirme e revalide na ferramenta correspondente.';progFim(progress,'Proposta disponível; consulta encerrada.');
  }catch(e){if(alive())state.textContent=e.message;progFim(progress,cancelled?'Consulta cancelada; nada aplicado.':'Consulta interrompida ou recusada; nada aplicado.',!cancelled)}
  finally{busy=false;cancel.hidden=true;run.disabled=prepare.disabled=provider.disabled=choice.disabled=taskInput.disabled=layersInput.disabled=checkbox.disabled=false}
 });
 try{capabilities=await api('/api/assistencia/modelo');if(alive()){state.textContent=capabilities.message+' Pasta: '+capabilities.folder+(capabilities.online_host?' API online: '+capabilities.online_host:'');provider.options[1].disabled=!capabilities.online_configured;provider.options[1].textContent=capabilities.online_configured?'API online: '+capabilities.online_host:'API online (configuração pendente)'}}catch(e){if(alive())state.textContent=e.message}
}
window.RodoviaSmallAI=Object.freeze({open});
comando(['IA3B'],()=>open(),'Mini prompts revisáveis com modelo local 3B ou API opcional');
queueMicrotask(()=>queueMicrotask(()=>{const panel=document.querySelector('[data-activity="Projeto"]');if(panel){const b=el('button','IA local 3B');b.type='button';b.title='Conferir modelo, preparar mini prompts e revisar propostas';b.onclick=guard(()=>open());panel.append(b)}}));
})();
