// ---------- menu de contexto (botão direito), parecido com o do Windows ----------
let ctxDown=null;
canvas.addEventListener('pointerdown',e=>{if(e.button===2)ctxDown={x:e.clientX,y:e.clientY,t:performance.now()}},true);
canvas.addEventListener('pointerup',e=>{if(e.button!==2||!ctxDown)return;const moved=Math.hypot(e.clientX-ctxDown.x,e.clientY-ctxDown.y);ctxDown=null;if(moved>4||!ready())return;const c=canvasPt(e);openCanvasMenu(e.clientX,e.clientY,c.w)});
function ctxItems(w){const L=allSelected(),one=objOf(sel),n=layerAt(w||{x:0,y:0}),items=[];const run=c=>()=>runCommand(c);
 if(draft)items.push({hd:'Comando em andamento'},{ic:'✔',t:'Concluir',k:'Enter',h:'Conclui o desenho atual (mesmo que Enter).',f:()=>finishDraft()},{ic:'⌫',t:'Desfazer último ponto',k:'Backspace',h:'Remove o último ponto ou trecho do desenho.',f:()=>canvas.dispatchEvent(new KeyboardEvent('keydown',{key:'Backspace',bubbles:true}))},{ic:'✖',t:'Cancelar',k:'Esc',h:'Sai do comando (pede confirmação).',f:()=>escapeCommand()},{sep:1});
 if(L.length){items.push({hd:L.length>1?`${L.length} objetos selecionados`:one?one.label:'Seleção'});
  items.push({ic:'☰',t:L.length>1?'Atributos em comum…':'Propriedades…',k:L.length>1?'AT':'PR',h:'Abre o painel para alterar os atributos; Enter confirma.',f:run(L.length>1?'ATRIB':'PR')},
   {ic:'✥',t:'Mover',k:'M',h:'Ponto base e segundo ponto (clique ou @dx,dy).',f:run('MOVER')},{ic:'⧉',t:'Copiar',k:'CO',h:'Cria cópias deslocadas.',f:run('COPIAR')},{ic:'⟳',t:'Girar',k:'RO',h:'Gira em torno de um ponto, ângulo em graus.',f:run('GIRAR')},
   {ic:'⤢',t:'Escala',k:'SC',h:'Aumenta/diminui a partir de um ponto base.',f:run('ESCALA')},{ic:'⇋',t:'Espelhar',k:'MI',h:'Espelha por uma linha de dois pontos (cópias).',f:run('ESPELHAR')},
   {ic:'∥',t:'Paralela (offset)',k:'OF',dis:!(one&&one.shape!=='pt'),h:'Linha ou área paralela à distância digitada.',f:run('OFFSET')},{ic:'🖌',t:'Copiar propriedades para…',k:'MA',dis:!one,h:'Aplica o estilo deste objeto a outros do mesmo tipo.',f:run('PINTAR')},
   {ic:'🗑',t:'Apagar',k:'Del',h:'Apaga a seleção (Ctrl+Z desfaz).',f:()=>deleteSel()},{ic:'◌',t:'Desmarcar',k:'Esc',h:'Limpa a seleção.',f:()=>{sel=null;selSet=[];showProps();draw()}},{sep:1})}
 if(n)items.push({ic:'▤',t:`Camada “${n.length>28?n.slice(0,27)+'…':n}”`,k:'',sub:[{ic:'👁',t:'Ocultar camada',h:'Some no editor e no vídeo. O DXF não muda.',f:()=>{setLayerState(n,'h',true);msg(layerMsg(n,'h',true))}},{ic:'❄',t:layerSets().f.has(n)?'Descongelar camada':'Congelar camada',h:'Travada no editor; no vídeo aparece pronta desde o início.',f:()=>{const on=!layerSets().f.has(n);setLayerState(n,'f',on);msg(layerMsg(n,'f',on))}},{ic:'◎',t:'Isolar camada',h:'Mostra só esta camada (e o eixo).',f:()=>{cfg.hidden_layers=(vec.layer_names||[]).filter(x=>x!==n&&!Object.entries(cfg.layers||{}).some(([r,ls])=>r==='axis'&&ls.includes(x)));buildVectorPaths();draw();showLayers();scheduleSave();msg(`Só “${n}” visível. Use MOSTRAR para voltar.`)}},{ic:'⟋',t:'Usar a linha como alinhamento',h:'Seleciona a linha clicada inteira como eixo de referência.',f:async()=>{setTool('align');alignMode='linha';try{localStorage.setItem('rodovia_alignmode','linha')}catch{};toolOptions();await pickAlignLine(w)}}]},{sep:1});
 items.push({ic:'✚',t:'Inserir',sub:[{ic:'⊓',t:'Pórtico',k:'PT',h:'Dois cliques nos apoios e a imagem da placa.',f:()=>setTool('gantry')},{ic:'★',t:'Destaque com caixa de chamada',h:'Ponto especial com caixa de informação.',f:()=>setTool('highlight')},{ic:'⟋',t:'Alinhamento',k:'AL',h:'Por cliques, linha do desenho ou seleção contínua.',f:()=>setTool('align')},{ic:'◇',t:'Placa',h:'Placa vertical.',f:()=>setTool('sign')}]});
 items.push({ic:'↶',t:'Desfazer',k:'Ctrl+Z',dis:!undoStack.length,h:'Desfaz a última alteração.',f:()=>undo()},{ic:'↷',t:'Refazer',k:'Ctrl+Y',dis:!redoStack.length,h:'Refaz.',f:()=>redo()});
 if(lastCmd)items.push({ic:'↻',t:`Repetir ${lastCmd}`,k:'Enter',h:'Repete o último comando.',f:run(lastCmd)});
 items.push({sep:1},{ic:'⤧',t:'Enquadrar tudo',k:'ZOOM',h:'Ajusta a vista ao projeto.',f:()=>fitView()},{ic:'⊙',t:'Centralizar aqui',h:'Leva este ponto ao centro da tela.',f:()=>{const [x,y]=worldToImg(w);view.ox=canvas.width/2-x*view.s;view.oy=canvas.height/2-y*view.s;draw()}},{ic:'▦',t:'Selecionar tudo',k:'SELTUDO',h:'Seleciona todas as marcações.',f:run('SELTUDO')},
  {sep:1},{ic:'⟳',t:'Regenerar prévia',k:'RP',h:'Gera de novo a prévia no modo escolhido.',f:run('RP')},{ic:'▣',t:'Prévia desta vista',h:'Renderiza o enquadramento atual em alta resolução.',f:()=>$('renderView')?.click()},{ic:'⟲',t:'Regenerar tela',k:'REGEN',h:'Redesenha imagem, vetores e snap.',f:()=>regenScreen()},
  {ic:'💾',t:'Sessão',sub:[{ic:'💾',t:'Salvar sessão…',k:'SS',h:'Guarda vista, ferramenta, camadas e painéis.',f:()=>saveSessionPrompt()},{ic:'↺',t:'Retomar última sessão',dis:!lastAutoSession,h:'Volta à vista e ferramenta da última sessão automática.',f:()=>restoreSession(lastAutoSession)}]},
  {ic:'❔',t:'Comandos e ajuda',k:'?',h:'Lista dos comandos da linha de comando.',f:run('?')});
 return items}
let ctxState=null;
function renderMenu(el,items,x,y){el.innerHTML=items.map((it,i)=>it.sep?'<div class="sep"></div>':it.hd?`<div class="hd">${esc(it.hd)}</div>`:`<div class="it${it.dis?' dis':''}${it.sub?' sub':''}" data-i="${i}" role="menuitem"><span class="ic">${it.ic||''}</span><span>${esc(it.t)}</span><span class="k">${esc(it.k||'')}</span></div>`).join('')+'<div class="ctxHelp">Passe o mouse sobre um item para ver a ajuda.</div>';
 el.hidden=false;const r=el.getBoundingClientRect();el.style.left=Math.max(4,Math.min(x,innerWidth-r.width-6))+'px';el.style.top=Math.max(4,Math.min(y,innerHeight-r.height-6))+'px'}
function openCanvasMenu(x,y,w){closeMenu();const el=$('ctxMenu');const items=ctxItems(w);ctxState={items,stack:[],el,x,y,on:-1};renderMenu(el,items,x,y)}
function closeMenu(){const el=$('ctxMenu');if(el){el.hidden=true;el.innerHTML=''}ctxState=null}
function menuActivate(i){const it=ctxState?.items[i];if(!it||it.dis||it.sep||it.hd)return;if(it.sub){ctxState.stack.push(ctxState.items);ctxState.items=[{ic:'‹',t:'Voltar',h:'Volta ao menu anterior.',back:1},{sep:1},...it.sub];ctxState.on=-1;renderMenu(ctxState.el,ctxState.items,ctxState.x,ctxState.y);return}
 if(it.back){ctxState.items=ctxState.stack.pop();renderMenu(ctxState.el,ctxState.items,ctxState.x,ctxState.y);return}const f=it.f;closeMenu();try{const r=f&&f();if(r&&r.catch)r.catch(e=>msg(e.message,true))}catch(e){msg(e.message,true)}}
function menuHover(i){if(!ctxState)return;ctxState.on=i;ctxState.el.querySelectorAll('.it').forEach(d=>d.classList.toggle('on',Number(d.dataset.i)===i));const it=ctxState.items[i];const h=ctxState.el.querySelector('.ctxHelp');if(h&&it)h.textContent=(it.h||it.t)+(it.k?` (${it.k})`:'')}
$('ctxMenu')?.addEventListener('mousemove',e=>{const d=e.target.closest('.it');if(d)menuHover(Number(d.dataset.i))});
$('ctxMenu')?.addEventListener('click',e=>{const d=e.target.closest('.it');if(d)menuActivate(Number(d.dataset.i))});
$('ctxMenu')?.addEventListener('contextmenu',e=>e.preventDefault());
document.addEventListener('pointerdown',e=>{if(ctxState&&!e.target.closest('#ctxMenu'))closeMenu()},true);
window.addEventListener('keydown',e=>{if(!ctxState)return;const sel_=ctxState.items.map((it,i)=>[it,i]).filter(([it])=>!it.sep&&!it.hd&&!it.dis).map(([,i])=>i);
 if(e.key==='Escape'){e.preventDefault();e.stopImmediatePropagation();if(ctxState.stack.length){ctxState.items=ctxState.stack.pop();renderMenu(ctxState.el,ctxState.items,ctxState.x,ctxState.y)}else closeMenu();return}
 if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();e.stopImmediatePropagation();const k=sel_.indexOf(ctxState.on);const nk=k<0?(e.key==='ArrowDown'?0:sel_.length-1):(k+(e.key==='ArrowDown'?1:-1)+sel_.length)%sel_.length;menuHover(sel_[nk]);return}
 if(e.key==='Enter'||e.key==='ArrowRight'){e.preventDefault();e.stopImmediatePropagation();if(ctxState.on>=0)menuActivate(ctxState.on);return}
 if(e.key==='ArrowLeft'&&ctxState.stack.length){e.preventDefault();e.stopImmediatePropagation();ctxState.items=ctxState.stack.pop();renderMenu(ctxState.el,ctxState.items,ctxState.x,ctxState.y)}},true);
canvas.addEventListener('keydown',e=>{if((e.key==='ContextMenu'||(e.shiftKey&&e.key==='F10'))&&ready()){e.preventDefault();const r=canvas.getBoundingClientRect();openCanvasMenu(r.left+r.width/2,r.top+r.height/2,lastWorld||C2W(canvas.width/2,canvas.height/2))}});

// ---------- tela ampla, compacta e divisor arrastável ----------
{const main=document.querySelector('main');const cols=main?main.children:[];if(main&&cols.length>=2&&!$('splitter')){const sp=document.createElement('div');sp.id='splitter';sp.className='splitter';sp.title='Arraste para ajustar a largura do painel (duplo clique: padrão)';main.insertBefore(sp,cols[1])}
 const get=(k,d)=>{try{const v=localStorage.getItem(k);return v===null?d:v}catch{return d}};const set=(k,v)=>{try{localStorage.setItem(k,v)}catch{}};
 const apply=()=>{document.body.classList.toggle('wide',$('layoutWide').checked);document.body.classList.toggle('compact',$('layoutCompact').checked);document.documentElement.style.setProperty('--side',get('rodovia_side','420')+'px');requestAnimationFrame(()=>resizeCanvas())};
 if($('layoutWide')){$('layoutWide').checked=get('rodovia_wide','1')==='1';$('layoutCompact').checked=get('rodovia_compact','0')==='1';apply();
  $('layoutWide').onchange=()=>{set('rodovia_wide',$('layoutWide').checked?'1':'0');apply()};$('layoutCompact').onchange=()=>{set('rodovia_compact',$('layoutCompact').checked?'1':'0');apply()}}
 const sp=$('splitter');if(sp){let st=null;sp.addEventListener('pointerdown',e=>{st={x:e.clientX,w:Number(get('rodovia_side','420'))};sp.setPointerCapture(e.pointerId);sp.classList.add('drag')});
  sp.addEventListener('pointermove',e=>{if(!st)return;const w=Math.max(300,Math.min(Math.round(innerWidth*.6),st.w+e.clientX-st.x));document.documentElement.style.setProperty('--side',w+'px');resizeCanvas()});
  sp.addEventListener('pointerup',e=>{if(!st)return;const w=parseInt(getComputedStyle(document.documentElement).getPropertyValue('--side'))||420;set('rodovia_side',String(w));st=null;sp.classList.remove('drag')});
  sp.addEventListener('dblclick',()=>{set('rodovia_side','420');apply()})}
 window.addEventListener('resize',()=>{clearTimeout(window._rsz);window._rsz=setTimeout(resizeCanvas,80)})}

// ---------- fluidez do PAN/ZOOM: quadros agrupados e imagem da tela durante o gesto ----------
{const _draw=draw;let cost=0,raf=0,gesture=false,idle=null,snap=null,snapView=null;
 function full(){const t0=performance.now();ctx.imageSmoothingQuality='high';_draw();cost=performance.now()-t0;
  if(cost>16&&ready()){if(!snap)snap=document.createElement('canvas');if(snap.width!==canvas.width||snap.height!==canvas.height){snap.width=canvas.width;snap.height=canvas.height}snap.getContext('2d').drawImage(canvas,0,0);snapView={...view}}else snapView=null}
 function endGesture(){clearTimeout(idle);idle=setTimeout(()=>{gesture=false;if(raf){cancelAnimationFrame(raf);raf=0}full()},140)}
 draw=function(){if(!gesture)return full();endGesture();
  if(snapView&&cost>16){const k=view.s/snapView.s;ctx.setTransform(1,0,0,1,0,0);ctx.fillStyle='#0c1722';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='low';ctx.drawImage(snap,view.ox-snapView.ox*k,view.oy-snapView.oy*k,snap.width*k,snap.height*k);return}
  if(!raf)raf=requestAnimationFrame(()=>{raf=0;full()})};
 canvas.addEventListener('wheel',()=>{gesture=true},{capture:true,passive:true});
 canvas.addEventListener('pointermove',()=>{if(drag&&drag.type==='pan')gesture=true},true);
 window.drawStats=()=>({cost,gesture})}

