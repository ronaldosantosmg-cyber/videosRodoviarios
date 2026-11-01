// 2.27: registro dos erros que antes eram engolidos por catch vazio. Uso: try{…}catch(e){RodoviaErros.avisar('contexto',e)}
// Mantém os últimos 80 eventos, avisa no console uma vez por contexto e envia ao servidor quando houver canal.
(()=>{'use strict';
 const lista=[],vistos=new Set();
 function avisar(contexto,erro){const msg=String((erro&&erro.message)||erro||'erro desconhecido').slice(0,300);
  lista.push({t:Date.now(),contexto:String(contexto),msg,stack:erro&&erro.stack?String(erro.stack).slice(0,800):''});if(lista.length>80)lista.shift();
  const k=contexto+'|'+msg;if(!vistos.has(k)){vistos.add(k);try{console.warn('[Rodovia] '+contexto+': '+msg)}catch(_){}
   try{if(typeof reportClient==='function')reportClient(msg,erro&&erro.stack,'erro tratado: '+contexto)}catch(_){}}}
 function seguro(contexto,fn,padrao){return function(...a){try{return fn.apply(this,a)}catch(e){avisar(contexto,e);return padrao}}}
 function resumo(){const por={};for(const e of lista)por[e.contexto]=(por[e.contexto]||0)+1;return{total:lista.length,por,ultimos:lista.slice(-10)}}
 const api={avisar,seguro,resumo,lista};
 if(typeof window!=='undefined')window.RodoviaErros=api;if(typeof globalThis!=='undefined')globalThis.RodoviaErros=api;
 if(typeof comando==='function'&&typeof COMANDOS!=='undefined'&&!COMANDOS.has('DIAGNOSTICOJS'))
  comando(['DIAGNOSTICOJS','ERROSJS'],()=>{const r=resumo();msg(r.total?`Erros tratados nesta sessão: ${r.total}. `+Object.entries(r.por).map(([k,v])=>`${k} (${v})`).join(', ')+'. Detalhes no console do navegador.':'Nenhum erro tratado registrado nesta sessão.');if(r.total)console.table(r.ultimos)},'Mostra erros que o aplicativo tratou sem interromper (diagnóstico do JavaScript)');
})();
