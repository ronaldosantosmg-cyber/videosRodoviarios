/* Proposta local/online revisável: nenhuma resposta executa código. */
(()=>{'use strict';
const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n};
async function connect(updated=async()=>{}){
 const capabilities=await api('/api/assistencia/modelo'),d=el('dialog');d.className='winDlg rsOnlineConnection';d.setAttribute('aria-label','Conectar API online');
 d.append(el('h2','Conectar API online'),el('p','Informe sua chave aqui. Ela fica somente na memória desta sessão, fora dos projetos e logs. Planos, cobrança e limites são definidos pelo provedor.'));
 const provider=el('select'),model=el('input'),key=el('input'),links=el('div'),status=el('p');
 provider.setAttribute('aria-label','Serviço de IA');model.setAttribute('aria-label','Modelo da API');model.maxLength=160;model.placeholder='Identificador do modelo compatível com JSON';key.type='password';key.maxLength=4096;key.autocomplete='off';key.setAttribute('aria-label','Chave da API');
 for(const p of capabilities.providers)provider.append(new Option(p.name,p.id));
 provider.value=capabilities.providers.some(p=>p.id===capabilities.online_provider)?capabilities.online_provider:'openai';model.value=capabilities.online_model||(provider.value==='openai'?'gpt-4.1-mini':'');
 for(const [title,input] of [['Serviço',provider],['Modelo',model],['Chave da API',key]]){const label=el('label',title);label.append(input);d.append(label)}
 function sources(){links.replaceChildren();const p=capabilities.providers.find(p=>p.id===provider.value);for(const [label,href] of [['Obter chave no provedor',p.keys_url],['Consultar modelos disponíveis',p.models_url]]){const a=el('a',label);a.href=href;a.target='_blank';a.rel='noopener noreferrer';links.append(a)}}
 provider.onchange=()=>{key.value='';model.value=provider.value==='openai'?'gpt-4.1-mini':'';sources()};sources();status.setAttribute('role','status');
 const row=el('div');row.className='row';const save=el('button','Usar conexão nesta sessão'),disconnect=el('button','Desconectar'),close=el('button','Fechar');for(const b of [save,disconnect,close])b.type='button';row.append(save,disconnect,close);d.append(links,status,row);
 const finish=()=>{key.value='';d.close();d.remove()};close.onclick=finish;d.oncancel=e=>{e.preventDefault();finish()};
 let busy=false;
 async function commit(remove=false){if(busy)return;busy=true;save.disabled=disconnect.disabled=true;try{
  if(remove)await api('/api/assistencia/conexao',{method:'DELETE'});else await api('/api/assistencia/conexao',json('POST',{provider:provider.value,model:model.value.trim(),key:key.value}));
  key.value='';await updated();finish();msg(remove?'API desconectada.':'API configurada nesta sessão. A primeira consulta verificará a chave e o modelo.');
 }catch(e){status.textContent=e.message;key.value=''}finally{busy=false;save.disabled=disconnect.disabled=false}}
 save.onclick=()=>void commit();disconnect.onclick=()=>void commit(true);document.body.append(d);d.showModal();
}
async function open(phase='general',segment=null){
 requireProject();if(!await RodoviaPanels.close())return;await save();
 const project=pid,context=projectSession.context,d=el('dialog');d.className='winDlg rsSmallAI';d.setAttribute('aria-label','IA de apoio e mini prompts');
 d.append(el('h2','IA de apoio e mini prompts'));
 const state=el('p','Conferindo disponibilidade…'),choice=el('select'),provider=el('select'),taskInput=el('textarea'),preview=el('pre'),output=el('section'),actions=el('div');
 choice.setAttribute('aria-label','Etapa da assistência');provider.setAttribute('aria-label','Provedor IA');taskInput.setAttribute('aria-label','Pedido para a IA');taskInput.maxLength=500;taskInput.rows=3;taskInput.placeholder='Descreva o problema ou a melhoria desejada. A proposta será conferida pelo motor antes de aplicar.';
 for(const [key,label] of [['general','Diagnóstico geral'],['files','Arquivos'],['flow','Fluxo selecionado'],['chainage','Esquerda/direita e estaqueamento'],['textures','Texturas'],['video','Apresentação do vídeo']])choice.append(new Option(label,key));choice.value=phase;
 provider.append(new Option('Modelo local 3B','local'),new Option('API online opcional','online'));
 const connection=el('button','Conectar API online');connection.type='button';
 const prepare=el('button','Preparar mini prompt'),run=el('button','Consultar IA'),cancel=el('button','Cancelar consulta'),close=el('button','Fechar');for(const b of [prepare,run,cancel,close])b.type='button';run.disabled=true;cancel.hidden=true;
 const layersInput=el('textarea');layersInput.rows=2;layersInput.maxLength=2400;layersInput.setAttribute('aria-label','Camadas para consultar');layersInput.placeholder='Até 8 nomes de layers, um por linha. Em branco: até 3 camadas por consulta.';layersInput.value=dxfSel?.layer||'';layersInput.hidden=phase!=='textures';
 const agree=el('label'),checkbox=el('input');checkbox.type='checkbox';agree.append(checkbox,document.createTextNode(' Autorizo enviar somente o mini prompt exibido à API online configurada.'));agree.hidden=true;
 const previewBox=el('details');previewBox.append(el('summary','Conferir mini prompt e dados compartilhados'),preview);
 preview.className='rsMiniPrompt';preview.setAttribute('aria-label','Mini prompt que será enviado');actions.className='row';actions.append(connection,prepare,run,cancel,close);d.append(state,choice,provider,taskInput,layersInput,agree,previewBox,output,actions);document.body.append(d);d.showModal();
 let prompt=null,busy=false,capabilities=null,cancelled=false;
 const alive=()=>pid===project&&projectSession.context===context&&d.isConnected;
 function reset(){prompt=null;run.disabled=true;checkbox.checked=false;preview.textContent='Prepare um novo mini prompt após alterar o pedido ou a etapa.';output.replaceChildren()}
 taskInput.oninput=reset;layersInput.oninput=reset;choice.onchange=()=>{layersInput.hidden=choice.value!=='textures';reset()};provider.onchange=()=>{agree.hidden=provider.value!=='online';checkbox.checked=false};
 const guarded=fn=>guard(async()=>{try{if(!alive())throw Error('O projeto mudou. Reabra a assistência.');return await fn()}catch(e){if(d.isConnected)state.textContent=e.message;throw e}});
 prepare.onclick=guarded(async()=>{if(busy)return;prompt=await api('/api/projects/'+project+'/assistencia/mini_prompt',json('POST',{phase:choice.value,task:taskInput.value,segment:segment??selSeg?.id??null,layers:choice.value==='textures'?layersInput.value.split('\n').map(s=>s.trim()).filter(Boolean):[]}));if(!alive())return;preview.textContent=JSON.stringify({messages:prompt.messages,response_schema:prompt.response_schema},null,2);output.replaceChildren(el('p',prompt.notice));run.disabled=false});
 cancel.onclick=guarded(async()=>{cancelled=true;cancel.disabled=true;state.textContent='Cancelamento solicitado; a resposta pendente não será aplicada. Você pode fechar esta janela.';await api('/api/projects/'+project+'/assistencia/modelo/cancelar',json('POST',{}));state.textContent='Cancelamento solicitado; aguardando encerramento do provedor.'});
 function finish(){if(busy&&!cancelled){state.textContent='Solicite o cancelamento antes de fechar. A resposta pendente não será aplicada.';return}d.close();d.remove()}
 close.onclick=finish;d.oncancel=e=>{e.preventDefault();finish()};
 run.onclick=guarded(async()=>{if(!prompt||busy)return;if(provider.value==='online'&&!checkbox.checked)throw Error('Revise o mini prompt e marque a autorização de envio online.');
  if(provider.value==='local'&&!capabilities?.installed){state.textContent='Pacote do modelo ainda não instalado. A integração está disponível, mas não há inferência local habilitada.';return}
  busy=true;cancelled=false;connection.disabled=run.disabled=prepare.disabled=provider.disabled=choice.disabled=taskInput.disabled=layersInput.disabled=checkbox.disabled=true;cancel.hidden=false;cancel.disabled=false;const progress='mini:'+project+Date.now();
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
  finally{busy=false;cancel.hidden=true;connection.disabled=run.disabled=prepare.disabled=provider.disabled=choice.disabled=taskInput.disabled=layersInput.disabled=checkbox.disabled=false}
 });
 async function refreshCapabilities(){capabilities=await api('/api/assistencia/modelo');if(alive()){
  state.textContent=(capabilities.online_configured?'API configurada: '+capabilities.online_host+' · modelo '+capabilities.online_model+'. ':capabilities.message+' ')+(!capabilities.installed?'Modelo local ainda não instalado.':'');
  provider.options[1].disabled=!capabilities.online_configured;provider.options[1].textContent=capabilities.online_configured?'API online: '+capabilities.online_host:'API online (configuração pendente)';
  provider.value=capabilities.online_configured?'online':'local';agree.hidden=provider.value!=='online';checkbox.checked=false;
 }}
 connection.onclick=guarded(()=>connect(refreshCapabilities));
 try{await refreshCapabilities()}catch(e){if(alive())state.textContent=e.message}

}
window.RodoviaSmallAI=Object.freeze({open,connect});
comando(['IA3B'],()=>open(),'Mini prompts revisáveis com modelo local 3B ou API opcional');
queueMicrotask(()=>queueMicrotask(()=>{const panel=document.querySelector('[data-activity="Projeto"]');if(panel){const b=el('button','IA de apoio');b.type='button';b.title='Conectar API online ou consultar modelo local com mini prompts revisáveis';b.onclick=guard(()=>open());panel.append(b)}}));
})();
