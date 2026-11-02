// A recuperação recorta somente a circulação; o eixo original e os limites permanecem.
(()=>{'use strict';
 const recoveryIndex=s=>(M.flow_recoveries||[]).findIndex(o=>o.enabled!==false&&(!o.target_key||o.target_key===s.origin_key)&&distPolyline(o,s.points.map(P))<=6);
 const previous=showSegProps;
 showSegProps=function(...args){const result=previous(...args),s=segById(selSeg?.id),box=$('propPanel');if(!s||!box||box.hidden)return result;
 const row=document.createElement('div');row.className='row';
 const button=document.createElement('button');button.type='button';button.dataset.flowRecovery='recover';button.innerHTML=RodoviaInfraRail.icon('auto-fix')+'<span>Recuperar fluxo principal…</span>';button.title='Preserva o eixo original, exclui da circulação os intervalos reprovados e revalida os trechos restantes. Não liga através das lacunas.';
 row.appendChild(button);
 if(recoveryIndex(s)>=0){const remove=document.createElement('button');remove.type='button';remove.dataset.flowRecovery='remove';remove.textContent='Remover recuperação';row.appendChild(remove)}
 box.appendChild(row);return result;
 };
 document.addEventListener('click',guard(async e=>{
  const button=e.target.closest?.('#propPanel [data-flow-recovery]');if(!button)return;
  const s=segById(selSeg?.id);if(!s)return;
  const index=recoveryIndex(s);
  if(button.dataset.flowRecovery==='remove'){if(index<0)return;checkpoint();M.flow_recoveries.splice(index,1)}
  else{if(s.disabled||segOverride(s,'disable')>=0)throw Error('O fluxo está desativado manualmente. Revise essa condição antes de solicitar recuperação.');if(index<0){checkpoint();M.flow_recoveries.push({id:uid(),x:s.mid[0],y:s.mid[1],target_key:s.origin_key||'',enabled:true})}}
  changed(button.dataset.flowRecovery==='remove'?'Recuperação removida; configuração original preservada.':'Recuperação solicitada: o eixo será preservado e somente partes revalidadas poderão receber veículos.');
  const completed=await start('analyze');if(completed===false)return;
  msg('Cálculo concluído. Selecione o fluxo e confira os comprimentos recuperados e excluídos nas propriedades.');
 }));
})();
