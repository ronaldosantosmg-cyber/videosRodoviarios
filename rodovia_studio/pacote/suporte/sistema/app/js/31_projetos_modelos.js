// =====================================================================================================
// 1.30: abrir projeto, renomear, modelos; rotas de veículos (pista simples/dupla/sentido único por trecho);
// painéis recolhíveis; gerenciador de camadas; pincel de textura.
// =====================================================================================================

// ---------- Abrir projeto ----------
let opRows=[],opSel=null;
async function openProjectDialog(){opRows=await api('/api/projects_info');opSel=pid||(opRows[0]&&opRows[0].id)||null;$('opSearch').value='';renderOpen();if(!$('openDlg').open)$('openDlg').showModal();setTimeout(()=>$('opSearch').focus(),0)}
function opFiltered(){const q=$('opSearch').value.trim().toLowerCase(),sort=$('opSort').value;
 const R=opRows.filter(r=>!q||[r.name,r.origin,r.destination,...Object.values(r.file_names||{})].some(x=>String(x||'').toLowerCase().includes(q)));
 R.sort((a,b)=>sort==='name'?String(a.name).localeCompare(String(b.name),'pt-BR'):String(b[sort]||'').localeCompare(String(a[sort]||'')));return R}
function renderOpen(){const R=opFiltered();
 $('opGrid').innerHTML=R.length?R.map(r=>`<div class="prjCard${r.id===opSel?' on':''}${r.id===pid?' cur':''}" data-op="${r.id}" tabindex="0" title="Duplo clique abre">${r.preview?`<img loading="lazy" alt="" src="/api/projects/${r.id}/miniatura.jpg?v=${encodeURIComponent(r.modified||'')}">`:'<div class="noimg">sem prévia</div>'}<b>${esc(r.name)}</b><small>${r.missing?'pasta ausente':`DXF ${r.files?.dxf?'✓':'—'} · KMZ ${r.files?.kmz?'✓':'—'}${r.video?' · vídeo ✓':''}`}</small><small>Gravado ${esc(r.modified||'—')}</small></div>`).join(''):'<p class="muted">Nenhum projeto encontrado.</p>';
 opButtons()}
function opButtons(){const r=opRows.find(x=>x.id===opSel);for(const id of ['opOpen','opRename','opDup','opTpl','opDel'])$(id).disabled=!r||(!!r.missing&&id!=='opDel');
 $('opDel').textContent=r?.missing?'Remover registro…':'Excluir…';
 $('opInfo').textContent=r?`${r.name}${r.origin||r.destination?` — ${r.origin||'?'} → ${r.destination||'?'}`:''} · criado ${String(r.created||'').slice(0,16)}${r.file_names&&Object.keys(r.file_names).length?' · arquivos: '+Object.values(r.file_names).filter(Boolean).join(', '):''}`:`${opRows.length} projeto(s). Clique para escolher; duplo clique abre.`}
async function openProjectId(id){if(pid&&id!==pid&&typeof savePending!=='undefined'&&savePending){clearTimeout(saveTimer);try{await save()}catch(e){}}
 await load(id);await list();announce({t:'project'});msg(`Projeto “${cfg.name}” aberto.`)}
function otherNames(rows,id){return rows.filter(r=>r.id!==id).map(r=>r.name)}
async function renameProject(id=pid){if(!id)return msg('Abra um projeto primeiro.',true);const rows=opRows.length?opRows:await api('/api/projects_info');const r=rows.find(x=>x.id===id)||{name:cfg.name};
 const v=await inputBox('Renomear projeto','Novo nome do projeto:',r.name||'',{taken:otherNames(rows,id)});if(!v||v===r.name)return;
 if(id===pid){clearTimeout(saveTimer);try{await save()}catch(e){}}
 const res=await api(`/api/projects/${id}/rename`,json('POST',{name:v}));
 if(id===pid){cfg.name=res.name;if($('name'))$('name').value=res.name;document.title=`${res.name} — Rodovia Studio`}
 await list();if($('openDlg').open){opRows=await api('/api/projects_info');renderOpen()}msg(`Projeto renomeado para “${res.name}”.`)}
$('opSearch')?.addEventListener('input',renderOpen);$('opSort')?.addEventListener('change',renderOpen);
$('opGrid')?.addEventListener('click',e=>{const c=e.target.closest('[data-op]');if(!c)return;opSel=c.dataset.op;document.querySelectorAll('#opGrid .prjCard').forEach(x=>x.classList.toggle('on',x===c));opButtons()});
$('opGrid')?.addEventListener('dblclick',guard(async e=>{const c=e.target.closest('[data-op]');if(!c)return;opSel=c.dataset.op;$('openDlg').close();await openProjectId(opSel)}));
$('openDlg')?.addEventListener('keydown',guard(async e=>{if(e.key==='Enter'&&opSel&&!e.target.closest('button')){e.preventDefault();e.stopPropagation();$('openDlg').close();await openProjectId(opSel)}}));
$('opOpen')?.addEventListener('click',guard(async()=>{if(!opSel)return;$('openDlg').close();await openProjectId(opSel)}));
$('opRename')?.addEventListener('click',guard(async()=>{if(opSel)await renameProject(opSel)}));
$('opDup')?.addEventListener('click',guard(async()=>{const r=opRows.find(x=>x.id===opSel);if(!r)return;if(r.id===pid){clearTimeout(saveTimer);try{await save()}catch(e){}}
 const v=await inputBox('Duplicar projeto','Nome da cópia:',(r.name+' (cópia)').slice(0,80),{taken:opRows.map(x=>x.name)});if(!v)return;const n=await api(`/api/projects/${r.id}/save_as`,json('POST',{name:v}));opRows=await api('/api/projects_info');opSel=n.id;renderOpen();await list();msg(`Cópia “${n.name}” criada (o projeto aberto não mudou).`)}));
$('opTpl')?.addEventListener('click',guard(async()=>{if(opSel)await openTplSave(opSel)}));
$('opDel')?.addEventListener('click',guard(async()=>{const r=opRows.find(x=>x.id===opSel);if(!r)return;
 if(!await confirmBox(r.missing?`Remover o registro “${r.name}” da lista? Nenhum arquivo será apagado e uma cópia do cadastro será preservada.`:`Excluir o projeto “${r.name}” da lista? A pasta vai para “_lixeira” (pode ser recuperada manualmente).`,r.missing?'Remover registro':'Excluir','Cancelar'))return;
 const res=await api(r.missing?`/api/project-records/${r.id}`:`/api/projects/${r.id}`,{method:'DELETE'});if(r.id===pid){pid='';cfg={};meta=null;geo=null;baseImage=null;editor=null;try{localStorage.removeItem('rodovia_project')}catch{}draw()}
 opRows=await api('/api/projects_info');opSel=opRows[0]?.id||null;renderOpen();await list();msg(res.removed_record?'Registro removido da lista. Nenhum arquivo foi apagado; cadastro guardado em _registros_removidos.':`Projeto retirado da lista (pasta ${res.trash} em _lixeira).`)}));
$('opNew')?.addEventListener('click',guard(async()=>{const v=await inputBox('Novo projeto','Nome do novo projeto:','Novo trecho',{taken:opRows.map(x=>x.name)});if(!v)return;const r=await api('/api/projects',json('POST',{name:v}));$('openDlg').close();await list();await load(r.id);msg(`Projeto “${v}” criado. Envie o DXF e o KMZ.`)}));
$('opClose')?.addEventListener('click',()=>$('openDlg').close());

// ---------- Modelos (templates) ----------
let tplRows=[],tplSel=null,tplFor=null;
async function openTemplates(){tplRows=await api('/api/modelos');if(!tplRows.some(r=>r.id===tplSel))tplSel=tplRows[0]?.id||null;renderTpl();if(!$('tplDlg').open)$('tplDlg').showModal()}
function renderTpl(){$('tplRows').innerHTML=tplRows.length?tplRows.map(r=>`<tr data-tpl="${r.id}" class="${r.id===tplSel?'on':''}"><td><b>${esc(r.name)}</b></td><td>${esc(r.description||'')}</td><td>${r.include_marks?`configurações + ${r.marks} marcação(ões)`:'só configurações'}</td><td>${esc(r.created||'')}</td><td>${esc(r.source||'')}</td></tr>`).join(''):'<tr><td colspan="5" class="muted">Nenhum modelo ainda. Abra um projeto bem configurado e clique “Salvar projeto aberto como modelo…”.</td></tr>';
 const r=tplRows.find(x=>x.id===tplSel);$('tplNewPrj').disabled=$('tplRename').disabled=$('tplDel').disabled=!r;$('tplApply').disabled=!r||!pid;$('tplSave').disabled=!pid}
$('tplRows')?.addEventListener('click',e=>{const tr=e.target.closest('[data-tpl]');if(!tr)return;tplSel=tr.dataset.tpl;renderTpl()});
$('tplRows')?.addEventListener('dblclick',e=>{const tr=e.target.closest('[data-tpl]');if(!tr)return;tplSel=tr.dataset.tpl;$('tplNewPrj').click()});
$('tplNewPrj')?.addEventListener('click',guard(async()=>{const t=tplRows.find(x=>x.id===tplSel);if(!t)return;const names=(await api('/api/projects')).map(x=>x.name);
 const v=await inputBox('Novo projeto a partir de modelo',`Nome do novo projeto (modelo “${t.name}”):`,'Novo trecho',{taken:names});if(!v)return;
 const r=await api(`/api/modelos/${t.id}/novo`,json('POST',{name:v}));$('tplDlg').close();await list();await load(r.id);announce({t:'project'});msg(`Projeto “${v}” criado com o modelo “${t.name}”. Envie o DXF e o KMZ e analise.`)}));
$('tplApply')?.addEventListener('click',guard(async()=>{const t=tplRows.find(x=>x.id===tplSel);if(!t||!pid)return;
 if(!await confirmBox(`Aplicar as configurações do modelo “${t.name}” ao projeto “${cfg.name}”? As marcações, o km, os arquivos e as camadas do projeto ficam como estão. Uma cópia da configuração atual é guardada na pasta do projeto.`,'Aplicar','Cancelar'))return;
 clearTimeout(saveTimer);await save();const r=await api(`/api/projects/${pid}/aplicar_modelo/${t.id}`,{method:'POST'});$('tplDlg').close();await load(pid);msg(`Modelo “${r.template}” aplicado. Configuração anterior guardada em ${r.backup}. Gere a prévia para ver.`)}));
$('tplRename')?.addEventListener('click',guard(async()=>{const t=tplRows.find(x=>x.id===tplSel);if(!t)return;const v=await inputBox('Renomear modelo','Novo nome do modelo:',t.name,{taken:tplRows.filter(x=>x.id!==t.id).map(x=>x.name)});if(!v||v===t.name)return;await api(`/api/modelos/${t.id}/rename`,json('POST',{name:v}));await openTemplates();msg(`Modelo renomeado para “${v}”.`)}));
$('tplDel')?.addEventListener('click',guard(async()=>{const t=tplRows.find(x=>x.id===tplSel);if(!t)return;if(!await confirmBox(`Excluir o modelo “${t.name}”? Os projetos criados com ele não mudam. O arquivo vai para “_lixeira”.`,'Excluir','Cancelar'))return;await api(`/api/modelos/${t.id}`,{method:'DELETE'});tplSel=null;await openTemplates();msg('Modelo excluído.')}));
$('tplSave')?.addEventListener('click',guard(async()=>{if(pid)await openTplSave(pid)}));
$('tplClose')?.addEventListener('click',()=>$('tplDlg').close());
async function openTplSave(id=pid){if(!id)return msg('Abra um projeto primeiro.',true);tplFor=id;tplRows=await api('/api/modelos');const rows=await api('/api/projects');const r=rows.find(x=>x.id===id);
 $('tsName').value=('Modelo — '+(r?.name||'projeto')).slice(0,80);$('tsDesc').value='';$('tsMarks').checked=false;tsCheck();$('tplSaveDlg').showModal();setTimeout(()=>{$('tsName').focus();$('tsName').select()},0)}
function tsCheck(){const r=nameCheck($('tsName').value);let why=r.ok?'':r.why;if(r.ok&&tplRows.some(x=>x.name.toLowerCase()===r.value.toLowerCase()))why='Já existe um modelo com este nome.';$('tsErr').textContent=why;$('tsOk').disabled=!!why;return why?null:r.value}
$('tsName')?.addEventListener('input',tsCheck);
$('tsOk')?.addEventListener('click',guard(async()=>{const name=tsCheck();if(!name)return;if(tplFor===pid){clearTimeout(saveTimer);await save()}
 const r=await api(`/api/projects/${tplFor}/modelo`,json('POST',{name,description:$('tsDesc').value.trim().slice(0,200),include_marks:$('tsMarks').checked}));$('tplSaveDlg').close();if($('tplDlg').open)await openTemplates();msg(`Modelo “${r.name}” salvo${r.include_marks?' (com as marcações)':' (só configurações)'}. Use Arquivo › Novo a partir de modelo.`)}));
$('tsCancel')?.addEventListener('click',()=>$('tplSaveDlg').close());
$('tplSaveDlg')?.addEventListener('keydown',e=>{if(e.key==='Enter'&&e.target.tagName==='INPUT'&&e.target.type!=='checkbox'){e.preventDefault();e.stopPropagation();$('tsOk').click()}});
document.addEventListener('keydown',e=>{if(e.ctrlKey&&!e.shiftKey&&(e.key==='o'||e.key==='O')){e.preventDefault();guard(openProjectDialog)()}});

// Arquivo (menu), faixa de opções e comandos.
itemArquivo('Novo projeto',['Novo a partir de modelo…',()=>openTemplates()],['Abrir projeto…','Ctrl+O',()=>openProjectDialog()]);
itemArquivo('Salvar como…',['Renomear projeto…',()=>renameProject()],null,['Salvar como modelo…',()=>openTplSave()],['Modelos de projeto…',()=>openTemplates()]);
itemFaixa('Início','Projeto',['Abrir…','📂',()=>openProjectDialog(),1],{posicao:1});
for(const it of [['Renomear','✎',()=>renameProject()],['Modelos','▤',()=>openTemplates()],['Salvar como modelo','⬒',()=>openTplSave()]])itemFaixa('Início','Projeto',it);
comando(['ABRIR','OPEN'],()=>guard(openProjectDialog)(),'Abre um projeto salvo (lista com miniaturas, busca, renomear, duplicar) — também Ctrl+O');
comando(['MODELOS','MODELO','TEMPLATE'],()=>guard(openTemplates)(),'Modelos de projeto: novo a partir de modelo, aplicar, salvar');
comando(['RENOMEAR','REN'],()=>guard(()=>renameProject())(),'Renomeia o projeto aberto');

