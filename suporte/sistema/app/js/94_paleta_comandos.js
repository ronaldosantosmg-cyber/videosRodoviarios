// 2.26: paleta de comandos (Ctrl+K). Lista todos os comandos registrados, sem remover nenhum atalho existente.
(()=>{'use strict';
 function itens(){const out=[],vistos=new Set();
  for(const [nomes,aj] of (typeof CMD_HELP!=='undefined'?CMD_HELP:[])){const p=String(nomes).split(' / ');if(vistos.has(p[0]))continue;vistos.add(p[0]);out.push({nome:p[0],todos:p,ajuda:aj||''})}
  if(typeof COMANDOS!=='undefined')for(const n of COMANDOS.keys())if(![...vistos].some(v=>v===n)&&!out.some(o=>o.todos.includes(n)))out.push({nome:n,todos:[n],ajuda:''});
  return out}
 function filtrar(lista,q){q=(q||'').trim().toLowerCase();if(!q)return lista.slice(0,60);
  return lista.map(i=>{const t=(i.todos.join(' ')+' '+i.ajuda).toLowerCase();const k=i.todos.some(n=>n.toLowerCase()===q)?0:i.todos.some(n=>n.toLowerCase().startsWith(q))?1:t.includes(q)?2:9;return[k,i]}).filter(x=>x[0]<9).sort((a,b)=>a[0]-b[0]).map(x=>x[1]).slice(0,60)}
 function abrir(){if(typeof document==='undefined')return;let d=document.getElementById('rsPaleta');
  if(!d){d=document.createElement('dialog');d.id='rsPaleta';d.className='rsPaleta';d.innerHTML='<input type="search" id="rsPaletaQ" placeholder="Digite um comando ou o que deseja fazer…" autocomplete="off"><ul id="rsPaletaL"></ul>';document.body.appendChild(d);
   const q=d.querySelector('input'),ul=d.querySelector('ul');let sel=0,vis=[];
   const pintar=()=>{vis=filtrar(itens(),q.value);sel=Math.min(sel,Math.max(0,vis.length-1));ul.innerHTML=vis.map((i,n)=>`<li data-n="${n}" class="${n===sel?'on':''}"><b>${i.nome}</b><span>${i.ajuda}</span></li>`).join('')||'<li class="vazio">Nenhum comando encontrado.</li>'};
   const exec=n=>{const i=vis[n];if(!i)return;d.close();try{runCommand(i.nome)}catch(e){console.warn(e)}};
   q.addEventListener('input',()=>{sel=0;pintar()});
   q.addEventListener('keydown',e=>{if(e.key==='ArrowDown'){sel=Math.min(vis.length-1,sel+1);pintar();e.preventDefault()}else if(e.key==='ArrowUp'){sel=Math.max(0,sel-1);pintar();e.preventDefault()}else if(e.key==='Enter'){exec(sel);e.preventDefault()}});
   ul.addEventListener('click',e=>{const li=e.target.closest('li[data-n]');if(li)exec(+li.dataset.n)});
   d.pintar=pintar}
  d.showModal();d.querySelector('input').value='';d.pintar();d.querySelector('input').focus()}
 if(typeof document!=='undefined')document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'&&!e.shiftKey){e.preventDefault();abrir()}});
 const api={itens,filtrar,abrir};if(typeof window!=='undefined')window.RodoviaPaleta=api;if(typeof globalThis!=='undefined')globalThis.RodoviaPaleta=api;
})();
