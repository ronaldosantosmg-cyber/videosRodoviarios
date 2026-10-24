// =====================================================================================================
// 1.35: obras do PER e cronograma.
//  • Tabela das obras (editável), importação de Excel/CSV/MS Project XML com conferência, modelo e exportação Excel.
//  • Ferramenta “Obra do PER”: clique o início e o fim no desenho; uma janela pede nome, tipo, lado e datas.
//  • As obras aparecem no editor como faixas coloridas ao longo do eixo (cor do tipo).
//  • Destaques ganharam mais categorias; intervenções pontuais aceitam os mesmos tipos de obra.
// =====================================================================================================
MARK_KEYS.push('works');estender('emptyMarks',_em=>function(){return {..._em(),works:[]}},'obras do PER');if(!M.works)M.works=[];
fields.push('per_display','schedule_mode','schedule_start','schedule_end');checks.push('schedule_show_planned');
let OBRA_TIPOS=[{id:'duplicacao',rotulo:'Duplicação',cor:'#ff9f1c',sigla:'DUP'},{id:'outro',rotulo:'Outra obra',cor:'#ff8a3d',sigla:'O'}];
const obraTipo=k=>OBRA_TIPOS.find(t=>t.id===k)||OBRA_TIPOS.find(t=>t.id==='outro')||OBRA_TIPOS[0];
fetch('/api/obras/tipos').then(r=>r.json()).then(L=>{OBRA_TIPOS=L;
 const pk=$('poiKind');if(pk){const v=pk.value;pk.innerHTML=L.map(t=>`<option value="${t.id}">${esc(t.rotulo)}</option>`).join('');pk.value=v||'outro'}
 renderObras();draw()}).catch(()=>{});
// Destaques: mais categorias (as anteriores mantêm nome, cor e letra).
Object.assign(HL_LABEL,{rede_agua:'Rede de água/esgoto',gas:'Gasoduto/oleoduto',telecom:'Fibra/telefonia',torre:'Linha de transmissão/torre',arvore:'Árvore/vegetação',
 cerca:'Cerca/muro',placa:'Placa/outdoor',desapropriacao:'Desapropriação',ocupacao:'Ocupação na faixa',escola:'Escola',saude:'Hospital/posto de saúde',comercio:'Comércio/indústria',
 curso_dagua:'Curso d’água/nascente',geotecnia:'Talude/risco geotécnico',patrimonio:'Patrimônio/área protegida',ponto_onibus:'Ponto de ônibus',pedestre:'Travessia de pedestres',acidente:'Ponto crítico de acidentes'});
Object.assign(HL_STYLE,{rede_agua:['#3fa9f5','H'],gas:['#f5a623','G'],telecom:['#9b8cff','T'],torre:['#e8e8e8','LT'],arvore:['#5cc96a','V'],cerca:['#c9a97a','C'],placa:['#ffef7a','PL'],
 desapropriacao:['#ff7aa8','$'],ocupacao:['#ff9f5a','O'],escola:['#6fd3ff','ES'],saude:['#ff6b6b','+'],comercio:['#ffc061','CM'],curso_dagua:['#4fc3f7','≈'],geotecnia:['#d4886a','GT'],
 patrimonio:['#c792ea','PH'],ponto_onibus:['#7ee0a8','BUS'],pedestre:['#ffffff','PD'],acidente:['#ff4040','AC']});
{const o=HL_LABEL.outro;delete HL_LABEL.outro;HL_LABEL.outro=o}   // “Ponto especial” no fim da lista

// ---------- geometria: km -> ponto do eixo ----------
function ptAtS(s){const d=axisData();if(!d)return null;const S=d.s;s=Math.max(0,Math.min(S[S.length-1],s));let i=1;while(i<S.length-1&&S[i]<s)i++;
 const t=(s-S[i-1])/Math.max(1e-9,S[i]-S[i-1]),A=d.a[i-1],B=d.a[i];return {x:A.x+(B.x-A.x)*t,y:A.y+(B.y-A.y)*t}}
function obraPontos(w){const d=axisData();if(!d)return [];let a=w.km_start_m,b=w.km_end_m;if(b-a<30){const c=(a+b)/2;a=c-15;b=c+15}
 const sa=sOfKm(a),sb=sOfKm(b),n=Math.max(2,Math.min(400,Math.ceil(Math.abs(sb-sa)/5)+1));const P=[];for(let k=0;k<n;k++){const p=ptAtS(sa+(sb-sa)*k/(n-1));if(p)P.push(p)}return P}
function kmTexto(m){return m==null||!isFinite(m)?'':formatKm(m)}
function kmLer(t){t=String(t||'').trim();if(!t)return null;try{const v=parseKm(t);return isFinite(v)?v:null}catch{return null}}

// ---------- editor: faixas das obras ----------
estender('draw',anterior=>function(){anterior();if(!ready()||!(M.works||[]).length||vecOn?.obras===false)return;try{ctx.save();
 for(const [i,w] of M.works.entries()){if(w.show===false)continue;const P=obraPontos(w).map(p=>W2C(p));if(P.length<2)continue;const t=obraTipo(w.kind),cor=w.color||t.cor,sel=obraSel===i;
  ctx.globalAlpha=sel?.55:.32;ctx.strokeStyle=cor;ctx.lineCap='round';ctx.lineJoin='round';ctx.lineWidth=Math.max(6,Math.min(60,(w.side&&w.side!=='ambos'?14:26)*pxPerM()));
  ctx.beginPath();P.forEach(([x,y],k)=>k?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.stroke();ctx.globalAlpha=1;
  if(sel){ctx.lineWidth=2;ctx.setLineDash([6,4]);ctx.strokeStyle='#fff';ctx.stroke();ctx.setLineDash([])}
  const [x,y]=P[0];ctx.font='bold 11px "Segoe UI",system-ui';const lab=t.sigla+' '+(w.description||'').slice(0,28);const tw=ctx.measureText(lab).width;
  ctx.fillStyle='#000a';ctx.fillRect(x+6,y-20,tw+10,17);ctx.fillStyle=cor;ctx.fillText(lab,x+11,y-7)}
 ctx.restore()}catch(e){ctx.restore()}},'obras do PER no editor');
let obraSel=-1;

// ---------- lista (como uma lista do Windows: duplo clique ou ✎ abre a janela da obra) ----------
const dBR=d=>d?d.split('-').reverse().join('/'):'';
function renderObras(){const tb=$('obRows');if(!tb)return;const W=M.works||[];
 tb.innerHTML=W.length?W.map((w,i)=>{const t=obraTipo(w.kind);return `<tr data-ob="${i}" class="${obraSel===i?'on':''}" title="Duplo clique para editar">
  <td><span class="obCor" style="background:${esc(w.color||t.cor)}"></span><b>${esc(w.description)}</b><br><small class="muted">${esc(t.rotulo)}${w.side&&w.side!=='ambos'?' · lado '+w.side:''}</small></td>
  <td class="nw">${kmTexto(w.km_start_m)}${w.km_end_m!==w.km_start_m?'<br>'+kmTexto(w.km_end_m):''}</td>
  <td class="nw"><small>${w.start_date?dBR(w.start_date)+'<br>'+dBR(w.end_date):'<span class="muted">sem datas</span>'}</small></td>
  <td class="acts nw"><button type="button" class="mini" data-oba="edit" title="Editar">✎</button><button type="button" class="mini" data-oba="ver" title="Mostrar no desenho">⌖</button><button type="button" class="mini danger" data-oba="del" title="Excluir">🗑</button></td></tr>`}).join('')
  :'<tr><td colspan="4" class="muted">Nenhuma obra. Use “Marcar no desenho” ou “Importar Excel / cronograma…”.</td></tr>';
 const datas=W.filter(w=>w.start_date&&w.end_date).length;
 if($('obResumo'))$('obResumo').textContent=W.length?`${W.length} obra(s) · ${datas} com datas${datas?` (${dBR(W.filter(w=>w.start_date).map(w=>w.start_date).sort()[0])} a ${dBR(W.filter(w=>w.end_date).map(w=>w.end_date).sort().pop())})`:''}.`:''}
estender('refreshLists',anterior=>function(){anterior();renderObras()},'obras do PER: lista');
async function editarObra(i){const w=M.works[i];if(!w)return;const o=await pedirObra(w.km_start_m,w.km_end_m,w);if(!o)return;checkpoint();Object.assign(w,o);changed(`Obra “${w.description}” alterada.`)}
$('obRows')?.addEventListener('dblclick',e=>{const tr=e.target.closest('[data-ob]');if(tr)guard(()=>editarObra(Number(tr.dataset.ob)))()});
$('obRows')?.addEventListener('click',guard(async e=>{const tr=e.target.closest('[data-ob]');if(!tr)return;const i=Number(tr.dataset.ob);const b=e.target.closest('[data-oba]');
 obraSel=i;tr.parentNode.querySelectorAll('tr').forEach(r=>r.classList.toggle('on',r===tr));draw();if(!b)return;
 if(b.dataset.oba==='edit')return editarObra(i);
 if(b.dataset.oba==='ver'){const P=obraPontos(M.works[i]);if(P.length)zoomTo(P[Math.floor(P.length/2)]);return}
 if(b.dataset.oba==='del'){if(!await confirmBox(`Excluir a obra “${M.works[i].description}”?`,'Excluir','Cancelar'))return;checkpoint();M.works.splice(i,1);obraSel=-1;changed('Obra excluída (Ctrl+Z desfaz).')}}));
$('obExportar')?.addEventListener('click',guard(async()=>{requireProject();clearTimeout(saveTimer);await save();await baixarArquivo(`/api/projects/${pid}/obras.xlsx`,'Exportando obras para o Excel')}));

// ---------- importar (Excel, CSV, MS Project XML) com conferência ----------
function janelaImportar(){let d=$('obImpDlg');if(d)return d;document.body.insertAdjacentHTML('beforeend',`<dialog id="obImpDlg" class="winDlg bigDlg"><h3>Importar obras do PER</h3>
 <p class="muted">Planilha Excel (.xlsx) ou CSV com as colunas <b>Obra</b>, <b>Km inicial</b> e <b>Km final</b> (opcionais: Tipo, Lado, Início, Término, % concluído, Ano PER, Tabela PER), ou cronograma do <b>MS Project salvo como XML</b> (o km vem do nome da tarefa, ex.: “Duplicação km 325+850 a 326+200”).</p>
 <div class="dlgTools"><input type="file" id="obArq" accept=".xlsx,.xlsm,.csv,.txt,.xml"><span class="grow"></span><a class="link" href="/api/obras/modelo.xlsx" data-titulo="Baixando o modelo de planilha">Baixar modelo Excel</a></div>
 <div id="obImpInfo" class="muted"></div><div class="tblWrap"><table class="tbl"><thead><tr><th><input type="checkbox" id="obTodas" checked title="Marcar todas"></th><th>Obra</th><th>Tipo</th><th>Km inicial</th><th>Km final</th><th>Início</th><th>Término</th><th>%</th></tr></thead><tbody id="obImpRows"></tbody></table></div>
 <div class="row obModo"><label class="inl"><input type="radio" name="obModo" value="acrescentar" checked> Acrescentar às obras atuais</label><label class="inl"><input type="radio" name="obModo" value="substituir"> Substituir todas as obras</label><label class="inl"><input type="radio" name="obModo" value="datas"> Só atualizar datas e % das obras de mesmo nome</label></div>
 <div class="row"><span class="grow"></span><button type="button" id="obImpOk" class="primary" disabled>Importar</button><button type="button" id="obImpCancel">Cancelar</button></div></dialog>`);
 d=$('obImpDlg');arrumarJanela(d);
 d.addEventListener('input',e=>{const k=e.target.dataset.obkm??e.target.dataset.obkf;if(k!=null){const c=d.querySelector(`[data-obi="${k}"]`);if(c)c.checked=!!e.target.value.trim()}});   // digitou o km: a tarefa entra
 $('obImpCancel').onclick=()=>d.close();$('obTodas').onchange=e=>d.querySelectorAll('[data-obi]').forEach(c=>c.checked=e.target.checked);
 $('obArq').onchange=guard(async()=>{const f=$('obArq').files[0];if(!f)return;requireProject();const fd=new FormData();fd.append('file',f);$('obImpInfo').textContent='Lendo '+f.name+'…';
  const r=await api(`/api/projects/${pid}/obras/ler`,{method:'POST',body:fd});d._lidas=r;
  const L=[...r.obras,...r.sem_km];
  $('obImpRows').innerHTML=L.map((w,i)=>`<tr><td><input type="checkbox" data-obi="${i}" ${w.sem_km?'':'checked'}></td><td>${esc(w.description)}</td><td>${esc(obraTipo(w.kind).rotulo)}</td>
   <td>${w.sem_km?`<input data-obkm="${i}" placeholder="km inicial" size="8">`:kmTexto(w.km_start_m)}</td><td>${w.sem_km?`<input data-obkf="${i}" placeholder="km final" size="8">`:kmTexto(w.km_end_m)}</td>
   <td>${(w.start_date||'').split('-').reverse().join('/')}</td><td>${(w.end_date||'').split('-').reverse().join('/')}</td><td>${w.progress_pct??''}</td></tr>`).join('');
  $('obImpInfo').innerHTML=`<b>${esc(r.arquivo)}</b>: ${r.obras.length} obra(s) com km${r.sem_km.length?` · ${r.sem_km.length} tarefa(s) sem km (digite o km para incluir, ou use “Só atualizar datas”)`:''}.`+(r.avisos.length?`<br>${r.avisos.map(esc).join('<br>')}`:'');
  $('obImpOk').disabled=!L.length});
 $('obImpOk').onclick=()=>{const r=d._lidas;if(!r)return;const L=[...r.obras,...r.sem_km].map(w=>({...w}));const modo=d.querySelector('[name=obModo]:checked').value;
  const pega=[];d.querySelectorAll('[data-obi]').forEach(c=>{const i=Number(c.dataset.obi),w=L[i];if(!c.checked&&modo!=='datas')return;
   if(w.sem_km){const a=kmLer(d.querySelector(`[data-obkm="${i}"]`)?.value),b=kmLer(d.querySelector(`[data-obkf="${i}"]`)?.value);if(a!=null){w.km_start_m=a;w.km_end_m=b??a;delete w.sem_km}}
   if(c.checked||modo==='datas')pega.push(w)});
  const limpa=w=>{const o={id:w.id||uid(),description:w.description,kind:w.kind,km_start_m:Math.min(w.km_start_m,w.km_end_m),km_end_m:Math.max(w.km_start_m,w.km_end_m),side:w.side||'ambos',
   per_year:w.per_year||'',per_table:w.per_table||'',start_date:w.start_date||'',end_date:w.end_date||'',progress_pct:w.progress_pct??null,x:w.x??null,y:w.y??null,km_mode:'manual',color:'',show:true,task:w.task||''};return o};
  checkpoint();const atuais=M.works||[];let n=0;
  if(modo==='datas'){const key=s=>String(s||'').normalize('NFKD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/\s+/g,' ').trim();const by=new Map();pega.forEach(w=>{for(const k of [w.task,w.description])if(k&&!by.has(key(k)))by.set(key(k),w)});
   for(const e of atuais){const w=by.get(key(e.task))||by.get(key(e.description));if(w){e.start_date=w.start_date||e.start_date;e.end_date=w.end_date||e.end_date;if(w.progress_pct!=null)e.progress_pct=w.progress_pct;e.task=w.task||e.task;n++}}}
  else{const novas=pega.filter(w=>!w.sem_km).map(limpa);n=novas.length;M.works=modo==='substituir'?novas:atuais.concat(novas)}
  if(M.works.length>1000){undo();return msg('Limite de 1000 obras por projeto.',true)}
  d.close();changed(modo==='datas'?`Datas atualizadas em ${n} obra(s).`:`${n} obra(s) importada(s).`);
  if(n&&M.works.some(w=>w.start_date)&&$('schedule_mode').value==='off')msg(`${n} obra(s) importada(s). Para o vídeo seguir as datas, ligue “Linha do tempo pelo cronograma”.`)};
 return d}
function abrirImportarObras(){requireProject();const d=janelaImportar();$('obArq').value='';$('obImpRows').innerHTML='';$('obImpInfo').textContent='Escolha o arquivo.';$('obImpOk').disabled=true;d._lidas=null;d.showModal()}
$('obImportar')?.addEventListener('click',guard(abrirImportarObras));

// ---------- ferramenta: início e fim no desenho ----------
function janelaObra(){let d=$('obNovaDlg');if(d)return d;document.body.insertAdjacentHTML('beforeend',`<dialog id="obNovaDlg" class="winDlg"><h3 id="obNovaT">Obra do PER</h3>
 <div class="grid"><label class="span2">Nome da obra<input id="obNome" maxlength="300" placeholder="Ex.: Duplicação km 325 a 328"></label><label>Tipo<select id="obTipo"></select></label>
 <label>Lado<select id="obLado"><option value="ambos">Ambos</option><option value="direito">Direito (km crescente)</option><option value="esquerdo">Esquerdo</option></select></label>
 <label>Km inicial<input id="obKmA"></label><label>Km final<input id="obKmB"></label><label>Início (opcional)<input id="obIni" type="date"></label><label>Término (opcional)<input id="obFim" type="date"></label>
 <label>% concluído<input id="obPct" type="number" min="0" max="100" step="1"></label><label>Cor (vazio = do tipo)<input id="obCorI" type="color"></label><label>Ano PER<input id="obAno" maxlength="70"></label><label>Tabela/item PER<input id="obTab" maxlength="70"></label></div>
 <label><input id="obMostrar" type="checkbox" checked> Mostrar no vídeo e no desenho</label>
 <p id="obErr" class="inputErr"></p><div class="row"><span class="grow"></span><button type="button" id="obOk" class="primary">OK</button><button type="button" id="obCancel">Cancelar</button></div></dialog>`);
 d=$('obNovaDlg');arrumarJanela(d);return d}
function pedirObra(a,b,w=null){return new Promise(res=>{const d=janelaObra();$('obTipo').innerHTML=OBRA_TIPOS.map(t=>`<option value="${t.id}">${esc(t.rotulo)}</option>`).join('');
 let ult={};try{ult=JSON.parse(localStorage.getItem('rodovia_obra_ult')||'{}')}catch{}
 $('obNovaT').textContent=w?'Propriedades da obra':'Nova obra do PER';
 $('obTipo').value=w?w.kind:(ult.kind||'duplicacao');$('obLado').value=w?(w.side||'ambos'):(ult.side||'ambos');
 $('obNome').value=w?w.description:'';$('obKmA').value=kmTexto(a);$('obKmB').value=kmTexto(b);$('obIni').value=w?.start_date||'';$('obFim').value=w?.end_date||'';
 $('obPct').value=w?.progress_pct??'';$('obAno').value=w?.per_year||'';$('obTab').value=w?.per_table||'';$('obMostrar').checked=w?w.show!==false:true;
 const corTipo=()=>obraTipo($('obTipo').value).cor;$('obCorI').value=w?.color||corTipo();$('obCorI').dataset.mexeu=w?.color?'1':'';$('obCorI').oninput=()=>$('obCorI').dataset.mexeu='1';$('obErr').textContent='';
 $('obTipo').onchange=()=>{$('obNome').placeholder=obraTipo($('obTipo').value).rotulo+' km '+$('obKmA').value;if(!$('obCorI').dataset.mexeu)$('obCorI').value=corTipo()};$('obTipo').onchange();
 let fim=false;const ok=()=>{const ka=kmLer($('obKmA').value),kb=kmLer($('obKmB').value);if(ka==null||kb==null){$('obErr').textContent='Km inválido (use 325+850).';return}
  const nome=$('obNome').value.trim()||$('obNome').placeholder;if($('obIni').value&&$('obFim').value&&$('obFim').value<$('obIni').value){$('obErr').textContent='O término é anterior ao início.';return}
  const pct=$('obPct').value===''?null:Math.max(0,Math.min(100,Number($('obPct').value)));
  fim=true;d.close();try{localStorage.setItem('rodovia_obra_ult',JSON.stringify({kind:$('obTipo').value,side:$('obLado').value}))}catch{}
  res({description:nome,kind:$('obTipo').value,side:$('obLado').value,km_start_m:Math.min(ka,kb),km_end_m:Math.max(ka,kb),start_date:$('obIni').value,end_date:$('obFim').value,
   progress_pct:pct,per_year:$('obAno').value.trim(),per_table:$('obTab').value.trim(),color:$('obCorI').dataset.mexeu&&$('obCorI').value!==corTipo()?$('obCorI').value:'',show:$('obMostrar').checked})};
 $('obOk').onclick=ok;$('obCancel').onclick=()=>d.close();d.onkeydown=e=>{if(e.key==='Enter'&&e.target.tagName!=='SELECT'){e.preventDefault();ok()}};d.onclose=()=>{if(!fim)res(null)};d.showModal();$('obNome').focus()})}
ferramenta('obra',{rotulo:'🏗 Obra do PER',dica:'Clique o INÍCIO e depois o FIM da obra sobre o eixo; escolha nome, tipo (duplicação, via marginal, iluminação…), lado e datas. Repita para a próxima; Esc encerra.',
 antesDe:'linkforce',icone:'M3 20h18M5 20V9l7-5 7 5v11M9 20v-6h6v6',
 async clique(w){if(!axisData())return msg('Analise os arquivos primeiro (o km vem do eixo).',true);const k=kmOf(w);if(!k)return;
  if(!draft||draft.type!=='obra'){draft={type:'obra',pts:[w],km:[k.km]};prompt_('OBRA — clique o FIM da obra (Esc cancela):');draw();return}
  const a=draft.km[0],b=k.km;draft=null;draw();const o=await pedirObra(a,b);prompt_('OBRA — clique o INÍCIO da próxima obra (Esc encerra):');if(!o)return msg('Obra cancelada.');
  checkpoint();(M.works=M.works||[]).push({id:uid(),x:null,y:null,km_mode:'manual',task:'',...o});obraSel=M.works.length-1;
  changed(`Obra “${o.description}” (km ${kmTexto(o.km_start_m)} a ${kmTexto(o.km_end_m)}) incluída. Clique o início da próxima ou Esc.`)},
 entrar(){prompt_('OBRA — clique o INÍCIO da obra sobre o eixo:')}});
$('obTela')?.addEventListener('click',()=>{if(document.body.classList.contains('paineis')&&!pnEstado.fixado)pnAbrir(null);setTool('obra');canvas.focus({preventScroll:true})});   // painel solto sai da frente do desenho
// Faixa de opções, menu e comandos.
itemFaixa('Início','Obras do PER',['Obra no desenho','🏗',()=>setTool('obra'),1]);itemFaixa('Início','Obras do PER',['Importar Excel / cronograma','📥',()=>guard(abrirImportarObras)()]);
itemFaixa('Início','Obras do PER',['Tabela de obras','▦',()=>openSection('Obras do PER')]);
comando(['OBRA','PER'],()=>setTool('obra'),'Obra do PER: clique o início e o fim no desenho');
comando(['CRONOGRAMA','IMPORTAROBRAS'],()=>guard(abrirImportarObras)(),'Importa obras de Excel/CSV ou o cronograma do MS Project (XML)');
renderObras();
