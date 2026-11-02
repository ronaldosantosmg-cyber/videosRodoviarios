// Canvas fluido (boas praticas MDN/web.dev): no maximo um redesenho por quadro durante arrasto/zoom.
// A 1a chamada de cada quadro desenha na hora (comportamento igual ao anterior); chamadas seguidas no mesmo quadro
// viram UM redesenho final por requestAnimationFrame. draw.agora() desenha de forma imediata.
(function(){
 if(typeof draw!=='function'||draw.__fluido)return;
 var orig=draw,ultimo=0,pend=0;
 function fluido(){
  var t=performance.now();
  if(t-ultimo>=14){ultimo=t;if(pend){cancelAnimationFrame(pend);pend=0}return orig.apply(this,arguments)}
  if(!pend)pend=requestAnimationFrame(function(){pend=0;ultimo=performance.now();orig()});
 }
 fluido.__fluido=true;fluido.agora=function(){if(pend){cancelAnimationFrame(pend);pend=0}ultimo=performance.now();return orig()};
 draw=fluido;window.RodoviaDesenho={agora:fluido.agora};
})();
