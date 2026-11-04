// Rodovia Studio 1.0 — Barra de comandos sob o menu principal.
// Botões agrupados por finalidade (mesmos nomes dos menus), com ícones do pacote do usuário.
// O usuário escolhe quais aparecem e a ordem; a escolha fica neste navegador. Nenhuma ação é duplicada:
// cada botão chama o item do menu de mesmo nome, então menu e barra nunca divergem.
(()=>{'use strict';
const KEY='rodovia_barra_v1';
const GRUPOS=[
 ['Arquivo',[['Novo projeto','projeto-novo'],['Abrir projeto…','projeto-abrir'],['Salvar','projeto-salvar'],['Salvar como…','projeto-salvar-como'],['Exportar e importar…','projeto-exportar'],['Proteção e recuperação de dados','operacoes-backup']]],
 ['Editar',[['Desfazer','editar-desfazer'],['Refazer','editar-refazer'],['Mover','editar-mover'],['Girar','editar-girar'],['Copiar','editar-copiar'],['Apagar','editar-apagar'],['TRIM — ocultar trecho da linha','editar-recortar-segmento'],['Inserir vértice','editar-inserir-ponto'],['Enquadrar','navegacao-enquadrar-projeto']]],
 ['Cálculo',[['Escolher eixo e configurar faixas','eixos-secao-tipica'],['Gerar e visualizar','trafego-gerar-fluxos'],['Testar circulação','operacoes-verificar-integridade'],['Central de correção dos fluxos','correcao-diagnostico'],['Conferir classificação e contornos','correcao-localizar-conflito']]],
 ['Engenharia',[['Alinhamento (cliques)','precisao-alinhar'],['Zebrado','sinalizacao-zebrado-amarelo'],['Placa','sinalizacao-placa'],['Faixa de pedestre','sinalizacao-faixa-pedestres'],['OAE (2 pontos)','cena-oae-ponte'],['Semáforo','sinalizacao-semaforo'],['Ferrovia','ferrovia-criar-ferrovia'],['Sentido','trafego-sentido-unico']]],
 ['Cenas e Vídeo',[['Preparar Rodovia Studio','projeto-configuracoes'],['Gerar vídeo','video-gerar-video'],['Dia e noite','cena-dia-e-noite'],['Materiais e texturas','cena-texturas'],['Clima e sol','cena-clima-sol'],['Configurar','video-configurar-camera'],['Prévia no instante','video-previa'],['Vídeos gerados…','video-abrir-pasta-de-videos'],['Vista 3D / editor 2D','navegacao-vista-3d']]],
 ['IA',[['Analisar camadas e eixos / IA','ia-assistente'],['Diagnóstico dos logs / IA','operacoes-logs']]]
];
const norm=t=>String(t||'').toLowerCase().replace(/[….\s]+$/g,'').replace(/\s+/g,' ').trim();
const esc=t=>String(t).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let cfg=null,rascunho=null;
const ler=()=>{try{return JSON.parse(localStorage.getItem(KEY)||'null')}catch{return null}};
const gravar=c=>{try{localStorage.setItem(KEY,JSON.stringify(c));return true}catch{return false}};
const padrao=()=>({grupos:GRUPOS.map(([g,it])=>({g,it:it.map(([t])=>({t,on:true}))})),todas:false});
function valida(c){ // reconcilia com o catálogo: remove nomes que não existem mais e acrescenta os novos
 const base=padrao();if(!c||!Array.isArray(c.grupos))return base;
 const out={todas:!!c.todas,grupos:[]};const gs=new Map(c.grupos.map(x=>[x.g,x]));
 const ordem=[...c.grupos.map(x=>x.g).filter(g=>base.grupos.some(b=>b.g===g)),...base.grupos.map(b=>b.g).filter(g=>!gs.has(g))];
 for(const g of ordem){const b=base.grupos.find(x=>x.g===g),u=gs.get(g);const its=[];
  for(const x of (u?.it||[]))if(b.it.some(y=>y.t===x.t))its.push({t:x.t,on:x.on!==false});
  for(const y of b.it)if(!its.some(x=>x.t===y.t))its.push({...y});out.grupos.push({g,it:its})}
 return out;
}
function achar(titulo){ // procura a ação no menu atual (sempre o item vigente)
 const alvo=norm(titulo);let achado=null;
 const varre=items=>{for(const i of items||[]){if(achado)return;if(i.sub)varre(i.sub);else if(i.t&&norm(i.t)===alvo)achado=i}};
 try{for(const m of window.RodoviaMenus.definitions())varre(m.sub)}catch(_e){}
 return achado;
}
function executar(f){try{const r=f?.();if(r?.catch)r.catch(e=>{try{msg(e.message,true)}catch{}})}catch(e){try{msg(e.message,true)}catch{}}}
function icone(id){try{return window.RodoviaIconPack?.icon(id)||''}catch{return ''}}
const info=Object.fromEntries(GRUPOS.flatMap(([,it])=>it.map(([t,i])=>[t,i])));
function barra(){
 let el=document.getElementById('gsBarra');
 if(!el){el=document.createElement('div');el.id='gsBarra';el.setAttribute('role','toolbar');el.setAttribute('aria-label','Barra de comandos');
  const alvo=document.getElementById('menuBar');if(!alvo)return null;alvo.insertAdjacentElement('afterend',el)}
 return el;
}
function desenhar(c){
 const el=barra();if(!el)return;el.replaceChildren();
 for(const grp of c.grupos){const vis=grp.it.filter(x=>x.on);if(!vis.length)continue;
  const box=document.createElement('div');box.className='gsGrupo';box.setAttribute('role','group');box.setAttribute('aria-label',grp.g);
  for(const x of vis){const b=document.createElement('button');b.type='button';b.className='gsBtn';b.dataset.gsCmd=x.t;
   const rotulo=x.t.replace(/…$/,'');b.title=rotulo+' ('+grp.g+')';b.setAttribute('aria-label',rotulo);b.innerHTML=icone(info[x.t])||'<span aria-hidden="true">•</span>';
   b.onclick=()=>{const it=achar(x.t);if(!it||it.dis){try{msg('Comando indisponível agora: '+rotulo,true)}catch{}return}try{window.RodoviaMenus.close?.()}catch{}executar(it.f)};
   box.appendChild(b)}
  el.appendChild(box)}
 const cfgBtn=document.createElement('button');cfgBtn.type='button';cfgBtn.className='gsBtn gsCfg';cfgBtn.title='Personalizar a barra de comandos';cfgBtn.setAttribute('aria-label','Personalizar a barra de comandos');cfgBtn.innerHTML=icone('projeto-configuracoes')||'⚙';cfgBtn.onclick=abrir;el.appendChild(cfgBtn);
 const all=document.createElement('button');all.type='button';all.className='gsBtn gsAll';all.setAttribute('aria-pressed',String(!!c.todas));all.title='Mostrar ou ocultar a faixa completa de ferramentas';all.setAttribute('aria-label','Todas as ferramentas');all.innerHTML=(icone('camadas-camadas')||'☰')+'';
 all.onclick=()=>{cfg.todas=!cfg.todas;gravar(cfg);aplicarTodas();all.setAttribute('aria-pressed',String(cfg.todas))};el.appendChild(all);
 aplicarTodas();
}
function aplicarTodas(){document.documentElement.classList.toggle('gsFaixaCompleta',forcaFaixa??!!cfg?.todas);try{window.dispatchEvent(new Event('resize'))}catch{}}
// ---- janela de personalização: flutua sobre o desenho (não empurra o CAD) e fecha sem travar o aplicativo
function abrir(){
 if(document.getElementById('gsBarraDlg'))return;rascunho=JSON.parse(JSON.stringify(cfg));
 const d=document.createElement('div');d.id='gsBarraDlg';d.setAttribute('role','dialog');d.setAttribute('aria-label','Personalizar a barra de comandos');
 d.innerHTML='<div class="gsTit"><b>Personalizar a barra de comandos</b><button type="button" class="gsX" aria-label="Fechar" data-a="fechar">×</button></div><p class="gsDica">Marque o que deve aparecer e use as setas para mudar a posição. “Aplicar” testa na barra; “Salvar” guarda neste computador; “Fechar” descarta o que não foi salvo.</p><div class="gsLista"></div><div class="gsAcoes"><button type="button" data-a="padrao">Restaurar padrão</button><span></span><button type="button" data-a="aplicar">Aplicar</button><button type="button" data-a="salvar">Salvar</button><button type="button" data-a="fechar">Fechar</button></div>';
 document.body.appendChild(d);lista();
 d.addEventListener('click',e=>{const a=e.target.closest('[data-a]')?.dataset.a;if(a==='fechar'){fechar(true)}else if(a==='aplicar'){cfg=valida(rascunho);desenhar(cfg)}else if(a==='salvar'){cfg=valida(rascunho);const ok=gravar(cfg);desenhar(cfg);try{msg(ok?'Barra de comandos salva.':'Não foi possível gravar neste navegador; a barra vale só nesta sessão.',!ok)}catch{}fechar(false)}else if(a==='padrao'){rascunho=padrao();rascunho.todas=cfg.todas;lista()}
  const m=e.target.closest('[data-mv]');if(m){const [gi,ii,dir]=m.dataset.mv.split(',').map(Number);mover(gi,ii,dir)}});
 d.addEventListener('change',e=>{const c=e.target.closest('[data-ck]');if(c){const [gi,ii]=c.dataset.ck.split(',').map(Number);rascunho.grupos[gi].it[ii].on=c.checked}});
 d.addEventListener('keydown',e=>{if(e.key==='Escape'){e.stopPropagation();fechar(true)}});d.querySelector('input,button')?.focus();
}
function mover(gi,ii,dir){const g=rascunho.grupos;if(ii<0){const j=gi+dir;if(j<0||j>=g.length)return;[g[gi],g[j]]=[g[j],g[gi]]}else{const a=g[gi].it,j=ii+dir;if(j<0||j>=a.length)return;[a[ii],a[j]]=[a[j],a[ii]]}lista()}
function lista(){const L=document.querySelector('#gsBarraDlg .gsLista');if(!L)return;
 L.innerHTML=rascunho.grupos.map((g,gi)=>`<fieldset><legend>${esc(g.g)} <button type="button" data-mv="${gi},-1,-1" aria-label="Subir grupo ${esc(g.g)}">▲</button><button type="button" data-mv="${gi},-1,1" aria-label="Descer grupo ${esc(g.g)}">▼</button></legend>${g.it.map((x,ii)=>`<label><input type="checkbox" data-ck="${gi},${ii}" ${x.on?'checked':''}><span class="gsIco">${icone(info[x.t])}</span><span>${esc(x.t.replace(/…$/,''))}</span><button type="button" data-mv="${gi},${ii},-1" aria-label="Subir">▲</button><button type="button" data-mv="${gi},${ii},1" aria-label="Descer">▼</button></label>`).join('')}</fieldset>`).join('')}
function fechar(){rascunho=null;document.getElementById('gsBarraDlg')?.remove();document.getElementById('gsBarra')?.querySelector('.gsCfg')?.focus()}
const css=document.createElement('style');css.id='gsBarraCss';css.textContent=`
#gsBarra{display:flex;flex-wrap:wrap;align-items:center;gap:4px 10px;padding:4px 8px;background:var(--panel);border-bottom:1px solid var(--cromo-borda);color:var(--text,inherit)}
#gsBarra .gsGrupo{display:flex;gap:2px;padding-right:8px;border-right:1px solid var(--cromo-borda)}#gsBarra .gsGrupo:last-of-type{border-right:0}
#gsBarra .gsBtn{display:inline-flex;align-items:center;gap:4px;min-width:32px;min-height:32px;padding:4px 6px;border:1px solid transparent;border-radius:6px;background:transparent;color:inherit;cursor:pointer;font:inherit}
#gsBarra .gsBtn:hover,#gsBarra .gsBtn:focus-visible{background:color-mix(in srgb,currentColor 12%,transparent);border-color:var(--cromo-borda)}
#gsBarra .gsBtn[aria-pressed=true]{background:color-mix(in srgb,currentColor 18%,transparent)}
#gsBarra .gsCfg{margin-left:auto}#gsBarra svg{width:20px;height:20px}
:root.gsFaixaCompleta #rsToolRibbon{display:block}:root:not(.gsFaixaCompleta) #rsToolRibbon{display:none}
#gsBarraDlg{position:fixed;top:96px;right:16px;z-index:9000;width:min(420px,calc(100vw - 32px));max-height:calc(100vh - 140px);display:flex;flex-direction:column;background:var(--panel);color:var(--text,inherit);border:1px solid var(--cromo-borda);border-radius:8px;box-shadow:0 8px 28px rgba(0,0,0,.35)}
#gsBarraDlg .gsTit{display:flex;justify-content:space-between;align-items:center;padding:8px 10px;border-bottom:1px solid var(--cromo-borda)}
#gsBarraDlg .gsDica{margin:6px 10px;font-size:12px;opacity:.85}#gsBarraDlg .gsLista{overflow:auto;padding:0 10px}
#gsBarraDlg fieldset{border:1px solid var(--cromo-borda);border-radius:6px;margin:6px 0;padding:4px 8px}#gsBarraDlg legend{font-weight:600}
#gsBarraDlg label{display:flex;align-items:center;gap:6px;padding:2px 0}#gsBarraDlg label span:nth-of-type(2){flex:1}#gsBarraDlg .gsIco svg{width:18px;height:18px}
#gsBarraDlg button{background:transparent;color:inherit;border:1px solid var(--cromo-borda);border-radius:5px;cursor:pointer;padding:2px 7px}
#gsBarraDlg .gsAcoes{display:flex;gap:6px;padding:8px 10px;border-top:1px solid var(--cromo-borda)}#gsBarraDlg .gsAcoes span{flex:1}`;
document.head.appendChild(css);
function iniciar(t=0){
 if(!document.getElementById('menuBar')||!window.RodoviaMenus||!window.RodoviaIconPack){if(t<80)setTimeout(()=>iniciar(t+1),150);return}
 cfg=valida(ler());desenhar(cfg);
 new MutationObserver(()=>{if(!document.getElementById('gsBarra')&&cfg)desenhar(cfg)}).observe(document.body,{childList:true});
}
let forcaFaixa=null;
function faixaCompleta(v){forcaFaixa=!!v;if(cfg){cfg.todas=!!v;aplicarTodas();document.querySelector('#gsBarra .gsAll')?.setAttribute('aria-pressed',String(!!v))}else aplicarTodas()}
window.RodoviaBarra=Object.freeze({faixaCompleta,abrir,grupos:()=>JSON.parse(JSON.stringify(cfg||padrao())),restaurar(){cfg=padrao();gravar(cfg);desenhar(cfg)}});
iniciar();
})();
