// =====================================================================================================
// 1.24 — Enter aceita / Esc cancela (com confirmação) em todas as funções; menus; seleção por janela;
// copiar/girar; informação na tela; edição de fluxos pela seleção; editor de texturas.
// =====================================================================================================
// ---------- caixa de confirmação (Enter = Sim, Esc = Não) ----------
function confirmBox(text,yes='Sim',no='Não'){return new Promise(res=>{const d=$('confirmDlg');if(!d||d.open)return res(window.confirm(text));$('confirmText').textContent=text;$('confirmYes').textContent=yes;$('confirmYes').title='Enter';$('confirmNo').textContent=no;$('confirmNo').title='Esc';
 let done=false;const fin=v=>{if(done)return;done=true;d.close();res(v)};$('confirmYes').onclick=()=>fin(true);$('confirmNo').onclick=()=>fin(false);d.oncancel=e=>{e.preventDefault();fin(false)};
 d.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();e.stopPropagation();fin(true)}};d.showModal();setTimeout(()=>$('confirmYes').focus(),0)})}
function activeCommandName(){if(cadCmd)return 'comando da linha de comando';if(drag&&!['pan'].includes(drag.type))return 'edição em andamento';if(tool!=='pan'){const d=TOOLS.find(x=>x[0]===tool);return d?toolLabel(d):tool}return null}
async function escapeCommand(){if(document.querySelector('dialog[open]'))return;
 const name=activeCommandName();
 if(!name){if($('cmdLine'))$('cmdLine').value='';if(sel||(typeof selSet!=='undefined'&&selSet.length)||(typeof selSeg!=='undefined'&&selSeg)){sel=null;selSet=[];selSeg=null;showProps();if($('propPanel'))$('propPanel').hidden=true;draw();msg('Seleção desfeita.')}return}
 const pts=draft?.pts?.length||0;
 const ok=await confirmBox(`Cancelar “${name}”?`+(pts?` Os ${pts} ponto(s) marcados serão descartados.`:'')+' Nada já gravado é alterado.','Cancelar comando','Continuar');
 if(!ok){canvas.focus({preventScroll:true});return}
 if(drag&&drag.type!=='pan'){if(['grip','objmove','move','vertex','span','anchor','imgadj'].includes(drag.type))undo();drag=null}
 draft=null;cadCmd=null;prompt_('Comando:');$('cmdLine')&&($('cmdLine').value='');setTool('pan');msg('Comando cancelado.');canvas.focus({preventScroll:true})}
function inField(t){return t&&(t.tagName==='INPUT'||t.tagName==='TEXTAREA'||t.tagName==='SELECT'||t.isContentEditable)}
document.addEventListener('keydown',e=>{
 if(document.querySelector('.rsCascade'))return;
 if(e.key==='Escape'){const t=e.target;if(document.querySelector('dialog[open]'))return;if(t&&t.closest&&t.closest('#propPanel'))return;
  if(inField(t)&&t.id!=='cmdLine'&&!(t.closest&&t.closest('#toolOptions')))return;e.preventDefault();e.stopImmediatePropagation();escapeCommand();return}
 if(e.key==='Enter'){const t=e.target;if(document.querySelector('dialog[open]'))return;
  if(t&&t.closest&&t.closest('#toolOptions')&&inField(t)){e.preventDefault();e.stopImmediatePropagation();canvas.focus({preventScroll:true});msg('Valor aceito. Continue no desenho; Enter na tela conclui o comando.');return}
  // Enter num campo de formulário com botão associado = aceitar (ex.: Adicionar intervenção).
  const box=t&&t.closest&&t.closest('[data-enter]');if(box&&inField(t)&&t.tagName!=='TEXTAREA'){e.preventDefault();e.stopImmediatePropagation();$(box.dataset.enter)?.click();return}
  if(inField(t)||t?.tagName==='BUTTON')return;
  if(draft||cadCmd||tool!=='pan'){e.preventDefault();e.stopImmediatePropagation();if(cadCmd)runCommand('');else endCommand()}}},true);
// Enter no diálogo “Limpar trabalho” confirma.
$('resetDialog')?.addEventListener('keydown',e=>{if(e.key==='Enter'&&e.target.tagName!=='BUTTON'){e.preventDefault();$('resetGo')?.click()}});
// Formulário de intervenção: Enter adiciona.
{const f=$('poiTitle')?.closest('section');if(f)f.dataset.enter='addPoi'}

// ---------- menus: navegação por seções, recolher/expandir ----------
(function menus(){const secs=[...document.querySelectorAll('main section')].filter(s=>s.querySelector(':scope>h2'));if(!secs.length||$('secNav'))return;
 const nav=document.createElement('nav');nav.id='secNav';nav.className='secNav';
 const key=s=>'rodovia_sec_'+(s.id||s.querySelector(':scope>h2').textContent.trim().slice(0,30));
 secs.forEach((s,i)=>{const h=s.querySelector(':scope>h2');if(!s.id)s.id='sec_'+i;
  const b=document.createElement('button');b.type='button';b.innerHTML=(h.querySelector('.ico')?.outerHTML||'')+'<span>'+esc(h.textContent.trim().replace(/^\d+\.\s*/,''))+'</span>';b.title='Ir para: '+h.textContent.trim();
  b.onclick=()=>{s.classList.remove('collapsed');try{localStorage.setItem(key(s),'0')}catch{};s.scrollIntoView({behavior:'smooth',block:'start'})};nav.appendChild(b);
  h.classList.add('collapsible');h.title='Clique para recolher/expandir';h.addEventListener('click',e=>{if(e.target.closest('button,a,input,select'))return;const c=s.classList.toggle('collapsed');try{localStorage.setItem(key(s),c?'1':'0')}catch{}});
  try{if(localStorage.getItem(key(s))==='1'&&s.id!=='editorSection')s.classList.add('collapsed')}catch{}});
 const all=document.createElement('button');all.type='button';all.className='navAll';all.textContent='Recolher tudo';all.title='Recolhe as seções (o editor fica aberto)';
 all.onclick=()=>{const collapse=all.textContent==='Recolher tudo';secs.forEach(s=>{if(s.id==='editorSection')return;s.classList.toggle('collapsed',collapse);try{localStorage.setItem(key(s),collapse?'1':'0')}catch{}});all.textContent=collapse?'Expandir tudo':'Recolher tudo'};nav.appendChild(all);
 const first=document.querySelector('main');first.parentNode.insertBefore(nav,first)})();

// ---------- seleção múltipla: Shift+clique, janela (Ctrl+arrastar) ----------
let selSet=[];
function selKeyOf(s){return s.key+'#'+s.i}
function inSet(s){return selSet.some(x=>x.key===s.key&&x.i===s.i)}
function allSelected(){const L=selSet.slice();if(sel&&!inSet(sel))L.push(sel);return L.map(objOf).filter(Boolean)}
canvas.addEventListener('pointerdown',e=>{if(!ready()||e.button!==0||tool!=='pan'||cadCmd)return;
 if(e.ctrlKey){const c=canvasPt(e);e.stopImmediatePropagation();try{canvas.setPointerCapture(e.pointerId)}catch{};drag={type:'box',a:c,b:c};return}
 if(e.shiftKey){const c=canvasPt(e);const h=hitObject(c);if(h){e.stopImmediatePropagation();const s={key:h.key,i:h.i};if(sel&&!inSet(sel))selSet.push(sel);
   if(inSet(s)){selSet=selSet.filter(x=>!(x.key===s.key&&x.i===s.i));sel=selSet[selSet.length-1]||null}else{selSet.push(s);sel=s}showProps();draw();msg(`${allSelected().length} objeto(s) selecionado(s).`)}}},true);
canvas.addEventListener('pointermove',e=>{if(drag?.type!=='box')return;drag.b=canvasPt(e);e.stopImmediatePropagation();draw()},true);
canvas.addEventListener('pointerup',e=>{if(drag?.type!=='box')return;const d=drag;drag=null;e.stopImmediatePropagation();
 const x0=Math.min(d.a.cx,d.b.cx),x1=Math.max(d.a.cx,d.b.cx),y0=Math.min(d.a.cy,d.b.cy),y1=Math.max(d.a.cy,d.b.cy);if(x1-x0<4&&y1-y0<4){draw();return}
 const crossing=d.b.cx<d.a.cx;const got=[];
 for(const o of objList()){const P=o.grips.map(g=>W2C(gripGet(g)));const inside=P.map(([x,y])=>x>=x0&&x<=x1&&y>=y0&&y<=y1);if(crossing?inside.some(Boolean):inside.every(Boolean))got.push({key:o.key,i:o.i})}
 selSet=got;sel=got[got.length-1]||null;showProps();draw();msg(`${got.length} objeto(s) selecionado(s) por ${crossing?'cruzamento (direita→esquerda)':'janela (esquerda→direita)'}. Delete apaga; MOVER, COPIAR e GIRAR valem para todos.`)},true);
function drawBox(){if(drag?.type!=='box')return;const a=drag.a,b=drag.b,cr=b.cx<a.cx;ctx.save();ctx.strokeStyle=cr?'#3fe08a':'#4fa3ff';ctx.fillStyle=cr?'#3fe08a22':'#4fa3ff22';ctx.setLineDash(cr?[6,4]:[]);ctx.lineWidth=1.5;ctx.fillRect(Math.min(a.cx,b.cx),Math.min(a.cy,b.cy),Math.abs(b.cx-a.cx),Math.abs(b.cy-a.cy));ctx.strokeRect(Math.min(a.cx,b.cx),Math.min(a.cy,b.cy),Math.abs(b.cx-a.cx),Math.abs(b.cy-a.cy));ctx.restore()}
function drawSelSet(){for(const o of allSelected()){if(sel&&o.key===sel.key&&o.i===sel.i)continue;const P=o.grips.map(g=>W2C(gripGet(g)));ctx.save();ctx.strokeStyle='#4fa3ff';ctx.lineWidth=2;ctx.setLineDash([4,3]);ctx.beginPath();if(o.shape==='pt'){const [x,y]=P[0];ctx.arc(x,y,9,0,7)}else{P.forEach(([x,y],k)=>k?ctx.lineTo(x,y):ctx.moveTo(x,y));if(o.shape==='area')ctx.closePath()}ctx.stroke();ctx.restore()}}
// Apagar, mover, copiar e girar valem para a seleção inteira.
deleteSel=function(){const L=allSelected();if(!L.length)return false;checkpoint();const by={};for(const o of L)(by[o.key]??=[]).push(o.i);
 for(const [k,is] of Object.entries(by)){if(k==='custom_axis'){M.custom_axis=null;continue}is.sort((a,b)=>b-a).forEach(i=>M[k].splice(i,1))}sel=null;selSet=[];showProps();changed(`${L.length} objeto(s) apagado(s).`);return true};
function transformSel(fn,label,copy=false){const L=allSelected();if(!L.length)return msg('Selecione os objetos antes.',true);checkpoint();const made=[];
 for(const o of L){let tgt=o;if(copy){if(o.key==='custom_axis')continue;const cl=JSON.parse(JSON.stringify(o.o));if(cl&&typeof cl==='object'&&!Array.isArray(cl)&&'id' in cl)cl.id=uid();M[o.key].push(cl);const n=objList().find(x=>x.key===o.key&&x.i===M[o.key].length-1);tgt=n;made.push({key:o.key,i:M[o.key].length-1})}
  tgt.grips.forEach(g=>gripSet(g,fn(gripGet(g))));afterGeomEdit(tgt)}
 if(copy){selSet=made;sel=made[made.length-1]||null}changed(`${L.length} objeto(s) ${label}.`);showProps()}
estender('runCommand',_rc=>function(raw){const t=(raw||'').trim().toUpperCase();
 if(['CO','COPIAR','COPY','CP'].includes(t)){if(!allSelected().length)return msg('Selecione os objetos (clique, Shift+clique ou Ctrl+arrastar) e use COPIAR.',true);
  cadCmd={step(w){if(!this.base){this.base=w;prompt_('COPIAR — segundo ponto (ou @dx,dy):');return}const dx=w.x-this.base.x,dy=w.y-this.base.y;transformSel(p=>({x:p.x+dx,y:p.y+dy}),'copiado(s) '+Math.hypot(dx,dy).toFixed(3)+' m',true);cadCmd=null;prompt_('Comando:')}};prompt_('COPIAR — ponto base:');return}
 if(['RO','GIRAR','ROTATE','ROTACIONAR'].includes(t)){if(!allSelected().length)return msg('Selecione os objetos e use GIRAR.',true);
  cadCmd={step(w,ang){if(!this.base){this.base=w;prompt_('GIRAR — ângulo em graus (anti-horário) ou clique a direção:');return}const b=this.base;const a=ang!=null?ang:Math.atan2(w.y-b.y,w.x-b.x)*180/Math.PI;const r=a*Math.PI/180,c=Math.cos(r),s=Math.sin(r);
   transformSel(p=>({x:b.x+(p.x-b.x)*c-(p.y-b.y)*s,y:b.y+(p.x-b.x)*s+(p.y-b.y)*c}),`girado(s) ${a.toFixed(3)}°`);cadCmd=null;prompt_('Comando:')}};prompt_('GIRAR — ponto base:');return}
 if(cadCmd&&cadCmd.step.length===2&&cadCmd.base&&/^-?\d+([.,]\d+)?$/.test(t)){cadCmd.step(null,Number(t.replace(',','.')));return}
 if(['U','DESFAZER','UNDO'].includes(t)){undo();return}
 if(['REFAZER','REDO'].includes(t)){redo();return}
 if(['SELTUDO','TODOS','ALL'].includes(t)){selSet=objList().map(o=>({key:o.key,i:o.i}));sel=selSet[selSet.length-1]||null;showProps();draw();return msg(`${selSet.length} objeto(s) selecionado(s).`)}
 if(t==='MOVER'||t==='M'||t==='MOVE'){if(allSelected().length>1){cadCmd={step(w){if(!this.base){this.base=w;prompt_('MOVER — segundo ponto (ou @dx,dy):');return}const dx=w.x-this.base.x,dy=w.y-this.base.y;transformSel(p=>({x:p.x+dx,y:p.y+dy}),'movido(s) '+Math.hypot(dx,dy).toFixed(3)+' m');cadCmd=null;prompt_('Comando:')}};prompt_('MOVER — ponto base:');return}}
 return _rc(raw)},'Apagar, mover, copiar e girar valem para a seleção inteira.');
Object.assign(CMD_ALIAS,{CO:'x',COPIAR:'x',GIRAR:'x',RO:'x'});

// ---------- informação na tela (perto do cursor e da seleção) ----------
let hudOn=true;try{hudOn=localStorage.getItem('rodovia_hud')!=='0'}catch{}
function polyLen(P){let L=0;for(let i=1;i<P.length;i++)L+=Math.hypot(P[i].x-P[i-1].x,P[i].y-P[i-1].y);return L}
function polyArea(P){let a=0;for(let i=0,j=P.length-1;i<P.length;j=i++)a+=(P[j].x+P[i].x)*(P[j].y-P[i].y);return Math.abs(a/2)}
function objMetrics(o){const P=o.grips.map(gripGet);const out=[];if(o.shape==='line'||o.shape==='poly')out.push(`comprimento ${polyLen(P).toFixed(3)} m`);
 if(o.shape==='area'){out.push(`área ${polyArea(P).toLocaleString('pt-BR',{maximumFractionDigits:2})} m²`,`perímetro ${(polyLen(P)+Math.hypot(P[0].x-P[P.length-1].x,P[0].y-P[P.length-1].y)).toFixed(2)} m`)}
 if(axisData()){const ks=P.map(p=>kmOf(p)?.km).filter(v=>v!=null);if(ks.length)out.push(ks.length>1?`km ${formatKm(Math.min(...ks))} a ${formatKm(Math.max(...ks))}`:`km ${formatKm(ks[0])}`)}return out}
function drawHud(){if(!hudOn||!lastWorld)return;const lines=[];const w=lastWorld;
 if(tool!=='pan'||draft||cadCmd){const d=TOOLS.find(x=>x[0]===tool);lines.push(cadCmd?$('cmdPrompt').textContent:(d?toolLabel(d):tool)+(draft?.pts?.length?` · ${draft.pts.length} ponto(s)`:''))}
 const ref=draft?.pts?.length?draft.pts[draft.pts.length-1]:cadCmd?.base;
 if(ref){const d=Math.hypot(w.x-ref.x,w.y-ref.y),az=(Math.atan2(w.x-ref.x,w.y-ref.y)*180/Math.PI+360)%360;lines.push(`Δ ${d.toFixed(3)} m · ${az.toFixed(2)}°`)}
 if(draft?.pts?.length>=2&&['pavarea','hatch','exvert','block','lanes','oaepoly','noconnarea'].includes(draft.type)){const P=draft.pts.concat([w]);lines.push(`área ${polyArea(P).toLocaleString('pt-BR',{maximumFractionDigits:1})} m²`)}
 if(axisData()&&(tool!=='pan'||draft)){const k=kmOf(w);if(k)lines.push(`km ${formatKm(k.km)} · ${k.off.toFixed(2)} m do eixo`)}
 if(snapMark)lines.push('snap: '+snapMark.kind);
 if(!lines.length)return;const [x,y]=W2C(w);ctx.save();ctx.font='12px ui-monospace,Consolas,monospace';const wd=Math.max(...lines.map(l=>ctx.measureText(l).width))+14,ht=lines.length*16+8;
 let bx=x+18,by=y+18;if(bx+wd>canvas.width-4)bx=x-18-wd;if(by+ht>canvas.height-4)by=y-18-ht;ctx.fillStyle='#061420d9';ctx.strokeStyle='#2f7cf6';ctx.lineWidth=1;ctx.fillRect(bx,by,wd,ht);ctx.strokeRect(bx,by,wd,ht);ctx.fillStyle='#e8f4f8';lines.forEach((l,i)=>ctx.fillText(l,bx+7,by+18+i*16));ctx.restore()}
estender('showProps',_sp=>function(){_sp();const box=$('propPanel');if(!box)return;const L=allSelected();
 if(L.length>1){box.hidden=false;const by={};L.forEach(o=>by[o.label]=(by[o.label]||0)+1);box.innerHTML=`<h3>Seleção · ${L.length} objetos</h3><p>${Object.entries(by).map(([k,n])=>`${n} × ${esc(k)}`).join('<br>')}</p><div class="row"><button type="button" data-ppact="move">Mover (M)</button><button type="button" data-ppact="copy">Copiar (CO)</button><button type="button" data-ppact="rotate">Girar (RO)</button><button type="button" data-ppact="del" class="danger">Apagar (Del)</button><button type="button" data-ppact="close">Desmarcar</button></div><p class="muted">Shift+clique acrescenta/retira; Ctrl+arrastar seleciona por janela (→) ou cruzamento (←).</p>`;return}
 const o=objOf(sel);if(!o||box.hidden)return;const m=objMetrics(o);if(m.length)box.querySelector('h3')?.insertAdjacentHTML('afterend',`<p class="ppInfo">${m.map(esc).join(' · ')}</p>`)},'informação na tela (perto do cursor e da seleção)');
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('#propPanel [data-ppact]');if(!b)return;const a=b.dataset.ppact;if(a==='copy')runCommand('COPIAR');if(a==='rotate')runCommand('GIRAR');if(a==='close'){selSet=[]}});
$('hudOn')?.addEventListener('change',()=>{hudOn=$('hudOn').checked;try{localStorage.setItem('rodovia_hud',hudOn?'1':'0')}catch{};draw()});
if($('hudOn'))$('hudOn').checked=hudOn;

// ---------- fluxos: selecionar uma trajetória e editar o sentido ----------
let selSeg=null;
function segOverride(seg,action){const segPts=seg.points.map(P);return M.flow_overrides.findIndex(o=>o.action===action&&distPolyline(o,segPts)<=6)}
function segToggle(seg,action){checkpoint();const i=segOverride(seg,action);if(i>=0)M.flow_overrides.splice(i,1);else M.flow_overrides.push({id:uid(),x:seg.mid[0],y:seg.mid[1],action,enabled:true});changed();showSegProps();scheduleFlowUpdate()}
let flowTimer=null;function scheduleFlowUpdate(){if(!$('flowAuto')?.checked)return msg('Alteração registrada. Clique “Atualizar fluxos” para recalcular.');clearTimeout(flowTimer);flowTimer=setTimeout(guard(async()=>{await start('analyze');selSeg=null;showSegProps();msg('Fluxos atualizados.')}),1200)}
function showSegProps(){const box=$('propPanel');if(!box)return;if(!selSeg){if(!sel&&!selSet.length){box.hidden=true}return}const s=editor?.segments?.find(x=>x.id===selSeg.id)||selSeg;
 const rev=segOverride(s,'reverse')>=0,off=segOverride(s,'disable')>=0;const L=polyLen(s.points.map(P));
 box.hidden=false;box.innerHTML=`<h3>Trajetória ${esc(String(s.id))} · ${esc(({main:'Principal',marginal:'Marginal',device:'Dispositivo',return:'Retorno'})[s.kind]||s.kind||'')}</h3><p class="ppInfo">comprimento ${L.toFixed(1)} m · ${s.both?'dois sentidos':s.forward?'no sentido do desenho':'contra o sentido do desenho'}${s.manual?' · fluxo incluído':''}${s.source?' · '+esc(s.source):''}</p>
 <div class="row"><button type="button" data-seg="reverse" class="${rev?'primary':''}">⇄ ${rev?'Desfazer inversão':'Inverter sentido'}</button><button type="button" data-seg="disable" class="${off?'primary':''}">⦸ ${off?'Reativar':'Desativar'}</button><button type="button" data-seg="close">Fechar</button></div>
 <label><input type="checkbox" id="flowAuto" ${localStorage.getItem('rodovia_flowauto')==='1'?'checked':''}> Atualizar fluxos automaticamente após editar</label><p class="muted">Clique numa trajetória (verde, vermelha ou amarela) com Navegar para editá-la. A seta indica o sentido atual.</p>`}
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('#propPanel [data-seg]');if(!b)return;const a=b.dataset.seg;if(a==='close'){selSeg=null;$('propPanel').hidden=true;draw();return}const s=editor?.segments?.find(x=>x.id===selSeg?.id);if(s)segToggle(s,a)});
document.addEventListener('change',e=>{if(e.target.id==='flowAuto'){try{localStorage.setItem('rodovia_flowauto',e.target.checked?'1':'0')}catch{}}});
canvas.addEventListener('pointerup',e=>{if(tool!=='pan'||e.button!==0||cadCmd||e.shiftKey||e.ctrlKey||!ready())return;if(sel||selSet.length)return;
 const c=canvasPt(e);if(!c.w)return;const moved=lastDownPt?Math.hypot(c.cx-lastDownPt.cx,c.cy-lastDownPt.cy):99;if(moved>4)return;
 if(vecOn.flows===false)return;const seg=nearestSegment(c.w,6/Math.max(pxPerM(),1e-9));if(!seg){if(selSeg){selSeg=null;showSegProps();draw()}return}selSeg={id:seg.id};showSegProps();draw()});
let lastDownPt=null;canvas.addEventListener('pointerdown',e=>{lastDownPt=canvasPt(e)},true);
function drawSelSeg(){if(!selSeg||!editor)return;const s=editor.segments.find(x=>x.id===selSeg.id);if(!s)return;const pts=s.points.map(P);poly(pts);ctx.save();ctx.strokeStyle='#ffffff';ctx.lineWidth=6;ctx.globalAlpha=.25;ctx.stroke();ctx.restore()}

// ---------- editor de texturas ----------
const TEX_LABEL={pista_nova:'Pista nova (asfalto)',pista_existente:'Pista existente',concreto:'Concreto (OAE e pavimento rígido)',acostamento:'Acostamento',canteiro:'Canteiro (grama)',trilhas:'Trilhas de roda',talude_corte:'Talude de corte',talude_aterro:'Talude de aterro'};
const TEX_KEYS=[['grao','Grão / agregado',0,3,.05],['tom','Variação de tom',0,3,.05],['remendos','Remendos / manchas',0,3,.05],['fissuras','Fissuras',0,3,.05],['brilho','Brilho',-.3,.3,.01]];
function texUi(){const box=$('texEditor');if(!box)return;const tp=cfg.texture_params||{};
 box.innerHTML='<div class="texGrid">'+Object.entries(TEX_LABEL).map(([k,l])=>{const v={grao:1,tom:1,remendos:1,fissuras:1,brilho:0,...(tp[k]||{})};
  return `<div class="texCard" data-tex="${k}"><b>${l}</b><img alt="" class="texPrev"><div>${TEX_KEYS.map(([f,lab,a,b,st])=>`<label>${lab} <span>${Number(v[f]).toFixed(2)}</span><input type="range" data-f="${f}" min="${a}" max="${b}" step="${st}" value="${v[f]}"></label>`).join('')}</div><button type="button" data-texreset>Padrão</button></div>`}).join('')+'</div>';
 box.querySelectorAll('[data-tex]').forEach(texPrev)}
function texVals(card){const o={};card.querySelectorAll('input[data-f]').forEach(i=>o[i.dataset.f]=Number(i.value));return o}
function texPrev(card){const v=texVals(card);card.querySelector('.texPrev').src='/api/texture_preview.png?surface='+card.dataset.tex+'&realistic='+(($('texture_style')?.value||cfg.texture_style)!=='anterior')+'&estilo='+(($('texture_style')?.value||cfg.texture_style)||'')+'&p='+encodeURIComponent(JSON.stringify(v))}
let texTimer=null;
$('texEditor')?.addEventListener('input',e=>{const card=e.target.closest('[data-tex]');if(!card)return;if(e.target.dataset.f)e.target.previousElementSibling.textContent=Number(e.target.value).toFixed(2);clearTimeout(texTimer);texTimer=setTimeout(()=>texPrev(card),150)});
$('texEditor')?.addEventListener('change',e=>{const card=e.target.closest('[data-tex]');if(!card||!pid)return;const v=texVals(card),k=card.dataset.tex;const tp={...(cfg.texture_params||{})};
 if(v.grao===1&&v.tom===1&&v.remendos===1&&v.fissuras===1&&v.brilho===0)delete tp[k];else tp[k]=v;cfg.texture_params=tp;scheduleSave();msg(`Textura de “${TEX_LABEL[k]}” ajustada. Gere a prévia para ver no vídeo.`)});
$('texEditor')?.addEventListener('click',e=>{if(e.target.dataset.texreset===undefined)return;const card=e.target.closest('[data-tex]');card.querySelectorAll('input[data-f]').forEach(i=>{i.value=i.dataset.f==='brilho'?0:1;i.previousElementSibling.textContent=Number(i.value).toFixed(2)});texPrev(card);const tp={...(cfg.texture_params||{})};delete tp[card.dataset.tex];cfg.texture_params=tp;scheduleSave()});
estender('load',_l7=>async id=>{await _l7(id);try{texUi()}catch{}},'editor de texturas');

// ---------- desenho dos extras ----------
estender('draw',_d2=>function(){_d2();if(!ready())return;try{drawSelSet();drawSelSeg();drawBox();drawHud()}catch(err){}},'desenho dos extras');

