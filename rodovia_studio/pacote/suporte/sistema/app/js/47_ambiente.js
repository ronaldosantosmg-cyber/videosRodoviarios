// =====================================================================================================
// 1.36: câmera por pontos-chave, clima, sombras pela hora do sol e comparação antes/depois (estilo Twinmotion).
// =====================================================================================================
MARK_KEYS.push('camera_keys');estender('emptyMarks',_em=>function(){return {..._em(),camera_keys:[]}},'câmera por pontos-chave');if(!M.camera_keys)M.camera_keys=[];
fields.push('weather','weather_intensity','sun_hour','before_after_s');numeric.push('weather_intensity','sun_hour','before_after_s');checks.push('sun_shadows','before_after');
function vistaAtual(){const c=C2W(canvas.width/2,canvas.height/2),a=C2W(0,canvas.height/2),b=C2W(canvas.width,canvas.height/2);return {x:+c.x.toFixed(3),y:+c.y.toFixed(3),width_m:Math.max(20,Math.round(Math.hypot(b.x-a.x,b.y-a.y)))}}
function irParaVista(k){const [ix,iy]=worldToImg({x:k.x,y:k.y});const a=worldToImg({x:k.x-k.width_m/2,y:k.y}),b=worldToImg({x:k.x+k.width_m/2,y:k.y});const wimg=Math.hypot(b[0]-a[0],b[1]-a[1])||1;
 view.s=canvas.width/wimg;view.ox=canvas.width/2-ix*view.s;view.oy=canvas.height/2-iy*view.s;draw()}
function adicionarVista(){requireProject();if(!ready())return msg('Analise os arquivos primeiro.',true);const v=vistaAtual();checkpoint();
 (M.camera_keys=M.camera_keys||[]).push({id:uid(),...v,hold_s:3,title:''});
 if($('camera_mode')&&$('camera_mode').value!=='pontos'&&M.camera_keys.length>=2){$('camera_mode').value='pontos';scheduleSave()}
 changed(`Ponto-chave ${M.camera_keys.length} adicionado (largura ${v.width_m.toLocaleString('pt-BR')} m).`+(M.camera_keys.length<2?' Adicione mais um para o voo.':''))}
function renderVistas(){const tb=$('ckRows');if(!tb)return;const K=M.camera_keys||[];
 tb.innerHTML=K.length?K.map((k,i)=>`<tr data-ck="${i}"><td><b>${i+1}</b></td><td><input data-ckf="title" value="${esc(k.title||'')}" maxlength="100" placeholder="(sem título)"></td>
  <td><input data-ckf="hold_s" type="number" min="0" max="120" step="0.5" value="${k.hold_s}" style="width:64px"></td><td class="nw">${Math.round(k.width_m).toLocaleString('pt-BR')} m</td>
  <td class="acts nw"><button type="button" class="mini" data-cka="ver" title="Ir para esta vista">⌖</button><button type="button" class="mini" data-cka="aqui" title="Trocar pela vista atual">⟲</button><button type="button" class="mini" data-cka="sobe" title="Subir" ${i?'':'disabled'}>↑</button><button type="button" class="mini" data-cka="desce" title="Descer" ${i<K.length-1?'':'disabled'}>↓</button><button type="button" class="mini danger" data-cka="del" title="Excluir">🗑</button></td></tr>`).join('')
  :'<tr><td colspan="5" class="muted">Nenhum ponto-chave.</td></tr>';
 if($('ckInfo'))$('ckInfo').textContent=K.length?`${K.length} ponto(s); paradas somam ${K.reduce((a,k)=>a+Number(k.hold_s||0),0)} s`:''}
estender('refreshLists',anterior=>function(){anterior();renderVistas()},'câmera: lista de pontos-chave');
$('ckAdd')?.addEventListener('click',guard(adicionarVista));
$('ckRows')?.addEventListener('change',e=>{const el=e.target.closest('[data-ckf]');if(!el)return;const k=M.camera_keys[Number(el.closest('[data-ck]').dataset.ck)];if(!k)return;
 checkpoint();k[el.dataset.ckf]=el.dataset.ckf==='hold_s'?Math.max(0,Math.min(120,Number(el.value)||0)):el.value.slice(0,100);changed('Ponto-chave alterado.')});
$('ckRows')?.addEventListener('keydown',e=>{if(e.key==='Enter'&&e.target.closest('[data-ckf]')){e.preventDefault();e.stopPropagation();e.target.blur()}});
$('ckRows')?.addEventListener('click',e=>{const b=e.target.closest('[data-cka]');if(!b)return;const i=Number(b.closest('[data-ck]').dataset.ck),K=M.camera_keys,a=b.dataset.cka;
 if(a==='ver'){irParaVista(K[i]);return}checkpoint();
 if(a==='aqui')Object.assign(K[i],vistaAtual());else if(a==='sobe'&&i>0)[K[i-1],K[i]]=[K[i],K[i-1]];else if(a==='desce'&&i<K.length-1)[K[i+1],K[i]]=[K[i],K[i+1]];else if(a==='del')K.splice(i,1);
 changed('Pontos-chave alterados (Ctrl+Z desfaz).')});
// Editor: área aproximada de cada vista (círculo com a largura) e o caminho do voo.
estender('draw',anterior=>function(){anterior();const K=M.camera_keys||[];if(!ready()||!K.length||vecOn?.camera===false)return;try{ctx.save();
 const P=K.map(k=>W2C(k));ctx.setLineDash([8,6]);ctx.lineWidth=2;ctx.strokeStyle='#ffd400';ctx.beginPath();P.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.stroke();ctx.setLineDash([]);
 K.forEach((k,i)=>{const [x,y]=P[i];const r=k.width_m/2*pxPerM();ctx.globalAlpha=.9;ctx.strokeStyle='#ffd400';ctx.lineWidth=1.5;if(r>8&&r<4000){ctx.beginPath();ctx.rect(x-r,y-r*9/16,2*r,r*9/8);ctx.stroke()}
  ctx.globalAlpha=1;ctx.fillStyle='#ffd400';ctx.beginPath();ctx.arc(x,y,11,0,2*Math.PI);ctx.fill();ctx.fillStyle='#1b1b1b';ctx.font='bold 12px "Segoe UI",system-ui';ctx.textAlign='center';ctx.fillText(String(i+1),x,y+4);ctx.textAlign='left';
  if(k.title){ctx.fillStyle='#000a';const tw=ctx.measureText(k.title).width;ctx.fillRect(x+14,y-9,tw+8,18);ctx.fillStyle='#ffd400';ctx.fillText(k.title,x+18,y+4)}});
 ctx.restore()}catch(e){ctx.restore()}},'câmera: pontos-chave no editor');
// Rótulos dos controles deslizantes.
function rotulosAmbiente(){if($('wiVal'))$('wiVal').textContent=Math.round(Number($('weather_intensity')?.value||.6)*100)+'%';const h=Number($('sun_hour')?.value||15);if($('shVal'))$('shVal').textContent=`${Math.floor(h)}h${h%1?'30':'00'}`}
['weather_intensity','sun_hour'].forEach(id=>$(id)?.addEventListener('input',rotulosAmbiente));estender('fill',anterior=>function(s){anterior(s);rotulosAmbiente();renderVistas()},'ambiente: rótulos');
// Faixa de opções e comandos.
itemFaixa('Vídeo','Ambiente',['Ponto-chave da câmera','📍',()=>guard(adicionarVista)(),1]);itemFaixa('Vídeo','Ambiente',['Clima e sol','⛅',()=>openSection('Câmera, clima')]);
comando(['CAMERA','PC'],()=>guard(adicionarVista)(),'Adiciona a vista atual como ponto-chave da câmera do vídeo');
renderVistas();rotulosAmbiente();
