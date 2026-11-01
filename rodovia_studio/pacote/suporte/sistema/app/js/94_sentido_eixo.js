// 2.33: sentido POR EIXO (reconstruído). Cada eixo tem a sua linha e grava só a sua chave (FLUXO.definir); nada é copiado para os outros.
// "Definir para todos…" só preenche as linhas na tela; você confere e aplica. Regras antigas por layer aparecem e podem ser removidas.
(()=>{'use strict';
 const OPC=RodoviaGlossario.opcoes();
 const ORG={seta:'seta desenhada',rota:'rota cadastrada',oae:'OAE',eixo:'escolha do eixo',layer:'regra do layer',auto:'automático'};
 let fresco=null,relat=null;
 const e_=s=>typeof esc==='function'?esc(s):String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function eixos(){const base=fresco?fresco.axes:[];return base.map(a=>({chave:a.direction_key,idx:a.index,layer:a.name,m:Number(a.length_m)||0,ef:(relat?.eixos||[]).find(x=>x.chave===a.direction_key)}))}
 function rumo(i){const segs=(typeof editor!=='undefined'&&editor?.segments||[]).filter(sg=>{const m=String(sg.source||'').match(/Eixo DXF · ([\d,]+)/);return m&&m[1].split(',').includes(String(i))&&!sg.disabled});
  if(!segs.length)return '';let dx=0,dy=0;for(const sg of segs){const P=sg.points||[];if(P.length<2)continue;const a=P[0],b=P[P.length-1],f=sg.forward?1:-1;dx+=f*(b[0]-a[0]);dy+=f*(b[1]-a[1])}
  if(!isFinite(dx)||!isFinite(dy)||Math.hypot(dx,dy)<1)return '';const ang=(Math.atan2(dx,dy)*180/Math.PI+360)%360,nomes=['Norte','Nordeste','Leste','Sudeste','Sul','Sudoeste','Oeste','Noroeste'];return nomes[Math.round(ang/45)%8]}
 function resumo(layer){const rs=eixos().filter(r=>r.layer===layer);return {n:rs.length,km:rs.reduce((a,r)=>a+r.m,0)/1000,chaves:rs.map(r=>r.chave)}}
 // compatibilidade (testes e chamadas antigas): aplica a regra de LAYER pela fonte única
 function aplicar(c,layer,valor,limparEixos){const antes=typeof cfg!=='undefined'?cfg:null;const rd={...(c.route_directions||{})};const k='layer:'+layer;if(valor==='auto')delete rd[k];else rd[k]=valor;if(limparEixos)for(const ch of resumo(layer).chaves)delete rd[ch];c.route_directions=rd;return rd}
 function camadas(){return [...new Set(eixos().map(a=>a.layer).filter(Boolean))].sort()}
 async function abrir(){
  if(typeof document==='undefined')return;
  try{if(typeof pid!=='undefined'&&pid&&typeof api==='function'){fresco=await api(`/api/projects/${pid}/traffic-axes?include_short=true`);relat=await api(`/api/projects/${pid}/direction-report`)}}catch(e){fresco=null;window.RodoviaErros&&RodoviaErros.avisar('sentido eixo',e)}
  const lista=eixos();
  if(!lista.length){if(typeof msg==='function')msg('Nenhum eixo encontrado. Analise os arquivos e defina o papel “Eixo” nos layers.',true);return}
  const rd=FLUXO.todos();
  let d=document.getElementById('rsSentidoEixo');if(d)d.remove();
  d=document.createElement('dialog');d.id='rsSentidoEixo';d.className='rsPaleta';d.style.padding='18px';d.style.maxWidth='720px';
  const grupos={};lista.forEach((a,i)=>{(grupos[a.layer]=grupos[a.layer]||[]).push([a,i])});
  const opt=v=>OPC.map(([k,t])=>`<option value="${k}" ${k===v?'selected':''}>${t}</option>`).join('');
  const orf=fresco?.diagnostics?.orphan_keys||0;
  d.innerHTML='<h3 style="margin:0 0 6px">Sentido de cada eixo</h3><p class="muted" style="margin:0 0 10px">Cada eixo tem a sua própria escolha. Crescente segue o km; Decrescente inverte. Mudar um eixo não altera os outros.</p>'+(cfg.reverse_axis?'<p style="color:#ffdda5;margin:0 0 10px">“Inverter início e fim do eixo” está LIGADO: isso vale para todos os eixos de uma vez e faz Crescente correr contra o desenho. Confira o rumo mostrado em cada eixo.</p>':'')+
   (orf?`<p style="color:#ffdda5;margin:0 0 10px">${orf} escolha(s) antiga(s) não correspondem a nenhum eixo do desenho atual e serão removidas ao aplicar.</p>`:'')+
   Object.entries(grupos).map(([layer,linhas])=>{const regra=rd['layer:'+layer];
    return `<fieldset style="margin:10px 0;border:1px solid #fff3;border-radius:8px;padding:8px 10px"><legend><b>${e_(layer)}</b> <small class="muted">${linhas.length} eixo(s)</small></legend>`+
     (linhas.length>1?`<label style="display:block;margin:2px 0 6px"><small>Definir para todos os eixos deste layer (só preenche as linhas; confira e aplique):</small> <select data-todos="${e_(layer)}"><option value="">— escolher —</option>${OPC.map(([k,t])=>`<option value="${k}">${t}</option>`).join('')}</select></label>`:'')+
     (['forward','reverse','off'].includes(regra)?`<p style="margin:2px 0 6px;color:#ffdda5"><small>Regra antiga do layer: ${e_(OPC.find(o=>o[0]===regra)[1])} (vale só para eixos sem escolha própria). <label><input type="checkbox" data-rm-regra="${e_(layer)}"> remover esta regra</label></small></p>`:'')+
     linhas.map(([a,i])=>{const v=['forward','reverse','off'].includes(rd[a.chave])?rd[a.chave]:'auto',ef=a.ef;
      return `<div style="display:flex;gap:10px;align-items:center;margin:4px 0"><span style="flex:1">Eixo ${i+1} · ${a.m.toFixed(0)} m</span><select data-eixo="${i}" data-orig="${v}">${opt(v)}</select><small class="muted" data-vale="${i}" style="flex:1.2">${ef?`vale: <b>${e_(ef.rotulo)}</b> (${e_(ORG[ef.origem]||ef.origem)})${rumo(a.idx)?' · circula para <b>'+rumo(a.idx)+'</b>':''}${ef.conflitos?.length?' · '+e_(ef.conflitos.join('; ')):''}`:''}</small></div>`}).join('')+'</fieldset>'}).join('')+
   '<div class="row" style="margin-top:14px;justify-content:flex-end"><button type="button" id="rsSeCancel">Cancelar</button><button type="button" class="primary" id="rsSeOk">Aplicar e recalcular fluxos</button></div>';
  document.body.appendChild(d);d.showModal();
  d.querySelector('#rsSeCancel').onclick=()=>d.close();
  d.addEventListener('change',ev=>{const t=ev.target.closest&&ev.target.closest('select[data-todos]');if(!t||!t.value)return;
   const idx=new Set(grupos[t.dataset.todos].map(([,i])=>String(i)));d.querySelectorAll('select[data-eixo]').forEach(s=>{if(idx.has(s.dataset.eixo))s.value=t.value});t.value=''});
  d.querySelector('#rsSeOk').onclick=()=>{
   try{if(typeof checkpoint==='function')checkpoint()}catch(_e){}
   let mudou=0;
   try{
    d.querySelectorAll('select[data-eixo]').forEach(s=>{if(s.value===s.dataset.orig)return;FLUXO.definir(lista[Number(s.dataset.eixo)].chave,s.value);mudou++});
    d.querySelectorAll('input[data-rm-regra]').forEach(c=>{if(!c.checked)return;const rd2=FLUXO.todos();delete rd2['layer:'+c.dataset.rmRegra];cfg.route_directions=rd2;FLUXO.sync();mudou++});
    if(fresco){const n=FLUXO.limparOrfas(new Set(fresco.axes.map(a=>a.direction_key)));mudou+=n}
    if(typeof scheduleSave==='function')scheduleSave();if(typeof showRouteChoices==='function')showRouteChoices()
   }catch(err){window.RodoviaErros&&RodoviaErros.avisar('sentido eixo',err);if(typeof msg==='function')msg('Não foi possível aplicar: '+(err.message||err),true);return}
   d.close();if(typeof msg==='function')msg(mudou?'Sentido salvo. Recalculando fluxos…':'Nada mudou.');
   if(mudou){try{runCommand('CALCULARFLUXOS')}catch(err){window.RodoviaErros&&RodoviaErros.avisar('sentido eixo',err)}}}}
 if(typeof document!=='undefined'){const cb=document.getElementById('reverse_axis');if(cb&&!cb.dataset.avisoFluxo){cb.dataset.avisoFluxo='1';cb.addEventListener('change',()=>{if(typeof msg==='function')msg('Atenção: “Inverter início e fim do eixo” muda o sentido de TODOS os eixos de uma vez. Para um eixo só, use Sentido de cada eixo (SENTIDOEIXO).',true)})}}
 if(typeof comando==='function'&&typeof COMANDOS!=='undefined'&&!COMANDOS.has('SENTIDOEIXO'))
  comando(['SENTIDOEIXO','SENTIDOLAYER'],abrir,'Define o sentido (crescente, decrescente, sem veículos) de cada eixo, separadamente');
 const api={abrir,aplicar,camadas,resumo,rumo};if(typeof window!=='undefined')window.RodoviaSentidoEixo=api;if(typeof globalThis!=='undefined')globalThis.RodoviaSentidoEixo=api;
})();
