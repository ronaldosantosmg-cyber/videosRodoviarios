// 1.42.41: relatório de interpretação das camadas (somente leitura), com ícones por papel.
(()=>{'use strict';
const svg=d=>`<svg class="rsLayerIcon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="${d}"/></svg>`;
const ICON={axis:'M3 12h4m3 0h4m3 0h4',pavement:'M3 18 8 6h8l5 12zM12 8v3m0 3v3',existing_pavement:'M3 18 8 6h8l5 12zM9 14h6',shoulder:'M4 6v12m16-12v12M8 8v8',edge_line:'M3 8h18M3 16h18',median:'M3 12h18M6 9v6m6-6v6m6-6v6',barrier:'M3 16h18M5 16V9m7 7V9m7 7V9M3 9h18',oae:'M2 9h20M4 9v8m16-8v8M2 17h20M8 9v8m8-8v8',cut:'M3 20 10 6l4 8 7 6z',fill:'M3 20 9 10h6l6 10z',earthwork:'M2 20c4-8 8-12 10-12s6 4 10 12z',domain:'M4 4h16v16H4z',water:'M3 15c3-3 6 3 9 0s6 3 9 0M3 10c3-3 6 3 9 0s6 3 9 0',sign_h:'M4 12h4m4 0h4m4 0h2',sign_v:'M12 3v18M7 5h10v6H7z',none:'M5 5l14 14M19 5 5 19'};
const iconFor=role=>svg(ICON[role]||ICON.none);
const OR={projeto:'Projeto',perfil:'Perfil padrão',nenhum:'—'};
const CODE={incoerente:'⚠ geometria incoerente',sem_papel:'● sem papel',papel_duplo:'⚠ papel duplo',baixa_confianca:'? confirmar',ausente:'⚠ ausente',papel_ausente:'⛔ papel ausente',sem_dxf:'⛔ sem DXF'};
async function open(){
 requireProject();if(!await RodoviaPanels.close())return;
 const project=pid,context=projectSession.context;msg('Lendo as camadas do desenho…');
 const data=await api(`/api/projects/${project}/layer-report`);if(pid!==project||context!==projectSession.context)return;
 const s=data.summary,rows=data.layers.map(r=>`<tr class="${r.alerts.length?'rsWarn':''}"><td>${iconFor(r.role)} ${esc(r.layer)}</td><td>${esc(r.role_label||'Sem papel')}</td><td>${OR[r.origin]||''}${r.role?` · ${Math.round(r.confidence*100)}%`:''}</td><td>${r.entities}</td><td>${esc(Object.entries(r.types).map(([k,v])=>k+' '+v).join(', '))}</td><td>${r.alerts.map(a=>`<span title="${esc(a.text)}">${CODE[a.code]||esc(a.code)}</span>`).join(' ')}</td></tr>`).join('');
 const gaps=data.alerts.filter(a=>!a.layer).map(a=>`<li>${CODE[a.code]||''} ${esc(a.text)}</li>`).join('');
 const d=RodoviaModelDialog.open({id:'rsLayerReport',title:'Interpretação das camadas',html:`<p>${s.layers} camadas · ${s.with_role} com papel · ${s.without_role} com geometria e sem papel · ${s.alerts} alertas. Somente leitura: ajuste o tipo na lista de camadas.</p>${gaps?`<ul role="alert">${gaps}</ul>`:''}<div style="max-height:55vh;overflow:auto"><table class="rsTable"><thead><tr><th>Camada</th><th>Papel</th><th>Origem</th><th>Ent.</th><th>Tipos</th><th>Alertas</th></tr></thead><tbody>${rows}</tbody></table></div><div class="row"><button type="button" data-layer-csv>${svg('M12 4v11m-4-4 4 4 4-4M5 20h14')} Exportar CSV</button></div>`,save:async()=>true});
 d.querySelector('[data-save]').textContent='Fechar';
 d.querySelector('[data-layer-csv]').onclick=()=>{const csv=['layer;papel;origem;confianca;entidades;alertas',...data.layers.map(r=>[r.layer,r.role||'',r.origin,r.confidence,r.entities,r.alerts.map(a=>a.code).join('|')].map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(';'))].join('\n'),a=document.createElement('a');a.href=URL.createObjectURL(new Blob(['﻿'+csv],{type:'text/csv'}));a.download='interpretacao_layers.csv';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000)};
 msg('Relatório de camadas pronto.');return d;
}
async function openCoverage(){
 requireProject();if(!await RodoviaPanels.close())return;
 const project=pid,context=projectSession.context;msg('Conferindo a cobertura das hachuras…');
 const data=await api(`/api/projects/${project}/hatch-coverage`);if(pid!==project||context!==projectSession.context)return;
 const labels={pavement:'Pavimento novo',existing_pavement:'Pavimento existente',shoulder:'Acostamento',median:'Canteiro',barrier:'Barreira',oae:'OAE',cut:'Corte',fill:'Aterro',earthwork:'Terraplenagem',water:'Água',domain:'Faixa de domínio'};
 const areas=Object.entries(data.areas_m2).map(([r,a])=>`<tr><td>${iconFor(r)} ${esc(labels[r]||r)}</td><td>${Number(a).toLocaleString('pt-BR')} m²</td></tr>`).join('');
 const over=data.overlaps.map(o=>`<tr class="${o.expected?'':'rsWarn'}"><td>${esc(labels[o.over]||o.over)} sobre ${esc(labels[o.under]||o.under)}</td><td>${o.area_m2} m²</td><td>${o.expected?'esperada':'conferir'}</td></tr>`).join('');
 const alerts=data.alerts.map(a=>`<li>${esc(a.text)}</li>`).join('');
 const d=RodoviaModelDialog.open({id:'rsHatchCoverage',title:'Cobertura e conflitos das hachuras',html:`<p>${data.summary.roles} papéis · ${data.summary.joints} juntas fechadas pelo fluxo · ${data.summary.voids} vazios largos · ${data.summary.unexpected_overlaps} sobreposições a conferir. Somente leitura.</p>${alerts?`<ul>${alerts}</ul>`:'<p>Nenhum alerta.</p>'}<h3>Área por papel</h3><table class="rsTable"><tbody>${areas}</tbody></table><h3>Sobreposições (prevalece o papel de cima)</h3><table class="rsTable"><tbody>${over||'<tr><td>Nenhuma.</td></tr>'}</tbody></table>`,save:async()=>true});
 d.querySelector('[data-save]').textContent='Fechar';msg('Cobertura conferida.');return d;
}
comando(['HACHURACOBERTURA'],()=>openCoverage(),'Conferir juntas, vazios e sobreposições entre hachuras');
async function openAxes(){
 requireProject();if(!await RodoviaPanels.close())return;
 const project=pid,context=projectSession.context;msg('Conferindo a continuidade dos eixos…');
 const data=await api(`/api/projects/${project}/axis-validation`);if(pid!==project||context!==projectSession.context)return;
 const rows=data.axes.map(a=>`<tr class="${a.alerts.length?'rsWarn':''}"><td>${svg(ICON.axis)} ${esc(a.name)}</td><td>${a.length_m.toLocaleString('pt-BR')} m</td><td>${a.coverage==null?'—':Math.round(a.coverage*100)+'%'}</td><td>${a.alerts.map(x=>esc(x.text)).join(' ')||esc(a.info||'OK')}</td></tr>`).join('');
 const gaps=data.section_gaps.map(g=>`<li>${esc(g.name)}: ${g.gaps.length} intervalo(s) sem seção.</li>`).join('');
 const d=RodoviaModelDialog.open({id:'rsAxisValidation',title:'Continuidade dos eixos',html:`<p>${data.summary.axes} eixos · ${data.summary.with_alerts} com alerta · ${data.summary.section_gaps} com lacunas de seção. Somente leitura.</p>${gaps?`<ul>${gaps}</ul>`:''}<div style="max-height:55vh;overflow:auto"><table class="rsTable"><thead><tr><th>Eixo</th><th>Extensão</th><th>Sobre pavimento</th><th>Situação</th></tr></thead><tbody>${rows||'<tr><td colspan="4">Nenhum eixo reconhecido.</td></tr>'}</tbody></table></div>`,save:async()=>true});
 d.querySelector('[data-save]').textContent='Fechar';msg('Eixos conferidos.');return d;
}
comando(['EIXOSVALIDAR'],()=>openAxes(),'Conferir se os eixos estão sobre o pavimento e sem lacunas');
comando(['LAYERSRELATORIO'],()=>open(),'Mostrar como o motor interpretou cada camada do desenho');
queueMicrotask(()=>{for(const group of document.querySelectorAll('[data-rs-group="Áreas e sinalização"]')){const b=document.createElement('button');b.type='button';b.dataset.rsCommand='LAYERSRELATORIO';b.title='Interpretação das camadas';b.setAttribute('aria-label',b.title);b.innerHTML=svg('M12 3 3 8l9 5 9-5zM3 13l9 5 9-5M3 17l9 5 9-5');b.onclick=guard(()=>open());group.appendChild(b);const c=document.createElement('button');c.type='button';c.dataset.rsCommand='HACHURACOBERTURA';c.title='Cobertura das hachuras';c.setAttribute('aria-label',c.title);c.innerHTML=svg('M3 3h18v18H3zM3 9h18M3 15h18M9 3v18M15 3v18');c.onclick=guard(()=>openCoverage());group.appendChild(c);const x=document.createElement('button');x.type='button';x.dataset.rsCommand='EIXOSVALIDAR';x.title='Continuidade dos eixos';x.setAttribute('aria-label',x.title);x.innerHTML=svg('M3 12h4m3 0h4m3 0h4M12 5v2m0 10v2');x.onclick=guard(()=>openAxes());group.appendChild(x)}});
window.RodoviaLayerReport=Object.freeze({open,openCoverage,openAxes});
})();
