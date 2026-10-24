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
$('videosDlg')?.addEventListener('close',()=>{try{$('vdPlayer').pause()}catch{}});

// ---------- Limpar memória (resíduos) ----------
async function openCleanup(){const r=await api('/api/limpeza');const C=r.categorias||[];
 $('clRows').innerHTML=C.map(c=>`<tr><td><input type="checkbox" data-cl="${c.id}" ${c.padrao&&c.itens?'checked':''} ${c.itens?'':'disabled'}></td><td><b>${esc(c.rotulo)}</b><br><small class="muted">${esc(c.descricao)}</small></td><td>${c.itens}</td><td>${MB(c.bytes)}</td></tr>`).join('');
 const tot=C.reduce((a,c)=>a+c.bytes,0);$('clInfo').textContent=`Total recuperável: ${MB(tot)}. Marque o que deseja apagar.`;if(!$('cleanDlg').open)$('cleanDlg').showModal()}
$('clGo')?.addEventListener('click',guard(async()=>{const cats=[...document.querySelectorAll('#clRows [data-cl]:checked')].map(x=>x.dataset.cl);if(!cats.length)return msg('Marque ao menos um item.',true);
 if(!await confirmBox('Apagar os resíduos marcados? Os caches são refeitos quando precisar (a próxima prévia ou vídeo demora mais).','Limpar','Cancelar'))return;
 const r=await api('/api/limpeza',json('POST',{categorias:cats}));await openCleanup();$('clInfo').textContent=`Liberados ${MB(r.bytes)} (${r.items} itens).`+(r.errors.length?` Não foi possível apagar ${r.errors.length} item(ns) em uso.`:'');msg(`Limpeza concluída: ${MB(r.bytes)} liberados.`)}));
$('clClose')?.addEventListener('click',()=>$('cleanDlg').close());

// ---------- Atualizar pelo aplicativo ----------
async function openUpdate(){const r=await api('/api/atualizacao');const F=r.encontradas||[];const nova=F.find(f=>f.mais_nova);
 $('updBody').innerHTML=`<p>Versão instalada: <b>${esc(r.instalada)}</b></p>`+(F.length?`<table class="tbl"><tr><th>ZIP encontrado</th><th>Versão</th><th>Pasta</th></tr>${F.map(f=>`<tr><td>${esc(f.arquivo)}</td><td>${esc(f.versao)}${f.mais_nova?' <b>(nova)</b>':''}</td><td><small>${esc(f.pasta)}</small></td></tr>`).join('')}</table>`:'<p class="muted">Nenhum ZIP de atualização encontrado. Salve o arquivo RodoviaStudio_&lt;versão&gt;_atualizacao.zip na pasta “atualizacoes” (ou em Downloads).</p>')+
  (nova?(r.modo==='cmd'?`<p>O Rodovia Studio vai fechar, aplicar a versão ${esc(nova.versao)} numa janela própria e abrir de novo. Projetos e vídeos não são alterados.</p>`:r.modo==='exe'?'<p>Aberto pelo Rodovia Studio.exe: clique com o botão direito no ícone perto do relógio › <b>Procurar e aplicar atualização</b>.</p>':'<p class="muted">Atualização automática só na instalação do Windows.</p>'):'')+(r.rollback?`<p class="muted">Versão anterior disponível para restabelecimento${r.rollback.previous?`: <b>${esc(r.rollback.previous)}</b>`:''}. O rollback afeta somente arquivos do programa.</p>`:'');
 $('updGo').hidden=!(nova&&r.modo==='cmd');$('updRestore').hidden=!(r.rollback&&r.modo==='cmd');$('updDlg').dataset.pasta=r.pasta_atualizacoes;if(!$('updDlg').open)$('updDlg').showModal()}
$('updGo')?.addEventListener('click',guard(async()=>{if(!await confirmBox('Fechar o Rodovia Studio e aplicar a atualização agora?','Atualizar','Cancelar'))return;if(pid){clearTimeout(saveTimer);try{await save()}catch{}}
 await api('/api/atualizacao/aplicar',{method:'POST'});$('updBody').innerHTML='<p><b>Atualizando…</b> Esta janela vai parar de responder; o Rodovia Studio abre de novo ao terminar.</p>';$('updGo').hidden=true}));
$('updRestore')?.addEventListener('click',guard(async()=>{if(!await confirmBox('Restabelecer a versão anterior do Rodovia Studio? Projetos e vídeos serão preservados. Antes do rollback será criado um snapshot de segurança da versão atual.','Restabelecer','Cancelar'))return;if(pid){clearTimeout(saveTimer);try{await save()}catch{}}await api('/api/atualizacao/restaurar',{method:'POST'});$('updBody').innerHTML='<p><b>Restabelecendo…</b> O aplicativo será fechado e abrirá novamente ao concluir.</p>';$('updGo').hidden=true;$('updRestore').hidden=true}));
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
estender('poll',anterior=>async function(jid){const r=await anterior(jid);try{const j=await api('/api/jobs/'+jid);if(j.kind==='render'&&j.state==='done'&&/guardado em/.test(j.message||''))msg(j.message+' — Arquivo › Vídeos gerados para ver todos.')}catch{}return r},'vídeos: aviso do arquivo guardado');
