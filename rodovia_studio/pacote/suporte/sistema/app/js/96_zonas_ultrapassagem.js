// 2.14: trechos em que o motor permite ultrapassagem pela pista contrária (verde, translúcido). Só no estudo técnico; não entra no vídeo.
(()=>{'use strict';
 const ok=r=>Array.isArray(r)&&r.length>=2&&r.every(p=>Array.isArray(p)&&Number.isFinite(p[0])&&Number.isFinite(p[1]));
 function paint(){
  if(typeof vecOn!=='undefined'&&vecOn.flows===false)return;
  const zs=(typeof editor!=='undefined'&&editor&&editor.passing_zones)||[];if(!zs.length||typeof W2C!=='function')return;
  ctx.save();ctx.lineCap='round';ctx.lineJoin='round';
  for(const z of zs){if(!ok(z.p))continue;ctx.beginPath();z.p.forEach((p,i)=>{const q=W2C({x:p[0],y:p[1]});i?ctx.lineTo(q[0],q[1]):ctx.moveTo(q[0],q[1])});
   ctx.globalAlpha=.35;ctx.strokeStyle='#2fbf71';ctx.lineWidth=10;ctx.stroke();ctx.globalAlpha=.9;ctx.strokeStyle='#14803f';ctx.lineWidth=2;ctx.setLineDash([2,6]);ctx.stroke();ctx.setLineDash([])}
  ctx.restore()}
 const old=draw;draw=function(...a){const r=old(...a);try{paint()}catch(_e){window.RodoviaErros&&RodoviaErros.avisar('zonas_ultrapassagem',_e)}return r};
 window.RodoviaZonasUltrapassagem=Object.freeze({count:()=>((typeof editor!=='undefined'&&editor&&editor.passing_zones)||[]).length});
})();
