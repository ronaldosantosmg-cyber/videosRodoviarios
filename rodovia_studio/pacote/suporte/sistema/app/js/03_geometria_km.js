/* ---------- Geometria auxiliar (cliente) ---------- */
function axisPts(){const a=editor?.axis||vec?.axis_main;return a?a.map(p=>({x:p[0],y:p[1]})):null}
let axisCache=null;
function axisData(){const src=editor||vec;if(!src||!(src.axis||src.axis_main))return null;if(axisCache&&axisCache.src===src)return axisCache;const a=axisPts(),s=[0];for(let i=1;i<a.length;i++)s.push(s[i-1]+Math.hypot(a[i].x-a[i-1].x,a[i].y-a[i-1].y));axisCache={src,a,s};return axisCache}
function projectAxis(p){const d=axisData();if(!d)return null;let best={dist:Infinity};for(let i=0;i<d.a.length-1;i++){const A=d.a[i],B=d.a[i+1],vx=B.x-A.x,vy=B.y-A.y,L2=vx*vx+vy*vy||1e-9;let t=((p.x-A.x)*vx+(p.y-A.y)*vy)/L2;t=Math.max(0,Math.min(1,t));const q={x:A.x+t*vx,y:A.y+t*vy},dist=Math.hypot(p.x-q.x,p.y-q.y);if(dist<best.dist)best={dist,point:q,s:d.s[i]+t*Math.sqrt(L2)}}return best}
/* Estaqueamento: mesmo cálculo do servidor (início, sentido e fator). */
function station(){const c=M.chainage||{},man=c.mode==='manual',d=axisData();const L=d?d.s[d.s.length-1]:0;
 const s0=man&&c.start?(projectAxis(c.start)?.s??0):0;const se=man&&c.end?projectAxis(c.end)?.s:null;
 let dir=se!=null&&Math.abs(se-s0)>1e-6?(se>s0?1:-1):(man?(c.direction||1):1);let scale=1;
 if(man&&c.calibrate&&se!=null&&Math.abs(se-s0)>1){const v=(cfg.km_end_m-cfg.km_start_m)/(dir*(se-s0));if(v>0)scale=v}
 const kmEndGeo=se!=null?cfg.km_start_m+dir*scale*(se-s0):cfg.km_start_m+dir*scale*((dir>0?L:0)-s0);return {s0,se,dir,scale,L,kmEndGeo,mode:c.mode||'auto'}}
function s0(){return station().s0}
function kmOf(p){const r=projectAxis(p);if(!r)return null;const st=station();return {km:cfg.km_start_m+st.dir*st.scale*(r.s-st.s0),off:r.dist,point:r.point,s:r.s}}
function sOfKm(km){const st=station();return st.s0+st.dir*(km-cfg.km_start_m)/st.scale}
function axisAt(s){const d=axisData();s=Math.max(0,Math.min(d.s[d.s.length-1],s));let i=1;while(i<d.s.length-1&&d.s[i]<s)i++;const t=(s-d.s[i-1])/((d.s[i]-d.s[i-1])||1e-9);return {x:d.a[i-1].x+(d.a[i].x-d.a[i-1].x)*t,y:d.a[i-1].y+(d.a[i].y-d.a[i-1].y)*t}}
function axisSub(sa,sb){const d=axisData();if(sa>sb)[sa,sb]=[sb,sa];const out=[axisAt(sa)];for(let i=0;i<d.s.length;i++)if(d.s[i]>sa&&d.s[i]<sb)out.push(d.a[i]);out.push(axisAt(sb));return out}
function distSeg(p,a,b){const vx=b.x-a.x,vy=b.y-a.y,L2=vx*vx+vy*vy||1e-9;let t=((p.x-a.x)*vx+(p.y-a.y)*vy)/L2;t=Math.max(0,Math.min(1,t));return Math.hypot(p.x-a.x-t*vx,p.y-a.y-t*vy)}
function distPolyline(p,pts){let d=Infinity;for(let i=0;i<pts.length-1;i++)d=Math.min(d,distSeg(p,pts[i],pts[i+1]));return d}
const P=a=>({x:a[0],y:a[1]});
function nearestSegment(p,maxM=8){if(!editor)return null;let best=null;for(const s of editor.segments){const pts=s.points.map(P),d=distPolyline(p,pts);if(d<=maxM&&(!best||d<best.d))best={d,seg:s}}return best&&best.seg}
function simplify(pts,tol){if(pts.length<3)return pts;let dmax=0,idx=0;for(let i=1;i<pts.length-1;i++){const d=distSeg(pts[i],pts[0],pts[pts.length-1]);if(d>dmax){dmax=d;idx=i}}if(dmax>tol){const a=simplify(pts.slice(0,idx+1),tol),b=simplify(pts.slice(idx),tol);return a.slice(0,-1).concat(b)}return [pts[0],pts[pts.length-1]]}
function invAlign(p){const r=editor&&editor.alignment;if(!r||!M.dxf_alignment.applied)return p;const k=r.a*r.a+r.b*r.b,ia=r.a/k,ib=-r.b/k,x=p.x-r.tx,y=p.y-r.ty;return {x:ia*x-ib*y,y:ib*x+ia*y}}
function fwdAlign(p,r){return {x:r.a*p.x-r.b*p.y+r.tx,y:r.b*p.x+r.a*p.y+r.ty}}

