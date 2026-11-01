// 2.23: painel único "Via" (presets) e "Gerar tráfego" (semente + densidade). Usa o mesmo modelo das seções tipo.
(()=>{'use strict';
const PRESET_VISUAL={
 pista_simples:{b:[['p','←'],['p','→']]},
 pista_simples_adicional:{b:[['p','←'],['p','→'],['p','→']]},
 duplicada_canteiro:{b:[['p','←'],['p','←'],['m',''],['p','→'],['p','→']]},
 um_sentido_meio:{b:[['p','→'],['p','→']],eixo:1},
 um_sentido_bordo:{b:[['p','→'],['p','→']],eixo:0},
 ramal:{b:[['p','→']]},
 rotatoria:{b:[['p','↻']]}};
const COR={p:'#64748b',m:'#4b9a5a',a:'#b8a68b'};
function miniatura(id){const v=PRESET_VISUAL[id]||{b:[['p','→']]},w=34,h=22,n=v.b.length,total=n*w+8;let x=4;
 const rects=v.b.map(([k,t])=>{const r=`<rect x="${x}" y="8" width="${w}" height="${h}" fill="${COR[k]}" stroke="#fff" stroke-width="1"/><text x="${x+w/2}" y="${8+h/2+4}" text-anchor="middle" fill="#fff" font-size="12">${t}</text>`;x+=w;return r}).join('');
 const ex=v.eixo===0?4:v.eixo===1?4+(n/2)*w:id==='duplicada_canteiro'?4+(n/2)*w:id==='pista_simples'||id==='pista_simples_adicional'?4+w:null;
 return `<svg viewBox="0 0 ${total} 40" width="${total}" height="40" role="img" aria-hidden="true">${rects}${ex!=null?`<line x1="${ex}" y1="3" x2="${ex}" y2="36" stroke="#f4c846" stroke-width="2"/><text x="${ex}" y="2" font-size="6" text-anchor="middle" fill="currentColor">eixo</text>`:''}</svg>`}
const NOME_SENTIDO=RodoviaGlossario.rota;
async function abrirVia(){
 requireProject();if(!await RodoviaPanels.close())return;
 const project=pid,context=projectSession.context;
 const [axesData,catalog]=await Promise.all([api(`/api/projects/${pid}/traffic-axes`),api('/api/via/presets')]);
 if(pid!==project||context!==projectSession.context)return;
 const existentes=M.route_alignments||[],axes=axesData.axes;
 if(!axes.length&&!existentes.length)throw Error('Nenhum eixo encontrado. Em Camadas, designe a camada Eixo.');
 const ligada=a=>existentes.find(r=>r.source_axis_fingerprint===a.fingerprint);
 const html=`<p>Escolha o eixo e o <b>tipo de via</b>. Um clique monta as faixas, os acostamentos, o sentido e o canteiro; depois você pode refinar em “Seções tipo”.</p>
 <label>Eixo<select name="eixo">${axes.map((a,i)=>`<option value="${i}">${esc(a.name)} · ${a.length_m?Math.round(a.length_m)+' m':''}${ligada(a)?' · já configurado':''}</option>`).join('')}</select></label>
 <div class="rsViaGaleria" role="radiogroup" aria-label="Tipo de via">${catalog.presets.map((p,i)=>`<label class="rsViaCard"><input type="radio" name="preset" value="${p.id}" ${i===0?'checked':''}><span class="rsViaMini">${miniatura(p.id)}</span><b>${esc(p.nome)}</b><small>${esc(p.descricao)}</small></label>`).join('')}</div>
 <div class="grid"><label>Faixas por sentido (ou total, em um só sentido)<input name="faixas" type="number" min="1" max="4" value="1"></label><label>Largura da faixa (m)<input name="largura" type="number" min="2.5" max="5" step=".1" value="3.5"></label><label>Acostamento (m; 0 = sem)<input name="acostamento" type="number" min="0" max="5" step=".1" value="2.5"></label><label data-canteiro>Canteiro (m)<input name="canteiro" type="number" min="0" max="60" step=".5" value="3"></label><label>Sentido<select name="sentido">${Object.entries(NOME_SENTIDO).map(([k,t])=>`<option value="${k}">${t}</option>`).join('')}</select></label><label>Velocidade (km/h; vazio = automática)<input name="velocidade" type="number" min="5" max="130" step="5"></label></div>
 <p data-via-resumo aria-live="polite"></p><p data-error role="alert"></p>`;
 const d=RodoviaModelDialog.open({id:'rsVia',title:'Via — tipo de pista e faixas',html,calculate:true,save:async()=>{
  const {route}=await montar();if(!d.rsContext())throw Error('O projeto mudou. Reabra a janela.');
  await api('/api/modelagem/validate',json('POST',{...collect(),route_alignments:substituir(route)}));
  checkpoint();M.route_alignments=substituir(route);changed('Via configurada. Use “Gerar tráfego” para atualizar os fluxos.');await save();refreshRouteLanes(true);return true}});
 const el=n=>d.querySelector(`[name=${n}]`),erro=e=>{d.querySelector('[data-error]').textContent=e?e.message:''};
 const eixo=()=>axes[Number(el('eixo').value)];
 const preset=()=>d.querySelector('[name=preset]:checked').value;
 function parametros(){return {faixas:Number(el('faixas').value),largura:Number(el('largura').value),acostamento:Number(el('acostamento').value),canteiro:Number(el('canteiro').value),sentido:el('sentido').value,velocidade:el('velocidade').value?Number(el('velocidade').value):null}}
 async function montar(){const a=eixo();return api('/api/via/montar',json('POST',{preset:preset(),axis:{name:a.name,points:a.points?.map?.(p=>Array.isArray(p)?{x:p[0],y:p[1]}:p)||[],fingerprint:a.fingerprint,length_m:a.length_exact_m||a.length_m,level:a.level},params:parametros(),previous:ligada(a)||null}))}
 function substituir(route){const lista=(M.route_alignments||[]).filter(r=>r.id!==route.id&&!(route.source_axis_fingerprint&&r.source_axis_fingerprint===route.source_axis_fingerprint));return [...lista,route]}
 function aplicarPreset(){const p=catalog.presets.find(x=>x.id===preset());if(!p)return;el('faixas').value=p.faixas;el('acostamento').value=p.acostamento;el('canteiro').value=p.canteiro||3;
  d.querySelector('[data-canteiro]').hidden=preset()!=='duplicada_canteiro';el('faixas').disabled=preset()==='pista_simples'||preset()==='pista_simples_adicional'}
 let t=null;function resumo(){clearTimeout(t);t=setTimeout(async()=>{try{const r=await montar();erro(null);const n=r.lanes.length,f=r.lanes.filter(l=>l.direction==='f').length;d.querySelector('[data-via-resumo]').textContent=`${n} faixa(s) de circulação (${f} no sentido do desenho, ${n-f} no sentido contrário).`}catch(e){d.querySelector('[data-via-resumo]').textContent='';erro(e)}},250)}
 d.addEventListener('change',e=>{if(e.target.name==='preset')aplicarPreset();resumo()});d.addEventListener('input',resumo);
 aplicarPreset();resumo();return d}

function abrirGerar(){
 requireProject();
 const html=`<p>Gera os fluxos de tráfego com a configuração atual das vias. A <b>semente</b> define a sequência aleatória de veículos: mesma semente, mesma animação.</p>
 <div class="grid"><label>Semente<input name="semente" type="number" min="0" max="1000000000" value="${Number(cfg.traffic_seed??1729)}"></label><label>Densidade de veículos (0,2 a 8)<input name="densidade" type="number" min="0.2" max="8" step="0.1" value="${Number(cfg.traffic_density??1)}"></label></div>
 <button type="button" data-sortear>Sortear nova semente</button><p data-error role="alert"></p>`;
 const d=RodoviaModelDialog.open({id:'rsGerarTrafego',title:'Gerar tráfego',html,save:async()=>{
  const seed=Math.round(Number(d.querySelector('[name=semente]').value)),dens=Number(d.querySelector('[name=densidade]').value);
  if(!Number.isInteger(seed)||seed<0||seed>1e9)throw Error('Semente inválida (0 a 1.000.000.000).');if(!(dens>=.2&&dens<=8))throw Error('Densidade entre 0,2 e 8.');
  checkpoint();cfg.traffic_seed=seed;cfg.traffic_density=dens;changed('Parâmetros do tráfego atualizados.');await save();
  setTimeout(async()=>{const ok=await start('analyze');if(ok!==false){msg(`Tráfego gerado · semente ${seed} · densidade ${dens}.`);try{resumo(seed,dens)}catch(_e){window.RodoviaErros&&RodoviaErros.avisar('via_painel',_e)}}},0);return true}});
 d.querySelector('[data-save]').textContent='Gerar tráfego';
 d.querySelector('[data-sortear]').onclick=()=>{d.querySelector('[name=semente]').value=Math.floor(Math.random()*1e9);d.rsDirty?.()};
 return d}

function dadosResumo(){
 const e=(typeof editor!=='undefined'&&editor)||{},paths=e.paths||[],seg=e.segments||[];
 const porTipo={};for(const p of paths){const k=(p.kinds&&p.kinds[0])||'main';porTipo[k]=(porTipo[k]||0)+1}
 const cortes=seg.filter(s=>s.technical_status&&s.technical_status!=='ok'),desab=seg.filter(s=>s.disabled).length;
 return {faixas:paths.length,porTipo,segmentos:seg.length,cortes:cortes.length,desativados:desab,ligacoes:(e.connections||[]).length,negadas:(e.denied||[]).length,
  ultrapassagem:(e.passing_zones||[]).length,sem_pavimento:(e.ghost_zones||[]).length,alertas:(e.warnings||[]).length}}
const NOME_TIPO={main:'principal',marginal:'marginal',return:'retorno',device:'dispositivo',access:'acesso'};
function resumo(seed,dens){
 const r=dadosResumo(),tipos=Object.entries(r.porTipo).map(([k,v])=>`${v} ${NOME_TIPO[k]||k}`).join(', ')||'nenhuma';
 const ok=r.cortes===0;
 const html=`<p><b>${r.faixas}</b> faixa(s) de circulação: ${esc(tipos)}.</p><ul><li>Semente ${esc(String(seed))} · densidade ${esc(String(dens))}</li><li>${r.ligacoes} ligação(ões) entre trechos${r.negadas?` · ${r.negadas} proibida(s)`:''}</li><li>${r.ultrapassagem} trecho(s) onde a ultrapassagem pela pista contrária é permitida</li><li>${r.sem_pavimento} vão(s) sem pavimento tratados como fantasma</li></ul>
 <p role="status" style="font-weight:600;color:${ok?'#14803f':'#b45309'}">${ok?'Nenhum corte de fluxo encontrado.':r.cortes+' trecho(s) com corte ou problema de fluxo — veja o motivo de cada um no mapa.'}</p>
 <div class="row"><button type="button" data-resumo="DIAGNOSTICARVEICULOS">Ver cortes no mapa</button><button type="button" data-resumo="CORRIGIRFLUXOS">Corrigir fluxos…</button><button type="button" data-resumo="ANIMARFLUXOS">Animar fluxos</button></div>`;
 const d=RodoviaModelDialog.open({id:'rsResumoTrafego',title:'Resumo do tráfego',html,save:async()=>true});
 d.querySelector('[data-save]').textContent='Fechar';
 d.addEventListener('click',e=>{const b=e.target.closest('[data-resumo]');if(!b)return;d.close?.();setTimeout(()=>{try{runCommand(b.dataset.resumo)}catch(err){msg(err.message,true)}},50)});
 return d}
window.RodoviaResumoTrafego=Object.freeze({dados:dadosResumo});
comando(['VIA','TIPOVIA'],()=>guard(abrirVia)(),'Via: escolhe o tipo de pista (simples, duplicada, um só sentido, ramal, rotatória) e monta as faixas');
comando(['RESUMOTRAFEGO'],()=>resumo(Number(cfg.traffic_seed??1729),Number(cfg.traffic_density??1)),'Resumo do último cálculo de tráfego: faixas, ligações, cortes e atalhos de correção');
comando(['GERARTRAFEGO','TRAFEGO'],()=>abrirGerar(),'Gerar tráfego: semente, densidade e cálculo dos fluxos em um passo');
queueMicrotask(()=>{for(const group of document.querySelectorAll('[data-rs-group="Fluxos de tráfego"]')){
 for(const [cmd,titulo,icone,acao] of [['VIA','Via — tipo de pista e faixas','M3 19h18M5 17V9h5v8M14 17V9h5v8M7.5 6v6m-2-2 2 2 2-2','abrirVia'],['GERARTRAFEGO','Gerar tráfego (semente e densidade)','M5 4l14 8-14 8z',null]]){
  const b=document.createElement('button');b.type='button';b.dataset.rsCommand=cmd;b.title=titulo;b.setAttribute('aria-label',titulo);b.innerHTML=`<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="${icone}"/></svg>`;b.onclick=acao?guard(abrirVia):()=>abrirGerar();group.appendChild(b)}}});
window.RodoviaVia=Object.freeze({abrirVia,abrirGerar});
})();
