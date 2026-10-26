// ---------- arquivos do projeto: DXF e KMZ/KML enviados na hora, com nome, tamanho e data ----------
function fmtBytes(n){return n>=1048576?(n/1048576).toLocaleString('pt-BR',{maximumFractionDigits:1})+' MB':(n/1024).toLocaleString('pt-BR',{maximumFractionDigits:0})+' kB'}
let filesInfo=null;
function filesUi(info){filesInfo=info||filesInfo;const I=filesInfo||{};for(const k of ['dxf','kmz']){const tr=document.querySelector(`.fileTable tr[data-fk="${k}"]`);if(!tr)continue;const f=I[k];
  tr.querySelector('.fn').innerHTML=f?`<b>${esc(f.name)}</b><br><small>${fmtBytes(f.bytes)} · enviado ${esc(f.sent||'')}</small>`:'<span class="muted">não carregado</span>';tr.querySelector('[data-fdel]').hidden=!f;tr.classList.toggle('ok',!!f)}
 const ks=analysis?.kmz_status;let kmsg='';
 if(I.kmz&&ks){const usos=(ks.uses||[]).map(x=>({eixo_fallback:'eixo',georreferenciamento:'conferência geográfica',pois:'POIs',referencia_geometrica:'referência geométrica'}[x]||x)).join(', ');kmsg=ks.required?' · KMZ NECESSÁRIO'+(usos?` (${usos})`:''):ks.used?' · KMZ em uso'+(usos?` (${usos})`:''):' · KMZ validado como referência';}
 $('fileState').textContent=I.dxf||I.kmz?`DXF: ${I.dxf?'carregado':'ausente'} · KMZ/KML: ${I.kmz?'carregado':'ausente'}${I.dxf&&!analysis?' — clique “Analisar arquivos”.':''}${kmsg}`:'Nenhum arquivo carregado: envie o DXF (e o KMZ/KML, se houver).'}
async function sendFiles(list){requireProject();if(task||taskRequestPending||fileMutationPending){msg('Envio aguardando: conclua ou cancele a tarefa atual antes de trocar arquivos.');return}const files=[...list];if(!files.length)return;fileMutationPending=true;try{await save();const project=pid,context=projectSession.context;const ok=[],bad=[];
 for(const f of files){const ext=(f.name.split('.').pop()||'').toLowerCase();if(!['dxf','kmz','kml','dwg'].includes(ext)){bad.push(`${f.name}: tipo não aceito`);continue}
  msg(`Enviando ${f.name} (${fmtBytes(f.size)})…`);const d=new FormData();d.append('file',f);try{const r=await api('/api/projects/'+pid+'/files',{method:'POST',body:d});ok.push(f.name);filesUi(r.files);const snapshot=await api('/api/projects/'+project);if(pid!==project||projectSession.context!==context)return;await syncWorkerConfig(snapshot.config,snapshot.config_revision)}catch(e){bad.push(`${f.name}: ${e.message}`)}}
 if(ok.length){analysis=null;editor=null;axisCache=null;draw()}
 if(ok.length)msg(`${ok.join(' e ')} carregado(s). ${filesInfo?.dxf&&filesInfo?.kmz?'DXF e KMZ prontos.':filesInfo?.dxf?'Falta o KMZ/KML (opcional).':'Falta o DXF.'} Clique “Analisar arquivos”.`+(bad.length?' Problemas: '+bad.join('; '):''),!!bad.length);
 else if(bad.length)msg('Nenhum arquivo enviado: '+bad.join('; '),true);
 try{$('analyze').classList.add('attention')}catch{}}finally{fileMutationPending=false}}
$('upload').onclick=guard(async()=>{requireProject();if(!$('files').files.length)throw Error('Escolha o DXF e/ou o KMZ/KML (ou arraste os arquivos para a caixa).');await sendFiles($('files').files);$('files').value=''});
$('files')?.addEventListener('change',guard(async()=>{if(!pid)return msg('Crie ou abra um projeto antes de escolher os arquivos.',true);await sendFiles($('files').files);$('files').value=''}));
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('[data-fpick]');if(!b)return;if(!pid)return msg('Crie ou abra um projeto.',true);$(b.dataset.fpick==='dxf'?'fileDxf':'fileKmz').click()});
for(const id of ['fileDxf','fileKmz'])$(id)?.addEventListener('change',guard(async e=>{await sendFiles(e.target.files);e.target.value=''}));
document.addEventListener('click',guard(async e=>{const b=e.target.closest&&e.target.closest('[data-fdel]');if(!b)return;if(task||taskRequestPending){msg('Retirada aguardando: conclua ou cancele a tarefa atual antes de trocar arquivos.');return}const k=b.dataset.fdel;const ks=analysis?.kmz_status;let extra='';if(k==='kmz'&&ks?.required)extra=' ATENÇÃO: a análise atual depende deste KMZ como eixo/referência; sem ele o próximo cálculo pode não ser executado.';else if(k==='kmz'&&ks?.used)extra=' O KMZ está sendo usado na análise atual; a próxima análise poderá produzir resultado diferente.';if(!await confirmBox(`Retirar o ${k==='dxf'?'DXF':'KMZ/KML'} do projeto? O arquivo no seu computador não é alterado; a análise precisa ser refeita.${extra}`,'Retirar','Cancelar'))return;const r=await api(`/api/projects/${pid}/files/${k}`,{method:'DELETE'});filesUi(r.files);analysis=null;msg(`${k==='dxf'?'DXF':'KMZ/KML'} retirado do projeto.`)}));
{const dz=$('dropZone');const over=e=>{e.preventDefault();dz.classList.add('over')};
 for(const t of [dz,document.body]){t?.addEventListener('dragover',e=>{if([...(e.dataTransfer?.types||[])].includes('Files'))over(e)});}
 document.body.addEventListener('dragleave',e=>{if(e.target===document.body||e.target===dz)dz.classList.remove('over')});
 document.body.addEventListener('drop',guard(async e=>{if(!e.dataTransfer?.files?.length)return;const fs=[...e.dataTransfer.files].filter(f=>/\.(dxf|kmz|kml|dwg)$/i.test(f.name));if(!fs.length)return;e.preventDefault();dz.classList.remove('over');if(!pid)return msg('Crie ou abra um projeto antes de soltar os arquivos.',true);await sendFiles(fs)}))}
estender('load',_l=>async (id,...args)=>{const loaded=await _l(id,...args);if(loaded===false||pid!==id)return false;try{const r=await api('/api/projects/'+id);if(pid===id)filesUi(r.files_info)}catch{}},'arquivos do projeto: DXF e KMZ/KML enviados na hora, com nome, tamanho');

// ---------- aparência: taludes, canteiro, água e sinalização ----------
MARK_KEYS.push('texture_areas');estender('emptyMarks',_em=>function(){return {..._em(),texture_areas:[]}},'aparência: taludes, canteiro, água e sinalização');if(!M.texture_areas)M.texture_areas=[];
OBJ_SPECS.push(['texture_areas','Região de textura','area',o=>o.points.map((_,i)=>[o.points,i])]);
PROP_LABEL.surface=['Superfície','Tipo de superfície que recebe a textura dentro da região.'];
const SURF_MODE={cut:'talude_corte',fill:'talude_aterro',median:'canteiro',pavement:'pista_nova',existing_pavement:'pista_existente',shoulder:'acostamento',oae:'concreto'};
const SURF_NAME={talude_corte:'Talude de corte',talude_aterro:'Talude de aterro',canteiro:'Canteiro (grama)',pista_nova:'Pista nova',pista_existente:'Pista existente',acostamento:'Acostamento',concreto:'Concreto'};
let surfTarget=null;
function surfMode(m){document.querySelectorAll('#surfDlg [data-sm]').forEach(x=>x.hidden=x.dataset.sm!==m);$('surfDlg').dataset.mode=m}
async function openSurfDialog(mode,opts={}){surfTarget=opts;const tp=cfg.texture_params||{};
 if(mode==='tex'){const surf=opts.surface||'talude_corte';$('sd_surf').value=surf;const t=opts.area?.texture||(opts.scope==='tipo'?tp[surf]:null)||{};for(const [k,d] of [['grao',1],['tom',1],['remendos',1],['fissuras',1],['brilho',0]])$('sd_'+k).value=t[k]??d;
  $('sd_scope').value=opts.ring||opts.area?'area':'tipo';$('sd_scope').querySelector('option[value=area]').disabled=!(opts.ring||opts.area);$('sd_color').value=(cfg.role_colors||{})[{talude_corte:'cut',talude_aterro:'fill',canteiro:'median'}[surf]]||({talude_corte:'#df6262',talude_aterro:'#53bb77',canteiro:'#7f9b6e'}[surf]||'#808080');
  $('sd_look').value=cfg.earthwork_look||'hatch';$('sd_title').textContent=opts.ring?`Textura — área do desenho (${opts.layer})`:opts.area?`Textura — ${opts.area.name}`:'Textura por tipo de superfície'}
 if(mode==='agua'){$('sd_wcolor').value=(cfg.role_colors||{}).water||'#2a80b9';$('sd_wtex').checked=cfg.water_texture!==false;$('sd_wop').value=cfg.water_texture_opacity??.65;$('sd_wanim').checked=!!cfg.water_animated;$('sd_wnames').checked=cfg.water_names!==false;$('sd_title').textContent='Aparência da água (hidrografia)'}
 if(mode==='sin'){const sp=cfg.signage_paint||{};$('sd_white').value=sp.white||'#f4f2e2';$('sd_yellow').value=sp.yellow||'#f4c846';$('sd_wear').value=sp.wear??0;$('sd_sop').value=sp.opacity??1;$('sd_title').textContent='Aparência da sinalização horizontal (tinta)'}
 surfMode(mode);surfPreview();$('surfDlg').showModal()}
function surfVals(){const o={};for(const k of ['grao','tom','remendos','fissuras','brilho'])o[k]=Number($('sd_'+k).value);return o}
function surfPreview(){const m=$('surfDlg').dataset.mode;
 if(m==='tex'){const surf=$('sd_surf').value,v=surfVals();for(const k of Object.keys(v))$('sdv_'+k).textContent=k==='brilho'?v[k].toFixed(2):v[k].toFixed(2)+'×';$('sd_img').src=`/api/texture_preview.png?surface=${surf}&p=${encodeURIComponent(JSON.stringify(v))}&m_px=0.03`;
  const tal=surf.startsWith('talude');$('sd_lookrow').hidden=!tal;$('sd_colorrow').hidden=!['talude_corte','talude_aterro','canteiro'].includes(surf);$('sd_note').textContent=tal&&$('sd_look').value!=='natural'?'Nos taludes a textura aparece com a aparência “natural (terreno)”; com “hachura” vale a cor e a hachura.':''}
 if(m==='agua'){const c=$('sd_wprev').getContext('2d'),W=300,H=120;c.fillStyle=$('sd_wcolor').value;c.fillRect(0,0,W,H);if($('sd_wtex').checked){c.globalAlpha=Number($('sd_wop').value)*.5;c.strokeStyle='#ffffff';for(let y=8;y<H;y+=10){c.beginPath();for(let x=0;x<=W;x+=6)c.lineTo(x,y+Math.sin(x/17+y)*2.2);c.stroke()}c.globalAlpha=1}$('sdv_wop').textContent=Number($('sd_wop').value).toFixed(2)}
 if(m==='sin'){const c=$('sd_sprev').getContext('2d'),W=300,H=120;c.fillStyle='#4a4f52';c.fillRect(0,0,W,H);const wear=Number($('sd_wear').value),op=Number($('sd_sop').value);
  const line=(y,col,dash)=>{for(let x=0;x<W;x+=2){if(dash&&(x%40)>24)continue;const n=(Math.sin(x*.37)+Math.sin(x*.11+y)+Math.sin(x*1.7))/3;const a=op*Math.max(0,Math.min(1,1-wear*(.35+1.1*(.5+.35*n))));c.globalAlpha=a;c.fillStyle=col;c.fillRect(x,y,2,5)}c.globalAlpha=1};
  line(18,$('sd_white').value,false);line(58,$('sd_yellow').value,false);line(64,$('sd_yellow').value,false);line(100,$('sd_white').value,true);$('sdv_wear').textContent=wear.toFixed(2);$('sdv_sop').textContent=op.toFixed(2)}}
document.addEventListener('input',e=>{if(e.target.closest&&e.target.closest('#surfDlg'))surfPreview()});document.addEventListener('change',e=>{if(e.target.closest&&e.target.closest('#surfDlg'))surfPreview()});
function surfApply(){const m=$('surfDlg').dataset.mode;
 if(m==='tex'){const surf=$('sd_surf').value,v=surfVals(),neutral=v.grao===1&&v.tom===1&&v.remendos===1&&v.fissuras===1&&v.brilho===0;const role={talude_corte:'cut',talude_aterro:'fill',canteiro:'median'}[surf];
  if(role){const rc={...(cfg.role_colors||{})},def={cut:'#df6262',fill:'#53bb77',median:'#7f9b6e'}[role];if($('sd_color').value.toLowerCase()!==def)rc[role]=$('sd_color').value;else delete rc[role];cfg.role_colors=rc}
  if(surf.startsWith('talude')){cfg.earthwork_look=$('sd_look').value;if($('earthwork_look'))$('earthwork_look').value=cfg.earthwork_look}
  if($('sd_scope').value==='tipo'){const t={...(cfg.texture_params||{})};if(neutral)delete t[surf];else t[surf]=v;cfg.texture_params=t;scheduleSave();try{texUi()}catch{}msg(`Textura de “${SURF_NAME[surf]}” alterada em todo o projeto. A prévia mostra o resultado.`)}
  else if(surfTarget?.area){checkpoint();surfTarget.area.surface=surf;surfTarget.area.texture=neutral?null:v;changed(`Textura da região “${surfTarget.area.name}” alterada.`)}
  else if(surfTarget?.ring){checkpoint();const n=M.texture_areas.length+1;M.texture_areas.push({id:uid(),name:`${SURF_NAME[surf]} ${n} (${surfTarget.layer})`.slice(0,80),surface:surf,points:surfTarget.ring.map(P_),texture:neutral?null:v,enabled:true});dxfSel=null;changed(`Região com textura própria criada (${SURF_NAME[surf]}). O tipo e a geometria do desenho não mudam.`)}
  scheduleSave()}
 if(m==='agua'){const rc={...(cfg.role_colors||{})};if($('sd_wcolor').value.toLowerCase()!=='#2a80b9')rc.water=$('sd_wcolor').value;else delete rc.water;cfg.role_colors=rc;cfg.water_texture=$('sd_wtex').checked;cfg.water_texture_opacity=Number($('sd_wop').value);cfg.water_animated=$('sd_wanim').checked;cfg.water_names=$('sd_wnames').checked;
  for(const [id,v] of [['water_texture',cfg.water_texture],['water_animated',cfg.water_animated],['water_names',cfg.water_names]])if($(id))$(id).checked=v;if($('water_texture_opacity'))$('water_texture_opacity').value=cfg.water_texture_opacity;scheduleSave();msg('Aparência da água alterada. A prévia mostra o resultado.')}
 if(m==='sin'){const w=$('sd_white').value.toLowerCase(),y=$('sd_yellow').value.toLowerCase();cfg.signage_paint={white:w==='#f4f2e2'?'':w,yellow:y==='#f4c846'?'':y,wear:Number($('sd_wear').value),opacity:Number($('sd_sop').value)};scheduleSave();msg('Aparência da sinalização alterada (cores, desgaste e opacidade). A prévia mostra o resultado.')}
 $('surfDlg').close();window.RodoviaUpdatePolicy?.committed();setTimeout(clearSelection,0);scheduleViewPreview()}
$('sd_ok')?.addEventListener('click',surfApply);$('sd_cancel')?.addEventListener('click',()=>$('surfDlg').close());
$('sd_reset')?.addEventListener('click',()=>{const m=$('surfDlg').dataset.mode;if(m==='tex')for(const [k,d] of [['grao',1],['tom',1],['remendos',1],['fissuras',1],['brilho',0]])$('sd_'+k).value=d;if(m==='sin'){$('sd_white').value='#f4f2e2';$('sd_yellow').value='#f4c846';$('sd_wear').value=0;$('sd_sop').value=1}if(m==='agua'){$('sd_wcolor').value='#2a80b9';$('sd_wtex').checked=true;$('sd_wop').value=.65;$('sd_wanim').checked=false}surfPreview()});
$('surfDlg')?.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.target.matches('select,input[type=color]')){e.preventDefault();e.stopPropagation();surfApply()}});
// Trocar textura: o diálogo certo para o que está selecionado.
estender('openTexDialog',_o=>async function(){const L=selObjs();
 if(!L.length&&dxfSel){const role=dxfSel.role;if(role==='water')return openSurfDialog('agua');if(role==='sign_h')return openSurfDialog('sin');if(['cut','fill','median','oae'].includes(role))return openSurfDialog('tex',{surface:SURF_MODE[role],ring:dxfSel.points,layer:dxfSel.layer})}
 if(L.length===1&&L[0].key==='texture_areas')return openSurfDialog('tex',{surface:L[0].o.surface,area:L[0].o});
 if(L.length===1&&L[0].key==='hatch_areas')return openSurfDialog('sin');
 return _o()},'Trocar textura: o diálogo certo para o que está selecionado.');
estender('ctxItems',_ci=>function(w){const items=_ci(w);const L=selObjs();
 if(L.length===1&&['texture_areas','hatch_areas'].includes(L[0].key)&&!items.some(x=>x.t==='Trocar textura…'))items.splice(1,0,{ic:'▦',t:'Trocar textura…',h:L[0].key==='hatch_areas'?'Cores, desgaste e opacidade da tinta da sinalização.':'Grão, tom e brilho desta região.',f:()=>openTexDialog()});
 if(!L.length&&!dxfSel&&!selLink&&!selSeg&&!draft&&!cadCmd){const k=items.findIndex(x=>x.t==='Inserir');items.splice(k+1,0,{ic:'🎨',t:'Aparência',sub:[{ic:'⛰',t:'Taludes e canteiro…',h:'Textura e cor dos taludes (corte/aterro) e do canteiro.',f:()=>openSurfDialog('tex',{surface:'talude_corte',scope:'tipo'})},{ic:'≈',t:'Água (hidrografia)…',h:'Cor, textura, opacidade e animação da água.',f:()=>openSurfDialog('agua')},{ic:'═',t:'Sinalização horizontal…',h:'Cores da tinta, desgaste e opacidade.',f:()=>openSurfDialog('sin')},{ic:'▦',t:'Pavimento…',h:'Textura de cada tipo de pavimento.',f:()=>openSection('Perfil de apresentação')}]})}
 return items},'Trocar textura: o diálogo certo para o que está selecionado.');

