// 2.28: + estilos de mapa (Técnico/Maquete/Satélite) e minimapa. 2.26: acabamento do modo 2D: barra de escala e seta do norte sobre o mapa (não altera dados nem comandos).
(()=>{'use strict';
 function bonito(m){const p=Math.pow(10,Math.floor(Math.log10(m))),f=m/p;return(f>=5?5:f>=2?2:1)*p}
 function pintar(){
  if(typeof ctx==='undefined'||!ctx||typeof view==='undefined'||typeof pxPerM!=='function')return;
  const pxPorM=pxPerM();   // 2.32: mesma escala do desenho (metros do CRS); antes usava outra razão e a barra mentia
  if(!(pxPorM>0)||!isFinite(pxPorM))return;
  const alvo=bonito(110/pxPorM),w=alvo*pxPorM,x=18,y=ctx.canvas.height-26;
  ctx.save();ctx.setTransform(1,0,0,1,0,0);ctx.globalAlpha=.92;
  ctx.fillStyle='#05101acc';ctx.fillRect(x-8,y-22,w+16+(alvo>=1000?16:0),36);
  ctx.strokeStyle='#f4f2e2';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(x,y-4);ctx.lineTo(x,y+4);ctx.moveTo(x,y);ctx.lineTo(x+w,y);ctx.moveTo(x+w,y-4);ctx.lineTo(x+w,y+4);ctx.stroke();
  ctx.fillStyle='#f4f2e2';ctx.font='12px system-ui';ctx.fillText(alvo>=1000?(alvo/1000)+' km':alvo+' m',x,y-9);
  const cx=ctx.canvas.width-34,cy=44;ctx.fillStyle='#05101acc';ctx.beginPath();ctx.arc(cx,cy,24,0,6.2832);ctx.fill();
  ctx.fillStyle='#ff6b5e';ctx.beginPath();ctx.moveTo(cx,cy-18);ctx.lineTo(cx-7,cy+6);ctx.lineTo(cx,cy+2);ctx.lineTo(cx+7,cy+6);ctx.closePath();ctx.fill();
  ctx.fillStyle='#f4f2e2';ctx.font='bold 11px system-ui';ctx.textAlign='center';ctx.fillText('N',cx,cy+19);
  ctx.restore()}

 // ---- 2.28: estilos de mapa e minimapa ----
 const ESTILOS={tecnico:{tile:.38,vec:1,nome:'Técnico'},maquete:{tile:.8,vec:.9,nome:'Maquete'},satelite:{tile:1,vec:.65,nome:'Satélite'}};
 let estilo='maquete',mini=true;
 try{estilo=localStorage.getItem('rodovia_estilo_mapa')||estilo}catch(_e){}
 function aplicarEstilo(n,silencioso){const e=ESTILOS[n];if(!e)return false;estilo=n;
  try{tileAlpha=e.tile;vecAlpha=e.vec}catch(err){window.RodoviaErros&&RodoviaErros.avisar('estilo mapa',err)}
  try{localStorage.setItem('rodovia_estilo_mapa',n)}catch(_e){}
  try{const a=document.getElementById('tileAlpha'),b=document.getElementById('vecAlpha');if(a)a.value=e.tile;if(b)b.value=e.vec;saveBasePrefs();draw()}catch(err){window.RodoviaErros&&RodoviaErros.avisar('estilo mapa',err)}
  if(!silencioso&&typeof msg==='function')msg('Estilo do mapa: '+e.nome+'.');return true}
 function minimapa(){
  if(!mini||typeof editor==='undefined'||!editor||!Array.isArray(editor.paths)||!editor.paths.length||typeof C2W!=='function')return;
  let x0=1e18,y0=1e18,x1=-1e18,y1=-1e18;const linhas=[];
  for(const p of editor.paths){const q=p.p;if(!Array.isArray(q)||q.length<2)continue;const passo=Math.max(1,Math.floor(q.length/80));const l=[];for(let i=0;i<q.length;i+=passo){const a=q[i];l.push(a);if(a[0]<x0)x0=a[0];if(a[0]>x1)x1=a[0];if(a[1]<y0)y0=a[1];if(a[1]>y1)y1=a[1]}linhas.push(l)}
  if(!linhas.length||x1<=x0&&y1<=y0)return;
  const W=170,H=110,pad=8,sx=(W-2*pad)/Math.max(x1-x0,1),sy=(H-2*pad)/Math.max(y1-y0,1),k=Math.min(sx,sy),ox=ctx.canvas.width-W-12,oy=ctx.canvas.height-H-12;
  const M=a=>[ox+pad+(a[0]-x0)*k,oy+H-pad-(a[1]-y0)*k];
  ctx.save();ctx.setTransform(1,0,0,1,0,0);ctx.globalAlpha=.92;ctx.fillStyle='#05101acc';ctx.fillRect(ox,oy,W,H);ctx.strokeStyle='#ffffff33';ctx.strokeRect(ox+.5,oy+.5,W-1,H-1);
  ctx.strokeStyle='#ffd34d';ctx.lineWidth=1.2;for(const l of linhas){ctx.beginPath();l.forEach((a,i)=>{const m=M(a);i?ctx.lineTo(m[0],m[1]):ctx.moveTo(m[0],m[1])});ctx.stroke()}
  try{const a=C2W(0,0),b=C2W(ctx.canvas.width,ctx.canvas.height);const A=M([a.x??a[0],a.y??a[1]]),B=M([b.x??b[0],b.y??b[1]]);
   const rx=Math.min(A[0],B[0]),ry=Math.min(A[1],B[1]),rw=Math.abs(A[0]-B[0]),rh=Math.abs(A[1]-B[1]);
   ctx.strokeStyle='#ff6b5e';ctx.lineWidth=1.5;ctx.strokeRect(Math.max(ox,rx),Math.max(oy,ry),Math.max(2,Math.min(rw,W)),Math.max(2,Math.min(rh,H)))}catch(err){window.RodoviaErros&&RodoviaErros.avisar('minimapa',err)}
  ctx.restore()}
 if(typeof comando==='function'&&typeof COMANDOS!=='undefined'){
  if(!COMANDOS.has('ESTILOMAPA'))comando(['ESTILOMAPA','ESTILO'],()=>{const ordem=Object.keys(ESTILOS);aplicarEstilo(ordem[(ordem.indexOf(estilo)+1)%ordem.length])},'Alterna o estilo do mapa 2D: Técnico, Maquete ou Satélite');
  if(!COMANDOS.has('MINIMAPA'))comando(['MINIMAPA'],()=>{mini=!mini;try{draw()}catch(_e){}if(typeof msg==='function')msg('Minimapa '+(mini?'ligado':'desligado')+'.')},'Liga ou desliga o minimapa do traçado no canto do mapa 2D');
 }
 if(typeof document!=='undefined')document.addEventListener('DOMContentLoaded',()=>{try{if(estilo!=='maquete')aplicarEstilo(estilo,true)}catch(_e){}});
 if(typeof draw==='function'){const antigo=draw;draw=function(...a){const r=antigo(...a);try{pintar();minimapa()}catch(e){(window.RodoviaErros||{avisar(){}}).avisar('mapa 2D',e)}return r}}
 const api={bonito,pintar,ESTILOS,aplicarEstilo,minimapa};if(typeof window!=='undefined')window.RodoviaMapa2D=api;if(typeof globalThis!=='undefined')globalThis.RodoviaMapa2D=api;
})();
