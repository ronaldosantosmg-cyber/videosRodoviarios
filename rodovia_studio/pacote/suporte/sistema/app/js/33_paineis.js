// ---------- Painéis: dados editáveis em grupos que se expandem e recolhem ----------
const PP_GROUPS=[['ident','Identificação',['name','title','description','text','kind','category','code','type','mode','action','direction','surface','enabled','show','source']],
 ['aparencia','Aparência e dimensões',['color','style','text_scale','material','width_m','height_m','lane_width_m','lanes','median_m','taper_m','taper_in_m','taper_out_m','angle_deg','spacing_m','opacity','level','level_m','outside_pavement','callout','beam_width_m','heading_deg','radius_m','length_m']],
 ['video','Vídeo e tráfego',['show_in_video','show_km','stop','start_s','end_s','speed_kmh','speed_pct','duration_s','population','eye_height_m','fov_deg','pitch_deg','smoothing_s']]];
let ppState={};try{ppState=JSON.parse(localStorage.getItem('rodovia_ppgrp')||'{}')}catch{}
function ppSave(){try{localStorage.setItem('rodovia_ppgrp',JSON.stringify(ppState))}catch{}}
function ppDetails(id,title,count,defOpen){const d=document.createElement('details');d.className='ppGrp';d.dataset.grp=id;d.open=id in ppState?!!ppState[id]:defOpen;d.innerHTML=`<summary>${esc(title)}${count!=null?` <small>(${count})</small>`:''}</summary>`;d.addEventListener('toggle',()=>{ppState[id]=d.open;ppSave()});return d}
function groupProps(){const box=$('propPanel');if(!box||box.hidden||box.querySelector('.ppGrp'))return;const h3=box.querySelector(':scope>h3');if(!h3)return;
 const main=[...box.querySelectorAll(':scope>table')].find(t=>t.querySelector('[data-pp]'));
 if(main){const rows=[...main.querySelectorAll('tr')];const buckets={};for(const tr of rows){const k=tr.querySelector('[data-pp]')?.dataset.pp;const g=(PP_GROUPS.find(([,,ks])=>ks.includes(k))||['outros'])[0];(buckets[g]=buckets[g]||[]).push(tr)}
  const frag=document.createDocumentFragment();for(const [id,title] of [...PP_GROUPS.map(g=>[g[0],g[1]]),['outros','Outros']]){const R=buckets[id];if(!R||!R.length)continue;const d=ppDetails(id,title,R.length,true);const t=document.createElement('table');R.forEach(tr=>t.appendChild(tr));d.appendChild(t);frag.appendChild(d)}main.replaceWith(frag)}
 const sec=box.querySelector(':scope>.rtSecBox');if(sec){const n=sec.querySelectorAll('[data-rsdel]').length;const d=ppDetails('trechos','Trechos da rota',n,true);sec.replaceWith(d);const h=sec.querySelector('h4');if(h){d.querySelector('summary').innerHTML=`${esc(h.textContent)} <small>(${n})</small>`;h.remove()}d.appendChild(sec)}
 const h4=[...box.querySelectorAll(':scope>h4')].find(h=>/Grips/.test(h.textContent));
 if(h4){const t=h4.nextElementSibling;const n=t&&t.tagName==='TABLE'?t.querySelectorAll('tr').length:0;const d=ppDetails('grips',h4.textContent,n,n<=8);if(id_grips_force(n))d.open=false;h4.replaceWith(d);if(t&&t.tagName==='TABLE')d.appendChild(t)}
 if(box.querySelectorAll('.ppGrp').length>1)h3.insertAdjacentHTML('afterend','<div class="ppTools"><button type="button" data-ppall="1" title="Expandir todos os grupos">Expandir tudo</button><button type="button" data-ppall="0" title="Recolher todos os grupos">Recolher tudo</button></div>')}
function id_grips_force(n){return n>200&&!('grips' in ppState)}
estender('showProps',_sp=>function(){_sp();try{groupProps()}catch(e){console.warn(e)}},'Painéis: dados editáveis em grupos que se expandem e recolhem');
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('#propPanel [data-ppall]');if(!b)return;const open=b.dataset.ppall==='1';document.querySelectorAll('#propPanel .ppGrp').forEach(d=>{d.open=open;ppState[d.dataset.grp]=open});ppSave()});
function panelsAll(open){document.querySelectorAll('main section').forEach(s=>{if(s.id==='editorSection')return;s.classList.toggle('collapsed',!open);try{localStorage.setItem('rodovia_sec_'+(s.id||''),open?'0':'1')}catch{}});
 document.querySelectorAll('main section details').forEach(d=>{if(!d.closest('#propPanel'))d.open=open});msg(open?'Painéis expandidos.':'Painéis recolhidos (clique no título de uma seção para abri-la).')}
itemFaixa('Exibir','Janela',['Expandir painéis','⊞',()=>panelsAll(true)]);itemFaixa('Exibir','Janela',['Recolher painéis','⊟',()=>panelsAll(false)]);

