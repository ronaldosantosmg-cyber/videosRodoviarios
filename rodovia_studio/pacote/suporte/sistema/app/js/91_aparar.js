// ---------- Aparar (TRIM) ----------
// Remove o trecho de uma polilinha/linha entre as interseções vizinhas ao ponto clicado, usando como arestas de corte os demais objetos do desenho.
(function(root){
 const EPS=1e-9;
 function segInter(a,b,c,d){const r={x:b.x-a.x,y:b.y-a.y},s={x:d.x-c.x,y:d.y-c.y},den=r.x*s.y-r.y*s.x;if(Math.abs(den)<EPS)return null;
  const t=((c.x-a.x)*s.y-(c.y-a.y)*s.x)/den,u=((c.x-a.x)*r.y-(c.y-a.y)*r.x)/den;if(t<-EPS||t>1+EPS||u<-EPS||u>1+EPS)return null;return {t:Math.min(1,Math.max(0,t)),x:a.x+t*r.x,y:a.y+t*r.y}}
 function project(pts,p){let best={d:Infinity,t:0};for(let k=0;k+1<pts.length;k++){const a=pts[k],b=pts[k+1],dx=b.x-a.x,dy=b.y-a.y,L=dx*dx+dy*dy;let u=L?((p.x-a.x)*dx+(p.y-a.y)*dy)/L:0;u=Math.max(0,Math.min(1,u));const d=Math.hypot(p.x-a.x-u*dx,p.y-a.y-u*dy);if(d<best.d)best={d,t:k+u}}return best}
 function at(pts,t){const k=Math.min(pts.length-2,Math.floor(t)),u=t-k,a=pts[k],b=pts[k+1];return {x:a.x+u*(b.x-a.x),y:a.y+u*(b.y-a.y)}}
 // points: [{x,y}], edges: [[{x,y}...]] (polilinhas abertas ou fechadas já fechadas pelo chamador), click: {x,y}
 function compute(points,edges,click){
  if(!Array.isArray(points)||points.length<2)return {error:'Objeto sem trecho para aparar.'};
  const hits=[];
  for(const E of edges||[])for(let i=0;i+1<points.length;i++)for(let j=0;j+1<E.length;j++){const h=segInter(points[i],points[i+1],E[j],E[j+1]);if(h)hits.push(i+h.t)}
  hits.sort((a,b)=>a-b);const ts=hits.filter((t,i)=>i===0||t-hits[i-1]>1e-7);
  if(!ts.length)return {error:'Nenhuma aresta de corte cruza este objeto.'};
  const tc=project(points,click).t;let lo=null,hi=null;for(const t of ts){if(t<=tc)lo=t;else if(hi===null)hi=t}
  const pieces=[];
  if(lo!==null){const k=Math.floor(lo);pieces.push(dedupe(points.slice(0,k+1).concat([at(points,lo)])))}
  if(hi!==null){const k=Math.floor(hi);const p=[at(points,hi)].concat(points.slice(k+1));pieces.push(dedupe(p))}
  const ok=pieces.filter(p=>p.length>=2);
  return {pieces:ok,removed:{from:lo,to:hi},cuts:ts.length}}
 function dedupe(p){const o=[];for(const q of p)if(!o.length||Math.hypot(q.x-o[o.length-1].x,q.y-o[o.length-1].y)>1e-7)o.push({x:q.x,y:q.y});return o}
 const T={compute,segInter,project};
 if(typeof module!=='undefined'&&module.exports)module.exports=T;else root.RodoviaTrim=T;
})(typeof window!=='undefined'?window:globalThis);

if(typeof window!=='undefined'&&typeof comando==='function'){
 function trimEdges(self){const out=[];for(const o of objList()){if(o.key===self.key&&o.i===self.i)continue;if(o.shape==='pt')continue;const P=o.grips.map(g=>gripGet(g));if(P.length<2)continue;out.push(o.shape==='area'&&P.length>2?P.concat([P[0]]):P)}return out}
 function trimStep(w){
  const h=hitObject(W2C(w).length?{cx:W2C(w)[0],cy:W2C(w)[1]}:null);
  if(!h)return msg('APARAR: clique sobre o trecho a remover (fluxo, acesso ou linha).',true);
  const o=objOf(h);if(!o||!['poly','line'].includes(o.shape))return msg(`APARAR: “${o?o.label:'objeto'}” não é uma linha ou polilinha aberta.`,true);
  const pts=o.grips.map(g=>gripGet(g)),r=RodoviaTrim.compute(pts,trimEdges(h),w);
  if(r.error)return msg('APARAR: '+r.error,true);
  if(!r.pieces.length)return msg('APARAR: o trecho removido consumiria todo o objeto. Use APAGAR.',true);
  if(o.shape==='line'){if(r.pieces.length!==1||r.pieces[0].length!==2)return msg('APARAR: em uma linha simples só é possível cortar uma ponta.',true);checkpoint();gripSet(o.grips[0],r.pieces[0][0]);gripSet(o.grips[1],r.pieces[0][1]);sel=null;changed(`${o.label} aparada.`);return}
  if(!Array.isArray(o.o.points))return msg('APARAR: este objeto não permite edição de pontos.',true);
  checkpoint();const list=M[o.key];const orig=o.o;orig.points=r.pieces[0].map(p=>({x:p.x,y:p.y}));
  if(r.pieces.length>1){const c=JSON.parse(JSON.stringify(orig));c.points=r.pieces[1].map(p=>({x:p.x,y:p.y}));if('id' in c)c.id=uid();if(c.name)c.name=(c.name+' (2)').slice(0,80);list.splice(o.i+1,0,c)}
  sel=null;changed(`${o.label} aparada${r.pieces.length>1?' e dividida em duas partes':''}. Clique em outro trecho; Enter encerra.`);showProps&&showProps()}
 function startTrim(){if(!pid||!ready())return msg('Abra o editor de um projeto primeiro.',true);cadCmd={step:trimStep};prompt_('APARAR — clique no trecho a remover (Enter encerra):');msg('APARAR: os demais objetos do desenho são as arestas de corte. Clique no trecho a remover; Enter ou Esc encerra.')}
 comando(['APARAR','TRIM'],()=>startTrim(),'Aparar: remove o trecho do fluxo/acesso/linha até a interseção com os demais objetos');
 itemFaixa('Editar','Modificar',['Aparar','✂',()=>startTrim(),1]);
}
