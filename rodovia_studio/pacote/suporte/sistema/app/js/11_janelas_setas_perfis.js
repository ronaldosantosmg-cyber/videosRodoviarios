/* ---------- 1.13: duas janelas sincronizadas (configuração | visualização e resultados) ---------- */
const JANELA=new URLSearchParams(location.search).get('janela')||'unica';const WIN_ID=Math.random().toString(36).slice(2);
document.body.dataset.janela=JANELA;
let bc=null;try{bc=new BroadcastChannel('rodovia_studio')}catch{}
function announce(m){if(!bc||!pid)return;try{bc.postMessage({...m,pid,from:WIN_ID,janela:JANELA})}catch{}}
async function remoteSaved(){
 const r=await api('/api/projects/'+pid);const s=r.config;
 if(JANELA==='visual'){ // a janela de visualização não edita os campos: assume os da configuração e mantém as marcações locais
  const marks={};for(const k of MARK_KEYS)marks[k]=M[k];const keepUndo=[undoStack,redoStack];
  if(savePending){cfg={...s,...marks}}else{fill(s);[undoStack,redoStack]=keepUndo;updateUndo()}
  if(!savePending)for(const k of MARK_KEYS)M[k]=JSON.parse(JSON.stringify(s[k]));
  refreshLists();draw();return}
 if(JANELA==='config'){ // a configuração não edita marcações: assume as da visualização
  for(const k of MARK_KEYS)if(s[k]!==undefined)M[k]=JSON.parse(JSON.stringify(s[k]));cfg={...cfg,...Object.fromEntries(MARK_KEYS.map(k=>[k,s[k]]))};refreshLists();return}
 if(!savePending)await load(pid)}
if(bc)bc.onmessage=async e=>{const m=e.data||{};if(m.from===WIN_ID)return;
 try{
  if(m.t==='project'&&m.pid!==pid){await load(m.pid);return}
  if(m.pid!==pid)return;
  if(m.t==='saved')await remoteSaved();
  else if(m.t==='job'&&!task)await poll(m.id);
  else if(m.t==='hello'&&pid)announce({t:'project'});
 }catch(err){msg(err.message,true)}};
function openTwoWindows(){const w=window.open('/?janela=visual','rodovia_visual','width=1500,height=950');if(!w)return msg('O navegador bloqueou a nova janela: permita pop-ups para 127.0.0.1.',true);
 const u=new URL(location.href);u.searchParams.set('janela','config');history.replaceState(null,'',u);document.body.dataset.janela='config';location.reload()}
$('twoWindows').onclick=openTwoWindows;$('oneWindow').onclick=()=>{const u=new URL(location.href);u.searchParams.delete('janela');location.href=u.toString()};
if(JANELA!=='unica'){$('winLabel').textContent=JANELA==='config'?'Janela de configuração':'Janela de visualização e resultados';setTimeout(()=>{try{bc&&bc.postMessage({t:'hello',from:WIN_ID})}catch{}},600)}

/* ---------- 1.14: setas giráveis, camadas reutilizáveis (perfis), cores por tipo ---------- */
function hitArrow(c,maxPx=16*DPR()){if(!editor||!editor.arrows)return null;let best=null;
 for(const a of editor.arrows){const [x,y]=W2C({x:a[0],y:a[1]});const d=Math.hypot(x-c.cx,y-c.cy);if(d<=maxPx&&(!best||d<best.d))best={d,p:[a[0],a[1]],t:[a[2],a[3]],ref:a}}return best}
function rotateArrow(a,vec){
 // A seta se alinha à faixa: só pode apontar para um dos dois sentidos dela.
 const t=a.t;let sgn=-1;if(vec){const L=Math.hypot(vec.x,vec.y)||1;sgn=(vec.x*t[0]+vec.y*t[1])/L>=0?1:-1;if(sgn>0)return msg('A seta já aponta nesse sentido.')}
 const nt=[t[0]*sgn,t[1]*sgn];checkpoint();
 // 1.15: setas repetidas por faixa levam o ponto da trajetória da via (âncora) para o sentido valer na via toda.
 const P=a.ref.length>=6?[a.ref[4],a.ref[5]]:a.p;
 M.direction_marks=M.direction_marks.filter(m=>Math.hypot((m.start.x+m.end.x)/2-P[0],(m.start.y+m.end.y)/2-P[1])>4);
 M.direction_marks.push({id:uid(),start:{x:P[0]-nt[0]*3,y:P[1]-nt[1]*3},end:{x:P[0]+nt[0]*3,y:P[1]+nt[1]*3}});
 a.ref[2]=nt[0];a.ref[3]=nt[1];if(typeof buildSignage==='function')buildSignage();
 const seg=nearestSegment({x:P[0],y:P[1]},6);if(seg&&sgn<0){seg.forward=!seg.forward}
 changed('Seta girada: o fluxo da faixa passa a seguir a seta. Clique “⟳ Atualizar fluxos” para recalcular a rede (o vídeo usa o novo sentido).')}
let layerShow=null,layerPrev=null;
async function showLayer(name){
 if(layerShow&&layerShow.name===name){layerShow=null;draw();return}
 if(!layerPrev){try{layerPrev=await api('/api/projects/'+pid+'/layers_preview.json')}catch(e){return msg('Analise os arquivos para ver as camadas no editor.',true)}}
 const d=layerPrev[name];if(!d||!d.p.length)return msg('Camada sem geometria desenhável (texto, cota ou bloco vazio).',true);
 layerShow={name,p:d.p};let x0=Infinity,y0=Infinity,x1=-Infinity,y1=-Infinity;for(const q of d.p)for(const [x,y] of q){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y)}
 if(ready()){const c={x:(x0+x1)/2,y:(y0+y1)/2};const [ix,iy]=worldToImg(c);const span=Math.max(40,Math.hypot(x1-x0,y1-y0));view.s=Math.max(minScale(),Math.min(useGeo()?240:60,canvas.width*mpp()/span*.8));view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw()}
 msg(`Camada “${name}” destacada em magenta no editor${d.role?' ('+(roles[d.role]||d.role)+')':' (sem tipo)'}. Clique “Ver” de novo para apagar.`)}
document.addEventListener('click',e=>{const b=e.target.closest('[data-showlayer]');if(!b)return;e.preventDefault();const name=b.dataset.showlayer;if(JANELA==='config'){announce({t:'showLayer',name});msg('Camada destacada na janela de visualização.')}else showLayer(name)});
if(bc){const prev=bc.onmessage;bc.onmessage=async e=>{const m=e.data||{};if(m.t==='showLayer'&&m.pid===pid&&m.from!==WIN_ID){showLayer(m.name);return}if(m.t==='saved'&&m.pid===pid)layerPrev=null;return prev&&prev(e)}}
let profiles=[];
async function loadProfiles(){try{const r=await api('/api/layer_profiles');profiles=r.profiles;$('layerProfile').innerHTML=profiles.map(p=>`<option value="${esc(p.name)}">${esc(p.name)}${p.builtin?'':' ('+p.rules.length+' regras)'}</option>`).join('')}catch(e){}}
$('profileApply').onclick=guard(async()=>{requireProject();if(!analysis&&!sourceLayerCatalog?.layers?.length)throw Error('Importe um DXF para listar as camadas.');const r=await api(`/api/projects/${pid}/layer_profiles/apply`,json('POST',{name:$('layerProfile').value}));
 checkpointLayers();cfg.layer_materials={...(cfg.layer_materials||{}),...(r.materials||{})};document.querySelectorAll('#layers select').forEach(el=>{const role=Object.entries(r.layers).find(([k,v])=>v.includes(el.dataset.layer))?.[0];if(role)el.value=role});await save();msg(`Perfil aplicado: ${r.matched} de ${r.total} camadas reconhecidas. Confira a lista e clique “Analisar arquivos”.`)});
function checkpointLayers(){}
function currentRules(){const rules=[];document.querySelectorAll('#layers select').forEach(el=>{if(el.value)rules.push({pattern:el.dataset.layer,role:el.value})});return rules}
$('profileSave').onclick=guard(async()=>{const name=prompt('Nome do perfil (ex.: Padrão CAD da empresa):');if(!name)return;const rules=currentRules();if(!rules.length)throw Error('Nenhuma camada tem tipo definido.');await api('/api/layer_profiles',json('POST',{name,rules}));await loadProfiles();$('layerProfile').value=name;msg(`Perfil “${name}” salvo com ${rules.length} regras. Use-o em outros projetos (Aplicar perfil). Para generalizar nomes, use “Editar regras” com * e ?.`)});
$('profileEdit').onclick=guard(async()=>{const p=profiles.find(x=>x.name===$('layerProfile').value);const base=p&&!p.builtin?p:{name:'',rules:p?p.rules:currentRules()};
 $('ruleName').value=base.name;$('ruleText').value=base.rules.map(r=>`${r.pattern} => ${r.role}${r.material?' => '+r.material:''}`).join('\n');$('ruleRoles').textContent=Object.entries(roles).map(([k,v])=>k+' = '+v).join(' · ');$('ruleDialog').showModal()});
$('ruleSave').onclick=guard(async e=>{e.preventDefault();const rules=$('ruleText').value.split('\n').map(l=>l.trim()).filter(Boolean).map(l=>{const m=l.split('=>');if(m.length<2||m.length>3)throw Error('Use uma regra por linha: PADRÃO => tipo => material (opcional)');const role=m[1].trim();const key=roles[role]?role:Object.entries(roles).find(([k,v])=>v.toLowerCase()===role.toLowerCase())?.[0];if(!key)throw Error('Tipo desconhecido: '+role);return {pattern:m[0].trim(),role:key,...(m[2]?.trim()?{material:m[2].trim()}:{})}});
 const name=$('ruleName').value.trim();await api('/api/layer_profiles',json('POST',{name,rules}));$('ruleDialog').close();await loadProfiles();$('layerProfile').value=name;msg(`Perfil “${name}” salvo (${rules.length} regras).`)});
$('ruleCancel').onclick=e=>{e.preventDefault();$('ruleDialog').close()};
$('profileDelete').onclick=guard(async()=>{const name=$('layerProfile').value;const p=profiles.find(x=>x.name===name);if(!p||p.builtin)throw Error('O perfil padrão não pode ser excluído.');await api('/api/layer_profiles/'+encodeURIComponent(name),{method:'DELETE'});await loadProfiles();msg(`Perfil “${name}” excluído.`)});
function showRoleColors(){const rc=cfg.role_colors||{};$('roleColors').innerHTML=Object.entries(ROLE_COLOR).map(([k,c])=>`<label class="rc"><input type="color" data-rolecolor="${k}" value="${rc[k]||c}">${esc(roles[k]||k)}</label>`).join('')+'<button id="roleColorsReset" class="mini">Cores padrão</button>'}
document.addEventListener('change',e=>{const k=e.target.dataset?.rolecolor;if(!k)return;cfg.role_colors={...(cfg.role_colors||{}),[k]:e.target.value};scheduleSave();msg('Cor do tipo alterada: vale para a prévia e o vídeo.')});
document.addEventListener('click',e=>{if(e.target.id!=='roleColorsReset')return;e.preventDefault();cfg.role_colors={};showRoleColors();scheduleSave()});
loadProfiles();
// A lista de camadas do editor fecha ao clicar fora (não cobre a barra de ferramentas).
document.addEventListener('pointerdown',e=>{const d=document.querySelector('.vlist');if(d&&d.open&&!e.target.closest('.vlist'))d.open=false},true);

