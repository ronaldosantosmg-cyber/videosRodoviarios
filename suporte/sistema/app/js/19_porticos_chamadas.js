// =====================================================================================================
// 1.26 — pórticos, caixas de chamada, camadas ocultas/congeladas, hachuras, alinhamento por linha,
// menu de contexto (estilo Windows), atributos em lote, comandos, tela ampla, fluidez, sessões,
// regenerar prévia e registros (execução, erros, prompt para IA).
// =====================================================================================================
MARK_KEYS.push('gantries');
estender('emptyMarks',_em=>function(){return {..._em(),gantries:[]}},'regenerar prévia e registros (execução, erros, prompt para IA).');
if(!M.gantries)M.gantries=[];
fields.push('callout_layout');
OBJ_SPECS.push(['gantries','Pórtico','line',o=>[[o,'a'],[o,'b']]]);
ENUMS.kind.gantries={portico:'Pórtico (dois apoios)',semiportico:'Semipórtico (um apoio)',bandeira:'Bandeira (um apoio, em balanço)'};
ENUMS.style={cartao:'Cartão completo',compacto:'Compacto',etiqueta:'Etiqueta'};
ENUMS.leader={reta:'Reta',cotovelo:'Cotovelo'};
const PROP_LABEL={name:['Nome','Texto do título da caixa de chamada.'],description:['Descrição','Linha de texto abaixo do título (cartão completo).'],kind:['Tipo','Pórtico: dois apoios. Semipórtico/bandeira: um apoio (o primeiro clique).'],
 image:['Imagem','Arquivo PNG/JPG mostrado na caixa de chamada (ex.: arte da placa).'],beam_width_m:['Espessura em planta da viga (m)','Não é a largura de travessia. A travessia é medida entre seus próprios limites.'],height_m:['Altura (m)','Altura livre; define o tamanho da sombra no chão.'],
 color:['Cor (#rrggbb)','Cor da borda da caixa e da linha de chamada; vazio = padrão.'],show_in_video:['Mostrar no vídeo','Desmarcado: fica só no editor.'],callout:['Caixa de chamada','Mostra a caixa com nome e imagem no vídeo.'],
 start_s:['Mostrar a partir de (s)','Instante do vídeo em que a caixa aparece (vazio = sempre).'],end_s:['Mostrar até (s)','Instante em que a caixa some (vazio = até o fim).'],text_scale:['Tamanho do texto','1 = normal; 0,6 a 2.'],
 style:['Estilo da caixa','Cartão: título, tipo/km, descrição e imagem. Compacto: título e tipo. Etiqueta: só o título.'],leader:['Linha de chamada','Reta ou em cotovelo (horizontal/vertical).'],
 category:['Categoria','Define a cor e a letra do marcador.'],show_km:['Mostrar km','Inclui o km do ponto na caixa.'],stop:['Parada da câmera','A câmera para neste ponto durante o vídeo.'],code:['Código','Código da placa.'],text:['Texto','Texto da placa.'],
 width_m:['Largura (m)',''],enabled:['Ativo','Desmarcado: mantém a geometria mas não usa no vídeo.'],show:['Mostrar',''],material:['Material','Flexível (asfalto) ou rígido (concreto).'],lanes:['Faixas','Faixas por sentido no trecho.']};
const NULLABLE_NUM=new Set(['start_s','end_s','km_start_override_m','km_end_override_m','heading_deg','population','speed_kmh']);

// ---------- pórtico: ferramenta, desenho no editor e imagem ----------
TOOLS.splice(TOOLS.findIndex(t=>t[0]==='sign')+1,0,['gantry','⊓ Pórtico','Clique no primeiro apoio (pilar) e depois no segundo, do outro lado da pista. Depois envie a imagem da placa no painel de propriedades: ela aparece na caixa de chamada do vídeo. Esc cancela.']);
ICON_PATHS.gantry='M5 21V5M19 21V5M3 5h18v4H3zM7 5l3 4M11 5l3 4M15 5l3 4';
const imgCache=new Map();
function projImg(name){if(!name||!pid)return null;let im=imgCache.get(name);if(!im){im=new Image();im.onload=()=>draw();im.src=`/api/projects/${pid}/imagens/${name}`;imgCache.set(name,im)}return im.complete&&im.naturalWidth?im:null}
estender('click',_click=>function(w,e){if(tool!=='gantry')return _click(w,e);
 if(!draft||draft.type!=='gantry'){draft={type:'gantry',pts:[w]};draw();return msg('Primeiro apoio marcado. Clique no segundo apoio (do outro lado da pista). Esc cancela.')}
 const a=draft.pts[0],L=Math.hypot(w.x-a.x,w.y-a.y);if(L<2)return msg('Os apoios precisam estar a pelo menos 2 m.',true);if(L>120)return msg('Vão maior que 120 m.',true);
 draft=null;checkpoint();const n=M.gantries.length+1;
 const g={id:uid(),name:($('gtName')?.value||'').trim()||'Pórtico '+n,description:($('gtDesc')?.value||'').trim(),kind:$('gtKind')?.value||'portico',a,b:w,image:'',beam_width_m:1,height_m:7,color:'',show_in_video:true,callout:true,label:null,start_s:null,end_s:null,text_scale:1};
 M.gantries.push(g);sel={key:'gantries',i:M.gantries.length-1};selSet=[];changed(`${g.name} criado (${L.toFixed(2)} m entre eixos dos apoios). Envie a imagem da placa no painel de propriedades.`);showProps()},'pórtico: ferramenta, desenho no editor e imagem');
function drawGantries(){const ppm=pxPerM();for(const g of M.gantries||[]){if(!g.a||!g.b)continue;const [ax,ay]=W2C(g.a),[bx,by]=W2C(g.b);const bw=Math.max(5,(g.beam_width_m||1)*ppm);
  ctx.save();ctx.globalAlpha=g.show_in_video===false?.45:1;ctx.lineCap='butt';ctx.strokeStyle='#1a2630';ctx.lineWidth=bw+3;ctx.beginPath();ctx.moveTo(ax,ay);ctx.lineTo(bx,by);ctx.stroke();ctx.strokeStyle=g.color||'#cfd3d6';ctx.lineWidth=bw;ctx.stroke();
  const L=Math.hypot(bx-ax,by-ay),k=Math.max(2,Math.floor(L/Math.max(bw,6)));const ux=(bx-ax)/L,uy=(by-ay)/L,nx=-uy,ny=ux;ctx.strokeStyle='#76808a';ctx.lineWidth=1;ctx.beginPath();for(let i=0;i<=k;i++){const t=i/k,s=(i%2?1:-1)*bw*.38;const x=ax+(bx-ax)*t+nx*s,y=ay+(by-ay)*t+ny*s;i?ctx.lineTo(x,y):ctx.moveTo(x,y)}ctx.stroke();
  const ps=Math.max(1,.9*ppm);for(const [x,y] of g.kind==='portico'?[[ax,ay],[bx,by]]:[[ax,ay]]){ctx.fillStyle='#8e979d';ctx.strokeStyle='#1a2630';ctx.lineWidth=1.5;ctx.beginPath();for(const [i,[du,dn]] of [[-1,-1],[1,-1],[1,1],[-1,1]].entries()){const X=x+(ux*du+nx*dn)*ps/2,Y=y+(uy*du+ny*dn)*ps/2;i?ctx.lineTo(X,Y):ctx.moveTo(X,Y)}ctx.closePath();ctx.fill();ctx.stroke()}
  const mx=(ax+bx)/2,my=(ay+by)/2,im=projImg(g.image);if(im&&g.callout!==false){const h=48,w=Math.min(160,h*im.naturalWidth/im.naturalHeight);const lx=g.label?W2C(g.label)[0]-w/2:mx+24,ly=g.label?W2C(g.label)[1]-h/2:my-24-h;ctx.strokeStyle='#ffd66b';ctx.lineWidth=1.5;ctx.beginPath();ctx.moveTo(mx,my);ctx.lineTo(lx,ly+h);ctx.stroke();ctx.fillStyle='#0a1620';ctx.fillRect(lx-3,ly-3,w+6,h+6);ctx.drawImage(im,lx,ly,w,h)}
  ctx.restore();label('⊓ '+g.name,g.a,'#ffe7a3')}
 if(draft&&draft.type==='gantry'&&lastWorld){poly([draft.pts[0],lastWorld]);ctx.strokeStyle='#ffd66b';ctx.lineWidth=Math.max(4,pxPerM());ctx.setLineDash([8,5]);ctx.stroke();ctx.setLineDash([]);const d=Math.hypot(lastWorld.x-draft.pts[0].x,lastWorld.y-draft.pts[0].y);label(`apoios: ${d.toFixed(2)} m`,lastWorld,'#ffd66b')}}
estender('draw',_d=>function(){_d();if(!ready())return;try{drawGantries()}catch(err){window.RodoviaErros&&RodoviaErros.avisar('porticos_chamadas',err)}},'pórtico: ferramenta, desenho no editor e imagem');
async function uploadImage(file){if(!file)throw Error('Escolha uma imagem PNG ou JPG.');const fd=new FormData();fd.append('file',file);return api(`/api/projects/${pid}/imagens`,{method:'POST',body:fd})}

// ---------- propriedades: rótulos e ajuda, imagem, campos numéricos vazios, posição da chamada ----------
estender('showProps',_sp=>function(){_sp();const box=$('propPanel');if(!box||box.hidden)return;const o=objOf(sel);const L=allSelected();
 if(L.length>1){multiProps(box,L);return}if(!o)return;
 box.querySelectorAll('tr').forEach(tr=>{const td=tr.firstElementChild,inp=tr.querySelector('[data-pp]');if(!td||!inp)return;const k=inp.dataset.pp,lab=PROP_LABEL[k];if(lab){td.textContent=lab[0];if(lab[1])td.title=lab[1]}
  if(NULLABLE_NUM.has(k)&&inp.type!=='number'){inp.type='number';inp.step='any';inp.placeholder='vazio = sem limite'}if(['image','label','anchor'].includes(k))tr.remove()});
 if('image' in o.o){const nm=o.o.image;box.querySelector('h4')?.insertAdjacentHTML('beforebegin',`<div class="imgRow">${nm?`<img alt="imagem" src="/api/projects/${pid}/imagens/${nm}">`:'<span class="muted">Sem imagem.</span>'}<label class="link" style="margin:0">Enviar imagem…<input type="file" accept=".png,.jpg,.jpeg" data-ppimg hidden></label>${nm?'<button type="button" data-ppact="noimg">Remover imagem</button>':''}</div>`)}
 if(o.key==='gantries'||o.key==='highlights'){box.querySelector('.row')?.insertAdjacentHTML('beforeend',`<button type="button" data-ppact="label" title="Clique depois no lugar da caixa no editor">Posicionar caixa</button>${o.o.label?'<button type="button" data-ppact="autolabel">Caixa automática</button>':''}`)}
 box.insertAdjacentHTML('beforeend',`<label class="inl" title="Depois de alterar um atributo, gera de novo a prévia desta vista para ver o efeito no vídeo"><input type="checkbox" id="autoPrev" ${autoPrev?'checked':''}> Atualizar a prévia desta vista ao alterar</label>`)},'propriedades: rótulos e ajuda, imagem, campos numéricos vazios, posiçã');
let autoPrev=false;try{autoPrev=localStorage.getItem('rodovia_autoprev')==='1'}catch(_e){window.RodoviaErros&&RodoviaErros.avisar('porticos_chamadas',_e)}
let prevTimer=null;function scheduleViewPreview(){if(!autoPrev||!pid||!ready())return;clearTimeout(prevTimer);prevTimer=setTimeout(guard(async()=>{const c=C2W(canvas.width/2,canvas.height/2),a=C2W(0,canvas.height/2),b=C2W(canvas.width,canvas.height/2);cfg.preview_center=c;cfg.preview_width_m=Math.max(5,Math.min(50000,Math.hypot(b.x-a.x,b.y-a.y)));$('preview_mode').value='custom';msg('Atualizando a prévia desta vista…');await start('preview')}),1500)}
document.addEventListener('change',e=>{if(e.target.id==='autoPrev'){autoPrev=e.target.checked;try{localStorage.setItem('rodovia_autoprev',autoPrev?'1':'0')}catch(_e){window.RodoviaErros&&RodoviaErros.avisar('porticos_chamadas',_e)}}});
estender('commitProp',_cp=>function(el){const o=objOf(sel);if(o&&el.dataset.pp&&NULLABLE_NUM.has(el.dataset.pp)){const v=String(el.value).trim();checkpoint();o.o[el.dataset.pp]=v===''?null:Number(v.replace(',','.'));if(v!==''&&!isFinite(o.o[el.dataset.pp])){undoStack.pop();return msg('Valor numérico inválido.',true)}changed('Propriedade alterada.');showProps();scheduleViewPreview();return}
 _cp(el);scheduleViewPreview()},'propriedades: rótulos e ajuda, imagem, campos numéricos vazios, posiçã');
document.addEventListener('change',guard(async e=>{const inp=e.target;if(!inp.matches||!inp.matches('#propPanel input[data-ppimg]'))return;const o=objOf(sel);if(!o)return;const r=await uploadImage(inp.files[0]);checkpoint();o.o.image=r.image;changed(`Imagem enviada (${r.size[0]}×${r.size[1]} px). Ela aparece na caixa de chamada do vídeo.`);showProps();scheduleViewPreview()}));
let labelPick=null;
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('#propPanel [data-ppact]');if(!b)return;const a=b.dataset.ppact,o=objOf(sel);if(!o)return;
 if(a==='noimg'){checkpoint();o.o.image='';changed('Imagem removida.');showProps()}
 if(a==='autolabel'){checkpoint();o.o.label=null;changed('Caixa em posição automática (sem sobrepor outras).');showProps()}
 if(a==='label'){labelPick={key:o.key,i:o.i};cadCmd={step(w){const t=objOf(labelPick);labelPick=null;cadCmd=null;prompt_('Comando:');if(!t)return;checkpoint();t.o.label={x:w.x,y:w.y};changed('Posição da caixa definida.');showProps()}};prompt_('Clique onde fica a caixa de chamada:');canvas.focus({preventScroll:true})}});

// ---------- atributos em lote (ATRIB) e copiar propriedades (PINTAR) ----------
function commonFields(L){const keys=L.map(o=>Object.entries(o.key==='clean_areas'||o.key==='exclusions'?{}:o.o).filter(([k,v])=>!['id','points','polygon','x','y','image','label','anchor'].includes(k)&&(v===null||['string','number','boolean'].includes(typeof v))));
 if(!keys.length)return [];let common=keys[0].map(([k])=>k);for(const ks of keys.slice(1)){const s=new Set(ks.map(([k])=>k));common=common.filter(k=>s.has(k))}
 return common.map(k=>{const vals=L.map(o=>o.o[k]);const same=vals.every(v=>v===vals[0]);return [k,same?vals[0]:undefined,vals.find(v=>v!==null&&v!==undefined)]})}
function multiProps(box,L){const F=commonFields(L);const sameKey=L.every(o=>o.key===L[0].key);
 const rows=F.filter(([k])=>k!=='name'||sameKey).map(([k,v,ex])=>{const lab=PROP_LABEL[k]||[k,''];const typ=typeof ex;let inp;
  const en=ENUMS[k]&&(ENUMS[k][L[0].key]||(!Object.values(ENUMS[k]).some(x=>typeof x==='object')&&ENUMS[k]));
  if(en&&typeof en==='object'&&sameKey)inp=`<select data-mpp="${k}"><option value="" ${v===undefined?'selected':''}>(vários)</option>${Object.entries(en).map(([a,b])=>`<option value="${a}" ${String(v)===a?'selected':''}>${esc(b)}</option>`).join('')}</select>`;
  else if(typ==='boolean')inp=`<select data-mpp="${k}" data-bool="1"><option value="" ${v===undefined?'selected':''}>(vários)</option><option value="1" ${v===true?'selected':''}>Sim</option><option value="0" ${v===false?'selected':''}>Não</option></select>`;
  else if(typ==='number'||NULLABLE_NUM.has(k))inp=`<input data-mpp="${k}" type="number" step="any" value="${v===undefined||v===null?'':v}" placeholder="${v===undefined?'(vários)':''}">`;
  else inp=`<input data-mpp="${k}" value="${v===undefined?'':esc(v??'')}" placeholder="${v===undefined?'(vários)':''}">`;
  return `<tr><td title="${esc(lab[1])}">${esc(lab[0])}</td><td>${inp}</td></tr>`}).join('');
 box.insertAdjacentHTML('beforeend',rows?`<h4>Atributos em comum (ATRIB) — altera os ${L.length} de uma vez</h4><table>${rows}</table><p class="muted">Enter confirma; os campos “(vários)” ficam como estão em cada objeto.</p>`:'<p class="muted">Sem atributos em comum entre os objetos selecionados.</p>')}
function commitMulti(el){const L=allSelected();if(L.length<2)return;const k=el.dataset.mpp;let raw=el.value;if(raw===''&&el.tagName==='SELECT')return;
 checkpoint();let n=0;for(const o of L){if(!(k in o.o))continue;const old=o.o[k];let v;
  if(el.dataset.bool)v=raw==='1';else if(typeof old==='number'||NULLABLE_NUM.has(k)){if(String(raw).trim()===''){if(NULLABLE_NUM.has(k))v=null;else continue}else{v=Number(String(raw).replace(',','.'));if(!isFinite(v)){undoStack.pop();return msg('Valor numérico inválido.',true)}}}
  else{v=raw;if(['name','title'].includes(k)&&!String(v).trim()){undoStack.pop();return msg('O nome não pode ficar vazio.',true)}}
  o.o[k]=v;n++}
 changed(`Atributo “${(PROP_LABEL[k]||[k])[0]}” alterado em ${n} objeto(s).`);showProps();scheduleViewPreview()}
document.addEventListener('keydown',e=>{const el=e.target;if(!el.dataset||!el.dataset.mpp)return;if(e.key==='Enter'){e.preventDefault();e.stopPropagation();commitMulti(el)}},true);
document.addEventListener('change',e=>{const el=e.target;if(el.dataset&&el.dataset.mpp&&el.tagName==='SELECT')commitMulti(el)});
const STYLE_SKIP=new Set(['id','name','title','points','polygon','x','y','a','b','point','start','end','label','anchor','description']);
function matchProps(src,dst){let n=0;for(const [k,v] of Object.entries(src.o)){if(STYLE_SKIP.has(k)||!(k in dst.o)||(v!==null&&typeof v==='object'))continue;if(dst.o[k]!==v){dst.o[k]=v;n++}}return n}


// Auditoria em coordenadas: travessia, apoios e altura são medidas distintas.
function registerDimensionAudit(){comando(['AUDITARMEDIDAS'],async()=>{
 requireProject();const project=pid,context=projectSession.context;await save();const audit=await api(`/api/projects/${project}/dimension-audit`);if(project!==pid||context!==projectSession.context)return;const source=(M.gantries||[]).map(g=>structuredClone(g));let d;
 const span=g=>Math.hypot(g.b.x-g.a.x,g.b.y-g.a.y);
 const crossing=g=>g.crossing_a&&g.crossing_b?Math.hypot(g.crossing_b.x-g.crossing_a.x,g.crossing_b.y-g.crossing_a.y):null;
 const html='<p>Distâncias em planta, nas coordenadas do projeto. Altura dos postes não é somada. A travessia é independente dos eixos dos apoios.</p><p>Preencher uma nova travessia ajusta explicitamente os apoios, mantendo centro e orientação da travessia. Postes de 0,90 m ficam fora dela. Deixe vazio para não alterar.</p><table><tr><th>Pórtico</th><th>Entre apoios</th><th>Travessia medida</th><th>Nova travessia (m)</th></tr>'+source.map((g,i)=>`<tr><td>${esc(g.name)}</td><td>${span(g).toFixed(3)} m</td><td>${crossing(g)===null?'não medida':crossing(g).toFixed(3)+' m'}</td><td><input data-span="${i}" type="number" min="2" max="100" step="0.01" placeholder="não alterar"></td></tr>`).join('')+'</table><h3>Outros elementos · medidas em planta</h3><table><tr><th>Elemento</th><th>Medidas</th></tr>'+audit.elements.map(r=>`<tr><td>${esc(r.name)}</td><td>${[['length_m','Comprimento'],['endpoint_distance_m','Entre extremos'],['perimeter_m','Perímetro'],['area_m2','Área'],['configured_width_m','Largura cadastrada']].filter(([k])=>Number.isFinite(r[k])).map(([k,label])=>label+': '+r[k].toFixed(3)+(k==='area_m2'?' m²':' m')).join(' · ')}</td></tr>`).join('')+'</table><p>Comprimento, perímetro e largura são grandezas distintas. A auditoria não muda o DXF.</p>';
 d=RodoviaModelDialog.open({id:'rsDimensionAudit',title:'Auditoria de dimensões',html,save:async()=>{
  if(!d.rsContext())throw Error('O projeto mudou.');const updates=[];
  for(const input of d.querySelectorAll('[data-span]')){if(!input.value.trim())continue;const old=source[Number(input.dataset.span)],current=(M.gantries||[]).find(g=>g.id===old.id);if(!current||JSON.stringify(current)!==JSON.stringify(old))throw Error('O pórtico mudou. Reabra a auditoria.');const width=RodoviaModelDialog.number(input,'Travessia',2,100),L=span(old),u={x:(old.b.x-old.a.x)/L,y:(old.b.y-old.a.y)/L},c={x:(old.a.x+old.b.x)/2,y:(old.a.y+old.b.y)/2},point=t=>({x:c.x+u.x*t,y:c.y+u.y*t});updates.push([current,{a:point(-width/2-.45),b:point(width/2+(old.kind==='portico'?.45:0)),crossing_a:point(-width/2),crossing_b:point(width/2)}])}
  checkpoint();for(const [g,values] of updates)Object.assign(g,values);projectSession.epoch++;savePending=true;await save();refreshLists();draw();msg('Medidas aplicadas nas coordenadas do modelo. Confira a posição dos apoios na pista.');
 }});return d;
},'Audita travessia e apoios dos pórticos; ajusta somente as dimensões informadas');}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',registerDimensionAudit,{once:true});else registerDimensionAudit();
