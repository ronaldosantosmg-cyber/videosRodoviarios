// 2.29: Central do projeto. Mostra entradas, derivados e resultados, avisa quando o DXF mudou e faz limpeza protegida
// (arquivos vão para _limpeza e podem ser restaurados). Nenhum comando existente foi alterado.
(()=>{'use strict';
 const fmt=b=>b>=1048576?(b/1048576).toFixed(1)+' MB':b>=1024?(b/1024).toFixed(0)+' KB':b+' B';
 const ESC={resultados:'Limpar resultados',derivados:'Limpar derivados',dxf_novo:'Novo DXF'};
 let ultimo=null;
 async function ler(){if(typeof pid==='undefined'||!pid)throw new Error('Abra um projeto.');return ultimo=await api(`/api/projects/${pid}/central`)}
 function tabela(t,l){return l.length?`<table style="font-size:12px;margin:4px 0 10px"><tr><th>${t}</th><th>Tamanho</th><th>Estado</th></tr>${l.map(x=>`<tr><td>${esc(x.nome)}</td><td>${fmt(x.bytes)}</td><td>${x.desatualizado?'<span style="color:#ffdda5">desatualizado</span>':x.modificado?'em dia':(x.sha12||'')}</td></tr>`).join('')}</table>`:`<p class="muted" style="margin:4px 0 10px">${t}: nada gerado.</p>`}
 async function abrir(){
  let e;try{e=await ler()}catch(err){if(typeof msg==='function')msg(String(err.message||err),true);return}
  let d=document.getElementById('rsCentral');if(d)d.remove();
  d=document.createElement('dialog');d.id='rsCentral';d.className='rsPaleta';d.style.padding='18px';d.style.maxWidth='720px';
  d.innerHTML='<h3 style="margin:0 0 8px">Central do projeto</h3>'+
   (e.alertas.length?e.alertas.map(a=>`<p style="color:#ffdda5;margin:0 0 8px">${esc(a)}</p>`).join(''):'<p class="muted" style="margin:0 0 8px">Tudo em dia: nenhuma pendência encontrada.</p>')+
   tabela('Entradas (nunca apagadas)',e.entradas)+tabela('Derivados (recalculáveis)',e.derivados)+tabela('Resultados (recalculáveis)',e.resultados)+
   `<p class="muted" style="margin:0 0 8px">Proteção: ${e.protecao.copias_de_configuracao} cópia(s) de configuração · ${e.protecao.limpezas_restauraveis.length} limpeza(s) restaurável(is). Nada é apagado: os arquivos vão para a pasta _limpeza do projeto.</p>`+
   '<div class="row" style="margin-top:10px">'+Object.entries(ESC).map(([k,t])=>`<button type="button" data-esc="${k}" title="${esc(e.escopos[k].rotulo)}">${t}</button>`).join('')+'<button type="button" id="rsCenUndo">Desfazer última limpeza</button><button type="button" id="rsCenFechar" class="primary" style="margin-left:auto">Fechar</button></div><div id="rsCenSaida" class="muted" style="margin-top:10px"></div>';
  document.body.appendChild(d);d.showModal();
  const saida=d.querySelector('#rsCenSaida');
  d.querySelector('#rsCenFechar').onclick=()=>d.close();
  d.querySelectorAll('[data-esc]').forEach(b=>b.onclick=async()=>{
   try{const k=b.dataset.esc;const sim=await api(`/api/projects/${pid}/central/limpar`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({escopo:k,confirmar:false})});
    const ok=await (typeof confirmBox==='function'?confirmBox(`${ESC[k]}: ${sim.movidos.length} item(ns) irão para a pasta _limpeza (${sim.movidos.join(', ')||'nada'})`+(Object.values(sim.escolhas_removidas).some(Boolean)?` e ${Object.values(sim.escolhas_removidas).reduce((a,b)=>a+b,0)} escolha(s) antiga(s) de eixo serão removidas`:'')+'. Dá para desfazer. Continuar?','Limpar','Cancelar'):Promise.resolve(true));
    if(!ok)return;
    try{if(typeof checkpoint==='function')checkpoint()}catch(_e){}
    const r=await api(`/api/projects/${pid}/central/limpar`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({escopo:k,confirmar:true})});
    if(r.config&&typeof cfg!=='undefined')cfg.route_directions=r.config.route_directions;if(typeof FLUXO!=='undefined')FLUXO.sync();
    saida.textContent=`Feito: ${r.movidos.length} item(ns) movidos para _limpeza/${r.pasta}. Gere a análise/prévia novamente.`;if(typeof msg==='function')msg(saida.textContent)}
   catch(err){saida.textContent=String(err.message||err);window.RodoviaErros&&RodoviaErros.avisar('central',err)}});
  d.querySelector('#rsCenUndo').onclick=async()=>{try{const r=await api(`/api/projects/${pid}/central/desfazer`,{method:'POST'});if(typeof cfg!=='undefined'&&r.config)cfg.route_directions=r.config.route_directions;if(typeof FLUXO!=='undefined')FLUXO.sync();saida.textContent='Limpeza restaurada: '+r.restaurada}catch(err){saida.textContent=String(err.message||err)}}}
 // aviso discreto ao abrir um projeto: só quando há pendência
 let visto='';
 async function vigiar(){try{if(typeof pid==='undefined'||!pid||pid===visto)return;visto=pid;const e=await ler();if(e.alertas.length&&typeof msg==='function')msg('Central: '+e.alertas[0]+' (comando CENTRAL)',true)}catch(err){window.RodoviaErros&&RodoviaErros.avisar('central',err)}}
 if(typeof setInterval==='function'&&typeof document!=='undefined')setInterval(vigiar,4000);
 if(typeof comando==='function'&&typeof COMANDOS!=='undefined'&&!COMANDOS.has('CENTRAL'))comando(['CENTRAL','CENTRALPROJETO'],abrir,'Central do projeto: entradas, derivados e resultados, alertas de DXF novo e limpeza protegida com desfazer');
 const api_={abrir,ler};if(typeof window!=='undefined')window.RodoviaCentral=api_;if(typeof globalThis!=='undefined')globalThis.RodoviaCentral=api_;
})();
