// ---------- Pincel de textura ----------
let brush=null;
function brushFrom(o){if(!o)return null;if(o.key==='pavement_areas')return {mode:'pav',kind:o.o.kind||'pavement',material:o.o.material||'auto',texture:o.o.texture?{...o.o.texture}:null,name:o.o.name};
 if(o.key==='texture_areas')return {mode:'tex',surface:o.o.surface,texture:o.o.texture?{...o.o.texture}:null,name:o.o.name};return null}
function brushFromDxf(r){if(['pavement','existing_pavement','shoulder'].includes(r.role))return {mode:'pav',kind:r.role,material:'auto',texture:null,name:`área do desenho (${r.layer})`};
 const surf=SURF_MODE[r.role];if(surf&&!['pista_nova','pista_existente','acostamento'].includes(surf))return {mode:'tex',surface:surf,texture:(cfg.texture_params||{})[surf]?{...cfg.texture_params[surf]}:null,name:`área do desenho (${r.layer})`};return null}
function startBrush(){if(!pid||!ready())return msg('Abra o editor de um projeto primeiro.',true);const L=selObjs();const src=L.length===1?brushFrom(L[0]):null;brush={src,n:0};setTool('brush');canvas.style.cursor='copy';
 if(L.length)clearSelection();msg(src?`PINCEL — copiando a textura de “${src.name}”. Clique nas áreas de destino; Esc ou Enter encerra.`:'PINCEL — clique na área de ORIGEM (área de pista, região de textura ou área do desenho).');toolOptions()}
function inPoly(pts,w){let ins=false;for(let i=0,j=pts.length-1;i<pts.length;j=i++){const a=pts[i],b=pts[j];if(((a.y>w.y)!==(b.y>w.y))&&w.x<(b.x-a.x)*(w.y-a.y)/((b.y-a.y)||1e-12)+a.x)ins=!ins}return ins}
// Áreas com textura sob o ponto têm prioridade (rotas, fluxos e outros objetos por cima não atrapalham o pincel).
function brushHit(w){for(const key of ['texture_areas','pavement_areas']){const L=M[key]||[];for(let i=L.length-1;i>=0;i--)if(L[i].points&&L[i].points.length>2&&inPoly(L[i].points,w))return objOf({key,i})}return null}
async function brushClick(w,e){if(!brush)brush={src:null,n:0};const [cx,cy]=W2C(w);let o=brushHit(w);if(!o){const h=hitObject({cx,cy});o=h?objOf({key:h.key,i:h.i}):null;if(o&&!['pavement_areas','texture_areas'].includes(o.key)&&o.shape!=='area')o=null}
 if(!brush.src){let s=brushFrom(o);if(!s){try{const r=await api(`/api/projects/${pid}/area?x=${w.x}&y=${w.y}`);s=brushFromDxf(r)}catch(err){}}
  if(!s)return msg('Aqui não há área com textura. Clique numa área de pista, numa região de textura ou numa área do desenho.',true);brush.src=s;toolOptions();return msg(`Origem: “${s.name}”. Agora clique nas áreas de destino (Esc ou Enter encerra).`)}
 const s=brush.src;
 if(o&&(o.key==='pavement_areas'||o.key==='texture_areas')){checkpoint();
  if(o.key==='pavement_areas'){if(s.mode==='pav'){o.o.kind=s.kind;o.o.material=s.material}o.o.texture=s.texture?{...s.texture}:null}
  else{if(s.mode==='tex')o.o.surface=s.surface;o.o.texture=s.texture?{...s.texture}:null}
  brush.n++;changed(`Pincel: textura aplicada a “${o.o.name}” (${brush.n}). Continue clicando; Esc encerra.`);toolOptions();return}
 if(o)return msg(`“${o.label}” não tem textura. Clique numa área de pista, região de textura ou área do desenho.`,true);
 let r;try{r=await api(`/api/projects/${pid}/area?x=${w.x}&y=${w.y}`)}catch(err){return msg('Nenhuma área fechada do desenho neste ponto.',true)}
 checkpoint();
 if(s.mode==='pav'){const n=M.pavement_areas.length+1;M.pavement_areas.push({id:uid(),name:`${PAV_LABEL[s.kind]||'Área'} ${n} (${r.layer})`.slice(0,80),kind:s.kind,points:r.points.map(P_),source:'picked',material:s.material,enabled:true,texture:s.texture?{...s.texture}:null})}
 else{const n=M.texture_areas.length+1;M.texture_areas.push({id:uid(),name:`${SURF_NAME[s.surface]||s.surface} ${n} (${r.layer})`.slice(0,80),surface:s.surface,points:r.points.map(P_),texture:s.texture?{...s.texture}:null,enabled:true})}
 brush.n++;changed(`Pincel: área do desenho (camada ${r.layer}) recebeu a textura (${brush.n}). O DXF não muda. Esc encerra.`);toolOptions()}


function brushOptions(o){o.innerHTML=`<p><b>Pincel de textura</b> — ${brush&&brush.src?`origem: “${esc(brush.src.name)}” (${brush.src.mode==='pav'?esc(PAV_LABEL[brush.src.kind]||brush.src.kind):esc(SURF_NAME[brush.src.surface]||brush.src.surface)}${brush.src.texture?', textura própria':', textura do tipo'})`:'clique na área de origem'} · ${brush?brush.n:0} aplicação(ões).</p><p class="muted">Clique nas áreas de destino. Esc ou Enter encerra. Ctrl+Z desfaz a última aplicação.</p>`}
ferramenta('brush',{rotulo:'🖌 Pincel de textura',dica:'Clique na área de ORIGEM (área de pista, região de textura ou área do desenho); depois clique em quantas áreas quiser para aplicar a mesma textura. Esc ou Enter encerra.',
 icone:'M14 4l6 6-8 8-6-6zM6 12l-3 8 8-3M15 9l-2-2',clique:brushClick,opcoes:brushOptions,
 esc(){setTool('pan')},
 entrar(){canvas.style.cursor='copy'},
 sair(){const n=brush?brush.n:0;const had=!!brush;brush=null;if(had)msg(`Pincel encerrado: ${n} aplicação(ões).${n?' Gere a prévia para ver no vídeo.':''}`)}});
itemFaixa('Editar','Propriedades',['Pincel de textura','🖌',()=>startBrush(),1],{posicao:3});
comando(['PINCEL','PI','BRUSH'],()=>startBrush(),'Pincel de textura: copia de uma área e aplica em várias até Esc');
