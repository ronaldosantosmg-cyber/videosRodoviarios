// ---------------- 1.20: áreas de pista e acostamentos ----------------
const PAV_LABEL={pavement:'Pista nova',existing_pavement:'Pista existente',shoulder:'Acostamento'};
const PAV_STYLE={pavement:['#3a414355','#d8b45acc',9],existing_pavement:['#8fa3b455','#9fb4c8cc',9],shoulder:['#85898355','#e8dcaacc',6]};
let pavKind='pavement',pavMat='auto';
const MAT_LABEL={auto:'Material padrão do projeto',flexivel:'Flexível (asfalto)',rigido:'Rígido (concreto)'};
function pickRing(w){if(!vec||!vec.layers)return null;let best=null;
 for(const [role,list] of Object.entries(vec.layers)){if(!Array.isArray(list))continue;for(const r of list){if(!r.c||!r.p||r.p.length<3)continue;const P=r.p;let inside=false;for(let i=0,j=P.length-1;i<P.length;j=i++){const [xi,yi]=P[i],[xj,yj]=P[j];if(((yi>w.y)!==(yj>w.y))&&w.x<(xj-xi)*(w.y-yi)/(yj-yi)+xi)inside=!inside}
  if(!inside)continue;let a=0;for(let i=0,j=P.length-1;i<P.length;j=i++)a+=(P[j][0]+P[i][0])*(P[j][1]-P[i][1]);a=Math.abs(a/2);if(!best||a<best.a)best={a,p:P}}}
 if(!best)return null;let P=best.p;if(P.length>1&&P[0][0]===P[P.length-1][0]&&P[0][1]===P[P.length-1][1])P=P.slice(0,-1);return P.length>=3?P:null}

// 1.20: perfil "Apresentação técnica" (alinhado à especificação de vídeo técnico): só altera campos da configuração.
$('presetTech')?.addEventListener('click',guard(async()=>{requireProject();const set={width:2560,fps:24,duration_s:96,style_profile:'tecnico',camera_mode:'continuo',flow_arrows:'off'};
 for(const [k,v] of Object.entries(set))if($(k))$(k).value=v;$('traffic').checked=false;$('progress_indicator').checked=true;await save();
 $('presetInfo').textContent='Aplicado: 2560×1440, 24 q/s, 96 s, hachuras técnicas, voo contínuo, sem setas de fluxo e sem veículos, indicador de progresso. Ajuste a duração à extensão do trecho e gere a prévia.';msg('Perfil “Apresentação técnica” aplicado.')}));

$('project_contrast')?.addEventListener('input',()=>{$('pcVal').textContent=Math.round(Number($('project_contrast').value)*100)+'%'});

// ---------------- 1.21: representação do pavimento (escolha e alteração) ----------------
const PAT_LABEL={auto:'Automática (material + montagem)',solido:'Sólido',diagonal:'Hachura diagonal',cruzada:'Hachura cruzada',pontilhado:'Pontilhado',placas:'Placas de concreto (juntas)'};
const ROLE_LABEL={pavement:'Pista nova',existing_pavement:'Pista existente',shoulder:'Acostamento'};
const PAV_DEF={pavement:['#2a3033','#c8a55a'],existing_pavement:['#6f8291','#b7c7d4'],shoulder:['#5f5b51','#d6cda4']};
function pavStylesUi(){const box=$('pavStyles');if(!box)return;const st=cfg.pavement_styles||{};
 box.innerHTML='<table class="pavst">'+Object.keys(ROLE_LABEL).map(r=>{const v={pattern:'auto',fill:'',hatch:'',spacing_m:3,angle_deg:45,line_m:.15,...(st[r]||{})};
  return `<tr data-role="${r}"><td><b>${ROLE_LABEL[r]}</b><br><canvas class="swatch" width="84" height="48"></canvas></td><td><select data-k="pattern">${Object.entries(PAT_LABEL).map(([k,l])=>`<option value="${k}" ${v.pattern===k?'selected':''}>${l}</option>`).join('')}</select>
  <div class="grid"><label>Preenchimento<input data-k="fill" type="color" value="${v.fill||PAV_DEF[r][0]}"></label><label>Hachura/juntas<input data-k="hatch" type="color" value="${v.hatch||PAV_DEF[r][1]}"></label><label>Espaçamento (m)<input data-k="spacing_m" type="number" min="0.3" max="20" step="0.1" value="${v.spacing_m}"></label><label>Ângulo (°)<input data-k="angle_deg" type="number" min="-90" max="90" step="1" value="${v.angle_deg}"></label><label>Espessura do traço (m)<input data-k="line_m" type="number" min="0.02" max="1" step="0.01" value="${v.line_m}"></label></div></td></tr>`}).join('')+'</table>';
 box.querySelectorAll('tr[data-role]').forEach(drawSwatch)}
function drawSwatch(tr){const c=tr.querySelector('canvas'),g=c.getContext('2d'),v=readStyle(tr),r=tr.dataset.role;g.fillStyle=v.pattern==='auto'?PAV_DEF[r][0]:v.fill;g.fillRect(0,0,c.width,c.height);g.strokeStyle=v.hatch;g.fillStyle=v.hatch;const k=6;// 6 px por metro na amostra
 const S=v.spacing_m*k,w=Math.max(1,v.line_m*k);g.lineWidth=w;const lines=a=>{const t=a*Math.PI/180;g.save();g.translate(c.width/2,c.height/2);g.rotate(-t);g.beginPath();for(let y=-120;y<=120;y+=S){g.moveTo(-120,y);g.lineTo(120,y)}g.stroke();g.restore()};
 if(v.pattern==='diagonal'||v.pattern==='auto')lines(v.angle_deg);if(v.pattern==='cruzada'){lines(v.angle_deg);lines(v.angle_deg+90)}
 if(v.pattern==='pontilhado')for(let x=S/4;x<c.width;x+=S/2)for(let y=S/4;y<c.height;y+=S/2){g.beginPath();g.arc(x,y,w,0,7);g.fill()}
 if(v.pattern==='placas'){g.lineWidth=Math.max(1,w);for(let x=0;x<c.width;x+=(cfg.joint_spacing_m||5)*k){g.beginPath();g.moveTo(x,0);g.lineTo(x,c.height);g.stroke()}}}
function readStyle(tr){const o={};tr.querySelectorAll('[data-k]').forEach(el=>{o[el.dataset.k]=el.type==='number'?Number(el.value):el.value});return o}
$('pavStyles')?.addEventListener('change',e=>{const tr=e.target.closest('tr[data-role]');if(!tr||!pid)return;const v=readStyle(tr),r=tr.dataset.role;const st={...(cfg.pavement_styles||{})};
 if(v.pattern==='auto')delete st[r];else st[r]={...v,fill:v.fill.toLowerCase()===PAV_DEF[r][0]?'':v.fill,hatch:v.hatch.toLowerCase()===PAV_DEF[r][1]?'':v.hatch};
 cfg.natural_materials_only=false;if($('natural_materials_only'))$('natural_materials_only').checked=false;cfg.pavement_styles=st;drawSwatch(tr);scheduleSave();msg(`Representação de “${ROLE_LABEL[r]}”: ${PAT_LABEL[v.pattern]}. Gere a prévia para ver no vídeo.`)});
$('pavStyles')?.addEventListener('input',e=>{const tr=e.target.closest('tr[data-role]');if(tr)drawSwatch(tr)});
estender('load',_l3=>async (id,options={})=>{const loaded=await _l3(id,options);if(loaded===false||pid!==id)return false;if(options.resultsOnly)return loaded;try{pavStylesUi()}catch{};return loaded},'1.21: representação do pavimento (escolha e alteração)');

