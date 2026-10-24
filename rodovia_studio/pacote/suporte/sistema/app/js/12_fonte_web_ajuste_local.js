// ---------------- 1.19: fonte da imagem web ----------------
function webUi(){if(!$('webSource'))return;const w=cfg.web_imagery||{};$('webSource').value=w.source||'esri';$('webUrl').value=w.url||'';$('webLayers').value=w.wms_layers||'';$('webMaxZoom').value=w.max_zoom||19;$('webAttr').value=w.attribution||'';
 if(w.wayback_release&&!$('wbRelease').querySelector(`option[value="${w.wayback_release}"]`))$('wbRelease').insertAdjacentHTML('beforeend',`<option value="${w.wayback_release}">${esc(w.wayback_label||('versão '+w.wayback_release))}</option>`);$('wbRelease').value=w.wayback_release||'';webVis();
 $('webInfo').textContent=(w.source&&w.source!=='esri')?'Fonte em uso: '+({wayback:'Esri Wayback '+(w.wayback_label||''),xyz:'XYZ',wms:'WMS'}[w.source])+(w.attribution?' · '+w.attribution:''):'Fonte em uso: Esri World Imagery atual.'}
function webVis(){const v=$('webSource').value;$('wbBox').hidden=v!=='wayback';$('wbLoad').hidden=v!=='wayback';$('webCustom').hidden=!(v==='xyz'||v==='wms');$('webLayers').parentElement.hidden=v!=='wms'}
$('webSource')?.addEventListener('change',webVis);
$('wbLoad')?.addEventListener('click',guard(async()=>{const r=await api('/api/wayback/releases');const cur=$('wbRelease').value;$('wbRelease').innerHTML='<option value="">— escolha a data —</option>'+r.releases.map(x=>`<option value="${x.release}">${esc(x.date||x.title)}</option>`).join('');if(cur)$('wbRelease').value=cur;msg(r.releases.length+' datas disponíveis na Esri Wayback (a mais recente primeiro). Compare no editor antes de gerar o vídeo.')}));
$('webApply')?.addEventListener('click',guard(async()=>{if(!pid)throw Error('Abra um projeto.');const v=$('webSource').value,o=$('wbRelease').selectedOptions[0];const lastWeb=cfg.web_imagery?{...cfg.web_imagery}:null;
 if(v==='wayback'&&!$('wbRelease').value)throw Error('Carregue a lista e escolha a data da Wayback.');
 if((v==='xyz'||v==='wms')&&!/^https?:\/\//i.test($('webUrl').value.trim()))throw Error('Informe o endereço http/https do serviço.');
 cfg.web_imagery={source:v,wayback_release:v==='wayback'?Number($('wbRelease').value):null,wayback_label:v==='wayback'?(o?.textContent||''):'',url:$('webUrl').value.trim(),wms_layers:$('webLayers').value.trim(),attribution:$('webAttr').value.trim(),max_zoom:Number($('webMaxZoom').value)||19};
 {const prev=lastWeb;if(prev&&prev.qms_id&&prev.source===v&&prev.url===cfg.web_imagery.url&&prev.wms_layers===cfg.web_imagery.wms_layers)Object.assign(cfg.web_imagery,{wms_version:prev.wms_version,wms_format:prev.wms_format,qms_id:prev.qms_id,qms_name:prev.qms_name,terms_url:prev.terms_url})}
 tiles.clear();await save();webUi();draw();msg('Fonte da imagem web aplicada. O editor já usa a nova fonte; gere a prévia para atualizar o mosaico do vídeo.')}));

// ---------------- 1.19: ajuste da imagem local por grips (deslocar, girar, escalar) ----------------
const imgAdj={index:0,cur:null,undo:[],redo:[],t:null,k0:null};
function imgSrc(){return localInfo?.sources?.find(s=>s.index===imgAdj.index)}
function adjFwd(a,c,p){const r=a.rotation_deg*Math.PI/180,k=a.scale,ca=Math.cos(r)*k,sa=Math.sin(r)*k,u=p.x-c.x,v=p.y-c.y;return {x:c.x+ca*u-sa*v+a.shift_x,y:c.y+sa*u+ca*v+a.shift_y}}
function adjInv(a,c,p){const r=a.rotation_deg*Math.PI/180,k=a.scale,ca=Math.cos(r)/k,sa=Math.sin(r)/k,u=p.x-c.x-a.shift_x,v=p.y-c.y-a.shift_y;return {x:c.x+ca*u+sa*v,y:c.y-sa*u+ca*v}}
function imgCorners(){const s=imgSrc();if(!s)return null;if(!imgAdj.cur||imgAdj.curFor!==s.file+imgAdj.index){imgAdj.cur={...s.adjust};imgAdj.curFor=s.file+imgAdj.index}
 const c={x:s.center[0],y:s.center[1]};const raw=s.corners.map(q=>adjInv(s.adjust,c,{x:q[0],y:q[1]}));return {c,pts:raw.map(p=>adjFwd(imgAdj.cur,c,p))}}
function imgAdjHit(cp){const g=imgCorners();if(!g)return null;for(let i=0;i<4;i++){const [x,y]=W2C(g.pts[i]);if(Math.hypot(x-cp.cx,y-cp.cy)<12)return 'corner'}
 const P=g.pts.map(W2C);let inside=false;for(let i=0,j=3;i<4;j=i++){const [xi,yi]=P[i],[xj,yj]=P[j];if(((yi>cp.cy)!==(yj>cp.cy))&&cp.cx<(xj-xi)*(cp.cy-yi)/(yj-yi)+xi)inside=!inside}return inside?'move':null}
function imgAdjDrag(d,w){const s=imgSrc();if(!s)return;const a=imgAdj.cur,a0=d.a0;
 if(d.mode==='move'){a.shift_x=a0.shift_x+w.x-d.w0.x;a.shift_y=a0.shift_y+w.y-d.w0.y}
 else{const C={x:s.center[0]+a0.shift_x,y:s.center[1]+a0.shift_y},v0={x:d.w0.x-C.x,y:d.w0.y-C.y},v1={x:w.x-C.x,y:w.y-C.y};const L0=Math.hypot(v0.x,v0.y);if(L0<1e-6)return;
  if(!d.scl)a.rotation_deg=Math.max(-30,Math.min(30,a0.rotation_deg+(Math.atan2(v1.y,v1.x)-Math.atan2(v0.y,v0.x))*180/Math.PI));
  if(!d.rot)a.scale=Math.max(.8,Math.min(1.25,a0.scale*Math.hypot(v1.x,v1.y)/L0))}
 a.shift_x=Math.max(-2000,Math.min(2000,a.shift_x));a.shift_y=Math.max(-2000,Math.min(2000,a.shift_y))}
async function imgAdjSend(a){requireProject();await api(`/api/projects/${pid}/imagery/${imgAdj.index}/adjust`,json('PUT',{shift_x:a.shift_x,shift_y:a.shift_y,rotation_deg:a.rotation_deg,scale:a.scale}));await load(pid);localTiles.clear();await localUi();imgAdj.cur={...imgSrc().adjust};draw()}
const imgAdjCommit=guard(async a0=>{imgAdj.k0=null;imgAdj.undo.push({index:imgAdj.index,a:{...a0}});imgAdj.redo=[];await imgAdjSend(imgAdj.cur);toolOptions();const a=imgAdj.cur;msg(`Imagem ajustada: deslocamento ${a.shift_x.toFixed(2)} / ${a.shift_y.toFixed(2)} m, rotação ${a.rotation_deg.toFixed(3)}°, escala ${a.scale.toFixed(4)}. O arquivo original não é alterado.`)});
async function imgAdjStep(from,to){const h=from.pop();if(!h)return msg('Nada para desfazer/refazer no ajuste da imagem.',true);imgAdj.index=h.index;to.push({index:h.index,a:{...(imgSrc()?.adjust||h.a)}});imgAdj.cur={...h.a};await imgAdjSend(h.a);toolOptions()}
function imgAdjOptions(o){if(!localInfo?.sources?.length){o.innerHTML='<p class="muted">Envie uma imagem local (Camadas, imagem local e intercâmbio).</p>';return}
 o.innerHTML=`<div class="grid"><label>Imagem<select id="adjImg">${localInfo.sources.map(s=>`<option value="${s.index}" ${s.index===imgAdj.index?'selected':''}>${esc(s.name)}</option>`).join('')}</select></label></div><div class="row"><button id="adjUndo" type="button">↶ Desfazer ajuste</button><button id="adjRedo" type="button">↷ Refazer</button><button id="adjReset" type="button">Posição original</button></div>`;
 $('adjImg').onchange=()=>{imgAdj.index=Number($('adjImg').value);imgAdj.cur=null;draw()};$('adjUndo').onclick=guard(()=>imgAdjStep(imgAdj.undo,imgAdj.redo));$('adjRedo').onclick=guard(()=>imgAdjStep(imgAdj.redo,imgAdj.undo));
 $('adjReset').onclick=guard(async()=>{const a0={...(imgAdj.cur||imgSrc().adjust)};imgAdj.cur={shift_x:0,shift_y:0,rotation_deg:0,scale:1};await imgAdjCommit(a0)})}
function drawImgAdjust(){if(tool!=='imgadjust')return;const g=imgCorners();if(!g)return;poly(g.pts,true);ctx.strokeStyle='#ffd84d';ctx.lineWidth=2;ctx.setLineDash([8,5]);ctx.stroke();ctx.setLineDash([]);
 for(const p of g.pts){const [x,y]=W2C(p);ctx.fillStyle='#fff';ctx.strokeStyle='#b08a00';ctx.lineWidth=2;ctx.beginPath();ctx.rect(x-6,y-6,12,12);ctx.fill();ctx.stroke()}
 const a=imgAdj.cur,C={x:g.c.x+a.shift_x,y:g.c.y+a.shift_y},[x,y]=W2C(C);ctx.strokeStyle='#ffd84d';ctx.beginPath();ctx.moveTo(x-9,y);ctx.lineTo(x+9,y);ctx.moveTo(x,y-9);ctx.lineTo(x,y+9);ctx.stroke()}

// ---------------- 1.19: limpar trabalho / retirar projeto ----------------
$('resetWork')?.addEventListener('click',guard(async()=>{requireProject();const r=await api('/api/reset_groups');$('resetGroups').innerHTML=r.groups.map(g=>`<label><input type="checkbox" data-group="${g.id}" ${g.default?'checked':''}> ${esc(g.label)}</label>`).join('');$('resetOutputs').checked=false;$('resetDialog').showModal()}));
$('resetCancel')?.addEventListener('click',()=>$('resetDialog').close());
$('resetGo')?.addEventListener('click',guard(async()=>{const groups=[...document.querySelectorAll('#resetGroups input:checked')].map(i=>i.dataset.group);if(!groups.length)throw Error('Escolha ao menos um grupo.');
 const r=await api(`/api/projects/${pid}/reset_work`,json('POST',{groups,outputs:$('resetOutputs').checked}));$('resetDialog').close();await load(pid);
 const n=Object.values(r.cleared).reduce((a,b)=>a+b,0);msg(`Trabalho limpo (${n} item(ns)). Segmento mantido. Cópia da configuração anterior: ${r.backup}. Use “Desfazer limpeza” para voltar.`)}));
$('resetUndo')?.addEventListener('click',guard(async()=>{requireProject();const r=await api(`/api/projects/${pid}/reset_work/undo`,{method:'POST'});await load(pid);msg('Configuração anterior à limpeza restaurada ('+r.restored+').')}));
$('trashProject')?.addEventListener('click',guard(async()=>{requireProject();const name=cfg.name||pid;if(!confirm(`Retirar o projeto “${name}” da lista? A pasta vai para “_lixeira” dentro da pasta de projetos e pode ser recuperada manualmente.`))return;const r=await api(`/api/projects/${pid}`,{method:'DELETE'});pid='';cfg={};meta=null;geo=null;baseImage=null;editor=null;await list();draw();msg('Projeto retirado da lista (pasta '+r.trash+' em _lixeira).')}));

const _drawBase=draw;draw=function(){_drawBase();if(ready())drawImgAdjust()};
// 1.19: ícones nos títulos das seções.
(()=>{const P={'1.':'M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z','2.':'M12 9a3 3 0 100 6 3 3 0 000-6zM19 12l2-1-1-3-2 .3-1.3-1.3.3-2-3-1-1 2h-2L9 3 6 4l.3 2L5 7.3 3 7 2 10l2 1v2l-2 1 1 3 2-.3L6.3 18 6 20l3 1 1-2h2l1 2 3-1-.3-2 1.3-1.3 2 .3 1-3-2-1z',
 'Camadas':'M12 3l9 5-9 5-9-5zM3 13l9 5 9-5M3 17l9 5 9-5','5.':'M4 6h12v12H4zM16 10l5-3v10l-5-3','Manutenção':'M14.7 6.3a4 4 0 00-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 005.4-5.4l-2.5 2.5-2.5-.6-.6-2.5z',
 '3.':'M9 4L3 6v14l6-2 6 2 6-2V4l-6 2zM9 4v14M15 6v14','4.':'M12 21s-6-6-6-11a6 6 0 0112 0c0 5-6 11-6 11zM12 8a2 2 0 100 4 2 2 0 000-4z','Progresso':'M4 20V10M10 20V4M16 20v-7M22 20H2'};
 document.querySelectorAll('section>h2').forEach(h=>{const k=Object.keys(P).find(k=>h.textContent.trim().startsWith(k));if(k&&!h.querySelector('.ico'))h.insertAdjacentHTML('afterbegin',`<span class="ico"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="${P[k]}"/></svg></span>`)})})();

