/* ---------- Estado das marcações + histórico ---------- */
const MARK_KEYS=['custom_axis','pavement_areas','shoulder_marks','pois','exclusions','traffic_paths','chainage','dxf_alignment','direction_marks','flow_overrides','flow_recoveries','flow_cuts','oae_marks','no_connection_zones','cabin','highlights','clean_areas','cities','lane_blocks','crossing_zones','crosswalks','hatch_areas','signs','lane_zones','accesses','lane_ranges'];
let M=emptyMarks(),undoStack=[],redoStack=[];
function emptyMarks(){return {custom_axis:null,pavement_areas:[],shoulder_marks:[],lane_ranges:[],accesses:[],crosswalks:[],hatch_areas:[],signs:[],lane_zones:[],lane_blocks:[],crossing_zones:[],clean_areas:[],cities:[],highlights:[],pois:[],exclusions:[],traffic_paths:[],chainage:{mode:'auto',start:null,end:null,direction:1,calibrate:false},dxf_alignment:{mode:'translation',pairs:[],applied:false},direction_marks:[],flow_overrides:[],flow_recoveries:[],flow_cuts:[],oae_marks:[],no_connection_zones:[],cabin:{enabled:false,start:null,duration_s:20,eye_height_m:1.25,fov_deg:72,pitch_deg:4,smoothing_s:1.2,speed_kmh:null,hood:true}}}
function pushHistory(stack,snapshot){stack.push(snapshot);let size=stack.reduce((n,s)=>n+s.length,0);while(stack.length>1&&(stack.length>200||size>32*1024*1024))size-=stack.shift().length}
function checkpoint(){pushHistory(undoStack,JSON.stringify(M));redoStack=[];updateUndo()}
function changed(text){refreshLists();draw();scheduleSave();if(text)msg(text)}
function restoreMarks(snapshot,message){M=JSON.parse(snapshot);draft=null;selected=null;drag=null;axisCache=null;snapIndex=null;exactSnap=null;
 if(typeof cadCmd!=='undefined')cadCmd=null;if(typeof rsDraft!=='undefined')rsDraft=null;if(typeof routeSig!=='undefined')routeSig='';
 if(typeof sel!=='undefined'&&sel&&!objOf(sel))sel=null;if(typeof selSet!=='undefined')selSet=selSet.filter(s=>objOf(s));
 changed(message);showProps();refreshRouteLanes(true);updateUndo()}
function undo(){const current=JSON.stringify(M);while(undoStack.length){const snapshot=undoStack.pop();if(snapshot===current)continue;pushHistory(redoStack,current);restoreMarks(snapshot,'Desfeito.');return}updateUndo()}
function redo(){const current=JSON.stringify(M);while(redoStack.length){const snapshot=redoStack.pop();if(snapshot===current)continue;pushHistory(undoStack,current);restoreMarks(snapshot,'Refeito.');return}updateUndo()}
function updateUndo(){$('undo').disabled=!undoStack.length;$('redo').disabled=!redoStack.length}
let saveTimer=null;
let savePending=false;
// Uma fila por projeto impede que uma resposta antiga confirme uma edição nova.
const projectSession={revision:null,epoch:0,context:0,loadIntent:0,queue:Promise.resolve(),artifacts:{},baseConfig:null};
window.RodoviaProjectState=Object.freeze({get snapshot(){return {project:pid,revision:projectSession.revision,epoch:projectSession.epoch,dirty:savePending,artifacts:structuredClone(projectSession.artifacts),undo:undoStack.length,redo:redoStack.length}}});
function scheduleSave(){if(!pid)return;projectSession.epoch++;savePending=true;$('saveState').textContent='alterações não salvas…';clearTimeout(saveTimer);saveTimer=setTimeout(async()=>{try{await save()}catch(e){$('saveState').textContent='não salvo: '+e.message;msg('A alteração NÃO foi salva: '+e.message+' Corrija o valor ou use Desfazer.',true)}},900)}


/* ---------- Configuração ---------- */
const fields=['name','origin','destination','work_year','crs','units_to_m','imagery','width','fps','duration_s','view_width_m','imagery_pixels','traffic_speed_kmh','preview_mode','preview_time_s','encoder','cpu_preset','short_video_mode','visual_quality','water_texture_opacity','water_names_opacity','render_workers','render_profile','signage_style','flow_arrows','flow_arrow_spacing_m','cities_radius_km','imagery_detail','traffic_model','traffic_density','traffic_capacity_vphpl','median_crossing','day_night','night_start_s','night_transition_s','night_darkness','signage_detail','lane_width_m','dxf_signage','texture_style','earthwork_look','detail_resolution_m','lane_arrow_repeat','arrow_min_gap_m','layer_split','lanes_per_direction','style_profile','camera_mode','vehicle_paths','direction_reference','pavement_material','existing_material','shoulder_material','joint_spacing_m','project_contrast','render_engine'];
const numeric=['units_to_m','width','fps','duration_s','view_width_m','imagery_pixels','traffic_speed_kmh','preview_time_s','water_texture_opacity','water_names_opacity','render_workers','flow_arrow_spacing_m','cities_radius_km','traffic_density','traffic_capacity_vphpl','night_start_s','night_transition_s','night_darkness','lane_width_m','detail_resolution_m','arrow_min_gap_m','lanes_per_direction','joint_spacing_m','project_contrast'];
const checks=['reverse_axis','coordinates_confirmed','traffic','hydrography','traffic_network_preview','queue_capacity_model','heavy_vehicle_reaction','heavy_shoulder_probe','water_texture','water_names','water_animated','headlights','km_markers','direction_badge','median_grass','cities_show','detail_textures','night_signage_glow','auto_earthworks','lane_arrows','gore_hatch','stop_lines','auto_signs','progress_indicator','technical_textures','hatch_auto'];
function fill(s){cfg=s;for(const k of fields){const el=$(k);if(el)el.value=s[k]??({encoder:'auto',cpu_preset:'veryfast',preview_mode:'overview',preview_time_s:30,short_video_mode:'auto',visual_quality:'enhanced',water_texture_opacity:.65,water_names_opacity:1,render_workers:0,render_profile:'final',signage_style:'clean',flow_arrows:'km_conflicts',flow_arrow_spacing_m:1000,cities_radius_km:25,imagery_detail:'auto',traffic_model:'simulado',traffic_density:1,traffic_capacity_vphpl:1900,median_crossing:'returns',day_night:'off',night_start_s:40,night_transition_s:8,night_darkness:.78,signage_detail:'full',lane_width_m:3.5,dxf_signage:'replace',texture_style:'realistic',earthwork_look:'hatch',detail_resolution_m:.2,lane_arrow_repeat:'conflicts',arrow_min_gap_m:25,layer_split:'auto',lanes_per_direction:2,style_profile:'padrao',camera_mode:'obras',vehicle_paths:'smooth',direction_reference:'axis',pavement_material:'flexivel',existing_material:'flexivel',shoulder_material:'flexivel',joint_spacing_m:5,project_contrast:0,render_engine:'otimizado'}[k]??'')}
 for(const k of checks)if($(k))$(k).checked=s[k]??['hydrography','queue_capacity_model','heavy_vehicle_reaction','heavy_shoulder_probe','water_texture','water_names','traffic','km_markers','direction_badge','median_grass','cities_show','detail_textures','night_signage_glow','auto_earthworks','lane_arrows','gore_hatch','stop_lines','auto_signs'].includes(k);$('km_start_m').value=formatKm(s.km_start_m);$('km_end_m').value=formatKm(s.km_end_m);$('reference_length_m').value=(s.reference_length_m/1000).toFixed(3).replace('.',',');
 M=emptyMarks();for(const k of MARK_KEYS)if(s[k]!==undefined)M[k]=JSON.parse(JSON.stringify(s[k]));undoStack=[];redoStack=[];updateUndo();
 $('preview_time_s').max=s.duration_s||202;$('timeLabel').textContent=tempo(s.preview_time_s??30);$('alignMode').value=M.dxf_alignment.mode;refreshLists()}
function collect(){let s={...cfg};for(const k of fields){const el=$(k);if(el)s[k]=numeric.includes(k)?Number(el.value):el.value}for(const k of checks)if($(k))s[k]=$(k).checked;
 s.km_start_m=parseKm($('km_start_m').value);s.km_end_m=parseKm($('km_end_m').value);s.reference_length_m=Number($('reference_length_m').value.replace(',','.'))*1000;
 for(const k of MARK_KEYS)s[k]=JSON.parse(JSON.stringify(M[k]));M.dxf_alignment.mode=$('alignMode').value;s.dxf_alignment.mode=M.dxf_alignment.mode;
 s.layers={};document.querySelectorAll('#layers select').forEach(el=>{if(el.value)(s.layers[el.value]??=[]).push(el.dataset.layer)});if(!analysis&&!sourceLayerCatalog?.layers?.length)s.layers=cfg.layers||{};
 s.route_directions={...(cfg.route_directions||{})};document.querySelectorAll('#routes select').forEach(el=>s.route_directions[el.dataset.route]=el.value);return s}
async function save(){
 requireProject();const id=pid,context=projectSession.context;clearTimeout(saveTimer);
 const pending=projectSession.queue.catch(()=>{}).then(async()=>{
   if(pid!==id||projectSession.context!==context)throw Error('O projeto mudou antes da gravação.');
   let epoch=projectSession.epoch,s=collect(),payload=JSON.stringify(s);
   let options=json('PUT',s);if(projectSession.revision)options.headers['If-Match']=projectSession.revision;
   let result;try{result=await api('/api/projects/'+id+'/config',options)}catch(error){
    if(error.unconfirmed&&pid===id&&projectSession.context===context){
     const stable=x=>JSON.stringify(x,(_,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v);
     try{const remote=await api('/api/projects/'+id,{timeoutMs:15000});if(pid!==id||projectSession.context!==context)throw error;
      if(stable(remote.config)===stable(s))return confirmSave(remote,s,epoch,payload,id,context);
     }catch(check){if(!check.unconfirmed&&check!==error)error.message+=' Não foi possível conferir a revisão: '+check.message}
     error.saveUncertain=true;error.message='Gravação não confirmada. Suas edições foram mantidas. Confira a conexão e tente salvar novamente; a revisão será conciliada.';throw error;
    }
    if(error.status!==409||pid!==id||projectSession.context!==context)throw error;
    const remote=await api('/api/projects/'+id);if(pid!==id||projectSession.context!==context)throw error;
    const conflicts=[];mergeProjectConfig(projectSession.baseConfig||cfg,collect(),remote.config,[],conflicts);
    if(conflicts.length)throw Error('Conflito de gravação nos campos: '+conflicts.map(c=>c.path.join(' · ')).join(', ')+'. Suas edições foram preservadas; confira a outra janela antes de gravar.');
    await syncWorkerConfig(remote.config,remote.config_revision);s=collect();payload=JSON.stringify(s);epoch=projectSession.epoch;options=json('PUT',s);options.headers['If-Match']=projectSession.revision;
    result=await api('/api/projects/'+id+'/config',options);
   }
   if(pid!==id||projectSession.context!==context)return result;
   return confirmSave(result,s,epoch,payload,id,context);
 });projectSession.queue=pending;
 try{return await pending}catch(e){if(pid===id&&projectSession.context===context){savePending=true;$('saveState').textContent='não salvo: '+e.message}throw e}
}

function confirmSave(result,s,epoch,payload,id,context){
   projectSession.revision=result.config_revision||result.revision||projectSession.revision;projectSession.artifacts=result.artifacts||{};projectSession.baseConfig=structuredClone(result.config||s);
   const unchanged=projectSession.epoch===epoch&&JSON.stringify(collect())===payload;
   if(unchanged){cfg=result.config||s;savePending=false;$('saveState').textContent='salvo na configuração';announce({t:'saved'})}
   else{savePending=true;$('saveState').textContent='alterações posteriores aguardam gravação…'}
   window.dispatchEvent(new CustomEvent('rodovia:project-state',{detail:{project:id,...result}}));$('configDownload').href='/api/projects/'+id+'/config.json';$('configDownload').hidden=false;return result;
}
async function list(){const rows=await api('/api/projects');$('projects').innerHTML='<option value="">Selecione…</option>'+rows.map(r=>`<option value="${r.id}">${esc(r.name)} · ${esc(r.created)}</option>`).join('');$('projects').value=pid}
let sourceLayerCatalog=null;
function showRouteChoices(preserve=false){
 if(!analysis){$('routes').innerHTML='';return}
 if(preserve){cfg.route_directions={...(cfg.route_directions||{})};document.querySelectorAll('#routes select[data-route]').forEach(e=>cfg.route_directions[e.dataset.route]=e.value)}
 const requested=Number($('min_route_segment_m')?.value??cfg.min_route_segment_m),minimum=Number.isFinite(requested)&&requested>0?requested:50;
 const rows=(analysis.routes||[]).filter(r=>Number.isFinite(Number(r.length_exact_m??r.length_m))&&Number(r.length_exact_m??r.length_m)>=minimum);
 $('routes').innerHTML=rows.map(r=>`<tr><td>Eixo ${esc(r.id)} · ${Number(r.length_m).toFixed(1)} m<br>${esc(r.layer)}</td><td><select data-route="${esc(r.id)}">${[['auto','Automático'],['forward','Crescente (km)'],['reverse','Decrescente (km)'],['off','Sem veículos']].map(([k,v])=>`<option value="${k}" ${(cfg.route_directions||{})[r.id]===k?'selected':''}>${v}</option>`).join('')}</select></td></tr>`).join('');
}
for(const event of ['input','change'])$('min_route_segment_m')?.addEventListener(event,()=>showRouteChoices(true));
function showLayers(){const rows=sourceLayerCatalog?.source==='input.dxf'?sourceLayerCatalog.layers:[...(analysis?.layers||[])];if(!rows)return;$('layers').innerHTML=rows.map(l=>{let current=Object.entries(cfg.layers||{}).find(([k,v])=>v.includes(l.name))?.[0]||(!Object.keys(cfg.layers||{}).length&&l.suggested_role!=='axis'?l.suggested_role:'');return `<tr><td>${esc(l.name)}<br><small>${l.count} entidades · ${l.declared?Number(l.count)===0?'CAD: camada declarada vazia':'Fonte CAD':'Análise do projeto'}</small></td><td><select data-layer="${esc(l.name)}"><option value="">Ignorar</option>${Object.entries(roles).map(([k,v])=>`<option value="${k}" ${k===current?'selected':''}>${v}</option>`).join('')}</select></td><td><button class="mini" data-showlayer="${esc(l.name)}" title="Destacar esta camada no editor">Ver</button></td></tr>`}).join('');showRoleColors();
 if(!analysis){$('routes').innerHTML='';$('warnings').textContent=(sourceLayerCatalog?.warnings||[]).join('\n');return}
 showRouteChoices();
 $('warnings').textContent=(analysis.warnings||[]).join('\n');$('geom').textContent=`Comprimento geométrico: ${(analysis.geometric_length_m/1000).toFixed(3)} km. A extensão de referência permanece independente.`+(analysis.georef_check?` Conferência DXF × KMZ (${analysis.georef_check.points} pontos ao longo do eixo): desvio mediano ${analysis.georef_check.median_m.toFixed(2)} m, 95% até ${analysis.georef_check.p95_m.toFixed(2)} m, máximo ${analysis.georef_check.max_m.toFixed(2)} m.`:' Sem KMZ: a posição não foi conferida contra outra referência.')}
function mergeProjectConfig(base,local,remote,path=[],conflicts=[]){
 const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),copy=v=>v===undefined?undefined:structuredClone(v);
 if(same(local,base))return copy(remote);if(same(remote,base)||same(local,remote))return copy(local);
 if([base,local,remote].every(v=>v&&typeof v==='object'&&!Array.isArray(v))){const out={};for(const key of new Set([...Object.keys(base),...Object.keys(local),...Object.keys(remote)])){const v=mergeProjectConfig(base[key],local[key],remote[key],[...path,key],conflicts);if(v!==undefined)out[key]=v}return out}
 conflicts.push({path,local:copy(local),remote:copy(remote)});return copy(local);
}
async function resolveProjectConflicts(conflicts){
 const d=document.createElement('dialog');d.className='winDlg';d.innerHTML='<h3>Conferir resultado da conversão</h3><p>Estes campos foram alterados durante o processamento: '+esc(conflicts.map(c=>c.path.join(' · ')).join(', '))+'. As demais edições serão preservadas.</p><div class="row"><button type="button" data-choice="local">Manter minha edição</button><button type="button" data-choice="remote">Usar resultado da conversão</button></div>';document.body.appendChild(d);
 return new Promise(resolve=>{const finish=v=>{d.close();d.remove();resolve(v)};d.onclick=e=>{const value=e.target.closest('[data-choice]')?.dataset.choice;if(value)finish(value)};d.oncancel=e=>{e.preventDefault();finish('local')};d.showModal()});
}
async function syncWorkerConfig(remote,revision){
 const context=projectSession.context,id=pid;clearTimeout(saveTimer);const local=collect(),conflicts=[];const merged=mergeProjectConfig(projectSession.baseConfig||cfg,local,remote,[],conflicts);
 if(conflicts.length&&await resolveProjectConflicts(conflicts)==='remote')for(const item of conflicts){let target=merged;for(const key of item.path.slice(0,-1))target=target[key];target[item.path.at(-1)]=structuredClone(item.remote)}
 if(pid!==id||projectSession.context!==context)throw Error('O projeto mudou durante a conferência da conversão. Reabra o projeto para receber o resultado.');
 const undo=undoStack.slice(),redo=redoStack.slice();fill(merged);undoStack=undo;redoStack=redo;updateUndo();
 projectSession.baseConfig=structuredClone(remote);projectSession.revision=revision;savePending=JSON.stringify(merged)!==JSON.stringify(remote);$('saveState').textContent=savePending?'Resultado recebido; edições locais aguardam gravação.':'Configuração da conversão recebida.';
}
// Dados derivados pertencem a um projeto; nunca conservar destaques do anterior.
function resetProjectPresentation(){
 if(window.Rodovia3D?.stats().project&&Rodovia3D.stats().project!==pid)Rodovia3D.close();
 analysis=null;editor=null;meta=null;baseImage=null;sourceLayerCatalog=null;lastRender=null;
 geo=null;vec=null;vecPaths=null;localInfo=null;geoPid='';axisCache=null;
 layerShow=null;layerPrev=null;hatchPrev=null;alignResult=null;
 selected=null;draft=null;drag=null;sel=null;selSeg=null;selSet=[];dxfSel=null;selLink=null;
 snapIndex=null;exactSnap=null;cadCmd=null;rsDraft=null;routeLanes=[];routeSig='';clearTimeout(routeTimer);
 localTiles.clear();window.RodoviaLayers?.invalidate();
 $('layers').replaceChildren();$('routes').replaceChildren();$('warnings').textContent='';$('geom').textContent='';
 window.dispatchEvent(new CustomEvent('rodovia:project-reset',{detail:{project:pid,context:projectSession.context}}));
}
async function load(id,options={}){
 const intent=++projectSession.loadIntent,resultsOnly=!!options.resultsOnly&&pid===id;
 const previousFrame={meta,baseImage};const retainedView=resultsOnly?captureProjectView():null;
 if(!resultsOnly&&pid&&savePending)await save();
 const openingFingerprint=!resultsOnly&&pid?JSON.stringify(collect()):null;
 const r=await api('/api/projects/'+id);if(intent!==projectSession.loadIntent)return false;
 if(!resultsOnly&&pid&&(savePending||JSON.stringify(collect())!==openingFingerprint)){savePending=true;throw Error('Existem novas alterações feitas durante a abertura. Salve-as antes de trocar de projeto.')}

 if(!resultsOnly){clearTimeout(saveTimer);pid=id;projectSession.context++;projectSession.epoch=0;savePending=false;localStorage.setItem('rodovia_project',pid);resetProjectPresentation();fill(r.config);projectSession.revision=r.config_revision||null;projectSession.baseConfig=structuredClone(r.config)}
 else if(options.syncConfig)await syncWorkerConfig(r.config,r.config_revision);
 if(!resultsOnly){sourceLayerCatalog=null;if(r.files.dxf)try{const catalog=await api('/api/projects/'+id+'/layers');if(intent===projectSession.loadIntent&&pid===id)sourceLayerCatalog=catalog}catch(e){msg(e.message,true)}if(intent!==projectSession.loadIntent)return false}
 projectSession.artifacts=r.artifacts||{};lastRender=r.render_info||null;analysis=r.analysis||null;meta=r.preview||(resultsOnly?previousFrame.meta:null);
 const retainedPreview=resultsOnly&&!r.preview&&!!(previousFrame.meta&&previousFrame.baseImage);
 $('fileState').textContent=`DXF: ${r.files.dxf?'carregado':'ausente'} · KMZ: ${r.files.kmz?'carregado':'ausente'}`;{const edits=resultsOnly?[...document.querySelectorAll('#layers select,#routes select')].map(el=>({layer:el.dataset.layer,route:el.dataset.route,value:el.value})):[];showLayers();for(const edit of edits){const el=[...document.querySelectorAll('#layers select,#routes select')].find(el=>edit.layer!==undefined?el.dataset.layer===edit.layer:el.dataset.route===edit.route);if(el)el.value=edit.value}}$('projects').value=pid;$('configDownload').href='/api/projects/'+pid+'/config.json';$('configDownload').hidden=false;
 let nextEditor=null;if(r.editor_ready||meta)try{nextEditor=await api('/api/projects/'+id+'/editor.json')}catch{}
 if(intent!==projectSession.loadIntent||pid!==id)return false;editor=nextEditor;
 const same=geoPid===pid;await loadGeo();if(intent!==projectSession.loadIntent||pid!==id)return false;
 if(retainedPreview){baseImage=previousFrame.baseImage;previewStale=true;draw()}else if(meta){try{await loadImage(!!retainedView||same&&useGeo())}catch(error){if(intent!==projectSession.loadIntent||pid!==id)return false;if(!resultsOnly||!previousFrame.baseImage)throw error;meta=previousFrame.meta;baseImage=previousFrame.baseImage;msg('A prévia não pôde ser atualizada. A vista anterior foi mantida: '+error.message,true)}}else{baseImage=null;if(!same||!ready())fitView();else draw()}
 if(intent===projectSession.loadIntent&&pid===id&&retainedView)restoreProjectView(retainedView);
 if(intent!==projectSession.loadIntent||pid!==id)return false;refreshLists();baseUi();
 window.dispatchEvent(new CustomEvent('rodovia:project-state',{detail:{project:id,...r}}));if(r.recovery)msg(r.recovery.message);return true;
}
async function loadImage(keepView=false){if(!meta)return;const id=pid,context=projectSession.context,im=new Image();await new Promise((resolve,reject)=>{im.onload=resolve;im.onerror=()=>reject(Error('Não foi possível carregar a prévia.'));im.src='/api/projects/'+id+'/preview.png?v='+Date.now()});if(pid!==id||projectSession.context!==context)return;baseImage=im;if(keepView)draw();else fitView();}
