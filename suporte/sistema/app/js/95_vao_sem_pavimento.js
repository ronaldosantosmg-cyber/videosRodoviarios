// 2.12: vãos sem pavimento atravessados pelo fluxo (canteiro de obra, túnel, semáforo/faixa de pedestre sem hachura) desenhados como faixa hachurada translúcida.
// Só apresentação do estudo técnico: não entra no vídeo e não altera cálculos.
(()=>{'use strict';
 let pattern=null;
 function makePattern(){const c=document.createElement('canvas');c.width=c.height=12;const g=c.getContext('2d');g.strokeStyle='rgba(255,176,32,.95)';g.lineWidth=2;g.beginPath();g.moveTo(-2,14);g.lineTo(14,-2);g.moveTo(-2,8);g.lineTo(8,-2);g.moveTo(4,14);g.lineTo(14,4);g.stroke();return ctx.createPattern(c,'repeat')}
 const ok=r=>Array.isArray(r)&&r.length>=3&&r.every(p=>Array.isArray(p)&&Number.isFinite(p[0])&&Number.isFinite(p[1]));
 function zonas(){return (typeof editor!=='undefined'&&editor&&editor.ghost_zones)||[]}
 function paint(){
  if(typeof vecOn!=='undefined'&&vecOn.flows===false)return;
  const zs=zonas();if(!zs.length||typeof W2C!=='function')return;
  try{pattern=pattern||makePattern()}catch{return}
  ctx.save();
  for(const z of zs){if(!ok(z.ring))continue;ctx.beginPath();z.ring.forEach((p,i)=>{const q=W2C({x:p[0],y:p[1]});i?ctx.lineTo(q[0],q[1]):ctx.moveTo(q[0],q[1])});ctx.closePath();
   ctx.globalAlpha=.28;ctx.fillStyle='#ffb020';ctx.fill();ctx.globalAlpha=.75;ctx.fillStyle=pattern;ctx.fill();ctx.globalAlpha=.9;ctx.strokeStyle='#d98a00';ctx.setLineDash([6,4]);ctx.lineWidth=1.5;ctx.stroke()}
  ctx.restore()}
 const old=draw;draw=function(...a){const r=old(...a);try{paint()}catch(_e){window.RodoviaErros&&RodoviaErros.avisar('vao_sem_pavimento',_e)}return r};
 window.RodoviaVaoSemPavimento=Object.freeze({count:()=>zonas().length});
})();
