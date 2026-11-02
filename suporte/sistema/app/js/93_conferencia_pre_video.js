// 1.42.43: conferência antes do vídeo — semáforo verde/amarelo/vermelho + materiais usados. Somente leitura.
(()=>{'use strict';
const LEVEL={green:{ic:'🟢',t:'Pronto: nenhum impedimento encontrado.'},yellow:{ic:'🟡',t:'Atenção: o vídeo sai, mas há pontos a conferir.'},red:{ic:'🔴',t:'Impedimento: algo essencial falta e o vídeo pode sair sem veículos ou sem eixo.'}};
const CRITICAL=new Set(['papel_ausente','sem_dxf','sem_pavimento','vazios']);
// Pura: junta os alertas dos relatórios e devolve o nível.
function judge(parts){const items=[];let level='green';
 for(const [src,alerts] of Object.entries(parts||{}))for(const a of alerts||[]){const crit=CRITICAL.has(a.code);items.push({src,code:a.code,text:a.text,level:crit?'red':'yellow'});if(crit)level='red';else if(level==='green')level='yellow'}
 return {level,items}}
function materials(model){const out=[];const cnt=(L,keyFn)=>{const m=new Map();for(const o of L||[]){if(o.enabled===false)continue;const k=keyFn(o);m.set(k,(m.get(k)||0)+1)}return m};
 for(const [k,n] of cnt(model?.pavement_areas,o=>`${(typeof PAV_LABEL!=='undefined'?PAV_LABEL:{})[o.kind]||o.kind||'Pista'} — ${(typeof MAT_LABEL!=='undefined'?MAT_LABEL:{})[o.material||'auto']||o.material||'automático'}${o.texture?' · textura própria':''}`))out.push({kind:'Área de pista',name:k,n});
 for(const [k,n] of cnt(model?.texture_areas,o=>`${(typeof SURF_NAME!=='undefined'?SURF_NAME:{})[o.surface]||o.surface}${o.texture?' · textura própria':''}`))out.push({kind:'Região de textura',name:k,n});
 return out}
const T={judge,materials};if(typeof module!=='undefined'&&module.exports)module.exports=T;
if(typeof window==='undefined')return;
async function open(){
 requireProject();if(!await RodoviaPanels.close())return;
 const project=pid,context=projectSession.context;msg('Conferindo o projeto antes do vídeo…');
 const get=p=>api(`/api/projects/${project}/${p}`);
 const [lr,hc,ax]=await Promise.allSettled([get('layer-report'),get('hatch-coverage'),get('axis-validation')]);
 if(pid!==project||context!==projectSession.context)return;
 const parts={'Camadas':lr.value?.alerts,'Hachuras':hc.value?.alerts,'Eixos':ax.value?.axes?.flatMap(a=>a.alerts.map(x=>({code:x.code,text:`${a.name}: ${x.text}`})))};
 const failed=[['Camadas',lr],['Hachuras',hc],['Eixos',ax]].filter(([,r])=>r.status==='rejected').map(([n])=>n);
 const j=judge(parts),L=LEVEL[j.level],mats=materials(M);
 const rows=j.items.map(i=>`<li>${LEVEL[i.level].ic} <b>${esc(i.src)}</b> — ${esc(i.text)}</li>`).join('');
 const mrows=mats.length?mats.map(m=>`<tr><td>${esc(m.kind)}</td><td>${esc(m.name)}</td><td>${m.n}</td></tr>`).join(''):'<tr><td colspan="3" class="muted">Sem áreas editadas: valem o material e as texturas padrão do projeto e das hachuras do desenho.</td></tr>';
 const d=RodoviaModelDialog.open({id:'rsPreVideo',title:'Conferência antes do vídeo',html:`<p style="font-size:1.1em">${L.ic} <b>${esc(L.t)}</b></p>${failed.length?`<p class="muted">Não consegui ler: ${esc(failed.join(', '))}.</p>`:''}${rows?`<ul>${rows}</ul>`:''}<h4>🧱 Materiais e texturas que o vídeo vai usar</h4><table class="rsTable"><thead><tr><th>Tipo</th><th>Material / textura</th><th>Áreas</th></tr></thead><tbody>${mrows}</tbody></table><p class="muted">Somente leitura. Nada é alterado no projeto.</p>`});
 {const sv=d.querySelector('[data-save]'),fc=sv.cloneNode(true);fc.textContent='Fechar';fc.title='Fecha a conferência (somente leitura; nada é gravado)';sv.replaceWith(fc);fc.addEventListener('click',()=>{d.close();d.remove()})}   // 2.36: janela só de leitura — 'Fechar' fecha de verdade (antes tentava gravar e ficava aberta)
 msg(`Conferência: ${L.ic}`);return d}
comando(['CONFERIR','PREVIDEO'],()=>open(),'Conferência antes do vídeo: semáforo e materiais usados');
try{itemFaixa('Vídeo','Gerar',['Conferir antes do vídeo','🚦',()=>open(),1])}catch(_e){window.RodoviaErros&&RodoviaErros.avisar('conferencia_pre_video',_e)}
})();
