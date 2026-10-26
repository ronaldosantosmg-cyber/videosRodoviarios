// Dois caches 2D + canvas de interação. Sem contextos WebGL adicionais ou arredondamento do CRS.
(()=>{'use strict';
const BUDGET=32*1024*1024,slots=new Map(),ids=new WeakMap();let nextId=1,revision=0,enabled=true;
const counters={backgroundBuilds:0,technicalBuilds:0,hits:0,buildMs:0,fallbacks:0,panReuses:0};
const id=o=>{if(!o||typeof o!=='object')return String(o);if(!ids.has(o))ids.set(o,nextId++);return ids.get(o)};
function clear(){for(const s of slots.values()){s.surface.width=1;s.surface.height=1}slots.clear()}
function compose(background,technical){
 if(!enabled||canvas.width*canvas.height*8>BUDGET){if(slots.size)clear();counters.fallbacks++;background();technical();return}
 const cameraBase=[pid,projectSession.context,canvas.width,canvas.height,view.s,id(geo),id(meta),baseMode].join('|');const camera=cameraBase+'|'+view.ox+'|'+view.oy;
 const keys=[camera+'|'+[revision,id(baseImage),id(localInfo),localInfo?.key,localInfo?.editor,tileAlpha,webKey()].join('|'),camera+'|'+[id(vecPaths),id(editor),id(M),MARK_KEYS.map(k=>id(M[k])).join(','),tool,selected,id(alignResult),cfg.km_start_m,cfg.km_end_m,window.RodoviaFlowStudy?.stale,vecAlpha,JSON.stringify(vecOn),JSON.stringify(M.image_groups||{}),JSON.stringify(cfg.role_colors||{})].join('|')];
 // Allocate both contexts before compositing: a fallback must never paint alpha twice.
 for(const name of ['background','technical'])if(!slots.has(name)){const surface=document.createElement('canvas'),context=surface.getContext('2d');if(!context){clear();counters.fallbacks++;background();technical();return}slots.set(name,{surface,context,key:null})}
 for(const [i,paint] of [background,technical].entries()){
  const name=i?'technical':'background',slot=slots.get(name);
  const dynamic=i&&!!(drag&&(drag.type!=='pan'||canvas.width*canvas.height>1500000)||draft||cadCmd);
  const content=keys[i].slice(camera.length),dx=view.ox-(slot.ox||0),dy=view.oy-(slot.oy||0);
  if(canvas.width*canvas.height<=1500000&&drag?.type==='pan'&&!draft&&!cadCmd&&slot.key&&slot.cameraBase===cameraBase&&slot.content===content&&Math.abs(dx)<canvas.width/2&&Math.abs(dy)<canvas.height/2){
   ctx.drawImage(slot.surface,dx,dy);ctx.save();ctx.beginPath();if(dx>0)ctx.rect(0,0,dx,canvas.height);if(dx<0)ctx.rect(canvas.width+dx,0,-dx,canvas.height);if(dy>0)ctx.rect(0,0,canvas.width,dy);if(dy<0)ctx.rect(0,canvas.height+dy,canvas.width,-dy);ctx.clip();paint();ctx.restore();counters.panReuses++;continue;
  }
  if(slot.key!==keys[i]||dynamic){const started=performance.now(),original=ctx;
   try{slot.surface.width=canvas.width;slot.surface.height=canvas.height;ctx=slot.context;paint();slot.key=dynamic?null:keys[i];slot.cameraBase=cameraBase;slot.content=content;slot.ox=view.ox;slot.oy=view.oy;counters[i?'technicalBuilds':'backgroundBuilds']++}
   catch(error){slot.key=null;throw error}finally{ctx=original;counters.buildMs+=performance.now()-started}
  }else counters.hits++;
  ctx.drawImage(slot.surface,0,0);
 }
}
const oldTileRedraw=tileRedraw;tileRedraw=function(...args){revision++;return oldTileRedraw(...args)};
// As chaves de fonte e câmera decidem a invalidação; uma confirmação de gravação não limpa imagens.
// Confirmações de gravação não invalidam os caches: conteúdo, câmera e fontes compõem as chaves.
const priorChanged=changed;changed=function(...args){const slot=slots.get('technical');if(slot)slot.key=null;return priorChanged(...args)};
window.RodoviaLayers=Object.freeze({compose,invalidate(layer){if(layer==='technical'){const slot=slots.get('technical');if(slot)slot.key=null}else{revision++;clear()}},setEnabled(value){enabled=!!value;clear();draw()},stats(){return {...counters,enabled,bytes:[...slots.values()].reduce((n,s)=>n+s.surface.width*s.surface.height*4,0),budgetBytes:BUDGET,surfaces:slots.size+1}}});
})();
