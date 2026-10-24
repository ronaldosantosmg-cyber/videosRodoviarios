// =====================================================================================================
// 1.37: vegetação (árvore avulsa, pincel e área), caminhos de pedestres, frota variada e abrir DWG.
// =====================================================================================================
const VEG_LABEL={arvore:'Árvore',ipe:'Ipê amarelo (florido)',eucalipto:'Eucalipto',palmeira:'Palmeira',arbusto:'Arbusto',cerca_viva:'Cerca-viva'};
const VEG_COR={arvore:'#3f7a34',ipe:'#e2b828',eucalipto:'#58745a',palmeira:'#4b8236',arbusto:'#356a2e',cerca_viva:'#30602a'};
const VEG_TAM={arvore:8,ipe:8,eucalipto:6,palmeira:7,arbusto:3,cerca_viva:2};
MARK_KEYS.push('vegetation_points','vegetation_areas','pedestrian_paths');
estender('emptyMarks',_em=>function(){return {..._em(),vegetation_points:[],vegetation_areas:[],pedestrian_paths:[]}},'vegetação e pedestres');
for(const k of ['vegetation_points','vegetation_areas','pedestrian_paths'])if(!M[k])M[k]=[];
checks.push('pedestrians');fields.push('vehicle_mix');
OBJ_SPECS.push(['vegetation_areas','Vegetação','area',o=>o.points.map((_,i)=>[o.points,i])],['pedestrian_paths','Caminho de pedestres','poly',o=>o.points.map((_,i)=>[o.points,i])],['vegetation_points','Planta','pt',o=>[[o,null]]]);
ENUMS.kind.vegetation_areas=VEG_LABEL;ENUMS.kind.vegetation_points=VEG_LABEL;
Object.assign(PROP_LABEL,{density:['Densidade (plantas por 1000 m²)','Quantas plantas a cada 1000 m² da área (6 = mata rala; 20 = bosque fechado).'],size_m:['Tamanho (m)','Diâmetro da copa em metros.'],
 seed:['Sorteio','Muda a posição das plantas na área (o mesmo número dá sempre o mesmo arranjo).'],people_per_100m:['Pessoas a cada 100 m','Quantas pessoas andam neste caminho.']});
let vegOpt={kind:'arvore',modo:'pincel',size:8,dens:8,passo:10};try{Object.assign(vegOpt,JSON.parse(localStorage.getItem('rodovia_veg')||'{}'))}catch{}
function vegSalvar(){try{localStorage.setItem('rodovia_veg',JSON.stringify(vegOpt))}catch{}}
function novaPlanta(w,esp=0){const a=Math.random()*2*Math.PI,r=Math.random()*esp;return {x:+(w.x+Math.cos(a)*r).toFixed(2),y:+(w.y+Math.sin(a)*r).toFixed(2),kind:vegOpt.kind,size_m:+(vegOpt.size*(.85+Math.random()*.3)).toFixed(2)}}
ferramenta('veg',{rotulo:'🌳 Vegetação',dica:'Árvore avulsa (clique), pincel (arraste para plantar ao longo do caminho) ou área (clique os vértices e Enter). Escolha o tipo e o tamanho nas opções. Esc encerra.',
 antesDe:'linkforce',icone:'M12 21v-6M7 15a5 5 0 1 1 3.5-8.6A5 5 0 1 1 17 15z',
 opcoes(el){el.innerHTML=`<div class="grid"><label>Tipo<select id="vegKind">${Object.entries(VEG_LABEL).map(([k,l])=>`<option value="${k}" ${k===vegOpt.kind?'selected':''}>${l}</option>`).join('')}</select></label>
  <label>Modo<select id="vegModo"><option value="arvore">Árvore avulsa (clique)</option><option value="pincel">Pincel (arrastar)</option><option value="area">Área (vértices + Enter)</option></select></label>
  <label>Tamanho da copa (m)<input id="vegSize" type="number" min="1" max="30" step="0.5" value="${vegOpt.size}"></label>
  <label id="vegDensL">${vegOpt.modo==='area'?'Densidade (por 1000 m²)':'Espaçamento do pincel (m)'}<input id="vegDens" type="number" min="0.2" max="60" step="0.5" value="${vegOpt.modo==='area'?vegOpt.dens:vegOpt.passo}"></label></div>`;
  $('vegModo').value=vegOpt.modo;
  const sync=()=>{vegOpt.kind=$('vegKind').value;const novo=$('vegModo').value;if(novo!==vegOpt.modo){vegOpt.modo=novo;vegSalvar();toolOptions();return}vegOpt.size=Math.max(1,Math.min(30,Number($('vegSize').value)||8));
   const v=Number($('vegDens').value)||8;if(vegOpt.modo==='area')vegOpt.dens=Math.max(.2,Math.min(60,v));else vegOpt.passo=Math.max(1,Math.min(60,v));vegSalvar()};
  el.querySelectorAll('select,input').forEach(x=>x.addEventListener('change',sync));
  $('vegKind').addEventListener('change',()=>{$('vegSize').value=VEG_TAM[$('vegKind').value]||8;sync()})},
 clique(w){if(vegOpt.modo==='arvore'){checkpoint();M.vegetation_points.push(novaPlanta(w));changed(`${VEG_LABEL[vegOpt.kind]} plantada. Clique para a próxima; Esc encerra.`);return}
  if(vegOpt.modo==='area'){if(!draft||draft.type!=='veg')draft={type:'veg',pts:[]};draft.pts.push(w);prompt_(`VEGETAÇÃO — ${draft.pts.length} vértice(s); Enter conclui a área:`);draw()}},
 concluir(d){if(d.pts.length<3)return msg('Marque pelo menos três vértices.',true);draft=null;checkpoint();
  M.vegetation_areas.push({id:uid(),name:`${VEG_LABEL[vegOpt.kind]} ${M.vegetation_areas.length+1}`,kind:vegOpt.kind,points:d.pts.map(p=>({x:p.x,y:p.y})),density:vegOpt.dens,size_m:vegOpt.size,seed:Math.floor(Math.random()*1e6),enabled:true});
  changed('Área de vegetação criada (as plantas não entram sobre a pista). Desenhe a próxima ou Esc.')}});
// Pincel: arrastar planta ao longo do caminho, com espaçamento e leve dispersão.
let pincelVeg=null;
canvas.addEventListener('pointerdown',e=>{if(tool!=='veg'||vegOpt.modo!=='pincel'||e.button!==0||!ready()||spaceDown)return;e.stopImmediatePropagation();e.preventDefault();
 try{canvas.setPointerCapture(e.pointerId)}catch{};const c=canvasPt(e);checkpoint();M.vegetation_points.push(novaPlanta(c.w));pincelVeg={ult:c.w,n:1};draw()},true);
canvas.addEventListener('pointermove',e=>{if(!pincelVeg)return;e.stopImmediatePropagation();const c=canvasPt(e);if(!c.w)return;const d=Math.hypot(c.w.x-pincelVeg.ult.x,c.w.y-pincelVeg.ult.y);
 if(d>=vegOpt.passo){const k=Math.floor(d/vegOpt.passo);for(let i=1;i<=k;i++){const f=i*vegOpt.passo/d;M.vegetation_points.push(novaPlanta({x:pincelVeg.ult.x+(c.w.x-pincelVeg.ult.x)*f,y:pincelVeg.ult.y+(c.w.y-pincelVeg.ult.y)*f},vegOpt.passo*.35));pincelVeg.n++}
  pincelVeg.ult={x:pincelVeg.ult.x+(c.w.x-pincelVeg.ult.x)*k*vegOpt.passo/d,y:pincelVeg.ult.y+(c.w.y-pincelVeg.ult.y)*k*vegOpt.passo/d};draw()}},true);
canvas.addEventListener('pointerup',e=>{if(!pincelVeg)return;e.stopImmediatePropagation();const n=pincelVeg.n;pincelVeg=null;if(M.vegetation_points.length>20000){undo();return msg('Limite de 20.000 plantas avulsas; use áreas para matas grandes.',true)}
 changed(`${n} ${n>1?'plantas':'planta'} (${VEG_LABEL[vegOpt.kind]}). Arraste de novo para continuar; Ctrl+Z desfaz o traço.`)},true);
ferramenta('pedestres',{rotulo:'🚶 Caminho de pedestres',dica:'Clique os pontos da calçada ou trilha e Enter: pessoas andam nos dois sentidos no vídeo (as faixas de pedestre e as passarelas já têm pessoas).',
 antesDe:'linkforce',icone:'M13 4a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zM10 21l2-6 2 2v4M9 12l3-3 3 2 2 3M12 9l-1 6',
 clique(w){if(!draft||draft.type!=='pedestres')draft={type:'pedestres',pts:[]};draft.pts.push(w);prompt_(`PEDESTRES — ${draft.pts.length} ponto(s); Enter conclui:`);draw()},
 concluir(d){if(d.pts.length<2)return msg('Marque pelo menos dois pontos.',true);draft=null;checkpoint();
  M.pedestrian_paths.push({id:uid(),name:`Caminho de pedestres ${M.pedestrian_paths.length+1}`,points:d.pts.map(p=>({x:p.x,y:p.y})),people_per_100m:3,enabled:true});
  if($('pedestrians')&&!$('pedestrians').checked){$('pedestrians').checked=true;scheduleSave()}changed('Caminho de pedestres criado. Desenhe o próximo ou Esc.')}});
// Editor: plantas, áreas e caminhos.
estender('draw',anterior=>function(){anterior();if(!ready()||vecOn?.vegetacao===false)return;const VP=M.vegetation_points||[],VA=M.vegetation_areas||[],PP=M.pedestrian_paths||[];if(!VP.length&&!VA.length&&!PP.length&&!(draft&&['veg','pedestres'].includes(draft.type)))return;
 try{ctx.save();const k=pxPerM();
  for(const a of VA){const P=a.points.map(p=>W2C(p));ctx.beginPath();P.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.closePath();ctx.globalAlpha=.22;ctx.fillStyle=VEG_COR[a.kind]||'#3f7a34';ctx.fill();ctx.globalAlpha=.9;
   ctx.setLineDash([6,4]);ctx.strokeStyle='#7fd06a';ctx.lineWidth=1.5;ctx.stroke();ctx.setLineDash([]);const [x,y]=P[0];ctx.fillStyle='#7fd06a';ctx.font='bold 11px "Segoe UI",system-ui';ctx.fillText('🌳 '+a.name,x+4,y-4)}
  ctx.globalAlpha=.85;for(const p of VP){const [x,y]=W2C(p);const r=Math.max(2.5,p.size_m/2*k);if(x<-r||y<-r||x>canvas.width+r||y>canvas.height+r)continue;ctx.beginPath();ctx.arc(x,y,r,0,2*Math.PI);ctx.fillStyle=VEG_COR[p.kind]||'#3f7a34';ctx.fill();ctx.strokeStyle='#183014';ctx.lineWidth=1;ctx.stroke()}
  ctx.globalAlpha=1;for(const p of PP){const P=p.points.map(q=>W2C(q));ctx.beginPath();P.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.setLineDash([3,5]);ctx.strokeStyle='#ffe08a';ctx.lineWidth=3;ctx.stroke();ctx.setLineDash([]);const [x,y]=P[0];ctx.fillStyle='#ffe08a';ctx.font='bold 11px "Segoe UI",system-ui';ctx.fillText('🚶 '+p.name,x+4,y-6)}
  if(draft&&['veg','pedestres'].includes(draft.type)&&draft.pts.length){const P=draft.pts.map(q=>W2C(q));ctx.beginPath();P.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));if(lastWorld){const [x,y]=W2C(lastWorld);ctx.lineTo(x,y)}ctx.strokeStyle=draft.type==='veg'?'#7fd06a':'#ffe08a';ctx.lineWidth=2;ctx.setLineDash([5,4]);ctx.stroke();ctx.setLineDash([])}
  ctx.restore()}catch(e){ctx.restore()}},'vegetação e pedestres no editor');
// ---------- abrir DWG ----------
estender('filesUi',anterior=>function(info){anterior(info);const f=(info||filesInfo||{}).dxf;const tr=document.querySelector('.fileTable tr[data-fk="dxf"] .fn small');if(f&&f.convertido&&tr&&!tr.dataset.dwg){tr.dataset.dwg='1';tr.insertAdjacentHTML('beforeend',' · convertido do DWG')}},'DWG: indicação de conversão');
estender('sendFiles',anterior=>async function(list){const fs=[...list];if(fs.some(f=>/\.dwg$/i.test(f.name))){let r={ok:true};try{r=await api('/api/dwg')}catch{}
  if(!r.ok){await confirmBox(r.ajuda||'Instale o ODA File Converter para abrir DWG.','Entendi','Fechar');const resto=fs.filter(f=>!/\.dwg$/i.test(f.name));if(!resto.length)return;return anterior(resto)}
  msg('Convertendo o DWG em DXF (ODA File Converter)… pode levar alguns segundos.')}return anterior(fs)},'DWG: conversão para DXF');
{const G=RIBBON.find(t=>t[0]==='Início')[1].find(g=>g[0]==='Arquivos');const it=G&&G[1].find(i=>i[0]==='DXF…');if(it)it[0]='DXF/DWG…'}
comando(['ARVORE','VEGETACAO','VEG'],()=>setTool('veg'),'Vegetação: árvore avulsa, pincel ou área');comando(['PEDESTRES','CAMINHO'],()=>setTool('pedestres'),'Caminho de pedestres (calçada ou trilha)');
