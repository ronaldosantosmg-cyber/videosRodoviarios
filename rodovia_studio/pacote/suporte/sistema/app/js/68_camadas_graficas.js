// Dois caches 2D + canvas de interação. Sem contextos WebGL adicionais ou arredondamento do CRS.
(()=>{'use strict';
const BUDGET=32*1024*1024,slots=new Map(),ids=new WeakMap();let nextId=1,revision=0,enabled=true;
const counters={backgroundBuilds:0,technicalBuilds:0,hits:0,buildMs:0,fallbacks:0};
const id=o=>{if(!o||typeof o!=='object')return String(o);if(!ids.has(o))ids.set(o,nextId++);return ids.get(o)};
function clear(){for(const s of slots.values()){s.surface.width=1;s.surface.height=1}slots.clear()}
function compose(background,technical){
 if(!enabled||canvas.width*canvas.height*8>BUDGET){if(slots.size)clear();counters.fallbacks++;background();technical();return}
 const camera=[pid,projectSession.context,canvas.width,canvas.height,view.s,view.ox,view.oy,id(geo),id(meta),baseMode].join('|');
 const keys=[camera+'|'+[revision,id(baseImage),id(localInfo),localInfo?.key,localInfo?.editor,tileAlpha,webKey()].join('|'),camera+'|'+[id(vecPaths),id(editor),id(M),MARK_KEYS.map(k=>id(M[k])).join(','),tool,selected,id(alignResult),cfg.km_start_m,cfg.km_end_m,window.RodoviaFlowStudy?.stale,projectSession.epoch,vecAlpha,JSON.stringify(vecOn),JSON.stringify(M.image_groups||{})].join('|')];
 // Allocate both contexts before compositing: a fallback must never paint alpha twice.
 for(const name of ['background','technical'])if(!slots.has(name)){const surface=document.createElement('canvas'),context=surface.getContext('2d');if(!context){clear();counters.fallbacks++;background();technical();return}slots.set(name,{surface,context,key:null})}
 for(const [i,paint] of [background,technical].entries()){
  const name=i?'technical':'background',slot=slots.get(name);
  const dynamic=i&&!!(drag||draft||cadCmd);
  if(slot.key!==keys[i]||dynamic){const started=performance.now(),original=ctx;
   try{slot.surface.width=canvas.width;slot.surface.height=canvas.height;ctx=slot.context;paint();slot.key=dynamic?null:keys[i];counters[i?'technicalBuilds':'backgroundBuilds']++}
   catch(error){slot.key=null;throw error}finally{ctx=original;counters.buildMs+=performance.now()-started}
  }else counters.hits++;
  ctx.drawImage(slot.surface,0,0);
 }
}
const oldTileRedraw=tileRedraw;tileRedraw=function(...args){revision++;return oldTileRedraw(...args)};
window.addEventListener('rodovia:project-state',()=>{revision++;clear()});
const priorChanged=changed;changed=function(...args){const slot=slots.get('technical');if(slot)slot.key=null;return priorChanged(...args)};
window.RodoviaLayers=Object.freeze({compose,invalidate(layer){if(layer==='technical'){const slot=slots.get('technical');if(slot)slot.key=null}else{revision++;clear()}},setEnabled(value){enabled=!!value;clear();draw()},stats(){return {...counters,enabled,bytes:[...slots.values()].reduce((n,s)=>n+s.surface.width*s.surface.height*4,0),budgetBytes:BUDGET,surfaces:slots.size+1}}});
})();
