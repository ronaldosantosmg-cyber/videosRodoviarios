// 3.1: preparo do DXF — renomeia camadas pelo papel, identifica eixos, une fragmentos e limpa lixo. Só DXF; o original é preservado.
(()=>{'use strict';
const post=body=>api(`/api/projects/${pid}/dxf/preparar`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),timeoutMs:300000});
function linhas(rel){return rel.camadas.filter(c=>c.origem!==c.destino||c.papel).slice(0,200).map(c=>`<tr><td>${esc(c.origem)}</td><td>${esc(c.destino)}</td><td>${esc((roles&&roles[c.papel])||c.papel||'—')}</td><td>${c.entidades}</td><td>${c.preservada?'preservada (bloqueada/oculta)':''}</td></tr>`).join('')}
function resumo(rel){const r=rel.removidas||{};return `<p><b>Eixos:</b> ${rel.eixos.length?rel.eixos.map(esc).join(', '):'nenhum identificado'}${rel.eixos_inferidos.length?' (inferidos pela geometria)':''} · <b>sem papel:</b> ${rel.sem_papel.length} camada(s) · <b>removidas:</b> ${r.invalidas||0} inválida(s), ${r.duplicadas||0} duplicada(s) · <b>fragmentos de eixo unidos:</b> ${rel.eixos_unidos||0}</p>${(rel.avisos||[]).map(a=>`<p role="alert">${esc(a)}</p>`).join('')}`}
async function abrir(){requireProject();clearTimeout(saveTimer);await save();
 const d=document.createElement('dialog');d.className='winDlg';d.id='rsPreparoDxf';d.setAttribute('aria-label','Preparar DXF');
 d.innerHTML='<header><h2>Preparar DXF</h2></header><section><p>Analisando as camadas…</p></section><footer><button type="button" data-close>Fechar</button></footer>';
 document.body.append(d);d.showModal();const sec=d.querySelector('section');d.querySelector('[data-close]').onclick=()=>{d.close();d.remove()};d.oncancel=e=>{e.preventDefault();d.querySelector('[data-close]').click()};
 try{const rel=await post({aplicar:false});
  sec.innerHTML=`<p>Renomeia as camadas para os nomes do modelo padrão (eixo, pista projetada/existente, acostamento, bordo, canteiro, barreira, OAE, corte/aterro, domínio), identifica os eixos e remove entidades inválidas e duplicadas. O DXF original é guardado.</p>${resumo(rel)}<div style="max-height:40vh;overflow:auto"><table><thead><tr><th>Camada original</th><th>Nome padrão</th><th>Papel</th><th>Entidades</th><th></th></tr></thead><tbody>${linhas(rel)}</tbody></table></div><p data-error role="alert"></p>`;
  const foot=d.querySelector('footer'),b1=document.createElement('button'),b2=document.createElement('button');b1.type=b2.type='button';b1.textContent='Gerar DXF preparado (cópia para baixar)';b2.textContent='Usar no projeto (guarda o original)';foot.prepend(b2);foot.prepend(b1);
  const go=async(usar)=>{b1.disabled=b2.disabled=true;sec.querySelector('[data-error]').textContent='Preparando…';try{const r=await post(usar?{usar:true}:{aplicar:true});sec.innerHTML=`<p><b>${usar?'DXF do projeto substituído; original em '+esc(r.backup||''):'DXF preparado gerado.'}</b></p>${resumo(r)}${usar?'':`<p><a href="/api/projects/${pid}/dxf/preparado" download>Baixar input_preparado.dxf</a></p>`}`;msg(usar?'DXF preparado em uso. Analise os arquivos novamente.':'DXF preparado gerado.')}catch(e){sec.querySelector('[data-error]')&&(sec.querySelector('[data-error]').textContent=e.message);b1.disabled=b2.disabled=false}};
  b1.onclick=()=>go(false);b2.onclick=()=>go(true);
 }catch(e){sec.innerHTML='<p role="alert">'+esc(e.message)+'</p>'}}
window.RodoviaPrepararDxf=Object.freeze({abrir});
comando(['PREPARARDXF','DXFPREP','PREPARAR'],()=>guard(abrir)(),'Prepara o DXF: renomeia camadas pelo papel, identifica eixos e limpa entidades inválidas/duplicadas (só DXF)');
try{itemArquivo('Abrir projeto…',['Preparar DXF…',()=>guard(abrir)()])}catch(_e){}
})();
