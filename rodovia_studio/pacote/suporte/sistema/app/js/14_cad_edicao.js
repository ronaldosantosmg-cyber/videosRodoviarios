// =====================================================================================================
// 1.22 — Edição tipo CAD: seleção com grips, propriedades com Enter, linha de comando, snap, orto,
// alinhamento por cliques, mover/apagar, salvar/salvar como.
// =====================================================================================================
let sel=null,snapMark=null,lastPick=null,cadCmd=null,snapIndex=null;
const OBJ_SPECS=[
 ['signs','Placa','pt',o=>[[o,'point']]],
 ['pois','Intervenção','pt',o=>[[o,null]].concat(o.anchor?[[o,'anchor']]:[])],
 ['highlights','Destaque','pt',o=>[[o,'point']].concat(o.label?[[o,'label']]:[])],
 ['cities','Cidade','pt',o=>[[o,'point']]],
 ['crosswalks','Faixa de pedestre','line',o=>[[o,'a'],[o,'b']]],
 ['lane_ranges','Faixa adicional','line',o=>[[o,'start'],[o,'end']]],
 ['shoulder_marks','Acostamento','line',o=>[[o,'start'],[o,'end']]],
 ['direction_marks','Seta de sentido','line',o=>[[o,'start'],[o,'end']]],
 ['accesses','Acesso','poly',o=>o.points.map((_,i)=>[o.points,i])],
 ['traffic_paths','Fluxo incluído','poly',o=>o.points.map((_,i)=>[o.points,i])],
 ['hatch_areas','Zebrado','area',o=>o.points.map((_,i)=>[o.points,i])],
 ['pavement_areas','Área de pista','area',o=>o.points.map((_,i)=>[o.points,i])],
 ['lane_zones','Faixas por trecho','area',o=>o.points.map((_,i)=>[o.points,i])],
 ['lane_blocks','Interdição','area',o=>o.points.map((_,i)=>[o.points,i])],
 ['clean_areas','Área sem sinalização','area',o=>o.map((_,i)=>[o,i])],
 ['exclusions','Área de exclusão','area',o=>o.map((_,i)=>[o,i])],
 ['crossing_zones','Travessia','auto',o=>o.kind==='point'?[[o,'point']]:o.points.map((_,i)=>[o.points,i])],
 ['no_connection_zones','Sem conexão','auto',o=>o.kind==='point'?[[o,'point']]:o.points.map((_,i)=>[o.points,i])],
 ['oae_marks','OAE','auto',o=>o.polygon&&o.polygon.length>=4?o.polygon.map((_,i)=>[o.polygon,i]):[[o,'start'],[o,'end']]],
];
const ENUMS={kind:{pavement_areas:PAV_LABEL},material:MAT_LABEL,color:{white:'Branco',yellow:'Amarelo'},code:SIGN_LABEL,mode:{both:'Entrada e saída',in:'Só entrada',out:'Só saída',partial:'Parcial',total:'Total',allow:'Permitida',deny:'Proibida'},category:HL_LABEL};
function gripGet([c,k]){return k===null?{x:c.x,y:c.y}:c[k]}
function gripSet([c,k],w){const p={x:+w.x,y:+w.y};if(k===null){c.x=p.x;c.y=p.y}else c[k]=p}
function objList(){const out=[];for(const [key,label,shape,fn] of OBJ_SPECS){const L=M[key];if(!Array.isArray(L))continue;L.forEach((o,i)=>{try{if(key==='image_features'&&(!o.enabled||!o.visible||M.image_groups?.[o.role]?.visible===false))return;const g=fn(o).filter(r=>{const p=gripGet(r);return p&&isFinite(p.x)});if(g.length)out.push({key,i,label,shape:shape==='auto'?(g.length===1?'pt':g.length===2?'line':'area'):shape,o,grips:g})}catch{}})}
 if(M.custom_axis&&M.custom_axis.points?.length)out.push({key:'custom_axis',i:0,label:'Alinhamento',shape:'poly',o:M.custom_axis,grips:M.custom_axis.points.map((_,i)=>[M.custom_axis.points,i])});return out}
function objOf(s){return s?objList().find(o=>o.key===s.key&&o.i===s.i)||null:null}
function segDist(px,py,ax,ay,bx,by){const dx=bx-ax,dy=by-ay,L=dx*dx+dy*dy;let t=L?((px-ax)*dx+(py-ay)*dy)/L:0;t=Math.max(0,Math.min(1,t));return Math.hypot(px-ax-t*dx,py-ay-t*dy)}
function hitObject(c){let best=null;for(const o of objList()){const P=o.grips.map(g=>W2C(gripGet(g)));let d=Infinity;
  if(o.shape==='pt')d=Math.min(...P.map(([x,y])=>Math.hypot(x-c.cx,y-c.cy)));
  else{for(let k=0;k+1<P.length;k++)d=Math.min(d,segDist(c.cx,c.cy,...P[k],...P[k+1]));if(o.shape==='area'&&P.length>2){d=Math.min(d,segDist(c.cx,c.cy,...P[P.length-1],...P[0]));let inside=false;for(let i=0,j=P.length-1;i<P.length;j=i++){const [xi,yi]=P[i],[xj,yj]=P[j];if(((yi>c.cy)!==(yj>c.cy))&&c.cx<(xj-xi)*(c.cy-yi)/(yj-yi)+xi)inside=!inside}if(inside)d=Math.min(d,7)}}
  if(d<=9&&(!best||d<best.d))best={key:o.key,i:o.i,d}}return best}
function hitGrip(c){const o=objOf(sel);if(!o)return null;for(let k=0;k<o.grips.length;k++){const [x,y]=W2C(gripGet(o.grips[k]));if(Math.abs(x-c.cx)<=7*DPR()&&Math.abs(y-c.cy)<=7*DPR())return {o,k}}return null}
function drawSelection(){const o=objOf(sel);if(!o)return;const P=o.grips.map(g=>W2C(gripGet(g)));ctx.save();ctx.strokeStyle='#4fa3ff';ctx.lineWidth=2;ctx.setLineDash([6,4]);
 if(o.shape!=='pt'){ctx.beginPath();P.forEach(([x,y],k)=>k?ctx.lineTo(x,y):ctx.moveTo(x,y));if(o.shape==='area')ctx.closePath();ctx.stroke()}ctx.setLineDash([]);
 const gs=5*DPR();for(const [x,y] of P){ctx.fillStyle=drag?.type==='grip'?'#ff4d4d':'#2f7cf6';ctx.strokeStyle='#fff';ctx.lineWidth=1.5;ctx.fillRect(x-gs,y-gs,2*gs,2*gs);ctx.strokeRect(x-gs,y-gs,2*gs,2*gs)}ctx.restore()}
function drawSnap(){if(!snapMark||!lastWorld)return;const [x,y]=W2C(snapMark.w);ctx.save();ctx.strokeStyle='#ffd400';ctx.lineWidth=2;ctx.beginPath();
 if(snapMark.kind==='vértice')ctx.rect(x-6,y-6,12,12);else if(snapMark.kind==='ponto médio'){ctx.moveTo(x,y-7);ctx.lineTo(x+7,y+6);ctx.lineTo(x-7,y+6);ctx.closePath()}else{ctx.moveTo(x-6,y-6);ctx.lineTo(x+6,y+6);ctx.moveTo(x+6,y-6);ctx.lineTo(x-6,y+6)}
 ctx.stroke();ctx.fillStyle='#ffd400';ctx.font='11px system-ui';ctx.fillText(snapMark.kind,x+9,y-8);ctx.restore()}
// ---------- snap ----------
function buildSnap(){snapIndex=new Map();const B=5;const add=(x,y,kind)=>{const k=Math.floor(x/B)+','+Math.floor(y/B);let a=snapIndex.get(k);if(!a)snapIndex.set(k,a=[]);a.push([x,y,kind])};
 for(const list of Object.values(vec?.layers||{})){if(!Array.isArray(list))continue;for(const r of list){const P=r.p||[];for(let i=0;i<P.length;i++){add(P[i][0],P[i][1],'vértice');if(i+1<P.length)add((P[i][0]+P[i+1][0])/2,(P[i][1]+P[i+1][1])/2,'ponto médio')}}}}
function snapPoint(c){const r=10/Math.max(pxPerM(),1e-9);let best=null;const B=5;const w=c.w;
 const cand=(x,y,kind,pri)=>{const d=Math.hypot(x-w.x,y-w.y);if(d<=r&&(!best||d+pri*r<best.score))best={w:{x,y},kind,score:d+pri*r}};
 if(!snapIndex)buildSnap();const n=Math.ceil(r/B);const bx=Math.floor(w.x/B),by=Math.floor(w.y/B);
 if(n<=40)for(let i=-n;i<=n;i++)for(let j=-n;j<=n;j++){const a=snapIndex.get((bx+i)+','+(by+j));if(a)for(const [x,y,k] of a)cand(x,y,k,0)}
 for(const o of objList())if(!(drag?.type==='grip'&&o.key===drag.g.o.key&&o.i===drag.g.o.i))for(const g of o.grips){const p=gripGet(g);cand(p.x,p.y,'vértice',0)}
 if(!best&&axisData()){const p=projectAxis(w);if(p&&p.dist<=r)best={w:p.point,kind:'eixo',score:p.dist+r}}
 return best}
function snapActive(){return $('snapOn')?.checked!==false&&ready()&&(tool!=='pan'||drag?.type==='grip'||drag?.type==='objmove'||!!cadCmd)}
function ortho(w){if(!$('orthoOn')?.checked)return w;const ref=draft?.pts?.length?draft.pts[draft.pts.length-1]:cadCmd?.base||null;if(!ref)return w;const dx=w.x-ref.x,dy=w.y-ref.y;return Math.abs(dx)>=Math.abs(dy)?{x:w.x,y:ref.y}:{x:ref.x,y:w.y}}
estender('canvasPt',_cp=>function(e){const c=_cp(e);if(c.w){snapMark=null;if(snapActive()){const s=snapPoint(c);if(s){c.w=s.w;snapMark=s}}c.w=ortho(c.w)}return c},'snap');
// ---------- seleção, grips e mover ----------
canvas.addEventListener('pointerdown',e=>{if(!ready()||e.button!==0||spaceDown||cadCmd)return;if(tool!=='pan')return;const c=canvasPt(e);try{canvas.setPointerCapture(e.pointerId)}catch{};canvas.focus({preventScroll:true});
 const g=hitGrip(c);if(g){checkpoint();drag={type:'grip',g};e.stopImmediatePropagation();canvas.style.cursor='move';return}
 const h=hitObject(c);if(h){if(sel&&sel.key===h.key&&sel.i===h.i){checkpoint();const o=objOf(sel);drag={type:'objmove',w0:c.w,base:o.grips.map(gripGet),o}}else{sel={key:h.key,i:h.i};showProps();draw();msg(`Selecionado: ${objOf(sel).label}. Arraste um grip ou o objeto; Delete apaga; edite as propriedades e confirme com Enter.`)}e.stopImmediatePropagation();return}
 if(sel){sel=null;showProps();draw()}},true);
canvas.addEventListener('pointermove',e=>{if(!drag||(drag.type!=='grip'&&drag.type!=='objmove'))return;const c=canvasPt(e);lastWorld=c.w;
 if(drag.type==='grip'){gripSet(drag.g.o.grips[drag.g.k],c.w);drag.moved=true}else{const dx=c.w.x-drag.w0.x,dy=c.w.y-drag.w0.y;drag.o.grips.forEach((g,k)=>gripSet(g,{x:drag.base[k].x+dx,y:drag.base[k].y+dy}));drag.moved=true}
 e.stopImmediatePropagation();draw();cursorInfo(c.w)},true);
canvas.addEventListener('pointerup',e=>{if(!drag||(drag.type!=='grip'&&drag.type!=='objmove'))return;const d=drag;drag=null;canvas.style.cursor='grab';e.stopImmediatePropagation();
 if(d.moved){afterGeomEdit(d.o||d.g.o);changed(d.type==='grip'?'Grip movido.':'Objeto movido.')}else undoStack.pop();showProps();draw()},true);
function afterGeomEdit(o){if(o&&o.key==='oae_marks'&&typeof oaeEnds==='function')try{oaeEnds(o.o)}catch{}}
function deleteSel(){const o=objOf(sel);if(!o)return false;checkpoint();if(o.key==='custom_axis')M.custom_axis=null;else M[o.key].splice(o.i,1);sel=null;showProps();changed(`${o.label} apagado(a).`);return true}
// ---------- propriedades ----------
function propInput(path,v,key,listKey){const id='pp_'+path.replace(/\W/g,'_');
 const en=ENUMS[key]&&(ENUMS[key][listKey]||(!Object.values(ENUMS[key]).some(x=>typeof x==='object')&&ENUMS[key]));
 if(en&&typeof en==='object')return `<select id="${id}" data-pp="${path}">${Object.entries(en).map(([k,l])=>`<option value="${k}" ${String(v)===k?'selected':''}>${esc(l)}</option>`).join('')}</select>`;
 if(typeof v==='boolean')return `<input id="${id}" data-pp="${path}" type="checkbox" ${v?'checked':''}>`;
 if(typeof v==='number')return `<input id="${id}" data-pp="${path}" type="number" step="any" value="${v}">`;
 return `<input id="${id}" data-pp="${path}" value="${esc(v??'')}">`}
function showProps(){const box=$('propPanel');if(!box)return;const o=objOf(sel);if(!o){box.hidden=true;box.innerHTML='';return}box.hidden=false;
 const fields=Object.entries(o.key==='clean_areas'||o.key==='exclusions'?{}:o.o).filter(([k,v])=>(o.key!=='image_features'||['name','enabled','visible'].includes(k))&&!['id','points','polygon','x','y'].includes(k)&&(v===null||['string','number','boolean'].includes(typeof v)));
 box.innerHTML=`<h3>Propriedades · ${esc(o.label)}</h3><table>`+fields.map(([k,v])=>`<tr><td>${esc(k)}</td><td>${propInput(k,v,k,o.key)}</td></tr>`).join('')+'</table>'+
  `<h4>Grips (coordenadas ${esc(cfg.crs||'')}, m)</h4><table>`+o.grips.map((g,k)=>{const p=gripGet(g);return `<tr><td>${k+1}</td><td>X<input data-grip="${k}" data-ax="x" type="number" step="0.001" value="${p.x.toFixed(3)}"></td><td>Y<input data-grip="${k}" data-ax="y" type="number" step="0.001" value="${p.y.toFixed(3)}"></td></tr>`}).join('')+'</table>'+
  `<div class="row"><button type="button" data-ppact="move">Mover (M)</button><button type="button" data-ppact="del" class="danger">Apagar (Del)</button><button type="button" data-ppact="zoom">Ver</button><button type="button" data-ppact="close">Fechar</button></div><p class="muted">Altere um valor e pressione Enter para confirmar (Esc desfaz a digitação).</p>`}
function commitProp(el){const o=objOf(sel);if(!o)return;checkpoint();
 if(el.dataset.grip!==undefined){const g=o.grips[Number(el.dataset.grip)],p=gripGet(g);const v=Number(String(el.value).replace(',','.'));if(!isFinite(v)){undoStack.pop();return msg('Coordenada inválida.',true)}gripSet(g,{...p,[el.dataset.ax]:v});afterGeomEdit(o)}
 else{const k=el.dataset.pp,old=o.o[k];let v=el.type==='checkbox'?el.checked:el.type==='number'?Number(String(el.value).replace(',','.')):el.value;
  if(typeof old==='string'&&old.trim()!==''&&String(v).trim()===''&&['name','title'].includes(k)){undoStack.pop();showProps();return msg(`O campo “${k}” não pode ficar vazio.`,true)}
  if(el.type==='number'&&String(el.value).trim()===''&&old!==null){undoStack.pop();showProps();return msg(`O campo “${k}” não pode ficar vazio.`,true)}if(typeof old==='number'&&!isFinite(v)){undoStack.pop();return msg('Valor numérico inválido.',true)}if(old===null&&el.value==='')v=null;o.o[k]=v}
 changed('Propriedade alterada.');showProps()}
document.addEventListener('keydown',e=>{const el=e.target;if(!el.closest||!el.closest('#propPanel'))return;if(e.key==='Enter'){e.preventDefault();commitProp(el)}if(e.key==='Escape'){e.preventDefault();showProps()}});
document.addEventListener('change',e=>{const el=e.target;if(el.closest&&el.closest('#propPanel')&&(el.tagName==='SELECT'||el.type==='checkbox'))commitProp(el)});
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('#propPanel [data-ppact]');if(!b)return;const a=b.dataset.ppact;
 if(a==='del')deleteSel();else if(a==='close'){sel=null;showProps();draw()}else if(a==='zoom'){const o=objOf(sel);if(o)zoomTo(gripGet(o.grips[0]))}else if(a==='move')runCommand('MOVER')});
// ---------- linha de comando ----------
const CMD_ALIAS={M:'MOVER',MOVE:'MOVER',MOVER:'MOVER',E:'APAGAR',DEL:'APAGAR',ERASE:'APAGAR',APAGAR:'APAGAR',EXCLUIR:'APAGAR',PR:'PROPRIEDADES',PROPRIEDADES:'PROPRIEDADES',
 AL:'tool:align',ALINHAMENTO:'tool:align',ALIGN:'tool:align',PLACA:'tool:sign',ZEBRADO:'tool:hatch',AREA:'tool:pavarea',ÁREA:'tool:pavarea',ACOSTAMENTO:'tool:shoulder',ACESSO:'tool:access',
 KM:'tool:chain',KMINI:'tool:chain',KMFIM:'tool:chainend',PASSARELA:'tool:span',CHAMADA:'tool:anchor',DESTAQUE:'tool:highlight',OAE:'tool:oaepoly',FAIXA:'tool:crosswalk',
 P:'tool:pan',PAN:'tool:pan',NAVEGAR:'tool:pan',SEL:'tool:pan',ZOOM:'ZOOM',Z:'ZOOM',SALVAR:'SALVAR',SAVE:'SALVAR',SNAP:'SNAP',ORTO:'ORTO',ORTHO:'ORTO',DIST:'DIST',DI:'DIST',ID:'ID'};
function prompt_(t){$('cmdPrompt').textContent=t}
function parsePoint(txt){const t=txt.trim();const rel=t.startsWith('@');const s=(rel?t.slice(1):t).replace(/\s*[;\s]\s*/,'|').replace(/^([^,|]+),([^,|]+)$/,'$1|$2');const m=s.split('|');if(m.length!==2)return null;const a=Number(m[0].replace(',','.')),b=Number(m[1].replace(',','.'));if(!isFinite(a)||!isFinite(b))return null;
 if(rel){const r=lastPick||cadCmd?.base;if(!r)return null;return {x:r.x+a,y:r.y+b}}return {x:a,y:b}}
function feedPoint(w){lastPick=w;if(cadCmd){cadCmd.step(w);return}if(tool==='pan')return msg('Ponto digitado: escolha antes uma ferramenta ou comando.',true);click(w,{shiftKey:false,ctrlKey:false});draw()}
function runCommand(raw){const t=raw.trim();if(!t){if(cadCmd){cadCmd=null;prompt_('Comando:');msg('Comando encerrado.');draw();return}endCommand();return}
 const pt=parsePoint(t);if(pt){feedPoint(pt);return}
 const c=CMD_ALIAS[t.toUpperCase()];if(!c)return msg(`Comando desconhecido: ${t}. Exemplos: MOVER (M), APAGAR (E), PROPRIEDADES (PR), ALINHAMENTO (AL), PLACA, AREA, ACOSTAMENTO, KMINI, KMFIM, SALVAR, DIST, ID, ou coordenadas X,Y e @dx,dy.`,true);
 if(c.startsWith('tool:')){setTool(c.slice(5));prompt_(TOOLS.find(x=>x[0]===c.slice(5))?.[1]+':');return}
 if(c==='APAGAR'){if(!deleteSel())msg('Selecione um objeto (clique nele com Navegar) e use APAGAR ou a tecla Delete.',true);return}
 if(c==='PROPRIEDADES'){if(!sel)return msg('Selecione um objeto para ver as propriedades.',true);showProps();$('propPanel').scrollIntoView({block:'nearest'});return}
 if(c==='SALVAR'){$('saveProject')?.click();return}
 if(c==='SNAP'){$('snapOn').checked=!$('snapOn').checked;return msg('Snap '+($('snapOn').checked?'ligado':'desligado')+'.')}
 if(c==='ORTO'){$('orthoOn').checked=!$('orthoOn').checked;return msg('Orto '+($('orthoOn').checked?'ligado':'desligado')+'.')}
 if(c==='ZOOM'){fitView();return}
 if(c==='ID'){cadCmd={step(w){msg(`X ${w.x.toFixed(3)} · Y ${w.y.toFixed(3)}`+(axisData()?` · km ${formatKm(kmOf(w).km)}`:''));cadCmd=null;prompt_('Comando:')}};prompt_('ID — clique ou digite o ponto:');return}
 if(c==='DIST'){cadCmd={pts:[],step(w){this.pts.push(w);this.base=w;if(this.pts.length===1)return prompt_('DIST — segundo ponto:');const [a,b]=this.pts;const d=Math.hypot(b.x-a.x,b.y-a.y),az=(Math.atan2(b.x-a.x,b.y-a.y)*180/Math.PI+360)%360;msg(`Distância ${d.toFixed(3)} m · ΔX ${(b.x-a.x).toFixed(3)} · ΔY ${(b.y-a.y).toFixed(3)} · azimute ${az.toFixed(4)}°`);cadCmd=null;prompt_('Comando:')}};prompt_('DIST — primeiro ponto:');return}
 if(c==='MOVER'){const o=objOf(sel);if(!o)return msg('Selecione o objeto (clique nele com Navegar) e use MOVER.',true);
  cadCmd={step(w){if(!this.base){this.base=w;prompt_('MOVER — segundo ponto (ou @dx,dy):');return}const dx=w.x-this.base.x,dy=w.y-this.base.y;checkpoint();o.grips.forEach(g=>{const p=gripGet(g);gripSet(g,{x:p.x+dx,y:p.y+dy})});afterGeomEdit(o);cadCmd=null;prompt_('Comando:');changed(`${o.label} movido(a) ${Math.hypot(dx,dy).toFixed(3)} m.`);showProps()}};prompt_('MOVER — ponto base:');return}}
$('cmdLine')?.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();const v=e.target.value;e.target.value='';runCommand(v)}if(e.key==='Escape'){e.target.value='';cadCmd=null;draft=null;prompt_('Comando:');setTool('pan')}});
// Cliques na tela durante um comando da linha de comando.
canvas.addEventListener('pointerdown',e=>{if(!cadCmd||e.button!==0||!ready())return;const c=canvasPt(e);e.stopImmediatePropagation();feedPoint(c.w);draw()},true);
// Atalhos: Delete apaga a seleção; Ctrl+S salva; F3 snap; F8 orto; teclas digitadas no editor vão para a linha de comando.
document.addEventListener('keydown',e=>{const t=e.target;const typing=t&&(t.tagName==='INPUT'||t.tagName==='TEXTAREA'||t.tagName==='SELECT');
 if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();$('saveProject')?.click();return}
 if(e.key==='F3'){e.preventDefault();$('snapOn').checked=!$('snapOn').checked;msg('Snap '+($('snapOn').checked?'ligado':'desligado')+' (F3).');return}
 if(e.key==='F8'){e.preventDefault();$('orthoOn').checked=!$('orthoOn').checked;msg('Orto '+($('orthoOn').checked?'ligado':'desligado')+' (F8).');return}
 if(typing)return;
 if(e.key==='Delete'&&sel){e.preventDefault();deleteSel();return}
});
// Com a tela do editor em foco, letras e números vão para a linha de comando (como no CAD).
document.addEventListener('keydown',e=>{if(e.target!==canvas||e.key.length!==1||e.ctrlKey||e.altKey||e.metaKey||e.key===' '||!$('cmdLine'))return;if(!/[A-Za-zÀ-ú@0-9.,;\-]/.test(e.key))return;e.preventDefault();e.stopImmediatePropagation();const c=$('cmdLine');c.focus();c.value+=e.key},true);
// ---------- alinhamento por cliques ----------
TOOLS.splice(TOOLS.findIndex(t=>t[0]==='chain'),0,['align','⟋ Alinhamento (cliques)','Clique dois ou mais pontos sobre o eixo da via (o snap atrai para vértices e para o eixo do DXF) e pressione Enter: o alinhamento vira o eixo de referência do estaqueamento, da câmera e do sentido. Edite os grips depois (Navegar + clique na linha).']);
ICON_PATHS.align='M3 19C8 18 9 6 14 5s5 3 7 2M3 19h.01M14 5h.01M21 7h.01';
estender('click',_click=>function(w,e){if(tool==='align'){if(!draft||draft.type!=='align')draft={type:'align',pts:[]};draft.pts.push(w);draw();return msg(`Alinhamento: ${draft.pts.length} ponto(s). Continue clicando sobre o eixo; Enter conclui.`)}return _click(w,e)},'alinhamento por cliques');
estender('finishDraft',_fin=>async function(){const d=draft;if(d&&d.type==='align'){if(d.pts.length<2)return msg('Marque pelo menos dois pontos sobre o eixo.',true);draft=null;checkpoint();
  let L=0;for(let i=1;i<d.pts.length;i++)L+=Math.hypot(d.pts[i].x-d.pts[i-1].x,d.pts[i].y-d.pts[i-1].y);M.custom_axis={name:'Alinhamento do editor',points:d.pts,smooth:true,enabled:true};
  changed(`Alinhamento com ${d.pts.length} pontos (${L.toFixed(3)} m em linha reta entre os pontos). Clique “Analisar arquivos” para usá-lo como eixo de referência.`);return}return _fin()},'alinhamento por cliques');
function drawCustomAxis(){const a=M.custom_axis;if(!a||!a.points||a.points.length<2)return;poly(a.points);ctx.strokeStyle=a.enabled===false?'#9aa3a8':'#ff4fd8';ctx.lineWidth=2.5;ctx.setLineDash([12,5,3,5]);ctx.stroke();ctx.setLineDash([]);
 for(const p of a.points){const [x,y]=W2C(p);ctx.strokeStyle='#ff4fd8';ctx.lineWidth=2;ctx.beginPath();ctx.arc(x,y,4,0,7);ctx.stroke()}label('⟋ '+a.name,a.points[0],'#ffc6f4')}
estender('draw',_d=>function(){_d();if(!ready())return;try{drawCustomAxis();drawSelection();drawSnap();if(draft&&draft.type==='align'){const pts=draft.pts.slice();if(lastWorld)pts.push(lastWorld);poly(pts);ctx.strokeStyle='#ff4fd8';ctx.lineWidth=2;ctx.setLineDash([6,4]);ctx.stroke();ctx.setLineDash([])}}catch(err){}},'alinhamento por cliques');
// ---------- precisão milimétrica no cursor ----------
estender('cursorInfo',_ci=>function(w){_ci(w);if(!w)return;const c=$('cursor');c.textContent=c.textContent.replace(/X [-\d.]+ · Y [-\d.]+/,`X ${w.x.toFixed(3)} · Y ${w.y.toFixed(3)}`);
 const ref=draft?.pts?.length?draft.pts[draft.pts.length-1]:cadCmd?.base;if(ref){const d=Math.hypot(w.x-ref.x,w.y-ref.y),az=(Math.atan2(w.x-ref.x,w.y-ref.y)*180/Math.PI+360)%360;c.textContent+=` · Δ ${d.toFixed(3)} m · azimute ${az.toFixed(3)}°`}if(snapMark)c.textContent+=` · snap: ${snapMark.kind}`},'precisão milimétrica no cursor');
// ---------- salvar / salvar como / excluir ----------
$('saveProject')?.addEventListener('click',guard(async()=>{requireProject();await save();$('saveState').textContent='salvo '+new Date().toLocaleTimeString();msg('Projeto salvo.')}));
$('saveAsProject')?.addEventListener('click',guard(async()=>{requireProject();await save();const name=prompt('Nome da cópia do projeto:',(cfg.name||'Projeto')+' (cópia)');if(!name)return;const r=await api(`/api/projects/${pid}/save_as`,json('POST',{name}));await list();await load(r.id);msg(`Projeto salvo como “${r.name}”. Você está trabalhando na cópia.`)}));
estender('load',_l4=>async (id,options={})=>{if(!options.resultsOnly){snapIndex=null;sel=null;showProps();}const loaded=await _l4(id,options);if(loaded===false||pid!==id)return false;if(options.resultsOnly)return loaded;;return loaded},'salvar / salvar como / excluir');
estender('loadGeo',_lg=>async(...a)=>{snapIndex=null;return _lg(...a)},'salvar / salvar como / excluir');
buildToolbar();

// Snap/orto lembrados por usuário (padrão: desligados, como nas versões anteriores).
try{for(const id of ['snapOn','orthoOn']){const v=localStorage.getItem('rodovia_'+id);if(v!==null&&$(id))$(id).checked=v==='1';$(id)?.addEventListener('change',()=>{try{localStorage.setItem('rodovia_'+id,$(id).checked?'1':'0')}catch{}})}}catch{}

