// Confirmação compartilhada: mantém rascunho em erro e uma pergunta por janela.
(()=>{'use strict';
const pending=new WeakMap();
function ask(owner,{title='Salvar alterações?',message='Há alterações ainda não salvas.',save,saveLabel='Salvar e fechar'}={}){
 if(pending.has(owner))return pending.get(owner);
 let resolve;const promise=new Promise(r=>resolve=r);pending.set(owner,promise);
 const q=document.createElement('dialog');q.className='winDlg rsDraftDecision';q.setAttribute('aria-label',title);
 const heading=document.createElement('h3'),text=document.createElement('p'),error=document.createElement('p'),row=document.createElement('div');heading.textContent=title;text.textContent=message;error.setAttribute('role','alert');row.className='row';q.append(heading,text,error,row);
 let busy=false;const finish=value=>{q.close();q.remove();pending.delete(owner);if(owner.isConnected)owner.querySelector('[data-close],button')?.focus();resolve(value)};
 for(const [value,label] of [['continue','Continuar editando'],['discard','Descartar'],...(save?[['save',saveLabel]]:[])]){const b=document.createElement('button');b.type='button';b.textContent=label;b.dataset.draftChoice=value;row.append(b);b.onclick=async()=>{
  if(busy)return;if(value!=='save'){finish(value);return}busy=true;error.textContent='';q.setAttribute('aria-busy','true');const states=[...row.querySelectorAll('button')].map(x=>[x,x.disabled]);states.forEach(([x])=>x.disabled=true);
  try{if(!owner.isConnected)throw Error('A janela original foi fechada.');if(await save()===false){error.textContent='Não foi possível salvar. Confira os campos e tente novamente.';return}finish('save')}
  catch(e){error.textContent=e.message||'Não foi possível salvar. O rascunho foi preservado.'}
  finally{busy=false;q.removeAttribute('aria-busy');states.forEach(([x,disabled])=>x.disabled=disabled)}};
 }
 q.oncancel=e=>{e.preventDefault();if(!busy)finish('continue')};document.body.append(q);q.showModal();return promise;
}
window.RodoviaDialogDecision=Object.freeze({ask});
})();
// Edição em rascunho, com salvar/descartar/continuar e erros visíveis.
(()=>{'use strict';
function open({id,title,html,save,calculate=false}){
 requireProject();const project=pid,context=projectSession.context;if(document.getElementById(id))return document.getElementById(id);
 const d=document.createElement('dialog');d.id=id;d.className='winDlg rsModelDialog';d.innerHTML=`<header><h2>${esc(title)}</h2><button type="button" data-close aria-label="Fechar">×</button></header><section>${html}<p data-error role="alert"></p></section><footer><button type="button" data-close>Cancelar</button>${calculate?'<button type="button" data-calculate title="Salva, fecha esta janela e atualiza os resultados">Salvar e atualizar</button>':''}<button type="button" data-save title="Confirma os dados e fecha esta janela; a atualização segue o modo Manual ou Automático">Salvar e fechar</button></footer>`;document.body.appendChild(d);
 let dirty=false,busy=false;d.addEventListener('input',()=>dirty=true);d.addEventListener('change',()=>dirty=true);
 const finish=()=>{d.close();d.remove()};
 async function apply(calc=false){if(busy)return false;const invalid=[...d.querySelectorAll('input,select,textarea')].find(el=>!el.checkValidity());if(invalid){invalid.reportValidity();d.querySelector('[data-error]').textContent='Confira os campos destacados antes de aplicar.';return false}const snapshot=structuredClone(M),history=undoStack.slice(),future=redoStack.slice(),pendingBefore=savePending,configBefore=structuredClone(cfg);let committed=false;busy=true;const controls=[...d.querySelectorAll('button,input,select,textarea')].map(el=>[el,el.disabled]);controls.forEach(([el])=>el.disabled=true);d.setAttribute('aria-busy','true');try{if(project!==pid||context!==projectSession.context)throw Error('O projeto mudou. Reabra a janela.');d.querySelector('[data-error]').textContent='Salvando e conferindo a configuração…';if(await save(d)===false)return false;dirty=false;committed=true;finish();if(calc){msg('Configuração aplicada. Atualização solicitada na fila; é possível limpar pedidos pendentes pelo rodapé.');if(project!==pid||context!==projectSession.context)return false;await (window.RodoviaUpdatePolicy?RodoviaUpdatePolicy.refresh():start('analyze'))}else window.dispatchEvent(new CustomEvent('rodovia:form-committed',{detail:{project,context}}));return true}catch(e){if(!committed&&!e.saveUncertain&&project===pid&&context===projectSession.context){cfg=configBefore;M=snapshot;undoStack=history;redoStack=future;savePending=pendingBefore;clearTimeout(saveTimer);updateUndo();draw()}if(d.isConnected)d.querySelector('[data-error]').textContent=e.message;else msg(e.message,true);return false}finally{busy=false;d.removeAttribute('aria-busy');controls.forEach(([el,disabled])=>el.disabled=disabled)}}
 async function close(){if(busy)return;if(!dirty){finish();return}const choice=await RodoviaDialogDecision.ask(d,{message:'As alterações desta janela ainda não foram aplicadas.',save:()=>apply()});if(choice==='discard')finish()}
 d.querySelectorAll('[data-close]').forEach(b=>b.onclick=close);d.querySelector('[data-save]').onclick=()=>void apply();d.querySelector('[data-calculate]')?.addEventListener('click',()=>void apply(true));d.oncancel=e=>{e.preventDefault();void close()};d.rsDirty=()=>dirty=true;d.rsContext=()=>project===pid&&context===projectSession.context;d.showModal();return d;
}
function number(input,name,min=-Infinity,max=Infinity){if(!input?.value?.trim())throw Error('Preencha '+name+'.');const v=Number(input.value.replace(',','.'));if(!Number.isFinite(v)||v<min||v>max)throw Error(name+' fora do intervalo permitido.');return v}
window.RodoviaModelDialog=Object.freeze({open,number});
})();
