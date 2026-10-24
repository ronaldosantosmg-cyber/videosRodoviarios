// ---------- 1.24: escalar, espelhar, deslocar paralelo (offset) ----------
function offsetPolyline(P,d,closed){const n=P.length,out=[];const N=(a,b)=>{const dx=b.x-a.x,dy=b.y-a.y,L=Math.hypot(dx,dy)||1;return {x:-dy/L,y:dx/L}};
 for(let i=0;i<n;i++){const prev=closed?P[(i-1+n)%n]:(i>0?P[i-1]:null),next=closed?P[(i+1)%n]:(i<n-1?P[i+1]:null);
  const n1=prev?N(prev,P[i]):null,n2=next?N(P[i],next):null;let m;
  if(n1&&n2){m={x:n1.x+n2.x,y:n1.y+n2.y};const L=Math.hypot(m.x,m.y)||1;m={x:m.x/L,y:m.y/L};const c=m.x*n1.x+m.y*n1.y;const k=1/Math.max(c,.25);m={x:m.x*k,y:m.y*k}}else m=n1||n2;
  out.push({x:P[i].x+m.x*d,y:P[i].y+m.y*d})}return out}
function pointSide(P,w,closed){if(closed){let inside=false;for(let i=0,j=P.length-1;i<P.length;j=i++){const a=P[i],b=P[j];if(((a.y>w.y)!==(b.y>w.y))&&w.x<(b.x-a.x)*(w.y-a.y)/(b.y-a.y)+a.x)inside=!inside}
  let s=0;for(let i=0,j=P.length-1;i<P.length;j=i++)s+=(P[i].x-P[j].x)*(P[i].y+P[j].y);const ccw=s<0;return (inside?-1:1)*(ccw?-1:1)}
 let best=null;for(let i=0;i+1<P.length;i++){const a=P[i],b=P[i+1];const d=segDist(w.x,w.y,a.x,a.y,b.x,b.y);if(!best||d<best.d)best={d,a,b}}const cr=(best.b.x-best.a.x)*(w.y-best.a.y)-(best.b.y-best.a.y)*(w.x-best.a.x);return cr>0?1:-1}
estender('runCommand',_rc2=>function(raw){const t=(raw||'').trim().toUpperCase();
 if(['SC','ESCALA','ESCALAR','SCALE'].includes(t)){if(!allSelected().length)return msg('Selecione os objetos e use ESCALA.',true);
  cadCmd={step(w,num){if(!this.base){this.base=w;prompt_('ESCALA — digite o fator (ex.: 1.5) e Enter:');return}if(num==null)return msg('Digite o fator de escala (número) e pressione Enter.',true);if(!(num>0))return msg('Fator deve ser maior que zero.',true);const b=this.base;
   transformSel(p=>({x:b.x+(p.x-b.x)*num,y:b.y+(p.y-b.y)*num}),`escalado(s) × ${num}`);cadCmd=null;prompt_('Comando:')}};prompt_('ESCALA — ponto base:');return}
 if(['MI','ESPELHAR','MIRROR'].includes(t)){if(!allSelected().length)return msg('Selecione os objetos e use ESPELHAR.',true);
  cadCmd={pts:[],step(w){this.pts.push(w);this.base=w;if(this.pts.length===1)return prompt_('ESPELHAR — segundo ponto da linha de simetria:');const [a,b]=this.pts;const dx=b.x-a.x,dy=b.y-a.y,L=dx*dx+dy*dy;if(L<1e-9)return msg('Pontos coincidentes.',true);
   transformSel(p=>{const t2=((p.x-a.x)*dx+(p.y-a.y)*dy)/L;const fx=a.x+t2*dx,fy=a.y+t2*dy;return {x:2*fx-p.x,y:2*fy-p.y}},'espelhado(s) (cópia; os originais foram mantidos)',true);cadCmd=null;prompt_('Comando:')}};prompt_('ESPELHAR — primeiro ponto da linha de simetria:');return}
 if(['OF','OFFSET','DESLOCAR','PARALELA'].includes(t)){const o=objOf(sel);if(!o||o.shape==='pt')return msg('Selecione uma linha, polilinha ou área e use OFFSET.',true);
  cadCmd={dist:null,step(w,num){if(this.dist==null){if(num==null||!(num>0))return msg('Digite a distância (m) do deslocamento e Enter.',true);this.dist=num;prompt_('OFFSET — clique o lado do deslocamento:');return}
   const P=o.grips.map(gripGet),closed=o.shape==='area';const sgn=pointSide(P,w,closed);const Q=offsetPolyline(P,sgn*this.dist,closed);
   checkpoint();if(o.key==='custom_axis'){M.custom_axis={...M.custom_axis,points:Q}}else{const cl=JSON.parse(JSON.stringify(o.o));if(cl&&!Array.isArray(cl)&&'id' in cl)cl.id=uid();M[o.key].push(cl);const n=objList().find(x=>x.key===o.key&&x.i===M[o.key].length-1);n.grips.forEach((g,k)=>gripSet(g,Q[k]));sel={key:o.key,i:M[o.key].length-1};selSet=[]}
   changed(`Paralela a ${this.dist.toFixed(3)} m criada.`);showProps();cadCmd=null;prompt_('Comando:')}};prompt_('OFFSET — distância (m):');cadCmd.base=null;return}
 if(['TELACHEIA','TC','FULL'].includes(t)){toggleFullscreen();return}
 if(['PAINEL','PN'].includes(t)){$('toggleSide')?.click();return}
 if(cadCmd&&cadCmd.step.length===2&&/^-?\d+([.,]\d+)?$/.test(t)&&(cadCmd.base||cadCmd.dist===null)){cadCmd.step(null,Number(t.replace(',','.')));return}
 return _rc2(raw)},'1.24: escalar, espelhar, deslocar paralelo (offset)');
Object.assign(CMD_ALIAS,{SC:'x',ESCALA:'x',MI:'x',ESPELHAR:'x',OF:'x',OFFSET:'x'});
// Atalhos que funcionam também com a tela em foco: Ctrl+Shift+F tela cheia, Ctrl+Shift+L painel.
document.addEventListener('keydown',e=>{if(e.ctrlKey&&e.shiftKey&&!e.altKey){const k=e.key.toLowerCase();if(k==='f'){e.preventDefault();toggleFullscreen()}else if(k==='l'){e.preventDefault();$('toggleSide')?.click()}}},true);

// ---------- 1.24: snap com vértices exatos do desenho (sem simplificação) ----------
let exactSnap=null,exactTimer=null,exactReq=0;
function viewBox(){const a=C2W(0,0),b=C2W(canvas.width,canvas.height),c=C2W(0,canvas.height),d=C2W(canvas.width,0);const xs=[a.x,b.x,c.x,d.x],ys=[a.y,b.y,c.y,d.y];return [Math.min(...xs),Math.min(...ys),Math.max(...xs),Math.max(...ys)]}
function refreshExactSnap(){clearTimeout(exactTimer);exactTimer=setTimeout(async()=>{if(!pid||!ready()||!geo)return;const [x0,y0,x1,y1]=viewBox();if((x1-x0)>1200||(y1-y0)>1200){exactSnap=null;return}
 if(exactSnap&&x0>=exactSnap.b[0]&&y0>=exactSnap.b[1]&&x1<=exactSnap.b[2]&&y1<=exactSnap.b[3])return;const mx=(x1-x0)*.5,my=(y1-y0)*.5,b=[x0-mx,y0-my,x1+mx,y1+my];const id=++exactReq;
 try{const r=await api(`/api/projects/${pid}/snap?x0=${b[0]}&y0=${b[1]}&x1=${b[2]}&y1=${b[3]}`);if(id!==exactReq||!r.available)return;exactSnap={b,v:r.v,m:r.m,trunc:r.truncated}}catch{}},250)}
estender('snapPoint',_sp2=>function(c){const w=c.w;if(exactSnap&&!exactSnap.trunc&&w.x>=exactSnap.b[0]&&w.x<=exactSnap.b[2]&&w.y>=exactSnap.b[1]&&w.y<=exactSnap.b[3]){
  const r=10/Math.max(pxPerM(),1e-9);let best=null;const cand=(x,y,kind,pri)=>{const d=Math.hypot(x-w.x,y-w.y);if(d<=r&&(!best||d+pri*r<best.score))best={w:{x,y},kind,score:d+pri*r}};
  for(const [x,y] of exactSnap.v)if(Math.abs(x-w.x)<=r&&Math.abs(y-w.y)<=r)cand(x,y,'vértice',0);
  for(const [x,y] of exactSnap.m)if(Math.abs(x-w.x)<=r&&Math.abs(y-w.y)<=r)cand(x,y,'ponto médio',.02);
  for(const o of objList())if(!(drag?.type==='grip'&&o.key===drag.g.o.key&&o.i===drag.g.o.i))for(const g of o.grips){const p=gripGet(g);cand(p.x,p.y,'vértice',0)}
  if(!best&&axisData()){const p=projectAxis(w);if(p&&p.dist<=r)best={w:p.point,kind:'eixo',score:p.dist+r}}
  if(best)best.kind+=' (exato)';return best}return _sp2(c)},'1.24: snap com vértices exatos do desenho (sem simplificação)');
estender('draw',_d3=>function(){_d3();if($('snapOn')?.checked)refreshExactSnap()},'1.24: snap com vértices exatos do desenho (sem simplificação)');

