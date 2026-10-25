// ---------- Gerenciador de camadas ----------
let lmChecked=new Set(),lmHist=[];
function lmLayers(){return [...new Map([...(vec?.layer_names||[]).map(name=>({name,count:null})),...(sourceLayerCatalog?.layers||[]),...(analysis?.layers||[])].map(l=>[l.name,{name:l.name,count:l.count}])).values()]}
function lmRole(n){const e=Object.entries(cfg.layers||{}).find(([,ls])=>(ls||[]).includes(n));return e?e[0]:''}
function lmMatch(n,q){if(!q)return true;if(q.includes('*')){const re=new RegExp('^'+q.split('*').map(x=>x.replace(/[.+?^${}()|[\]\\]/g,'\\$&')).join('.*')+'$','i');return re.test(n)}return n.toLowerCase().includes(q.toLowerCase())}
function lmVisible(){const q=$('lmSearch').value.trim(),f=$('lmShow').value,st=layerSets();return lmLayers().filter(l=>lmMatch(l.name,q)&&(f==='all'||(f==='vis'&&!st.h.has(l.name))||(f==='hid'&&st.h.has(l.name))||(f==='frz'&&st.f.has(l.name))||(f==='role'&&lmRole(l.name))))}
function openLayerManager(){if(!pid)return msg('Abra um projeto primeiro.',true);if(!lmLayers().length)return msg('Analise os arquivos (ou abra o editor) para listar as camadas do DXF.',true);lmChecked=new Set();lmHist=[];$('lmUndo').disabled=true;renderLM();if(!$('layerDlg').open)$('layerDlg').showModal();setTimeout(()=>$('lmSearch').focus(),0)}
function renderLM(){const st=layerSets(),R=lmVisible();const roleOpts=v=>`<option value="">(ignorar)</option>`+Object.entries(roles).map(([k,l])=>`<option value="${k}" ${k===v?'selected':''}>${esc(l)}</option>`).join('');
 $('lmRows').innerHTML=R.map(l=>{const h=st.h.has(l.name),f=st.f.has(l.name);return `<tr class="${lmChecked.has(l.name)?'on':''}" data-lmn="${esc(l.name)}"><td><input type="checkbox" data-lmc ${lmChecked.has(l.name)?'checked':''}></td><td>${esc(l.name)}</td><td><select data-lmrole>${roleOpts(lmRole(l.name))}</select></td><td>${l.count??'—'}</td><td><input type="checkbox" data-lmv ${h?'':'checked'}></td><td><input type="checkbox" data-lmf ${f?'checked':''}></td><td><button type="button" data-showlayer="${esc(l.name)}" title="Destacar no editor">Ver</button></td></tr>`}).join('')||'<tr><td colspan="7" class="muted">Nenhuma camada com este filtro.</td></tr>';
 $('lmAll').checked=R.length>0&&R.every(l=>lmChecked.has(l.name));const all=lmLayers();$('lmInfo').textContent=`${all.length} camadas · ${st.h.size} oculta(s) · ${st.f.size} congelada(s) · ${lmChecked.size} marcada(s). Ocultar: some no editor e no vídeo. Congelar: travada no editor e pronta desde o início no vídeo. O DXF não é alterado.`}
function lmApply(fn,text){lmHist.push({h:[...(cfg.hidden_layers||[])],f:[...(cfg.frozen_layers||[])]});$('lmUndo').disabled=false;const st=layerSets();fn(st.h,st.f);
 cfg.hidden_layers=[...st.h];cfg.frozen_layers=[...st.f].filter(n=>!st.h.has(n));buildVectorPaths();snapIndex=null;exactSnap=null;draw();showLayers();scheduleSave();announce({t:'layers'});renderLM();if(text)msg(text)}
function lmNames(){return [...lmChecked]}
$('lmSearch')?.addEventListener('input',renderLM);$('lmShow')?.addEventListener('change',renderLM);
$('lmAll')?.addEventListener('change',()=>{const R=lmVisible();R.forEach(l=>$('lmAll').checked?lmChecked.add(l.name):lmChecked.delete(l.name));renderLM()});
$('lmRows')?.addEventListener('change',e=>{const tr=e.target.closest('[data-lmn]');if(!tr)return;const n=tr.dataset.lmn,el=e.target;
 if(el.matches('[data-lmc]')){el.checked?lmChecked.add(n):lmChecked.delete(n);tr.classList.toggle('on',el.checked);$('lmInfo').textContent=$('lmInfo').textContent.replace(/\d+ marcada\(s\)/,lmChecked.size+' marcada(s)');return}
 if(el.matches('[data-lmv]'))return lmApply((h,f)=>{if(el.checked)h.delete(n);else{h.add(n);f.delete(n)}},`Camada “${n}” ${el.checked?'visível':'oculta'}.`);
 if(el.matches('[data-lmf]'))return lmApply((h,f)=>{if(el.checked){f.add(n);h.delete(n)}else f.delete(n)},`Camada “${n}” ${el.checked?'congelada':'descongelada'}.`);
 if(el.matches('[data-lmrole]')){const L={...(cfg.layers||{})};for(const k of Object.keys(L))L[k]=(L[k]||[]).filter(x=>x!==n);if(el.value)L[el.value]=[...(L[el.value]||[]),n];for(const k of Object.keys(L))if(!L[k].length)delete L[k];cfg.layers=L;showLayers();scheduleSave();msg(`Camada “${n}”: função ${el.value?'“'+roles[el.value]+'”':'ignorada'}. Clique “Analisar arquivos” para aplicar.`)}});
$('lmRows')?.addEventListener('click',e=>{const tr=e.target.closest('[data-lmn]');if(!tr||e.target.closest('input,select,button'))return;const n=tr.dataset.lmn;lmChecked.has(n)?lmChecked.delete(n):lmChecked.add(n);renderLM()});
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('#layerDlg [data-lm]');if(!b)return;const a=b.dataset.lm,N=lmNames(),all=lmLayers().map(l=>l.name);
 if(a==='reset')return lmApply((h,f)=>{h.clear();f.clear()},'Todas as camadas visíveis e descongeladas.');
 if(!N.length)return msg('Marque uma ou mais camadas na lista (caixa à esquerda, ou clique na linha).',true);
 const axis=new Set((cfg.layers||{}).axis||[]);
 if(a==='show')lmApply((h)=>N.forEach(n=>h.delete(n)),`${N.length} camada(s) visíveis.`);
 if(a==='hide')lmApply((h,f)=>N.forEach(n=>{h.add(n);f.delete(n)}),`${N.length} camada(s) ocultas. Clique “Analisar arquivos” para recalcular sem elas.`);
 if(a==='freeze')lmApply((h,f)=>N.forEach(n=>{f.add(n);h.delete(n)}),`${N.length} camada(s) congeladas.`);
 if(a==='thaw')lmApply((h,f)=>N.forEach(n=>f.delete(n)),`${N.length} camada(s) descongeladas.`);
 if(a==='isolate')lmApply((h,f)=>{all.forEach(n=>{if(!N.includes(n)&&!axis.has(n))h.add(n)});N.forEach(n=>{h.delete(n)})},`Só as ${N.length} camada(s) marcadas (e o eixo) ficam visíveis.`);
 if(a==='final')lmApply((h,f)=>{all.forEach(n=>{if(N.includes(n)){f.delete(n);h.delete(n)}else if(!h.has(n))f.add(n)})},`Edição final: ${all.length-N.length} camada(s) congeladas; só as ${N.length} marcadas continuam editáveis.`)});
$('lmUndo')?.addEventListener('click',()=>{const s=lmHist.pop();if(!s)return;cfg.hidden_layers=s.h;cfg.frozen_layers=s.f;buildVectorPaths();snapIndex=null;exactSnap=null;draw();showLayers();scheduleSave();announce({t:'layers'});$('lmUndo').disabled=!lmHist.length;renderLM();msg('Camadas: alteração desfeita.')});
$('lmClose')?.addEventListener('click',()=>$('layerDlg').close());
itemFaixa('Aparência','Camadas',['Gerenciador de camadas','☷',()=>openLayerManager(),1],{inicio:true});
comando(['CAMADAS','LA','LAYER','GERENCIADOR'],()=>openLayerManager(),'Gerenciador de camadas (visível, oculta, congelada, em grupo)');

