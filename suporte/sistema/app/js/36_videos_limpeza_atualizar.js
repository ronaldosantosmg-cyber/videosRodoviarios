// =====================================================================================================
// 1.32: qualidade do vídeo, vídeos guardados (um por geração), limpar memória (resíduos) e atualizar pelo aplicativo.
// =====================================================================================================
fields.push('video_quality');

// ---------- Vídeos gerados ----------
const MB=b=>b<1048576?Math.max(b?1:0,Math.round(b/1024)).toLocaleString('pt-BR')+' KB':b<1073741824?(b/1048576).toLocaleString('pt-BR',{maximumFractionDigits:b<1048576*10?1:0})+' MB':(b/1073741824).toLocaleString('pt-BR',{maximumFractionDigits:2})+' GB';
const Q_LABEL={padrao:'Padrão',alta:'Alta',maxima:'Máxima'};
async function openVideos(){requireProject();const r=await api(`/api/projects/${pid}/videos`);const V=r.videos||[];
 $('vdPasta').textContent=r.pasta?`Pasta: ${r.pasta} — cada geração fica num arquivo novo (nada é substituído).`:'Nenhum vídeo guardado ainda. Ao gerar, cada vídeo fica na pasta “videos”, numa subpasta com o nome do projeto.';
 $('vdRows').innerHTML=V.length?V.map(v=>`<tr data-vd="${esc(v.nome)}"><td class="fname"><b>${esc(v.nome)}</b></td><td class="nw">${esc(v.data)}</td><td>${v.largura?`${v.largura}×${v.altura} · ${v.fps} q/s`:'—'}</td><td>${esc(Q_LABEL[v.qualidade]||v.qualidade||'—')}</td><td>${v.duracao_s?tempo(v.duracao_s):'—'}</td><td>${MB(v.bytes)}</td><td class="acts"><button type="button" class="mini" data-vda="ver" title="Assistir aqui">▶ Assistir</button><a class="link mini" href="/api/projects/${pid}/videos/${encodeURIComponent(v.nome)}?baixar=1" title="Baixar o arquivo">⭳ Baixar</a><button type="button" class="mini danger" data-vda="del" title="Apagar (vai para a lixeira da pasta de vídeos)">🗑</button></td></tr>`).join(''):'<tr><td colspan="7" class="muted">Nenhum vídeo.</td></tr>';
 $('vdPlayer').hidden=true;$('vdPlayer').removeAttribute('src');if(!$('videosDlg').open)$('videosDlg').showModal()}
$('vdRows')?.addEventListener('click',guard(async e=>{const b=e.target.closest('[data-vda]');if(!b)return;const name=b.closest('[data-vd]').dataset.vd;
 if(b.dataset.vda==='ver'){const p=$('vdPlayer');p.src=`/api/projects/${pid}/videos/${encodeURIComponent(name)}`;p.hidden=false;p.play().catch(()=>{});return}
 if(!await confirmBox(`Apagar o vídeo “${name}”? Ele vai para a lixeira da pasta de vídeos (Limpar memória esvazia).`,'Apagar','Cancelar'))return;
 await api(`/api/projects/${pid}/videos/${encodeURIComponent(name)}`,{method:'DELETE'});await openVideos();msg('Vídeo enviado para a lixeira da pasta de vídeos.')}));
async function openFolder(tipo){const r=await api('/api/abrir_pasta',json('POST',{tipo,pid:pid||null}));msg(r.aberta?`Pasta aberta: ${r.pasta}`:`Pasta: ${r.pasta}`)}
$('vdFolder')?.addEventListener('click',guard(()=>openFolder(pid?'videos_projeto':'videos')));
$('vdClose')?.addEventListener('click',()=>{$('vdPlayer').pause?.();$('videosDlg').close()});
$('videosDlg')?.addEventListener('close',()=>{try{$('vdPlayer').pause()}catch(_e){window.RodoviaErros&&RodoviaErros.avisar('videos_limpeza_atualizar',_e)}});

// ---------- Limpar memória (resíduos) ----------
async function openCleanup(){const r=await api('/api/limpeza');const C=r.categorias||[];
 $('clRows').innerHTML=C.map(c=>`<tr><td><input type="checkbox" data-cl="${c.id}" ${c.padrao&&c.itens?'checked':''} ${c.itens?'':'disabled'}></td><td><b>${esc(c.rotulo)}</b><br><small class="muted">${esc(c.descricao)}</small></td><td>${c.itens}</td><td>${MB(c.bytes)}</td></tr>`).join('');
 const tot=C.reduce((a,c)=>a+c.bytes,0);$('clInfo').textContent=`Total recuperável: ${MB(tot)}. Marque o que deseja mover para quarentena por 30 dias.`;if(!$('cleanDlg').open)$('cleanDlg').showModal()}
$('clGo')?.addEventListener('click',guard(async()=>{const cats=[...document.querySelectorAll('#clRows [data-cl]:checked')].map(x=>x.dataset.cl);if(!cats.length)return msg('Marque ao menos um item.',true);
 if(!await confirmBox('Mover os resíduos marcados para quarentena por 30 dias? Os caches são refeitos quando precisar (a próxima prévia ou vídeo demora mais).','Limpar','Cancelar'))return;
 let r;try{r=await api('/api/limpeza',json('POST',{categorias:cats}))}catch(e){if(!/tarefa em andamento/.test(String(e&&e.message||e)))throw e;if(!await confirmBox('Há tarefa em andamento ou na fila. Cancelar as tarefas pendentes e limpar?','Cancelar tarefas e limpar','Voltar'))return;r=await api('/api/limpeza',json('POST',{categorias:cats,cancelar_pendentes:true}))}
 await openCleanup();$('clInfo').textContent=`Movidos para quarentena: ${MB(r.bytes)} (${r.items} itens), retidos por 30 dias.`+(r.errors.length?` Não foi possível mover ${r.errors.length} item(ns) em uso.`:'');msg(`Limpeza concluída: ${MB(r.bytes)} em quarentena. O espaço físico será liberado após a retenção.`)}));
$('clClose')?.addEventListener('click',()=>$('cleanDlg').close());

// ---------- Atualizar pelo aplicativo ----------
async function openUpdate(){const r=await api('/api/atualizacao');const F=r.encontradas||[];const nova=F.find(f=>f.mais_nova||f.reparo_disponivel);
 $('updBody').innerHTML=`<p>Versão instalada: <b>${esc(r.instalada)}</b></p>`+(F.length?`<table class="tbl"><tr><th>ZIP encontrado</th><th>Versão</th><th>Pasta</th></tr>${F.map(f=>`<tr><td>${esc(f.arquivo)}</td><td>${esc(f.versao)}${f.mais_nova?' <b>(nova)</b>':f.reparo_disponivel?' (verificar/reparar)':''}</td><td><small>${esc(f.pasta)}</small></td></tr>`).join('')}</table>`:'<p class="muted">Nenhum ZIP de atualização encontrado. Salve o arquivo RodoviaStudio_&lt;versão&gt;_atualizacao.zip na pasta “atualizacoes”.</p>')+
  (nova?((r.modo==='cmd'||r.modo==='exe')?`<p>O Rodovia Studio vai fechar, aplicar a versão ${esc(nova.versao)} numa janela própria e pedir para reabrir o aplicativo. Projetos e vídeos não são alterados.</p>`:r.modo==='exe'?'<p>Aberto pelo Rodovia Studio.exe: clique com o botão direito no ícone perto do relógio › <b>Procurar e aplicar atualização</b>.</p>':'<p class="muted">Atualização automática só na instalação do Windows.</p>'):'')+(r.rollback?`<p class="muted">Versão anterior disponível para restabelecimento${r.rollback.previous?`: <b>${esc(r.rollback.previous)}</b>`:''}. O rollback afeta somente arquivos do programa.</p>`:'');
 $('updGo').hidden=!(nova&&(r.modo==='cmd'||r.modo==='exe'));$('updRestore').hidden=!(r.rollback&&(r.modo==='cmd'||r.modo==='exe'));$('updDlg').dataset.pasta=r.pasta_atualizacoes;if(!$('updDlg').open)$('updDlg').showModal()}
$('updGo')?.addEventListener('click',guard(async()=>{if(!await confirmBox('Fechar o Rodovia Studio e aplicar a atualização agora?','Atualizar','Cancelar'))return;if(!await window.rodoviaPrepararAtualizacao())return;
 await api('/api/atualizacao/aplicar',{method:'POST'});$('updBody').innerHTML='<p><b>Atualizando…</b> Esta janela vai parar de responder; reabra o Rodovia Studio após a confirmação de conclusão.</p>';$('updGo').hidden=true}));
$('updRestore')?.addEventListener('click',guard(async()=>{if(!await confirmBox('Restabelecer a versão anterior do Rodovia Studio? Projetos e vídeos serão preservados. Antes do rollback será criado um snapshot de segurança da versão atual.','Restabelecer','Cancelar'))return;if(!await window.rodoviaPrepararAtualizacao())return;await api('/api/atualizacao/restaurar',{method:'POST'});$('updBody').innerHTML='<p><b>Restabelecendo…</b> O aplicativo será fechado. Reabra após a confirmação de conclusão.</p>';$('updGo').hidden=true;$('updRestore').hidden=true}));
$('updFolder')?.addEventListener('click',guard(()=>openFolder('atualizacoes')));
$('updClose')?.addEventListener('click',()=>$('updDlg').close());

// Menu Arquivo, faixa de opções e comandos.
itemArquivo('Excluir projeto…',null,['Vídeos gerados…',()=>guard(openVideos)()],['Limpar memória (resíduos)…',()=>guard(openCleanup)()],['Atualizar o Rodovia Studio…',()=>guard(openUpdate)()]);
itemFaixa('Vídeo','Vídeos',['Vídeos gerados','🎞',()=>guard(openVideos)(),1]);itemFaixa('Vídeo','Vídeos',['Pasta de vídeos','📁',()=>guard(()=>openFolder(pid?'videos_projeto':'videos'))()]);
itemFaixa('Vídeo','Suporte',['Limpar memória','🧹',()=>guard(openCleanup)()]);itemFaixa('Vídeo','Suporte',['Atualizar','⭳',()=>guard(openUpdate)()]);
comando(['VIDEOS','VID'],()=>guard(openVideos)(),'Vídeos gerados do projeto (assistir, baixar, apagar, abrir a pasta)');
comando(['LIMPAR','LIMPEZA'],()=>guard(openCleanup)(),'Limpar memória: apaga resíduos (caches, temporários, registros antigos, lixeira)');
comando(['ATUALIZAR'],()=>guard(openUpdate)(),'Procura e aplica a atualização mais nova');
comando(['VERSAOANTERIOR','ROLLBACK'],()=>guard(openUpdate)(),'Abre Atualização para restabelecer a versão anterior');
// Ao concluir um vídeo, a mensagem lembra que ele foi guardado e oferece a lista.
estender('poll',anterior=>async function(jid){const r=await anterior(jid);try{const j=await api('/api/jobs/'+jid);if(j.kind==='render'&&j.state==='done'&&/guardado em/.test(j.message||''))msg(j.message+' — Arquivo › Vídeos gerados para ver todos.')}catch(_e){window.RodoviaErros&&RodoviaErros.avisar('videos_limpeza_atualizar',_e)}return r},'vídeos: aviso do arquivo guardado');

// O iniciador aguarda esta promessa antes de encerrar a janela e o servidor.
window.rodoviaPrepararAtualizacao=async function(){
 try{
  if(task||taskRequestPending){msg('Há uma tarefa em andamento. Aguarde a conclusão ou use Cancelar; depois aplique a atualização.');return false}
  if((typeof draft!=='undefined'&&draft)||(typeof cadCmd!=='undefined'&&cadCmd)){msg('Conclua ou cancele o comando em andamento antes de atualizar.',true);return false}
  if(pid){clearTimeout(saveTimer);await save()}
  try{await api('/api/atualizacao/pronto')}catch(e){if(e.status===409){msg(e.message);return false}throw e}
  return true;
 }catch(e){msg('Não foi possível salvar o projeto. Atualização adiada: '+e.message,true);return false}
};

comando(['QUARENTENA'],async()=>{const r=await api('/api/limpeza/quarentena');const d=document.createElement('dialog');d.className='winDlg rsModelDialog';d.innerHTML='<header><h2>Quarentena · 30 dias</h2><button data-close aria-label="Fechar">×</button></header><section><p>Exclusão definitiva após 30 dias, verificada ao abrir o aplicativo e a cada 12 horas enquanto estiver aberto. Restaurar não sobrescreve arquivos existentes.</p>'+r.items.map(i=>`<p>${esc(i.name)} · ${esc(i.category)} <button data-restore="${esc(i.id)}">Restaurar</button></p>`).join('')+'<p data-error></p></section><footer><button data-close>Fechar</button></footer>';document.body.appendChild(d);d.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>{d.close();d.remove()});d.querySelectorAll('[data-restore]').forEach(b=>b.onclick=guard(async()=>{try{await api('/api/limpeza/quarentena/restaurar',json('POST',{token:b.dataset.restore}));b.closest('p').remove();msg('Item restaurado.')}catch(e){d.querySelector('[data-error]').textContent=e.message}}));d.showModal();},'Lista e restaura resíduos em quarentena antes da exclusão após 30 dias');

comando(['SANITIZAR'],async()=>{const r=await api('/api/higiene/inventario');const d=document.createElement('dialog');d.className='winDlg rsModelDialog';d.innerHTML='<header><h2>Sanitizar instalação</h2><button data-close aria-label="Fechar">×</button></header><section><p>Prévia dos arquivos fora de uso na instalação. Feche o aplicativo antes de executar LIMPAR E VERIFICAR.cmd. O script move os itens escolhidos para quarentena por 30 dias, mantendo o programa ativo, projetos e backups recentes.</p><table>'+r.itens.map(i=>`<tr><td>${esc(i.caminho)}</td><td>${MB(i.bytes)}</td><td>${esc(i.motivo)}</td></tr>`).join('')+'</table><p>Duplicados de vídeos: use Limpar memória → Vídeos duplicados por conteúdo. Restauração: comando QUARENTENA para resíduos; o script informa como restaurar a quarentena da instalação.</p></section><footer><button data-close>Fechar</button></footer>';document.body.appendChild(d);d.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>{d.close();d.remove()});d.showModal();},'Inventaria sobras da instalação para limpeza com quarentena de 30 dias');
