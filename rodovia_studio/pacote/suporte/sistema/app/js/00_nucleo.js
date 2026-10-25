'use strict';
/* Rodovia Studio — interface local. Editor da prévia (1.3): zoom/arraste, ferramentas de marcação,
   desfazer/refazer. Todas as marcações são gravadas na configuração em coordenadas do CRS. */
// 1.31: ponto de extensão. Uma função global declarada com `function nome(){}` pode ser estendida por outra parte
// do aplicativo: estender('nome', original => function(...args){ ... original(...args) ... }, 'rótulo').
// A ordem das extensões fica registrada em EXTENSOES (veja Ajuda › Sobre › Estrutura) — antes cada versão
// fazia {const _x=nome;nome=function(){...}} sem registro.
const EXTENSOES={};
function estender(nome,fabrica,rotulo=''){const original=globalThis[nome];if(typeof original!=='function')throw Error(`estender: “${nome}” não é uma função global.`);
 const nova=fabrica(original);if(typeof nova!=='function')throw Error(`estender: a extensão de “${nome}” não devolveu uma função.`);(EXTENSOES[nome]=EXTENSOES[nome]||[]).push(rotulo);globalThis[nome]=nova;return nova}
// 1.31: registros. Uma função nova se declara num lugar só, em vez de embrulhar click/finishDraft/toolOptions/
// escapeCommand/setTool/runCommand. Os despachantes ficam em 99_registros.js (por fora de tudo).
//   ferramenta('id',{rotulo,dica,icone,antesDe,clique(w,e),concluir(d),opcoes(el),esc(),entrar(),sair(proxima)})
//   comando(['NOME','N'],fn,'ajuda')        — linha de comando
//   itemFaixa('Aba','Grupo',[rótulo,ícone,fn,grande],{inicio,posicao})  — faixa de opções
//   itemArquivo('depois de…',[rótulo,atalho?,fn] | null …)               — menu Arquivo
const FERRAMENTAS={},COMANDOS=new Map();
function ferramenta(id,def){if(FERRAMENTAS[id])throw Error(`ferramenta “${id}” registrada duas vezes.`);FERRAMENTAS[id]=def;if(def.icone)ICON_PATHS[id]=def.icone;
 if(def.rotulo&&!TOOLS.some(t=>t[0]===id)){const at=def.antesDe?TOOLS.findIndex(t=>t[0]===def.antesDe):-1;const row=[id,def.rotulo,def.dica||''];row.internal=!!def.internal;if(at>=0)TOOLS.splice(at,0,row);else TOOLS.push(row)}return def}
function comando(nomes,fn,ajuda){for(const n of nomes){if(COMANDOS.has(n))throw Error(`comando “${n}” registrado duas vezes.`);COMANDOS.set(n,fn)}if(ajuda)CMD_HELP.push([nomes.join(' / '),ajuda])}
function itemFaixa(aba,grupo,item,{inicio=false,posicao=null}={}){const T=RIBBON.find(t=>t[0]===aba);if(!T||!T[1])throw Error(`aba “${aba}” não existe na faixa de opções.`);
 let g=T[1].find(x=>x[0]===grupo);if(!g){g=[grupo,[]];T[1].push(g)}if(posicao!=null)g[1].splice(posicao,0,item);else if(inicio)g[1].unshift(item);else g[1].push(item)}
function itemArquivo(depoisDe,...itens){const F=MENUBAR[0][1];const k=F.findIndex(it=>it&&it[0]===depoisDe);if(k<0)throw Error(`item “${depoisDe}” não existe no menu Arquivo.`);F.splice(k+1,0,...itens)}
const $=id=>document.getElementById(id);
let pid='',cfg={},analysis=null,meta=null,task='',baseImage=null,editingPoi=null,lastRender=null,editor=null,alignResult=null;
const canvas=$('canvas');let ctx=canvas.getContext('2d');
const roles={axis:'Eixo',pavement:'Pista projetada',existing_pavement:'Pista existente',shoulder:'Acostamento',edge_line:'Bordo (linha de borda)',median:'Canteiro',barrier:'Barreira',oae:'OAE',cut:'Corte',fill:'Aterro',earthwork:'Talude (corte/aterro pela proximidade)',domain:'Faixa de domínio',water:'Hidrografia'};
const ROLE_COLOR={edge_line:'#f4f2e2',water:'#2a80b9',existing_pavement:'#a4a8a9',pavement:'#454c4e',shoulder:'#858983',median:'#7f9b6e',barrier:'#e0ddd2',oae:'#b9bcb7',cut:'#df6262',fill:'#53bb77',domain:'#ffd56b'};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const uid=()=>(crypto.randomUUID?crypto.randomUUID():Date.now().toString(36)+Math.random().toString(36).slice(2));
function msg(s,error=false){$('message').textContent=s;$('message').classList.toggle('error',error)}
function validationMessage(detail){if(!Array.isArray(detail))return typeof detail==='string'?detail:'Não foi possível concluir a solicitação.';const labels={traffic_capacity_vphpl:'Capacidade nominal por faixa',traffic_demand_vphpl:'Demanda por faixa',min_wagons:'Mínimo de vagões',max_wagons:'Máximo de vagões'};return detail.map(e=>{const loc=(e.loc||[]).filter(v=>v!=='body'),key=loc.at(-1),label=labels[key]||loc.join(' · ')||'Configuração',ctx=e.ctx||{};let m=({greater_than:`informe um número maior que ${ctx.gt}`,greater_than_equal:`informe um número maior ou igual a ${ctx.ge}`,less_than_equal:`informe um número menor ou igual a ${ctx.le}`,less_than:`informe um número menor que ${ctx.lt}`,finite_number:'informe um número finito (sem NaN ou infinito)',float_parsing:'informe um número válido',float_type:'informe um número válido',int_parsing:'informe um número inteiro',int_from_float:'informe um número inteiro',missing:'campo obrigatório',literal_error:'selecione uma opção válida'})[e.type];if(!m)m=e.type==='value_error'?String(e.msg||'Valor inválido').replace(/^Value error, /,''):'valor ou formato inválido';return label+': '+m+'.'}).join(' ')}
async function api(url,opt={}){const r=await fetch(url,opt);if(!r.ok){let e;try{e=await r.json()}catch{throw Error('Falha HTTP '+r.status)}throw Error(validationMessage(e.detail))}return r.json()}
const json=(method,body)=>({method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
function guard(fn,label='ação'){return async(...a)=>{try{if(typeof fn!=='function')throw Error(`Ação indisponível: ${label}. Recarregue a interface ou restabeleça a versão anterior.`);return await fn(...a)}catch(e){const m=e&&e.message?e.message:String(e);try{if(typeof reportClient==='function')reportClient(m,e&&e.stack||'',label)}catch{};msg(m,true);return null}}}
function safeCall(fn,...a){try{if(typeof fn!=='function')return null;return fn(...a)}catch(e){try{if(typeof reportClient==='function')reportClient(e.message,e.stack,'safeCall')}catch{};msg(e.message||String(e),true);return null}}
function requireProject(){if(!pid)throw Error('Crie ou abra um projeto primeiro.')}
function parseKm(s){s=String(s).trim();if(s.includes('+')){const a=s.split('+');if(a.length!==2||!/^-?\d+$/.test(a[0])||!/^\d{1,3}$/.test(a[1]))throw Error('Km inválido: '+s);return Number(a[0])*1000+(a[0].startsWith('-')?-1:1)*Number(a[1])}const v=Number(s.replace(',','.'));if(!Number.isFinite(v))throw Error('Km inválido: '+s);return v*1000}
function formatKm(m){if(m==null||!Number.isFinite(m))return '';const neg=m<0;const v=Math.round(Math.abs(m));return (neg?'-':'')+Math.floor(v/1000)+'+'+String(v%1000).padStart(3,'0')}

