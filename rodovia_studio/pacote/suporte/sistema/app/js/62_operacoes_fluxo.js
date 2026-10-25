// Corte por dois pontos e junção com geometria completa validada pelo motor.
(()=>{'use strict';
let operation=0,loading=false;
const cancel=()=>{operation++;loading=false;window.RodoviaFlowEditConflict=null};
const point=p=>Array.isArray(p)?{x:p[0],y:p[1]}:p;
function projection(points,w){let best=null,s=0;for(let i=1;i<points.length;i++){const a=point(points[i-1]),b=point(points[i]),dx=b.x-a.x,dy=b.y-a.y,L=Math.hypot(dx,dy);if(L<1e-9)continue;const u=Math.max(0,Math.min(1,((w.x-a.x)*dx+(w.y-a.y)*dy)/(L*L))),q={x:a.x+u*dx,y:a.y+u*dy},d=Math.hypot(w.x-q.x,w.y-q.y);if(!best||d<best.distance)best={point:q,s:s+u*L,distance:d};s+=L}return best}
const near=w=>{const s=nearestSegment(w,12/Math.max(pxPerM(),1e-9));if(!s)throw Error('Clique sobre uma trajetória calculada. Recalcule os fluxos se necessário.');return s};
ferramenta('flowcut',{rotulo:'Apagar intervalo do fluxo',dica:'Clique no início e no fim do intervalo defeituoso do mesmo segmento. O eixo original será preservado.',icone:'M3 6h18M5 3v6M19 3v6M8 12l8 8M16 12l-8 8M3 16h2M19 16h2',clique:guard(async w=>{
 const stamp=operation,project=pid,context=projectSession.context,s=near(w);
 if(!draft||draft.type!=='flowcut'){const full=await api(`/api/projects/${pid}/flow-tools/segment/${s.id}?revision=${encodeURIComponent(editor.engine_revision||'')}`);if(stamp!==operation||tool!=='flowcut')return;if(pid!==project||projectSession.context!==context)throw Error('O projeto mudou durante a seleção.');const start=projection(full.points,w);draft={type:'flowcut',project,context,revision:editor.engine_revision,id:s.id,target_key:full.origin_key||'',points:full.points,start,pts:[start.point]};msg('Início marcado. Clique no fim do intervalo do mesmo segmento.');draw();return}
 if(draft.project!==pid||draft.context!==projectSession.context||draft.revision!==editor?.engine_revision)throw Error('O projeto mudou. Reinicie o corte.');
 if(s.id!==draft.id)throw Error('Marque o fim no mesmo segmento; use Esc para trocar a seleção.');
 const end=projection(draft.points,w),first=draft.start;
 if(Math.abs(end.s-first.s)<.1)throw Error('Marque um intervalo maior que 10 cm.');
 checkpoint();M.flow_cuts.push({id:uid(),target_key:draft.target_key,start:first.point,end:end.point,enabled:true});draft=null;changed('Intervalo excluído da circulação; eixo original preservado. Recalculando…');await start('analyze');
 },'Apagar intervalo do fluxo')});
ferramenta('flowjoin',{rotulo:'Juntar subsegmentos',dica:'Clique no primeiro e no segundo subsegmento, na ordem do fluxo. A junção será conferida pelo motor.',icone:'M2 5h7v5M22 19h-7v-5M4 19l16-14M8 19H4v-4M16 5h4v4',clique:guard(async w=>{
 const stamp=operation,project=pid,context=projectSession.context,s=near(w);if(!draft||draft.type!=='flowjoin'){draft={type:'flowjoin',project,context,revision:editor.engine_revision,id:s.id,segment:s,pts:[w]};msg('Primeiro segmento marcado. Clique no segundo, na ordem do fluxo.');draw();return}
 if(draft.project!==pid||draft.context!==projectSession.context||draft.revision!==editor?.engine_revision)throw Error('O projeto mudou. Reinicie a junção.');
 if(s.id===draft.id)throw Error('Escolha outro subsegmento.');
 const a=draft.segment,result=await api(`/api/projects/${pid}/flow-tools/join`,json('POST',{first:a.id,second:s.id,revision:draft.revision||''}));
 if(stamp!==operation||tool!=='flowjoin'||draft?.type!=='flowjoin')return;
 if(pid!==project||projectSession.context!==context)throw Error('O projeto mudou durante a validação.');
 if(!result.ok){if(result.at)window.RodoviaFlowEditConflict={project,revision:editor.engine_revision,point:point(result.at),message:result.reason};draw();throw Error(result.reason)}
 checkpoint();M.route_alignments.push({id:uid(),name:'Fluxo unido '+(M.route_alignments.length+1),points:result.points.map(point),enabled:true,type:'unico',lanes:1,median_m:0,lane_width_m:3.5,taper_m:40,level:result.level,outside_pavement:false,source:'junção validada',sections:[],lane_change:'off',lane_change_sections:[]});
 for(const original of [a,s])if(segOverride(original,'disable')<0)M.flow_overrides.push({id:uid(),x:original.mid[0],y:original.mid[1],target_key:original.origin_key||'',action:'disable',enabled:true});
 draft=null;window.RodoviaFlowEditConflict=null;changed('Junção validada: fluxo único criado e subsegmentos originais desativados.');await start('analyze');
 },'Juntar subsegmentos')});
for(const id of ['flowcut','flowjoin']){const definition=FERRAMENTAS[id],click=definition.clique;definition.clique=async(...args)=>{if(loading){msg('Aguarde a operação atual ou use Esc para cancelar.');return false}const stamp=operation;loading=true;try{return await click(...args)}finally{if(stamp===operation)loading=false}};definition.sair=cancel;definition.esc=()=>{cancel();draft=null;setTool('pan');draw()}}
function buttons(){for(const id of ['flowcut','flowjoin'])for(const group of document.querySelectorAll('[data-rs-group="Fluxos de tráfego"]')){if(group.querySelector(`[data-rs-tool=${id}]`))continue;const panel=group.closest('[role=tabpanel]')||group.closest('[id^=rsToolPanel]'),existing=panel?.querySelector(`[data-rs-tool=${id}]`);if(existing){const prior=existing.parentElement;group.appendChild(existing);if(prior.dataset.rsGroup&&!prior.children.length)prior.remove();continue}const def=FERRAMENTAS[id],b=document.createElement('button');b.type='button';b.dataset.rsTool=id;b.title=def.rotulo+' — '+def.dica;b.setAttribute('aria-label',def.rotulo);b.innerHTML=toolIcon(id);b.onclick=guard(()=>setTool(id));group.appendChild(b)}}
queueMicrotask(buttons);
const oldProps=showSegProps;showSegProps=function(...args){const r=oldProps(...args),s=segById(selSeg?.id);if(s&&!$('propPanel').hidden){const p=document.createElement('p');p.textContent=s.both?'↔ Sentido duplo':'→ Sentido único';p.className='rsFlowDirection';$('propPanel').appendChild(p)}return r};
window.RodoviaFlowTools=Object.freeze({projection});
})();
