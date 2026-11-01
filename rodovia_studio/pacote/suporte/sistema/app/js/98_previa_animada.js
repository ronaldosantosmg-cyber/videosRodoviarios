// 2.24: prévia animada dos fluxos no editor (poucos segundos de movimento, sem gerar vídeo).
// Usa as trajetórias já calculadas (editor.paths), a semente (traffic_seed) e a densidade do projeto.
(()=>{'use strict';
 let ativa=false,t0=0,raf=0,cache=null,cacheKey='';
 const COR={main:'#ffd34d',marginal:'#7ee0ff',return:'#ff9f7a',device:'#c8a2ff',access:'#9be58b'};
 function lcg(seed){let s=(seed>>>0)||1;return()=>{s=(Math.imul(s,1664525)+1013904223)>>>0;return s/4294967296}}
 function preparar(){
  const paths=(typeof editor!=='undefined'&&editor&&editor.paths)||[];const seed=Number((typeof cfg!=='undefined'&&cfg.traffic_seed)??1729),dens=Number((typeof cfg!=='undefined'&&cfg.traffic_density)??1);
  const key=paths.length+':'+seed+':'+dens+':'+(editor?.engine_revision||'');if(cache&&key===cacheKey)return cache;
  const rnd=lcg(seed),out=[];
  for(const p of paths){const q=p.p;if(!Array.isArray(q)||q.length<2)continue;const cum=[0];for(let i=1;i<q.length;i++)cum.push(cum[i-1]+Math.hypot(q[i][0]-q[i-1][0],q[i][1]-q[i-1][1]));const L=cum[cum.length-1];if(L<20)continue;
   const kind=(p.kinds&&p.kinds[0])||'main',n=Math.max(1,Math.min(400,Math.round(L/(55/Math.max(.2,dens)))));
   const cars=Array.from({length:n},()=>({off:rnd()*L,v:(kind==='main'?15:9)*(.8+rnd()*.4),len:4.5+rnd()*3.5*(rnd()<.18?1:0)}));
   out.push({q,cum,L,kind,cars})}
  cache=out;cacheKey=key;return out}
 function ponto(P,s){const {q,cum}=P;let lo=0,hi=cum.length-1;while(hi-lo>1){const m=(lo+hi)>>1;if(cum[m]<=s)lo=m;else hi=m}const f=(s-cum[lo])/Math.max(1e-9,cum[hi]-cum[lo]);return [q[lo][0]+(q[hi][0]-q[lo][0])*f,q[lo][1]+(q[hi][1]-q[lo][1])*f,q[hi][0]-q[lo][0],q[hi][1]-q[lo][1]]}
 function pintar(){
  if(!ativa||typeof W2C!=='function'||typeof ctx==='undefined')return;
  const t=(performance.now()-t0)/1000,A=W2C({x:0,y:0}),B=W2C({x:1,y:0}),px=Math.hypot(B[0]-A[0],B[1]-A[1]);   // pixels por metro
  const W=ctx.canvas.width,H=ctx.canvas.height,r=Math.max(2,Math.min(9,1.9*px));
  ctx.save();ctx.lineCap='round';
  for(const P of preparar()){ctx.fillStyle=COR[P.kind]||COR.main;ctx.strokeStyle='rgba(0,0,0,.55)';ctx.lineWidth=1;
   for(const c of P.cars){const s=(c.off+t*c.v)%P.L,[x,y,dx,dy]=ponto(P,s),z=W2C({x,y});if(z[0]<-20||z[1]<-20||z[0]>W+20||z[1]>H+20)continue;
    const n=Math.hypot(dx,dy)||1,z2=W2C({x:x+dx/n,y:y+dy/n}),ang=Math.atan2(z2[1]-z[1],z2[0]-z[0]);   // rumo na tela (eixo Y já tratado por W2C)
    ctx.beginPath();ctx.ellipse(z[0],z[1],Math.max(r,c.len*px/2),r*.62,ang,0,6.2832);ctx.fill();ctx.stroke()}}
  ctx.restore()}
 function laco(){cancelAnimationFrame(raf);if(!ativa)return;try{draw()}catch(_e){window.RodoviaErros&&RodoviaErros.avisar('previa_animada',_e)}raf=requestAnimationFrame(laco)}
 function alternar(ligar=!ativa){if(ligar&&!((typeof editor!=='undefined'&&editor&&editor.paths||[]).length)){msg('Calcule os fluxos antes de animar (Gerar tráfego).',true);return}
  ativa=!!ligar;t0=performance.now();if(ativa){msg('Prévia animada ligada — clique de novo em “Animar fluxos” ou pressione Esc para parar.');laco()}else{cancelAnimationFrame(raf);msg('Prévia animada desligada.');try{draw()}catch(_e){window.RodoviaErros&&RodoviaErros.avisar('previa_animada',_e)}}}
 const antigo=draw;draw=function(...a){const r=antigo(...a);try{pintar()}catch(_e){window.RodoviaErros&&RodoviaErros.avisar('previa_animada',_e)}return r};
 document.addEventListener('keydown',e=>{if(ativa&&e.key==='Escape'&&!document.querySelector('dialog[open]'))alternar(false)});
 document.addEventListener('visibilitychange',()=>{if(document.hidden&&ativa)alternar(false)});
 comando(['ANIMARFLUXOS','ANIMAR'],()=>alternar(),'Prévia animada dos fluxos no editor (usa a semente e a densidade do projeto); Esc para parar');
 queueMicrotask(()=>{for(const group of document.querySelectorAll('[data-rs-group="Fluxos de tráfego"]')){const b=document.createElement('button');b.type='button';b.dataset.rsCommand='ANIMARFLUXOS';b.title='Animar fluxos (prévia no editor)';b.setAttribute('aria-label',b.title);b.innerHTML='<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M3 12h4m3 0h4m3 0h3M18 8l3 4-3 4"/></svg>';b.onclick=()=>alternar();group.appendChild(b)}});
 window.RodoviaPreviaAnimada=Object.freeze({alternar,ativa:()=>ativa,preparar});
})();
