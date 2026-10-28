// ---------- sessões de trabalho ----------
let lastAutoSession=null,sessTimer=null;
function sessionState(){const c=ready()?C2W(canvas.width/2,canvas.height/2):null,a=ready()?C2W(0,canvas.height/2):null,b=ready()?C2W(canvas.width,canvas.height/2):null;
 return {view:c?{cx:c.x,cy:c.y,w:Math.hypot(b.x-a.x,b.y-a.y)}:null,tool,baseMode,vecOn:{...vecOn},hud:hudOn,snap:$('snapOn')?.checked,ortho:$('orthoOn')?.checked,alignMode,
  collapsed:[...document.querySelectorAll('main section.collapsed')].map(s=>s.id||s.querySelector('h2')?.textContent||''),open:[...document.querySelectorAll('#editorSection details[open]')].map(d=>d.querySelector('summary')?.textContent||''),
  selection:allSelected().map(o=>({key:o.key,i:o.i})),layerShow:layerShow?.name||null,preview_mode:$('preview_mode')?.value}}
function restoreSession(st){if(!st)return;if(st.view&&ready()){const [ix,iy]=worldToImg({x:st.view.cx,y:st.view.cy});view.s=Math.max(minScale(),Math.min(useGeo()?240:60,canvas.width*mpp()/Math.max(1,st.view.w)));view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s}
 if(st.vecOn)Object.assign(vecOn,st.vecOn);if(st.baseMode&&$('baseMode')){baseMode=st.baseMode;$('baseMode').value=st.baseMode}
 if(typeof st.hud==='boolean'){hudOn=st.hud;if($('hudOn'))$('hudOn').checked=hudOn}for(const [id,v] of [['snapOn',st.snap],['orthoOn',st.ortho]])if(typeof v==='boolean'&&$(id))$(id).checked=v;
 if(st.alignMode)alignMode=st.alignMode;if(st.preview_mode&&$('preview_mode'))$('preview_mode').value=st.preview_mode;
 document.querySelectorAll('main section').forEach(s=>{const id=s.id||s.querySelector('h2')?.textContent||'';if(st.collapsed&&s.querySelector('h2.collapsible'))s.classList.toggle('collapsed',st.collapsed.includes(id))});
 document.querySelectorAll('#editorSection details').forEach(d=>{const t=d.querySelector('summary')?.textContent||'';if(st.open)d.open=st.open.includes(t)});
 const S=(st.selection||[]).filter(s=>objOf(s));selSet=S.length>1?S:[];sel=S[S.length-1]||null;showProps();
 if(st.tool&&TOOLS.some(t=>t[0]===st.tool))setTool(st.tool);else draw();resizeCanvas()}
async function sessionsUi(){if(!pid||!$('sessList'))return;const project=pid,context=projectSession.context;let r;try{r=await api(`/api/projects/${project}/sessoes`)}catch{return}if(pid!==project||projectSession.context!==context)return;const cur=$('sessList').value;
 lastAutoSession=(r.sessions.find(s=>s.name==='(última)')||{}).state||null;
 $('sessList').innerHTML='<option value="">— sessões salvas —</option>'+r.sessions.map(s=>`<option value="${esc(s.name)}">${esc(s.name)} · ${esc(s.saved||'')}</option>`).join('');if(cur&&r.sessions.some(s=>s.name===cur))$('sessList').value=cur;return r.sessions}
async function saveSession(name,quiet){requireProject();const project=pid,context=projectSession.context;await api(`/api/projects/${project}/sessoes/${encodeURIComponent(name)}`,json('PUT',{state:sessionState()}));if(pid!==project||projectSession.context!==context)return;if(!quiet){await sessionsUi();if(pid!==project||projectSession.context!==context)return;$('sessList').value=name;msg(`Sessão “${name}” salva (vista, ferramenta, camadas e painéis).`)}}
$('sessSave')?.addEventListener('click',()=>saveSessionPrompt());
$('sessLoad')?.addEventListener('click',guard(async()=>{const project=pid,context=projectSession.context,name=$('sessList').value;if(!name)throw Error('Escolha uma sessão na lista.');const r=await sessionsUi();if(pid!==project||projectSession.context!==context||$('sessList').value!==name)return;const s=(r||[]).find(x=>x.name===name);if(!s)throw Error('Sessão não encontrada.');restoreSession(s.state);msg(`Sessão “${name}” restaurada.`)}));
$('sessDel')?.addEventListener('click',guard(async()=>{const name=$('sessList').value;if(!name)throw Error('Escolha uma sessão na lista.');if(!await confirmBox(`Apagar a sessão “${name}”? As marcações do projeto não são afetadas.`,'Apagar','Cancelar'))return;await api(`/api/projects/${pid}/sessoes/${encodeURIComponent(name)}`,{method:'DELETE'});await sessionsUi();msg(`Sessão “${name}” apagada.`)}));
{const v=(()=>{try{return localStorage.getItem('rodovia_sessauto')==='1'}catch{return false}})();if($('sessAuto')){$('sessAuto').checked=v;$('sessAuto').onchange=()=>{try{localStorage.setItem('rodovia_sessauto',$('sessAuto').checked?'1':'0')}catch{}}}}
function autoSession(){if(!pid||!ready())return;clearTimeout(sessTimer);sessTimer=setTimeout(()=>saveSession('(última)',true).then(()=>{lastAutoSession=sessionState()}).catch(()=>{}),4000)}
canvas.addEventListener('wheel',autoSession,{passive:true});canvas.addEventListener('pointerup',autoSession);
window.addEventListener('beforeunload',()=>{if(!pid||!ready())return;try{navigator.sendBeacon&&fetch(`/api/projects/${pid}/sessoes/${encodeURIComponent('(última)')}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({state:sessionState()}),keepalive:true})}catch{}});
estender('load',_l=>async (id,options={})=>{const loaded=await _l(id,options);if(loaded===false||pid!==id)return false;if(options.resultsOnly)return loaded;const S=await sessionsUi();if($('sessAuto')?.checked&&lastAutoSession){restoreSession(lastAutoSession);msg('Sessão anterior retomada (vista e ferramenta).')};return loaded},'sessões de trabalho');

// ---------- regenerar prévia ----------
$('regenPreview')?.addEventListener('click',guard(async()=>{requireProject();if(!analysis)throw Error('Analise os arquivos primeiro.');const mode=$('preview_mode').value;msg(`Regenerando a prévia (${$('preview_mode').selectedOptions[0]?.textContent||mode})…`);await start('preview');msg('Prévia regenerada.')}));

// ---------- registros: execução, erros, prompt para IA; erros da tela ----------
async function openLogs(kind){requireProject();const r=await api(`/api/projects/${pid}/registros?tipo=${kind}&limite=500`);$('logTitle').textContent=kind==='erros'?'Registro de erros':'Registro de execução';
 document.querySelectorAll('#logDlg [data-lg]').forEach(b=>b.classList.toggle('primary',b.dataset.lg===kind));
 $('logView').textContent=r.eventos.length?r.eventos.map(e=>kind==='erros'?`${e.t}  ${e.evento}  ${e.tipo||''} ${e.erro||''}\n  ${e.mensagem||''}${e.rastreamento?'\n'+e.rastreamento:''}${e.pilha?'\n'+e.pilha:''}`:`${e.t}  ${String(e.evento).padEnd(6)} ${String(e.tipo||'').padEnd(8)} ${e.progresso!=null?Math.round(e.progresso*100)+'% ':''}${e.mensagem||''}${e.duracao_s!=null?` (${e.duracao_s} s)`:e.s!=null?` (+${e.s} s)`:''}${e.erro?' · '+e.erro:''}`).join('\n'):'Nenhum registro ainda.';
 for(const id of ['logZip','logZip2'])if($(id))$(id).href=`/api/projects/${pid}/registros.zip`;for(const id of ['logPrompt','logPrompt2'])if($(id))$(id).href=`/api/projects/${pid}/prompt_ia.md`;
 if(!$('logDlg').open)$('logDlg').showModal()}
$('logOpen')?.addEventListener('click',guard(()=>openLogs('execucao')));
document.querySelectorAll('#logDlg [data-lg]').forEach(b=>b.addEventListener('click',guard(()=>openLogs(b.dataset.lg))));
$('logClose')?.addEventListener('click',()=>$('logDlg').close());
$('logCopy')?.addEventListener('click',guard(async()=>{requireProject();const t=await (await fetch(`/api/projects/${pid}/prompt_ia.md`)).text();try{await navigator.clipboard.writeText(t);msg(`Prompt copiado (${t.length.toLocaleString('pt-BR')} caracteres). Cole na IA de sua preferência.`)}catch{$('logView').textContent=t;msg('Não foi possível copiar automaticamente: o prompt está na janela; selecione e copie.',true)}}));
$('logClear')?.addEventListener('click',guard(async()=>{if(!await confirmBox('Apagar todos os registros de execução e de erros deste projeto?','Apagar','Cancelar'))return;const r=await api(`/api/projects/${pid}/registros`,{method:'DELETE'});await openLogs('execucao');msg(`${r.removed} arquivo(s) de registro apagados.`)}));
for(const id of ['logPrompt2','logZip2'])$(id)?.addEventListener('click',e=>{if(!pid){e.preventDefault();msg('Abra um projeto.',true);return}e.currentTarget.href=id==='logZip2'?`/api/projects/${pid}/registros.zip`:`/api/projects/${pid}/prompt_ia.md`});
let clientErrs=0;function reportClient(m,stack,acao){if(!pid||clientErrs>40)return;clientErrs++;try{fetch(`/api/projects/${pid}/registros/erro_tela`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensagem:String(m).slice(0,2000),pilha:String(stack||'').slice(0,8000),origem:location.pathname+location.search,acao:String(acao||'').slice(0,300)})}).catch(()=>{})}catch{}}
window.addEventListener('error',e=>reportClient(e.message,e.error&&e.error.stack,'erro de script'));
window.addEventListener('unhandledrejection',e=>reportClient(e.reason&&e.reason.message||String(e.reason),e.reason&&e.reason.stack,'promessa rejeitada'));
estender('msg',_m=>function(s,error=false){_m(s,error);if(error)reportClient(s,'',`mensagem ao usuário (ferramenta ${tool})`)},'registros: execução, erros, prompt para IA; erros da tela');

// ---------- ajudas dos campos novos ----------
Object.assign(HELP,{callout_layout:'Automáticas: as caixas de chamada procuram uma posição livre e não ficam umas sobre as outras; aceitam imagem, estilo e janela de tempo. Clássico: disposição fixa das caixas de chamada.',
 sessList:'Sessões guardam onde você estava: vista, ferramenta, camadas visíveis, painéis abertos e seleção. Não alteram as marcações.',sessAuto:'Ao abrir o projeto, volta para a última vista e ferramenta usadas.',
 layoutWide:'Usa toda a largura da tela; arraste o divisor entre o painel e o editor para ajustar.',layoutCompact:'Menos espaçamento: cabe mais coisa na tela.'});
try{for(const id of ['callout_layout','sessList','sessAuto']){const el=$(id);if(!el)continue;const lab=el.closest('label');if(!lab||lab.querySelector(':scope > .help'))continue;const b=document.createElement('span');b.className='help';b.tabIndex=0;b.textContent='?';b.dataset.help=HELP[id];b.setAttribute('aria-label','Ajuda: '+HELP[id]);const fi=lab.querySelector('input,select');if(fi&&fi.type==='checkbox')lab.appendChild(b);else lab.insertBefore(b,fi)}}catch{}
estender('refreshLists',_rl=>function(){_rl();const box=$('markList');if(!box||!(M.gantries||[]).length)return;
 box.insertAdjacentHTML('beforeend','<h3>Pórticos</h3><table>'+M.gantries.map((g,i)=>`<tr><td>⊓ ${esc(g.name)}</td><td>${Math.hypot(g.b.x-g.a.x,g.b.y-g.a.y).toFixed(2)} m${axisData()&&kmOf(g.a)?' · km '+formatKm(kmOf({x:(g.a.x+g.b.x)/2,y:(g.a.y+g.b.y)/2}).km):''}${g.image?' · 🖼':''}</td><td><button type="button" data-gsel="${i}">Selecionar</button></td></tr>`).join('')+'</table>')},'ajudas dos campos novos');
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('[data-gsel]');if(!b)return;const i=Number(b.dataset.gsel),g=M.gantries[i];if(!g)return;sel={key:'gantries',i};selSet=[];showProps();zoomTo({x:(g.a.x+g.b.x)/2,y:(g.a.y+g.b.y)/2});msg(`Selecionado: ${g.name}. Edite no painel de propriedades.`)});
buildToolbar();


// Catálogo local de falhas e duração, também incluído no prompt IA.
{const copy=$('logCopy');if(copy){const button=document.createElement('button');button.type='button';button.id='logInsights';button.textContent='Desempenho e melhorias';copy.before(button);button.onclick=guard(async()=>{requireProject();const data=await api(`/api/projects/${pid}/catalogo_uso`);$('logView').textContent=JSON.stringify(data,null,2);$('logTitle').textContent='Catálogo de uso: desempenho e melhorias';})}}
