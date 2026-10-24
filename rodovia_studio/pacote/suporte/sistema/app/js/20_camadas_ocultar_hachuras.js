// ---------- camadas: ocultar / congelar (no editor já; no vídeo ao gerar) ----------
VSTYLE.frozen=['#9fd4ff',1.3,[3,3],.10];
function layerSets(){return {h:new Set(cfg?.hidden_layers||[]),f:new Set(cfg?.frozen_layers||[])}}
estender('buildVectorPaths',_bvp=>function(){if(!vec||!vec.layer_names||!vec.layers)return _bvp();const st=layerSets(),names=vec.layer_names,orig=vec.layers,fz=[],L={};
 for(const [role,list] of Object.entries(orig)){if(!Array.isArray(list)){L[role]=list;continue}L[role]=list.filter(r=>{const n=names[r.l];if(n!=null&&st.h.has(n))return false;if(r.z||(n!=null&&st.f.has(n))){fz.push(r);return false}return true})}
 L.frozen=fz;vec.layers=L;try{_bvp()}finally{vec.layers=orig}},'camadas: ocultar / congelar (no editor já; no vídeo ao gerar)');
estender('buildSnap',_bs=>function(){if(!vec||!vec.layer_names||!vec.layers)return _bs();const st=layerSets(),names=vec.layer_names,orig=vec.layers,L={};
 for(const [role,list] of Object.entries(orig))L[role]=Array.isArray(list)?list.filter(r=>{const n=names[r.l];return !(r.z||(n!=null&&(st.h.has(n)||st.f.has(n))))}):list;vec.layers=L;try{_bs()}finally{vec.layers=orig}},'camadas: ocultar / congelar (no editor já; no vídeo ao gerar)');
function setLayerState(name,kind,on){const key=kind==='h'?'hidden_layers':'frozen_layers';const s=new Set(cfg[key]||[]);on?s.add(name):s.delete(name);cfg[key]=[...s];
 if(kind==='h'&&on){const f=new Set(cfg.frozen_layers||[]);f.delete(name);cfg.frozen_layers=[...f]}
 buildVectorPaths();snapIndex=null;exactSnap=null;draw();showLayers();scheduleSave();announce({t:'layers'})}
function layerMsg(name,kind,on){const was=(analysis?.warnings||[]).some(w=>w.includes('oculta'));
 return kind==='h'?(on?`Camada “${name}” oculta: some do editor e do vídeo. Clique “Analisar arquivos” para recalcular fluxos e sinalização sem ela.`:`Camada “${name}” visível de novo. Clique “Analisar arquivos” para ela voltar ao editor e aos fluxos.`)
  :(on?`Camada “${name}” congelada: fica travada no editor (sem snap nem seleção) e no vídeo aparece pronta desde o início, sem a construção progressiva.`:`Camada “${name}” descongelada.`)}
estender('showLayers',_sl=>function(){_sl();if(!analysis)return;const st=layerSets();
 document.querySelectorAll('#layers select[data-layer]').forEach(el=>{const name=el.dataset.layer,tr=el.closest('tr'),td=tr.lastElementChild;if(!td||td.querySelector('.layerBtns'))return;
  tr.classList.toggle('lyHidden',st.h.has(name));tr.classList.toggle('lyFrozen',st.f.has(name));
  td.insertAdjacentHTML('beforeend',`<span class="layerBtns"><button type="button" class="${st.h.has(name)?'on':''}" data-lyh="${esc(name)}" title="Ocultar: some no editor e no vídeo (o DXF não muda)">${st.h.has(name)?'🚫':'👁'}</button><button type="button" class="${st.f.has(name)?'on':''}" data-lyf="${esc(name)}" title="Congelar: travada no editor (sem snap/seleção); no vídeo aparece pronta desde o início">❄</button></span>`)})},'camadas: ocultar / congelar (no editor já; no vídeo ao gerar)');
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('[data-lyh],[data-lyf]');if(!b)return;e.preventDefault();if(!pid)return;const h='lyh' in b.dataset,name=h?b.dataset.lyh:b.dataset.lyf,st=layerSets();
 const on=!(h?st.h.has(name):st.f.has(name));if(h&&on&&Object.entries(cfg.layers||{}).some(([r,ls])=>r==='axis'&&ls.includes(name)))return msg(`“${name}” é a camada do eixo: ocultá-la deixa o projeto sem eixo. Mude o tipo da camada primeiro.`,true);
 setLayerState(name,h?'h':'f',on);msg(layerMsg(name,h?'h':'f',on))});
function layerAt(w,px=10){if(!vec||!vec.layer_names)return null;const r=px/Math.max(pxPerM(),1e-9);let best=null;
 for(const list of Object.values(vec.layers||{})){if(!Array.isArray(list))continue;for(const rec of list){const P=rec.p;if(!P||P.length<2)continue;for(let i=0;i+1<P.length;i++){const d=segDist(w.x,w.y,P[i][0],P[i][1],P[i+1][0],P[i+1][1]);if(d<=r&&(!best||d<best.d))best={d,name:vec.layer_names[rec.l]}}}}
 return best&&best.name}

// ---------- hachuras: confiança, motivo, indicação pela cor e “Ver” ----------
let hatchPrev=null;
hatchUi=function(){const box=$('hatchList');if(!box)return;const H=analysis?.hatches||[];if(!H.length){box.textContent=analysis?'Nenhuma hachura no DXF.':'Analise os arquivos para listar as hachuras.';return}
 const hr=cfg.hatch_roles||{};box.className='';
 box.innerHTML='<table class="hatchT"><tr><th>Camada · padrão · cor</th><th>Qtde · área</th><th>Sugestão</th><th>Tipo</th><th>Material</th><th></th></tr>'+H.map(h=>{const cur=hr[h.sig]||{};const sw=h.color.startsWith('#')?h.color:aciHex(h.color);
  const sug=h.suggested_role?`${RLABEL[h.suggested_role]||h.suggested_role}${h.suggested_material?' · '+(h.suggested_material==='rigido'?'concreto':'asfalto'):''}<br><small class="conf-${esc(h.confidence||'')}" title="${esc(h.reason||'')}">confiança ${esc(h.confidence||'?')}</small>`:(h.color_hint?`<span class="hint" title="Só pela cor; escolha o tipo se concordar">talvez ${esc(RLABEL[h.color_hint]||h.color_hint)}</span>`:'—');
  return `<tr data-sig="${esc(h.sig)}"><td><span class="sw" style="background:${sw}"></span>${esc(h.layer)}${h.frozen?' ❄':''}<br><small>${esc(h.pattern)} · ${esc(h.color)}${h.entity==='MPOLYGON'?' · MPOLYGON':''}</small></td><td>${h.count}<br><small>${h.area_m2.toLocaleString('pt-BR')} m²${h.islands?` · ${h.islands} ilha(s)`:''}</small></td>
  <td>${sug}${h.current_role?'<br><small>camada: '+(RLABEL[h.current_role]||h.current_role)+'</small>':''}${h.auto_applied?'<br><small class="ok">aplicada</small>':''}${h.reason?`<br><small class="why">${esc(h.reason)}</small>`:''}</td>
  <td><select data-hk="role">${Object.entries(HROLE).map(([k,l])=>`<option value="${k}" ${(cur.role||'')===k?'selected':''}>${l}</option>`).join('')}</select></td><td><select data-hk="material">${Object.entries(MAT_LABEL).map(([k,l])=>`<option value="${k}" ${(cur.material||'auto')===k?'selected':''}>${l}</option>`).join('')}</select></td>
  <td><button type="button" class="mini" data-hatchshow="${esc(h.sig)}" title="Destacar estas hachuras no editor">Ver</button></td></tr>`}).join('')+'</table><div class="row"><button type="button" id="hatchSuggest">Usar todas as sugestões</button><span class="muted">Sugestões com confiança alta/média são aplicadas sozinhas quando “Aplicar as sugestões automaticamente” está marcado; as indicações pela cor nunca são aplicadas sozinhas.</span></div>'};
function showGeom(name,P,text){if(layerShow&&layerShow.name===name){layerShow=null;draw();return}if(!P||!P.length)return msg('Sem geometria para mostrar.',true);layerShow={name,p:P};
 let x0=Infinity,y0=Infinity,x1=-Infinity,y1=-Infinity;for(const q of P)for(const [x,y] of q){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y)}
 if(ready()){const c={x:(x0+x1)/2,y:(y0+y1)/2};const [ix,iy]=worldToImg(c);const span=Math.max(40,Math.hypot(x1-x0,y1-y0));view.s=Math.max(minScale(),Math.min(useGeo()?240:60,canvas.width*mpp()/span*.8));view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw()}msg(text)}
document.addEventListener('click',guard(async e=>{const b=e.target.closest&&e.target.closest('[data-hatchshow]');if(!b)return;e.preventDefault();requireProject();if(!hatchPrev)hatchPrev=await api(`/api/projects/${pid}/hachuras_previa`);
 const sig=b.dataset.hatchshow;showGeom('hatch:'+sig,hatchPrev[sig],`Hachuras “${sig}” destacadas em magenta. Clique “Ver” de novo para apagar.`)}));
estender('load',_l=>async (id,options={})=>{hatchPrev=null;imgCache.clear();const loaded=await _l(id,options);if(loaded===false||pid!==id)return false;if(options.resultsOnly)return loaded;try{hatchUi()}catch{};return loaded},'hachuras: confiança, motivo, indicação pela cor e “Ver”');

