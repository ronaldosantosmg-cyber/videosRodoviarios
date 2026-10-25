// Recupera captura/cursor quando o sistema interrompe um arraste.
(()=>{'use strict';
 const cursor=()=>{canvas.style.cursor=tool==='pan'?'grab':'crosshair'};
 function cancelDrag(e){
  const interrupted=drag;drag=null;sb=null;spaceDown=false;
  if(interrupted&&['grip','objmove','mmove','rot','label','move'].includes(interrupted.type)&&undoStack.length){
   undo();msg('Arraste interrompido. A geometria anterior foi restaurada.');
  }
  if(e?.pointerId!=null)try{if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId)}catch{}
  cursor();draw();
 }
 canvas.addEventListener('pointercancel',cancelDrag);
 canvas.addEventListener('lostpointercapture',e=>{if(drag)cancelDrag(e);else cursor()});
 window.addEventListener('blur',()=>{if(drag)cancelDrag();else cursor()});
})();
