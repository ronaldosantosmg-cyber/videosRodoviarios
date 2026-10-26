// =====================================================================================================
// 1.33: mais área para o desenho.
//  • Barra da direita (propriedades, marcações, ajuste DXF × imagem, conexões, avisos) vira um painel com abas,
//    que recolhe numa faixa de ícones e reabre sozinho ao editar (seleção); cada aba pode virar janela flutuante.
//  • “Área máxima”: esconde a coluna da esquerda e recolhe a barra da direita; ela volta quando é preciso editar.
//  • Mensagens, barra de progresso, tempo e Cancelar ficam na barra de status (rodapé); Registros e “Gerar vídeo”
//    ficam nos menus. Tempos acima de 60 s aparecem em minutos.
// =====================================================================================================

// ---------- tempos legíveis ----------
function tempo(s){s=Number(s);if(!isFinite(s))return '—';s=Math.max(0,Math.round(s));if(s<60)return s+' s';
 if(s<3600){const m=Math.floor(s/60),r=s%60;return r?`${m} min ${String(r).padStart(2,'0')} s`:`${m} min`}
 const h=Math.floor(s/3600),m=Math.floor((s%3600)/60);return m?`${h} h ${String(m).padStart(2,'0')} min`:`${h} h`}
function tempoTexto(t){return String(t??'').replace(/(\d+(?:[.,]\d+)?)\s?s\b(?! *\/)/g,(m,n)=>{const v=Number(String(n).replace(',','.'));return v>=60?tempo(v):m})}

// ---------- preferências ----------
const AREA={get(k,d){try{const v=localStorage.getItem('rodovia_area_'+k);return v==null?d:JSON.parse(v)}catch{return d}},set(k,v){try{localStorage.setItem('rodovia_area_'+k,JSON.stringify(v))}catch{}}};

// ---------- painel da direita com abas ----------
const DOCK_ITENS=[{id:'prop',t:'Propriedades',ico:'☰'},{id:'marc',t:'Marcações do projeto',ico:'📌'},{id:'ajuste',t:'Ajuste DXF × imagem',ico:'⌖'},{id:'fluxos',t:'Conexões de tráfego',ico:'⤳'},{id:'avisos',t:'Avisos da análise',ico:'⚠'}];
let dockClosedSelection=null;
function dockSelectionKey(){return JSON.stringify([typeof sel!=='undefined'?sel:null,typeof selSeg!=='undefined'?selSeg?.id:null,typeof selLink!=='undefined'?selLink:null,typeof dxfSel!=='undefined'?dxfSel?.id:null])}
let dockState={aba:AREA.get('aba','marc'),recolhida:AREA.get('recolhida',false),fixada:AREA.get('fixada',true),soltas:AREA.get('soltas',{})},dockAuto=false;
function montarDock(){const side=document.querySelector('.editorSide');if(!side||side.dataset.dock)return;side.dataset.dock='1';side.classList.add('dock');
 const det=[...side.querySelectorAll(':scope>details')];const els={prop:[$('propPanel')],marc:[det[0]],ajuste:[det[1]],fluxos:[det[2]],avisos:[$('warnings'),$('geom')]};
 const head=document.createElement('div');head.className='dockHead';
 head.innerHTML=DOCK_ITENS.map(i=>`<button type="button" class="dockTab" data-dt="${i.id}" title="${esc(i.t)}"><span class="di">${i.ico}</span><span class="dl">${esc(i.t)}</span><span class="db" hidden></span></button>`).join('')+
  `<span class="grow"></span><button type="button" class="dockBtn" data-dk="pin" title="Fixar / desafixar a barra">📌</button><button type="button" class="dockBtn" data-dk="pop" title="Destacar esta aba numa janela flutuante">⧉</button><button type="button" class="dockBtn" data-dk="col" title="Recolher / expandir a barra (mais área para o desenho)">⯈</button>`;
 const box=document.createElement('div');box.className='dockItems';
 for(const it of DOCK_ITENS){const d=document.createElement('div');d.className='dockItem';d.dataset.dock=it.id;
  d.innerHTML=`<div class="dockTitle">${esc(it.t)}</div>`;for(const e of els[it.id])if(e){if(e.tagName==='DETAILS')e.open=true;d.appendChild(e)}
  if(it.id==='prop')d.insertAdjacentHTML('beforeend','<p class="dockEmpty muted">Clique num objeto do desenho (ou numa área, trajetória ou ligação) para ver e editar as propriedades aqui.</p>');
  box.appendChild(d)}
 side.prepend(box);side.prepend(head);
 // Uma aba destacada continua sendo a mesma: os elementos (ids, eventos) só mudam de lugar.
 head.addEventListener('click',e=>{const t=e.target.closest('[data-dt]');if(t){abrirAba(t.dataset.dt,true);return}
  const b=e.target.closest('[data-dk]');if(!b)return;if(b.dataset.dk==='col')recolherDock(!dockState.recolhida);else if(b.dataset.dk==='pin')fixarDock(!dockState.fixada);else destacar(dockState.aba)});
 aplicarDock();for(const id of Object.keys(dockState.soltas||{}))if(dockState.soltas[id])destacar(id,true);
 // Editar reapresenta o painel: ao selecionar um objeto, a aba Propriedades abre sozinha (e recolhe de novo depois).
 const pp=$('propPanel');new MutationObserver(()=>{const vis=!pp.hidden;atualizarAvisos();
  const solta=document.querySelector('.floatWin[data-dock="prop"]');
  if(solta){solta.classList.toggle('vazia',!vis);return}
  if(vis&&dockClosedSelection!==dockSelectionKey()&&(dockState.recolhida||dockState.aba!=='prop')){dockAuto={antes:dockState.aba,recolhida:dockState.recolhida};dockState.aba='prop';dockState.recolhida=false;aplicarDock(false)}
  else if(!vis&&dockAuto){dockState.aba=dockAuto.antes;dockState.recolhida=dockAuto.recolhida;dockAuto=false;aplicarDock(false)}
  document.querySelector('.dockItem[data-dock="prop"]')?.classList.toggle('vazia',!vis)}).observe(pp,{attributes:true,attributeFilter:['hidden']});
 document.querySelector('.dockItem[data-dock="prop"]')?.classList.toggle('vazia',pp.hidden);
 new MutationObserver(atualizarAvisos).observe($('warnings'),{childList:true,characterData:true,subtree:true});atualizarAvisos()}
function aplicarDock(salvar=true){const side=document.querySelector('.editorSide.dock');if(!side)return;
 const sobre=!dockState.recolhida&&!dockState.fixada;side.classList.toggle('recolhida',!!dockState.recolhida);side.classList.toggle('sobreposta',sobre);document.querySelector('.editorBody')?.classList.toggle('dockRecolhida',!!dockState.recolhida||sobre);
 side.querySelector('[data-dk="pin"]')?.classList.toggle('on',!!dockState.fixada);
 side.querySelectorAll('.dockTab').forEach(b=>b.classList.toggle('on',b.dataset.dt===dockState.aba&&!dockState.recolhida));
 side.querySelectorAll('.dockItem').forEach(d=>d.hidden=d.dataset.dock!==dockState.aba);
 const c=side.querySelector('[data-dk="col"]');if(c){c.textContent=dockState.recolhida?'⯇':'⯈';c.title=dockState.recolhida?'Expandir a barra':'Recolher a barra (mais área para o desenho)'}
 if(salvar){AREA.set('aba',dockState.aba);AREA.set('recolhida',!!dockState.recolhida);AREA.set('fixada',!!dockState.fixada)}
 setTimeout(()=>{try{resizeCanvas()}catch{}},40)}
function abrirAba(id,clique){const solta=document.querySelector(`.floatWin[data-dock="${id}"]`);if(solta){frente(solta);return}
 if(clique&&dockState.aba===id&&!dockState.recolhida){recolherDock(true);return}dockClosedSelection=null;dockState.aba=id;dockState.recolhida=false;dockAuto=false;aplicarDock()}
function recolherDock(v){dockClosedSelection=v?dockSelectionKey():null;dockState.recolhida=v;dockAuto=false;aplicarDock()}
function fixarDock(v){dockState.fixada=v;aplicarDock();msg(v?'Barra lateral fixada: o desenho se ajusta a ela.':'Barra lateral desafixada: abre por cima do desenho.')}
function atualizarAvisos(){const w=$('warnings');const n=w?w.textContent.split('\n').filter(x=>x.trim()).length:0;const b=document.querySelector('.dockTab[data-dt="avisos"] .db');if(b){b.hidden=!n;b.textContent=n}}

// ---------- janelas flutuantes ----------
let zFloat=3000;
function frente(w){w.style.zIndex=++zFloat}
function destacar(id,restaurar){const item=document.querySelector(`.dockItem[data-dock="${id}"]`);if(!item||document.querySelector(`.floatWin[data-dock="${id}"]`))return;
 const meta=DOCK_ITENS.find(i=>i.id===id);const pos=(AREA.get('pos',{})||{})[id]||{x:Math.max(20,innerWidth-420),y:140,w:380,h:Math.min(520,innerHeight-220)};
 const w=document.createElement('div');w.className='floatWin';w.dataset.dock=id;
 w.innerHTML=`<div class="fwHead"><span class="fwT">${meta.ico} ${esc(meta.t)}</span><button type="button" data-fw="dock" title="Voltar para a barra lateral">⇲</button><button type="button" data-fw="close" title="Fechar (volta para a barra lateral)">×</button></div><div class="fwBody"></div>`;
 const body=w.querySelector('.fwBody');while(item.childNodes.length>1)body.appendChild(item.childNodes[1]);   // mantém o título da aba na barra
 Object.assign(w.style,{left:Math.min(pos.x,innerWidth-200)+'px',top:Math.min(Math.max(pos.y,40),innerHeight-120)+'px',width:pos.w+'px',height:pos.h+'px'});
 document.body.appendChild(w);frente(w);item.classList.add('solto');item.insertAdjacentHTML('beforeend',`<p class="dockSolto muted">Esta aba está numa janela flutuante. <a href="#" data-fwfront="${id}">Mostrar</a> · <a href="#" data-fwdock="${id}">Voltar para cá</a></p>`);
 if(id==='prop')w.classList.toggle('vazia',$('propPanel').hidden);
 const sol={...(dockState.soltas||{}),[id]:true};dockState.soltas=sol;AREA.set('soltas',sol);
 if(!restaurar){const outra=DOCK_ITENS.find(i=>i.id!==id&&!document.querySelector(`.floatWin[data-dock="${i.id}"]`));if(dockState.aba===id&&outra){dockState.aba=outra.id;aplicarDock()}}
 // Arrastar pelo título; tamanho pelo canto (CSS resize). Posição lembrada.
 const guardar=()=>{const r=w.getBoundingClientRect();const P=AREA.get('pos',{})||{};P[id]={x:Math.round(r.left),y:Math.round(r.top),w:Math.round(r.width),h:Math.round(r.height)};AREA.set('pos',P)};
 w.addEventListener('pointerdown',()=>frente(w));
 w.querySelector('.fwHead').addEventListener('pointerdown',e=>{if(e.target.closest('button'))return;e.preventDefault();const r=w.getBoundingClientRect(),dx=e.clientX-r.left,dy=e.clientY-r.top;
  const mv=ev=>{w.style.left=Math.min(innerWidth-80,Math.max(0,ev.clientX-dx))+'px';w.style.top=Math.min(innerHeight-40,Math.max(0,ev.clientY-dy))+'px'};
  const up=()=>{window.removeEventListener('pointermove',mv);window.removeEventListener('pointerup',up);guardar()};window.addEventListener('pointermove',mv);window.addEventListener('pointerup',up)});
 new ResizeObserver(()=>{clearTimeout(w._rt);w._rt=setTimeout(guardar,300)}).observe(w);
 w.querySelector('.fwHead').addEventListener('click',e=>{const b=e.target.closest('[data-fw]');if(b)encaixar(id)})}
function encaixar(id){const w=document.querySelector(`.floatWin[data-dock="${id}"]`);const item=document.querySelector(`.dockItem[data-dock="${id}"]`);if(!w||!item)return;
 item.querySelector('.dockSolto')?.remove();const body=w.querySelector('.fwBody');while(body.firstChild)item.appendChild(body.firstChild);w.remove();item.classList.remove('solto');
 const sol={...(dockState.soltas||{})};delete sol[id];dockState.soltas=sol;AREA.set('soltas',sol);dockState.aba=id;dockState.recolhida=false;aplicarDock()}
document.addEventListener('click',e=>{const a=e.target.closest&&e.target.closest('[data-fwfront],[data-fwdock]');if(!a)return;e.preventDefault();
 if(a.dataset.fwdock)encaixar(a.dataset.fwdock);else{const w=document.querySelector(`.floatWin[data-dock="${a.dataset.fwfront}"]`);if(w){frente(w);w.classList.remove('vazia')}}});

// ---------- área máxima para o desenho ----------
let areaMax=AREA.get('max',false);
function aplicarAreaMax(){document.body.classList.toggle('areaMax',!!areaMax);if(areaMax&&!dockAuto){dockState.recolhida=true;aplicarDock(false)}
 const b=document.querySelector('[data-area="max"]');if(b)b.classList.toggle('on',!!areaMax);setTimeout(()=>{try{resizeCanvas()}catch{}},60)}
function alternarAreaMax(v){areaMax=v??!areaMax;AREA.set('max',areaMax);if(!areaMax){dockState.recolhida=AREA.get('recolhida_antes',false);aplicarDock()}else AREA.set('recolhida_antes',!!dockState.recolhida);aplicarAreaMax();
 msg(areaMax?'Área máxima: a coluna da esquerda e a barra lateral saem da frente. Ao editar, as propriedades aparecem; os menus continuam na faixa de opções. F10 volta.':'Colunas laterais de volta.')}
// Abrir uma seção pela faixa de opções mostra a coluna da esquerda (só enquanto for preciso).
estender('openSection',anterior=>function(title){if(areaMax){document.body.classList.add('areaMaxTemp');setTimeout(()=>{try{resizeCanvas()}catch{}},60)}return anterior(title)},'área máxima: seção abre a coluna da esquerda');
canvas.addEventListener('pointerdown',()=>{if(document.body.classList.contains('areaMaxTemp')){document.body.classList.remove('areaMaxTemp');setTimeout(()=>{try{resizeCanvas()}catch{}},60)}});
document.addEventListener('keydown',e=>{if(e.key==='F10'&&!e.ctrlKey&&!e.altKey){e.preventDefault();alternarAreaMax()}});

// ---------- rodapé: mensagens, progresso, tempo e Cancelar ----------
function montarRodape(){const ta=$('taskArea');if(!ta||ta.dataset.ok)return;ta.dataset.ok='1';
 const m=$('message'),p=$('progress'),c=$('cancel');
 ta.innerHTML='<span id="taskTime" class="taskTime" hidden></span>';ta.prepend(p);ta.prepend(m);ta.appendChild(c);
 m.classList.add('sbMsg');m.title='Clique para ver a mensagem inteira';p.classList.add('sbProg');c.classList.add('sbCancel');c.textContent='Cancelar';
 m.addEventListener('click',()=>abrirMensagem());
 // Seções que ficaram vazias saem da coluna (o conteúdo foi para o rodapé e para os menus).
 for(const id of ['logSection'])$(id)?.classList.add('retirada');
 const prog=[...document.querySelectorAll('main section')].find(s=>/Progresso e resultado/.test(s.querySelector('h2')?.textContent||''));
 if(prog){prog.classList.add('retirada');prog.id=prog.id||'progressSection'}
 $('render')?.classList.add('retirada')}
let taskStart=0,taskTimer=null;
function marcarTarefa(on){const ta=$('taskArea');if(!ta)return;ta.classList.toggle('running',on);$('taskTime').hidden=!on;clearInterval(taskTimer);
 if(on){taskStart=taskStart||Date.now();const tick=()=>{const el=(Date.now()-taskStart)/1000,pv=Number($('progress').value)||0;
   const rest=pv>.03?el*(1-pv)/pv:null;$('taskTime').textContent=`${Math.round(pv*100)}% · ${tempo(el)}${rest!=null?` · falta ~${tempo(rest)}`:''}`};tick();taskTimer=setInterval(tick,1000)}
 else taskStart=0}
estender('poll',anterior=>async function(jid){marcarTarefa(true);try{return await anterior(jid)}finally{marcarTarefa(false)}},'rodapé: progresso e tempo da tarefa');
estender('msg',anterior=>function(s,error=false){const t=tempoTexto(s);anterior(t,error);const m=$('message');if(m){m.title=t+'\n\n(Clique para ver a mensagem inteira)';m.classList.remove('pisca');void m.offsetWidth;m.classList.add('pisca')}},'rodapé: mensagens com tempos em minutos');
function abrirMensagem(){const m=$('message');let d=$('msgDlg');
 if(!d){document.body.insertAdjacentHTML('beforeend','<dialog id="msgDlg" class="winDlg"><h3>Mensagem</h3><pre id="msgFull" class="msgFull"></pre><div class="row"><button type="button" id="msgLogs">Ver registros…</button><span class="grow"></span><button type="button" class="primary" id="msgOk">Fechar</button></div></dialog>');
  d=$('msgDlg');arrumarJanela(d);$('msgOk').onclick=()=>d.close();$('msgLogs').onclick=()=>{d.close();openLogs(m.classList.contains('error')?'erros':'execucao')}}
 $('msgFull').textContent=m.textContent;$('msgFull').classList.toggle('erro',m.classList.contains('error'));d.showModal()}

// ---------- menus: gerar vídeo, registros, área máxima ----------
$('areaMaxBtn')?.addEventListener('click',()=>alternarAreaMax());
function gerarVideo(){$('render')?.click()}
function verRegistros(){guard(()=>openLogs('execucao'))()}
function cancelarTarefa(){const c=$('cancel');if(c&&!c.disabled)c.click();else msg('Nenhuma tarefa em andamento.')}
itemArquivo('Registros e suporte',['Baixar registros (.zip)',()=>baixarRegistros()],['Detalhes do último erro',()=>$('logs')?.click()]);
// A faixa de opções é o menu superior: “Gerar vídeo” fica em Início › Vídeo e na aba Vídeo (com os registros).
itemFaixa('Início','Vídeo',['Gerar vídeo','🎬',()=>gerarVideo(),1]);itemFaixa('Início','Vídeo',['Vídeos gerados','🎞',()=>guard(openVideos)()]);
itemFaixa('Vídeo','Gerar',['Configurar vídeo','⚙',()=>openSection('5. Exportar vídeo')]);itemFaixa('Vídeo','Gerar',['Cancelar','⏹',()=>cancelarTarefa()]);
itemFaixa('Vídeo','Suporte',['Baixar registros (.zip)','⭳',()=>baixarRegistros()]);itemFaixa('Vídeo','Suporte',['Detalhes do erro','⚠',()=>$('logs')?.click()]);
{const X=RIBBON.find(t=>t[0]==='Exibir');X[1].unshift(['Área de trabalho',[['Área máxima','⛶',()=>alternarAreaMax(),1],['Barra lateral','◨',()=>recolherDock(!dockState.recolhida),1],['Destacar aba','⧉',()=>destacar(dockState.aba)],['Encaixar janelas','⇲',()=>Object.keys(dockState.soltas||{}).forEach(encaixar)]]])}
// “Painel lateral” (Ctrl+Shift+L, PAINEL) passa a recolher/expandir a barra em abas.
if($('toggleSide'))$('toggleSide').onclick=()=>recolherDock(!dockState.recolhida);
comando(['AREA','MAX','AREAMAX'],()=>alternarAreaMax(),'Área máxima para o desenho (F10): esconde as colunas laterais');
comando(['VIDEO','GERAR'],()=>gerarVideo(),'Gera um novo vídeo (fica guardado em videos\\<projeto>)');

montarDock();montarRodape();aplicarAreaMax();
// Ao concluir um vídeo, a lista de vídeos gerados abre sozinha (assistir, baixar, abrir a pasta).
estender('poll',anterior=>async function(jid){const r=await anterior(jid);try{const j=await api('/api/jobs/'+jid);if(j.kind==='render'&&j.state==='done'&&pid)await openVideos()}catch{}return r},'vídeo pronto: abre a lista de vídeos gerados');
