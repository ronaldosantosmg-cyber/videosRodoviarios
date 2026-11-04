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
  try{if(!owner.isConnected)throw Error('A janela original foi fechada.');if(await save()===false){const motivo=(owner.querySelector('[data-error]')?.textContent||'').trim();error.textContent=motivo&&!/^Salvando|^Valores aplicados/.test(motivo)?'Não foi possível salvar: '+motivo:'Não foi possível salvar. Confira os campos e tente novamente.';return}finish('save')}
  catch(e){error.textContent=e.message||'Não foi possível salvar. O rascunho foi preservado.'}
  finally{busy=false;q.removeAttribute('aria-busy');states.forEach(([x,disabled])=>x.disabled=disabled)}};
 }
 q.oncancel=e=>{e.preventDefault();if(!busy)finish('continue')};document.body.append(q);q.showModal();return promise;
}
window.RodoviaDialogDecision=Object.freeze({ask});
})();
// Edição em rascunho, com salvar/descartar/continuar e erros visíveis.
(()=>{'use strict';
function open({id,title,html,save,calculate=false,applyable=true}){
 requireProject();const project=pid,context=projectSession.context;if(document.getElementById(id))return document.getElementById(id);
 const d=document.createElement('dialog');d.id=id;d.className='winDlg rsModelDialog';d.innerHTML=`<header><h2>${esc(title)}</h2><button type="button" data-close aria-label="Fechar">×</button></header><section>${html}<p data-error role="alert"></p></section><footer><button type="button" data-close>Cancelar</button>${applyable?'<button type="button" data-apply title="Confirma os valores válidos, grava e mantém esta janela aberta">Aplicar</button>':''}${calculate?'<button type="button" data-calculate title="Salva, fecha esta janela e atualiza os resultados">Salvar e atualizar</button>':''}<button type="button" data-save title="Confirma os dados e fecha esta janela; a atualização segue o modo Manual ou Automático">Salvar e fechar</button></footer>`;document.body.appendChild(d);
 let dirty=false,busy=false;d.addEventListener('input',()=>dirty=true);d.addEventListener('change',()=>dirty=true);
 const finish=()=>{d.close();d.remove()};
 async function apply(calc=false,keep=false){if(busy)return false;const snapshot=structuredClone(M),history=undoStack.slice(),future=redoStack.slice(),pendingBefore=savePending,configBefore=structuredClone(cfg);let committed=false;busy=true;const controls=[...d.querySelectorAll('button,input,select,textarea')].map(el=>[el,el.disabled]);controls.forEach(([el])=>el.disabled=true);d.setAttribute('aria-busy','true');try{if(project!==pid||context!==projectSession.context)throw Error('O projeto mudou. Reabra a janela.');d.querySelector('[data-error]').textContent='Salvando e conferindo a configuração…';if(await save(d)===false)return false;dirty=false;committed=true;if(!keep)finish();if(keep){d.querySelector('[data-error]').textContent='Valores aplicados.';window.dispatchEvent(new CustomEvent('rodovia:form-committed',{detail:{project,context}}));return true}if(calc){msg('Configuração aplicada. Aguardando o processamento atual para recalcular…');const deadline=Date.now()+120000;while(task||taskRequestPending){if(Date.now()>deadline)throw Error('Dados salvos. A tarefa atual continua; use Atualizar fluxos quando ela terminar.');await new Promise(resolve=>setTimeout(resolve,150));if(project!==pid||context!==projectSession.context)return false}await (window.RodoviaUpdatePolicy?RodoviaUpdatePolicy.refresh():start('analyze'))}else window.dispatchEvent(new CustomEvent('rodovia:form-committed',{detail:{project,context}}));return true}catch(e){if(!committed&&!e.saveUncertain&&project===pid&&context===projectSession.context){cfg=configBefore;M=snapshot;undoStack=history;redoStack=future;savePending=pendingBefore;clearTimeout(saveTimer);updateUndo();draw()}if(d.isConnected)mostrarErro(d,e);else msg(e.message,true);return false}finally{busy=false;d.removeAttribute('aria-busy');controls.forEach(([el,disabled])=>el.disabled=disabled)}}
 async function close(){if(busy)return;if(!dirty){finish();return}const choice=await RodoviaDialogDecision.ask(d,{message:'As alterações desta janela ainda não foram aplicadas.',save:()=>apply()});if(choice==='discard')finish()}
 d.querySelectorAll('[data-close]').forEach(b=>b.onclick=close);d.querySelector('[data-save]').onclick=()=>void apply();d.querySelector('[data-apply]')?.addEventListener('click',()=>void apply(false,true));d.querySelector('[data-calculate]')?.addEventListener('click',()=>void apply(true));d.oncancel=e=>{e.preventDefault();void close()};d.rsDirty=()=>dirty=true;d.rsContext=()=>project===pid&&context===projectSession.context;d.showModal();return d;
}
function falha(input,texto){const e=Error(texto);e.campo=input;return e}
function number(input,name,min=-Infinity,max=Infinity){if(!input?.value?.trim())throw falha(input,'Preencha '+name+'.');const v=Number(input.value.replace(',','.'));if(!Number.isFinite(v)||v<min||v>max){const faixa=Number.isFinite(min)&&Number.isFinite(max)?` (entre ${+min.toFixed(2)} e ${+max.toFixed(2)})`:Number.isFinite(max)?` (máximo ${+max.toFixed(2)})`:Number.isFinite(min)?` (mínimo ${+min.toFixed(2)})`:'';throw falha(input,name+' fora do intervalo permitido'+faixa+'.')}return v}
/* 2.36: o erro sempre fica visível (rola até ele, destaca e foca o campo) — antes ficava escondido no fim da janela e o botão parecia não fazer nada */
function mostrarErro(d,e){const p=d.querySelector('[data-error]');p.textContent=e.message;p.style.cssText='color:#ff8a8a;font-weight:600;margin:10px 0';try{p.scrollIntoView({block:'center'});const c=e.campo;if(c&&c.focus){c.setAttribute('aria-invalid','true');c.focus({preventScroll:true});c.addEventListener('input',()=>c.removeAttribute('aria-invalid'),{once:true})}}catch(_e){}msg(e.message,true)}
window.RodoviaModelDialog=Object.freeze({open,number,mostrarErro});
})();
