// 2.26: texturas ao vivo no editor 2D. Cada tipo de superfície ganha um padrão procedural contínuo
// (grão, tom, remendos, fissuras, brilho) ancorado no mundo, que reage na hora aos ajustes de texturas.
(()=>{'use strict';
 const SUP={terrain:'canteiro',rock:'rocha_exposta',pavement:'pista_nova',existing_pavement:'pista_existente',shoulder:'acostamento',median:'canteiro',cut:'talude_corte',fill:'talude_aterro',oae:'oae_nova'};
 const BASE={rocha_exposta:[138,135,129],pista_nova:[44,45,48],pista_existente:[118,118,114],acostamento:[138,128,106],canteiro:[112,142,92],talude_corte:[183,105,84],talude_aterro:[156,189,117],oae_nova:[176,176,171]};
 const LADO=128,TILE_M=4;// 128 px = 4 m de terreno
 let ligado=true,forca=.85;const cache=new Map();
 function lcg(s){s=(s>>>0)||1;return()=>{s=(Math.imul(s,1664525)+1013904223)>>>0;return s/4294967296}}
 // ruído de valor periódico (tileável)
 function ruido(rnd,n){const g=Array.from({length:n*n},()=>rnd());return(x,y)=>{x=((x%n)+n)%n;y=((y%n)+n)%n;const x0=Math.floor(x),y0=Math.floor(y),fx=x-x0,fy=y-y0,sx=fx*fx*(3-2*fx),sy=fy*fy*(3-2*fy),X=(x0+1)%n,Y=(y0+1)%n;
  const a=g[y0*n+x0],b=g[y0*n+X],c=g[Y*n+x0],d=g[Y*n+X];return a+(b-a)*sx+(c-a)*sy+(a-b-c+d)*sx*sy}}
 function gerar(sup,p,lado=LADO){
  p=Object.assign({grao:1,tom:1,remendos:1,fissuras:1,brilho:0},p||{});const cor=Array.isArray(p.baseColor)&&p.baseColor.length===3?p.baseColor:BASE[sup]||[100,100,100];
  const rnd=lcg(sup.length*7919+13),r1=ruido(rnd,16),r2=ruido(rnd,4),r3=ruido(rnd,32);const px=new Uint8ClampedArray(lado*lado*4);
  const asfalto=/pista|oae/.test(sup),veg=/canteiro|aterro|corte/.test(sup);
  for(let y=0;y<lado;y++)for(let x=0;x<lado;x++){const u=x/lado,v=y/lado;
   const ruidoFino=(rnd()-.5);let g=ruidoFino*(asfalto?30:veg?26:20)*p.grao+(r3(u*32,v*32)-.5)*(asfalto?14:18)*p.grao+(r1(u*16,v*16)-.5)*6*p.grao;
   if(sup==='pista_nova'&&rnd()>.925)g+=(34+rnd()*40)*p.grao;// agregado britado claro sobre ligante preto
   let t=(r2(u*4,v*4)-.5)*(asfalto?9:veg?14:12)*p.tom;
   if(p.artistic&&asfalto){g*=.35;t*=.35;}
   let rem=0;const rm=r2(u*4+7,v*4+3);if(!p.artistic&&rm>.8)rem=(rm-.8)*60*p.remendos*(asfalto?-1:.5);
   let fis=0;if(asfalto&&!p.artistic){const f=Math.abs(r1(u*16+3,v*16+9)-.5);if(f<.012*p.fissuras)fis=-26*Math.min(1.4,p.fissuras)}
   if(sup==='rocha_exposta'){g=(rnd()-.5)*8+(r2(u*4,v*4)-.5)*20;t=0;rem=0;fis=Math.abs(Math.sin(Math.PI*2*(3*u+v+.1*r1(u*16,v*16))))<.13?-35:0;}
   if(veg){g*=1.1}
   const br=p.brilho*60;const k=g+t+rem+fis+br;const i=(y*lado+x)*4;
   px[i]=cor[0]+k*(veg?.6:1);px[i+1]=cor[1]+k;px[i+2]=cor[2]+k*(veg?.4:1);px[i+3]=255}
  return px}
 function padrao(sup,p){const ch=sup+JSON.stringify(p||{});if(cache.has(ch))return cache.get(ch);
  if(typeof document==='undefined'){return null}
  const cv=document.createElement('canvas');cv.width=cv.height=LADO;const c=cv.getContext('2d');if(!c)return null;
  const im=c.createImageData(LADO,LADO);im.data.set(gerar(sup,p));c.putImageData(im,0,0);const pt=ctx.createPattern(cv,'repeat');
  if(cache.size>40)cache.clear();cache.set(ch,pt);return pt}
 /* 2.43: o TIPO de textura (material flexível/rígido, perfil técnico/artístico, estilo de representação por pista, ajustes de grão/tom...) vale na hora no editor 2D.
    Tudo vem de RodoviaAparencia.leitura() (caixas da tela + rascunho de quem está arrastando), igual ao que o vídeo usa depois de salvar. */
 const CONCRETO=[168,167,160],MATERIAL_DE={pavement:'pavement_material',existing_pavement:'existing_material',shoulder:'shoulder_material'};
 function ladrilho(sup,mat,junta,artistic=false){const ch='mat|'+sup+'|'+mat+'|'+junta+'|'+artistic;if(cache.has(ch))return cache.get(ch);if(typeof document==='undefined')return null;
  const C=artistic?[194,194,187]:CONCRETO,L=LADO,cv=document.createElement('canvas');cv.width=cv.height=L;const c=cv.getContext('2d');if(!c)return null;
  const im=c.createImageData(L,L);im.data.set(gerar(sup,{grao:.7,tom:1,remendos:.4,fissuras:.2,brilho:0,artistic}));
  // concreto: cor clara (a base de asfalto é escura) e juntas das placas no espaçamento configurado
  for(let i=0;i<L*L;i++){const k=(im.data[i*4]-BASE[sup][0]);im.data[i*4]=C[0]+k;im.data[i*4+1]=C[1]+k;im.data[i*4+2]=C[2]+k}
  c.putImageData(im,0,0);c.strokeStyle=artistic?'rgba(102,104,100,.4)':'rgba(60,60,58,.75)';c.lineWidth=artistic?1:2;/* Juntas são vetoriais e seguem o eixo; nunca ficam gravadas na imagem repetida. */
  const pt=ctx.createPattern(cv,'repeat');cache.set(ch,pt);return pt}
 function ladrilhoEstilo(st,mpx){const esp=Math.max(.3,Number(st.spacing_m)||3),K=32,px=Math.max(8,Math.min(512,Math.round(esp*K)));
  const ch='est|'+JSON.stringify(st)+'|'+px;if(cache.has(ch))return cache.get(ch);if(typeof document==='undefined')return null;
  const cv=document.createElement('canvas');cv.width=cv.height=px;const c=cv.getContext('2d');if(!c)return null;
  c.fillStyle=st.fill||'#2a3033';c.fillRect(0,0,px,px);c.strokeStyle=c.fillStyle=st.hatch||'#c8a55a';const w=Math.max(1,(Number(st.line_m)||.15)*K);c.lineWidth=w;
  const p=st.pattern;
  if(p==='diagonal'||p==='cruzada'){c.beginPath();c.moveTo(0,px/2);c.lineTo(px,px/2);c.stroke();if(p==='cruzada'){c.beginPath();c.moveTo(px/2,0);c.lineTo(px/2,px);c.stroke()}}
  else if(p==='pontilhado'){c.beginPath();c.arc(px/2,px/2,Math.max(1.2,w),0,7);c.fill()}
  else if(p==='placas'){c.strokeRect(0,0,px,px)}
  const pat=ctx.createPattern(cv,'repeat');cache.set(ch,{pat,px});return cache.get(ch)}
 // 2.54: afastado (ladrilho < 14 px) a textura não cabe, mas o TIPO escolhido tem de aparecer: preenche com a cor média do padrão (muda ao trocar material/ajustes)
 function corMedia(sup,p,rigido){const ch='med|'+sup+'|'+(rigido?'r':'f')+JSON.stringify(p||{});if(cache.has(ch))return cache.get(ch);
  const d=gerar(sup,rigido?{grao:.7,tom:1,remendos:.4,fissuras:.2,brilho:0}:p,32);let r=0,g=0,b=0;const n=d.length/4;for(let i=0;i<d.length;i+=4){r+=d[i];g+=d[i+1];b+=d[i+2]}
  let m=[r/n,g/n,b/n];if(rigido){const o=BASE[sup]||[100,100,100];const C=p?.artistic?[194,194,187]:CONCRETO;m=[C[0]+(m[0]-o[0]),C[1]+(m[1]-o[1]),C[2]+(m[2]-o[2])]}
  const css='rgb('+m.map(x=>Math.max(0,Math.min(255,Math.round(x)))).join(',')+')';cache.set(ch,css);return css}
 function drawDetails(c,v,mpx){
  if(!v.jointPath&&!v.railPath)return;c.save();if(v.fill)c.clip(v.fill,'evenodd');c.globalAlpha=typeof vecAlpha==='number'?vecAlpha:1;c.setLineDash([]);
  if(v.jointPath){c.lineWidth=Math.max(.025/mpx,.5/view.s);c.strokeStyle='#777a75';c.stroke(v.jointPath)}
  if(v.railPath){c.lineWidth=.65/mpx;c.strokeStyle='#747c7c';c.stroke(v.railPath);c.lineWidth=.32/mpx;c.strokeStyle='#e0e0d6';c.stroke(v.railPath)}c.restore();
 }
 function pintarRole(c,role,v,overrides={}){
  if(!ligado||!SUP[role]||!v||!v.fill||typeof geo==='undefined'||!geo)return;
  const A={...((typeof window!=='undefined'&&window.RodoviaAparencia)?window.RodoviaAparencia.leitura():{}),...overrides};
  if(['flexivel','rigido'].includes(v.material)&&MATERIAL_DE[role])A[MATERIAL_DE[role]]=v.material;
  if(A.texture_style==='anterior')return;
  const rigid=role==='oae'||v.material==='rigido'||A[MATERIAL_DE[role]]==='rigido';
  if(A.style_profile==='tecnico'&&!rigid)return;   // perfil técnico / texturas anteriores: sem textura procedural
  const mpx=geo.R0/geo.k;if(!mpx)return;
  const projected=role==='pavement'&&v.existing===false;
  const st=(A.ps||{})[role];
  if(st&&st.pattern&&st.pattern!=='auto'&&st.pattern!=='placas'&&!rigid){
   if(TILE_M/mpx*view.s<14){c.save();c.globalAlpha=Math.min(1,projected?1:(typeof vecAlpha==='number'?vecAlpha:1)*.8);c.fillStyle=st.fill||'#2a3033';c.fill(v.fill,'evenodd');c.restore();return}
   const e=ladrilhoEstilo(st,mpx);if(!e||!e.pat)return;const K=32,sc=1/mpx/K;
   if(e.pat.setTransform&&typeof DOMMatrix!=='undefined'){const m=new DOMMatrix();e.pat.setTransform((st.pattern==='diagonal'||st.pattern==='cruzada')?m.rotate(-(Number(st.angle_deg)||0)).scale(sc,sc):m.scale(sc,sc))}
   c.save();c.globalAlpha=Math.min(1,(typeof vecAlpha==='number'?vecAlpha:1));c.fillStyle=e.pat;c.fill(v.fill,'evenodd');c.restore();return}
  const pxTile=TILE_M/mpx*view.s;
  const mat=role==='oae'?'rigido':MATERIAL_DE[role]?A[MATERIAL_DE[role]]:null,rigido=mat==='rigido';
  let tp=A.tp||{};
  if(A.texture_style==='artistico'){const sup=SUP[role];tp={...tp,[sup]:{...(tp[sup]||{}),artistic:true,...(role==='existing_pavement'?{baseColor:[86,91,96]}:{})}};}
  // A cor manual muda a base, mantendo o grão de grama e os contornos DXF.
  const manual=(A.rc||A.role_colors||{})[role==='rock'?'cut':role];
  if(/^#[0-9a-f]{6}$/i.test(manual||''))tp={...tp,[SUP[role]]:{...(tp[SUP[role]]||{}),baseColor:[1,3,5].map(i=>parseInt(manual.slice(i,i+2),16))}};
  if(pxTile<14){c.save();c.globalAlpha=Math.min(1,projected?1:(typeof vecAlpha==='number'?vecAlpha:1)*.8);c.fillStyle=corMedia(SUP[role],tp[SUP[role]],rigido);c.fill(v.fill,'evenodd');c.restore();return}
const pt=rigido?ladrilho(SUP[role],'rigido',A.joint_spacing_m||5,A.texture_style==='artistico'):padrao(SUP[role],tp[SUP[role]]);if(!pt)return;
  const k=rigido?Math.max(.5,Number(A.joint_spacing_m)||5)/mpx/LADO:TILE_M/mpx/LADO;if(pt.setTransform&&typeof DOMMatrix!=='undefined')pt.setTransform(new DOMMatrix().scale(k,k));
  c.save();c.globalAlpha=Math.min(1,projected?1:(typeof vecAlpha==='number'?vecAlpha:1)*forca);c.fillStyle=pt;c.fill(v.fill,'evenodd');c.restore();if(rigido)drawDetails(c,v,mpx)}
 // Áreas editáveis usam os mesmos materiais e a mesma escala métrica dos vetores.
 function pintarArea(c,a){
  if(!ligado||!geo||a.enabled===false||!a.points||a.points.length<3)return false;
  const A=window.RodoviaAparencia?.leitura()||{};
  if(A.texture_style==='anterior'||(A.style_profile==='tecnico'&&a.material!=='rigido'&&A[MATERIAL_DE[a.kind]]!=='rigido'&&a.kind!=='oae'))return false;
  const role=a.kind||'pavement',field=MATERIAL_DE[role];if(!SUP[role])return false;
  const path=new Path2D();
  for(const ring of [a.points,...(a.holes||[])]){if(ring.length<3)continue;ring.forEach((p,i)=>{const q=worldToImg(p);if(i)path.lineTo(...q);else path.moveTo(...q)});path.closePath()}
  const overrides={};if(field&&['rigido','flexivel'].includes(a.material))overrides[field]=a.material;
  if(a.texture)overrides.tp={...(A.tp||{}),[SUP[role]]:{...((A.tp||{})[SUP[role]]||{}),...a.texture}};
  c.save();try{c.setTransform(view.s,0,0,view.s,view.ox,view.oy);const params={...((overrides.tp||A.tp||{})[SUP[role]]||{}),artistic:A.texture_style==='artistico'};if(role==='existing_pavement'&&params.artistic)params.baseColor=[86,91,96];c.globalAlpha=1;c.fillStyle=A.ps?.[role]?.fill||corMedia(SUP[role],params,(role==='oae'||(overrides[field]||A[field])==='rigido'));c.fill(path,'evenodd');pintarRole(c,role,{fill:path,existing:role==='existing_pavement',...(window.RodoviaAreaDetails?.get(a.id)||{})},overrides)}finally{c.restore()}
  return true;
 }
 function pintar(){return}
 function pintar_antigo(){
  if(!ligado||typeof vecPaths==='undefined'||!vecPaths||typeof ctx==='undefined'||!ctx)return;
  const mpx=(typeof geo!=='undefined'&&geo)?geo.R0/geo.k:0;if(!mpx)return;
  const tp=(typeof cfg!=='undefined'&&cfg&&cfg.texture_params)||{};
  const pxTile=TILE_M/mpx*view.s;if(pxTile<14)return;// distante demais: evita ruído
  ctx.save();ctx.setTransform(view.s,0,0,view.s,view.ox,view.oy);ctx.globalAlpha=Math.min(1,(typeof vecAlpha==='number'?vecAlpha:1)*forca);
  for(const role of Object.keys(SUP)){const v=vecPaths[role];if(!v||!v.fill||(typeof vecOn!=='undefined'&&vecOn[role]===false))continue;
   const pt=padrao(SUP[role],tp[SUP[role]]);if(!pt)continue;const k=TILE_M/mpx/LADO;
   if(pt.setTransform&&typeof DOMMatrix!=='undefined')pt.setTransform(new DOMMatrix().scale(k,k));
   ctx.fillStyle=pt;ctx.fill(v.fill,'evenodd')}
  ctx.restore()}
 function botao(){const box=document.getElementById('vecLayers');if(!box||document.getElementById('texVivaLbl'))return;
  const l=document.createElement('label');l.id='texVivaLbl';l.className='vl';l.innerHTML='<input type="checkbox" id="texViva" checked><span style="background:#8a8f98"></span>Texturas ao vivo';
  box.parentNode.insertBefore(l,box);l.querySelector('input').addEventListener('change',e=>{ligado=e.target.checked;try{draw()}catch(_e){window.RodoviaErros&&RodoviaErros.avisar('texturas_vivas',_e)}})}
 if(typeof draw==='function'){const antigo=draw;draw=function(...a){const r=antigo(...a);try{pintar()}catch(e){(window.RodoviaErros||{avisar(){}}).avisar('texturas ao vivo',e)}return r}}
 if(typeof document!=='undefined')document.addEventListener('DOMContentLoaded',()=>{try{botao()}catch(_e){window.RodoviaErros&&RodoviaErros.avisar('texturas_vivas',_e)}});
 const api={gerar,SUP,BASE,pintar,pintarRole,pintarArea,corMedia,ligar(v){ligado=!!v}};
 if(typeof window!=='undefined')window.RodoviaTexturasVivas=api;
 if(typeof globalThis!=='undefined')globalThis.RodoviaTexturasVivas=api;
})();
