// Central de correção: ações explícitas, mantendo barreiras e controles físicos.
(()=>{'use strict';
let dialog=null;
async function closePanels(){return !window.RodoviaPanels||await RodoviaPanels.close()}
function selected(id){const s=segById(id);if(!s)throw Error('O resultado mudou. Reabra a correção de fluxos.');return s}
function close(){dialog?.close();dialog?.remove();dialog=null}
async function action(id,kind){
 const s=selected(id);close();if(!await closePanels())return;
 selSeg={id:s.id};vecOn.flows=true;if(window.RodoviaFlowStudy)RodoviaFlowStudy.editing=true;
 if(kind==='locate'){setTool('pan');const p=s.technical_points?.[0]?.point||s.mid;zoomTo(P(p));draw();msg(s.technical_message||'Fluxo localizado.');return}
 if(kind==='cut'){setTool('flowcut');msg('Clique no início e no fim do intervalo defeituoso do mesmo segmento. O eixo original será preservado.');return}
 if(kind==='properties'){showSegProps();return}
 if(kind==='recover'){
  if(s.disabled)throw Error('Este fluxo foi desativado manualmente. Reative-o nas propriedades antes de recuperar.');
  const found=(M.flow_recoveries||[]).some(r=>r.enabled!==false&&r.target_key===s.origin_key&&distPolyline(r,s.points.map(P))<=6);
  if(!found){checkpoint();M.flow_recoveries.push({id:uid(),x:s.mid[0],y:s.mid[1],target_key:s.origin_key||'',enabled:true});changed('Recuperação: excluir partes inválidas e manter somente circulação revalidada.');}
  const completed=await start('analyze');if(completed===false)return;msg('Recuperação recalculada. Abra Corrigir fluxos para conferir o resultado; partes excluídas não recebem atalhos.');
 }
}
async function open(){
 requireProject();if(!editor?.segments?.length){if(await closePanels())await start('analyze');if(!editor?.segments?.length)throw Error('Nenhuma trajetória encontrada. Confira a camada Eixo e a área de pavimento em Camadas.');}
 if(dialog?.open)return;dialog=document.createElement('dialog');dialog.className='winDlg';dialog.style.width='min(1000px,94vw)';dialog.style.maxWidth='1000px';dialog.style.maxHeight='85vh';dialog.style.overflow='auto';dialog.setAttribute('aria-label','Corrigir fluxos');
 dialog.innerHTML='<h3>Corrigir fluxos</h3><p>Linhas de bordo, marcações e linhas perpendiculares de referência não são barreiras. Se uma camada foi interpretada incorretamente, corrija seu tipo em Camadas e recalcule. Não é necessário refazer o projeto.</p><p><b>Proteções mantidas:</b> barreiras/canteiros físicos, colisões, sinal vermelho e interdições com pare e siga. Curvas impossíveis e coordenadas inválidas também precisam ser corrigidas.</p><div class="row"><button data-global="layers">Revisar camadas que bloqueiam</button><button data-global="calculate">Recalcular fluxos</button><button data-global="criteria">Revisar critério automático de canteiro</button><button data-global="select">Selecionar fluxo em tela</button><button data-global="close">Fechar</button></div><p>Recuperar exclui somente partes reprovadas e revalida o restante. Recortar permite marcar início e fim do defeito. Ajustes automáticos de afastamento não movem o eixo DXF.</p><div data-flow-results></div>';
 const restrictive=document.createElement('p');const names=Object.keys(cfg.layers||{}).length?['barrier','median'].flatMap(role=>(cfg.layers[role]||[]).map(name=>name+' ('+(role==='barrier'?'barreira':'canteiro')+')')):(analysis?.layers||[]).filter(l=>['barrier','median'].includes(l.suggested_role)).map(l=>l.name+' (sugestão)');restrictive.textContent='Camadas restritivas cadastradas/sugeridas: '+(names.join(', ')||'nenhuma listada; confira também as áreas desenhadas e proibições manuais.');dialog.querySelector('[data-flow-results]').appendChild(restrictive);
 const rows=document.createElement('div');const segments=[...editor.segments].sort((a,b)=>(a.technical_status==='ok')-(b.technical_status==='ok'));
 for(const s of segments.slice(0,300)){
  const row=document.createElement('section');row.style.padding='10px';row.style.marginBottom='8px';row.dataset.flowRepair=String(s.id);
  const heading=document.createElement('b');heading.textContent=(s.route_name||s.source||'Fluxo')+' · '+s.id+' · '+({ok:'OK',problem:'Bloqueado',adjustment:'Revisar'}[s.technical_status]||'Revisar');row.appendChild(heading);
  const text=document.createElement('p');text.textContent=s.technical_message||'Recalcule para obter um diagnóstico atualizado.';row.appendChild(text);
  if(s.technical_lateral_fits?.length){const fit=document.createElement('p');fit.textContent=s.technical_lateral_fits.map(f=>'Afastamento: '+f.original_m+' → '+f.applied_m+' m.').join(' ');row.appendChild(fit)}
  const buttons=document.createElement('div');buttons.className='row';
  for(const [kind,label] of [['locate','Localizar defeito'],['recover','Recuperar partes válidas'],['cut','Recortar início/fim'],['properties','Editar / reativar fluxo']]){const b=document.createElement('button');b.type='button';b.textContent=label;b.dataset.repairAction=kind;b.onclick=guard(()=>action(s.id,kind));buttons.appendChild(b)}row.appendChild(buttons);rows.appendChild(row);
 }
 if(segments.length>300){const p=document.createElement('p');p.textContent='Mostrando os primeiros 300 trechos, com problemas primeiro. Use a seleção em tela para os demais.';rows.appendChild(p)}
 dialog.querySelector('[data-flow-results]').appendChild(rows);
 dialog.addEventListener('click',guard(async e=>{const kind=e.target.closest('[data-global]')?.dataset.global;if(!kind)return;close();if(kind==='close')return;if(!await closePanels())return;if(kind==='criteria'){const d=document.createElement('dialog');d.className='winDlg';d.innerHTML='<h3>Critério automático de canteiro</h3><p>A proximidade de eixos pode sugerir uma troca de pista inexistente. Suspender essa inferência não remove barreiras ou canteiros físicos, proibições manuais, colisões, sinais nem pare e siga.</p><div class="row"><button data-mode="free">Suspender inferência e recalcular</button><button data-mode="returns">Restaurar critério e recalcular</button><button data-cancel>Cancelar</button></div>';document.body.appendChild(d);d.onclick=guard(async e=>{if(e.target.closest('[data-cancel]')){d.close();d.remove();return}const mode=e.target.closest('[data-mode]')?.dataset.mode;if(!mode)return;checkpoint();$('median_crossing').value=mode;cfg.median_crossing=mode;changed('Critério automático de canteiro ajustado; proteções físicas mantidas.');d.close();d.remove();await start('analyze')});d.oncancel=()=>d.remove();d.showModal();}else if(kind==='layers'){psOpenHub('layers');msg('Confira as camadas classificadas como Barreira e Canteiro. Para referências e bordos, escolha o tipo correto. Recalcule após salvar.');}else if(kind==='calculate')await start('analyze');else{vecOn.flows=true;if(window.RodoviaFlowStudy)RodoviaFlowStudy.editing=true;selSeg=null;setTool('pan');draw();msg('Clique sobre uma trajetória para editar; utilize Localizar defeito na central se não conseguir selecioná-la.');}}));
 dialog.addEventListener('cancel',e=>{e.preventDefault();close()});document.body.appendChild(dialog);dialog.showModal();
}
comando(['CORRIGIRFLUXOS'],open,'Diagnosticar, localizar, recortar e recuperar fluxos sem apagar o eixo');
queueMicrotask(()=>queueMicrotask(()=>{const bar=$('rsTechnicalOptions');if(!bar||$('rsRepairFlows'))return;const button=document.createElement('button');button.type='button';button.id='rsRepairFlows';button.textContent='Corrigir fluxos…';button.title='Localizar defeitos, recuperar partes válidas, recortar e revisar camadas';button.onclick=guard(open);bar.prepend(button)}));
window.RodoviaFlowRepair=Object.freeze({open});
})();
