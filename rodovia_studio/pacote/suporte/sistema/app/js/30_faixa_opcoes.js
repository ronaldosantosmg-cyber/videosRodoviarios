// ---------- faixa de opções (ribbon) no estilo Windows ----------
const RI=(p)=>`<svg viewBox="0 0 24 24">${(p||'').split('M').filter(Boolean).map(d=>`<path d="M${d}"/>`).join('')}</svg>`;
const RIBBON=[
 ['Início',[['Projeto',[['Novo','➕',()=>$('new')?.click(),1],['Salvar','💾',()=>$('saveProject')?.click(),1],['Salvar como…','🗐',()=>$('saveAsProject')?.click()]]],
  ['Arquivos',[['DXF…','📐',()=>$('fileDxf')?.click(),1],['KMZ/KML…','🌐',()=>$('fileKmz')?.click(),1],['Analisar','🔎',()=>$('analyze')?.click(),1]]],
  ['Prévia',[['Regenerar prévia','⟳',()=>$('regenPreview')?.click(),1],['Detalhar vista','▣',()=>$('renderView')?.click()],['Enquadrar','⤧',()=>fitView()]]],
  ['Seleção',[['Selecionar tudo','▦',()=>runCommand('SELTUDO')],['Desmarcar','◌',()=>clearSelection()],['Propriedades','☰',()=>runCommand('PR')]]]]],
 ['Inserir',null],
 ['Editar',[['Modificar',[['Mover','✥',()=>runCommand('MOVER'),1],['Girar','⟳',()=>runCommand('GIRAR'),1],['Copiar','⧉',()=>runCommand('COPIAR'),1],['Escala','⤢',()=>runCommand('ESCALA')],['Espelhar','⇋',()=>runCommand('ESPELHAR')],['Paralela','∥',()=>runCommand('OFFSET')]]],
  ['Propriedades',[['Atributos','☰',()=>runCommand('ATRIB'),1],['Trocar nome','✎',()=>renameSel()],['Trocar textura','▦',()=>openTexDialog()],['Copiar propriedades','🖌',()=>runCommand('PINTAR')]]],
  ['Histórico',[['Desfazer','↶',()=>undo(),1],['Refazer','↷',()=>redo(),1],['Apagar','🗑',()=>deleteSel()]]]]],
 ['Aparência',[['Superfícies',[['Pavimento','▦',()=>openSection('Perfil de apresentação'),1],['Taludes e canteiro','⛰',()=>openSurfDialog('tex',{surface:'talude_corte',scope:'tipo'}),1],['Água','≈',()=>openSurfDialog('agua'),1],['Sinalização','═',()=>openSurfDialog('sin'),1]]],
  ['Camadas',[['Ocultar camada','👁',()=>runCommand('OCULTAR')],['Congelar camada','❄',()=>runCommand('CONGELAR')],['Mostrar todas','◎',()=>runCommand('MOSTRAR')]]]]],
 ['Fluxos',[['Tráfego',[['Atualizar fluxos','⟳',()=>$('updFlows')?.click(),1],['Forçar ligação','⤳',()=>setTool('linkforce'),1],['Inverter trecho','⇄',()=>setTool('flowrev')],['Desativar trecho','⦸',()=>setTool('flowoff')],['Mostrar ligações','⤳',()=>{showAllLinks=!showAllLinks;draw()}]]],
  ['Câmera',[['Avanço por trecho','⏱',()=>setTool('advzone'),1],['Velocidade de avanço','⏲',()=>openSection('Perfil de apresentação')]]]]],
 ['Vídeo',[['Gerar',[['Gerar vídeo','🎬',()=>$('render')?.click(),1],['Prévia no instante','▶',()=>$('openAtTime')?.click(),1]]],['Suporte',[['Ver registros','📋',()=>openLogs('execucao')],['Exportar prompt para IA','🤖',()=>promptIA()]]]]],
 ['Exibir',[['Janela',[['Tela cheia','⛶',()=>toggleFullscreen(),1],['Painel lateral','◧',()=>$('toggleSide')?.click()],['Tela ampla','▭',()=>$('layoutWide').click()],['Compacto','▤',()=>$('layoutCompact').click()]]],
  ['Desenho',[['Enquadrar','⤧',()=>fitView(),1],['Regenerar tela','⟲',()=>regenScreen()],['Snap','⌖',()=>{$('snapOn').click();statusBar()}],['Orto','⊥',()=>{$('orthoOn').click();statusBar()}]]]]],
 ['Ajuda',[['Ajuda',[['Como usar','❔',()=>$('helpBtn')?.click(),1],['Comandos','⌨',()=>runCommand('?'),1],['Sobre','ⓘ',()=>openAbout(),1]]]]]];
function ribbonInsertGroups(){const out=[];let g=0,cur=[];for(const t of TOOLS){if(t==='|'){if(cur.length)out.push([TOOL_GROUPS[g]||'',cur]);cur=[];g++;continue}if(t[0]==='pan'||t[0]==='move')continue;cur.push([toolLabel(t).replace(/^[^\p{L}\p{N}]+/u,''),{tool:t[0]},()=>setTool(t[0]),0,t[0]])}if(cur.length)out.push([TOOL_GROUPS[g]||'',cur]);return out}
function buildRibbon(){const old=$('menuBar');if(!old)return;const bar=old.cloneNode(false);old.replaceWith(bar);let cur=1;try{cur=Number(localStorage.getItem('rodovia_ribbon_tab')||1)}catch{}let mini=false;try{mini=localStorage.getItem('rodovia_ribbon_min')==='1'}catch{}
 const tabs=[['Arquivo']].concat(RIBBON);
 const render=()=>{const T=RIBBON[cur-1];const groups=T?(T[1]||ribbonInsertGroups()):[];
  bar.innerHTML=`<div class="rbTabs">${tabs.map(([n],i)=>`<button type="button" class="mb${i===0?' file':''}${i===cur?' on':''}" data-mb="${i}">${esc(n)}</button>`).join('')}<span class="grow"></span><button type="button" class="rbMin" title="Recolher/expandir a faixa (Ctrl+F1)">${mini?'▾':'▴'}</button></div>`+
  (mini?'':`<div class="rbPanel">${groups.map(([gn,items],gi)=>`<div class="rbGroup"><div class="rbItems">${items.map((it,ii)=>`<button type="button" class="rb${it[3]?' big':''}" data-rb="${gi}:${ii}" title="${esc(it[0])}">${typeof it[1]==='object'?toolIcon(it[1].tool):`<span class="ri">${it[1]}</span>`}<span class="rl">${esc(it[0])}</span></button>`).join('')}</div><div class="rbName">${esc(gn)}</div></div>`).join('')}</div>`);bar._groups=groups};
 render();
 bar.onclick=e=>{const t=e.target.closest('.mb');if(t){const i=Number(t.dataset.mb);if(i===0){fileMenu(t);return}cur=i;try{localStorage.setItem('rodovia_ribbon_tab',i)}catch{}if(mini){mini=false;try{localStorage.setItem('rodovia_ribbon_min','0')}catch{}}render();return}
  if(e.target.closest('.rbMin')){mini=!mini;try{localStorage.setItem('rodovia_ribbon_min',mini?'1':'0')}catch{}render();return}
  const b=e.target.closest('[data-rb]');if(!b)return;const [gi,ii]=b.dataset.rb.split(':').map(Number);const it=bar._groups[gi][1][ii];try{const r=it[2]();if(r&&r.catch)r.catch(err=>msg(err.message,true))}catch(err){msg(err.message,true)}};
 bar.ondblclick=e=>{if(e.target.closest('.mb')&&!e.target.closest('.file')){mini=!mini;try{localStorage.setItem('rodovia_ribbon_min',mini?'1':'0')}catch{}render()}};
 document.addEventListener('keydown',e=>{if(e.ctrlKey&&e.key==='F1'){e.preventDefault();mini=!mini;render()}});
 window.ribbonRender=render}
function fileMenu(anchor){const dd=$('menuDrop');const items=MENUBAR[0][1];dd.innerHTML=items.map((it,k)=>it?`<div class="it" data-mi="${k}"><span>${esc(it[0])}</span><span class="k">${typeof it[1]==='string'?esc(it[1]):''}</span></div>`:'<div class="sep"></div>').join('');const r=anchor.getBoundingClientRect();dd.style.left=r.left+'px';dd.style.top=r.bottom+'px';dd.hidden=false;
 dd.onclick=e=>{const d=e.target.closest('[data-mi]');if(!d)return;const it=items[Number(d.dataset.mi)];dd.hidden=true;const f=it[it.length-1];try{const r=f();if(r&&r.catch)r.catch(err=>msg(err.message,true))}catch(err){msg(err.message,true)}}}
document.addEventListener('pointerdown',e=>{const dd=$('menuDrop');if(dd&&!dd.hidden&&!e.target.closest('#menuDrop,#menuBar .file'))dd.hidden=true},true);
buildRibbon();
// Título da janela com o nome do projeto (como num programa do Windows).
estender('fill',_f=>function(s){_f(s);try{document.title=`${s.name||'Projeto'} — Rodovia Studio`}catch{}},'Título da janela com o nome do projeto (como num programa do Windows).');
if(cfg&&cfg.name)document.title=`${cfg.name} — Rodovia Studio`;
// Campos que não são listas de opções no esquema (ex.: cor #rrggbb) não podem virar uma lista fixa.
estender('propInput',_pi2=>function(path,v,key,listKey){if(SCHEMA&&SCHEMA[listKey]!==undefined&&!enumFor(listKey,key)&&ENUMS[key]&&(key==='color'))
  {const id='pp_'+path.replace(/\W/g,'_');return `<span class="colorField"><input id="${id}" data-pp="${path}" value="${esc(v??'')}" placeholder="#rrggbb (vazio = padrão)" maxlength="7"><input type="color" data-ppcolor="${path}" value="${/^#[0-9a-f]{6}$/i.test(v||'')?v:'#ffd66b'}" title="Escolher a cor"></span>`}
 return _pi2(path,v,key,listKey)},'Campos que não são listas de opções no esquema (ex.: cor #rrggbb) não ');
document.addEventListener('input',e=>{const c=e.target.closest&&e.target.closest('#propPanel [data-ppcolor]');if(!c)return;const t=document.querySelector(`#propPanel [data-pp="${c.dataset.ppcolor}"]`);if(t){t.value=c.value;commitProp(t)}});
estender('commitProp',_cp=>function(el){if(el.dataset&&el.dataset.pp==='color'&&el.tagName==='INPUT'){const v=String(el.value).trim();if(v&&!/^#[0-9a-fA-F]{6}$/.test(v)){msg('Cor inválida: use o formato #rrggbb (ex.: #ffd66b) ou deixe vazio para a cor padrão.',true);el.classList.add('bad');return}el.value=v.toLowerCase()}return _cp(el)},'Campos que não são listas de opções no esquema (ex.: cor #rrggbb) não ');
// 1.29: opções da ferramenta flutuando sobre a tela (a área de desenho não muda de tamanho ao trocar de ferramenta).
{const to=$('toolOptions'),wrap=document.querySelector('.canvasWrap');if(to&&wrap&&to.parentElement!==wrap)wrap.appendChild(to)}
// Mudança de tamanho da tela: só redesenha quando o tamanho realmente muda (evita saltos).
try{new ResizeObserver(()=>{const r=canvas.getBoundingClientRect(),d=window.devicePixelRatio||1;if(Math.round(r.width*d)!==canvas.width||Math.round(r.height*d)!==canvas.height)resizeCanvas()}).observe(canvas)}catch{}

