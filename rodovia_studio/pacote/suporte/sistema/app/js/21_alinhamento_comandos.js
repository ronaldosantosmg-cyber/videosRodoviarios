// ---------- alinhamento: cliques, selecionar linha do desenho ou seleção contínua ----------
let alignMode='cliques';try{alignMode=localStorage.getItem('rodovia_alignmode')||'cliques'}catch{}
estender('toolOptions',_to=>function(){_to();const o=$('toolOptions');if(!o)return;
 if(tool==='gantry')o.innerHTML=`<div class="grid"><label>Nome do pórtico<input id="gtName" placeholder="Ex.: Pórtico km 12+300"></label><label>Tipo<select id="gtKind">${Object.entries(ENUMS.kind.gantries).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select></label></div><label>Descrição (opcional)<input id="gtDesc" maxlength="160" placeholder="Ex.: Saída 12 — Ipatinga"></label>`;
 if(tool==='align')o.innerHTML=`<div class="grid"><label>Como criar o alinhamento<select id="alMode"><option value="cliques">Cliques sobre o eixo (dois ou mais pontos)</option><option value="linha">Selecionar uma linha do desenho</option><option value="continua">Seleção contínua (linhas conectadas, trecho a trecho)</option></select></label><label>Alcance do clique (pixels)<input id="alTol" type="number" min="3" max="60" value="12"></label></div><p class="muted">Enter confirma · Esc cancela (com confirmação) · Backspace desfaz o último ponto ou trecho. Na seleção contínua, cada clique acrescenta a linha seguinte (as conectadas sem bifurcação entram sozinhas).</p>`;
 if(tool==='align'){$('alMode').value=alignMode;$('alMode').onchange=()=>{alignMode=$('alMode').value;try{localStorage.setItem('rodovia_alignmode',alignMode)}catch{};draft=null;draw();msg({cliques:'Clique pontos sobre o eixo e pressione Enter.',linha:'Clique sobre uma linha do desenho (eixo): ela inteira vira o alinhamento. Enter confirma.',continua:'Clique na primeira linha; continue clicando nas seguintes. Enter confirma.'}[alignMode])}}},'alinhamento: cliques, selecionar linha do desenho ou seleção contínua');
estender('click',_c=>function(w,e){if(tool==='align'&&alignMode!=='cliques'){pickAlignLine(w);return}return _c(w,e)},'alinhamento: cliques, selecionar linha do desenho ou seleção contínua');
async function pickAlignLine(w){try{requireProject();const tolPx=Math.max(3,Math.min(60,Number($('alTol')?.value||12)));const tol=Math.max(.2,tolPx/Math.max(pxPerM(),1e-9));
 const r=await api(`/api/projects/${pid}/linha?x=${w.x}&y=${w.y}&tol=${tol.toFixed(3)}&continua=${alignMode==='continua'?1:0}`);const pts=r.points.map(([x,y])=>({x,y}));
 if(!draft||draft.type!=='align'||draft.src!==alignMode)draft={type:'align',pts:[],src:alignMode,hist:[],parts:0};
 draft.hist.push(draft.pts.slice());
 if(alignMode==='linha'||!draft.pts.length){draft.pts=pts;draft.parts=r.parts||1}
 else{const d=(p,q)=>Math.hypot(p.x-q.x,p.y-q.y),E=draft.pts[draft.pts.length-1],S=draft.pts[0],A=pts[0],B=pts[pts.length-1];
  const opt=[[d(E,A),'E',pts],[d(E,B),'E',pts.slice().reverse()],[d(S,B),'S',pts],[d(S,A),'S',pts.slice().reverse()]].sort((a,b)=>a[0]-b[0])[0];let add=opt[2];
  if(opt[1]==='E'){if(d(E,add[0])<.05)add=add.slice(1);draft.pts=draft.pts.concat(add)}else{if(d(S,add[add.length-1])<.05)add=add.slice(0,-1);draft.pts=add.concat(draft.pts)}
  draft.parts+=r.parts||1;if(opt[0]>1)msg(`Trecho acrescentado com uma lacuna de ${opt[0].toFixed(2)} m (ligada em linha reta). Enter confirma.`)}
 let L=0;for(let i=1;i<draft.pts.length;i++)L+=Math.hypot(draft.pts[i].x-draft.pts[i-1].x,draft.pts[i].y-draft.pts[i-1].y);draft.len=L;draw();
 if(!(alignMode==='continua'&&draft.hist.length>1&&L))msg(`Alinhamento: ${draft.parts} linha(s), ${draft.pts.length} vértices, ${L.toFixed(3)} m (camada ${(r.layers||[r.layer]).join(', ')}). ${alignMode==='continua'?'Clique a próxima linha ou ':''}Enter confirma; Esc cancela.`)}
 catch(e){msg(e.message,true)}}
estender('finishDraft',_fin=>async function(){const d=draft;if(d&&d.type==='align'&&d.src&&d.src!=='cliques'){if(d.pts.length<2)return msg('Selecione pelo menos uma linha do desenho.',true);if(d.pts.length>20000)return msg('Linha com mais de 20 000 vértices: selecione um trecho menor.',true);
  draft=null;checkpoint();M.custom_axis={name:d.src==='linha'?'Alinhamento (linha do desenho)':'Alinhamento (seleção contínua)',points:d.pts,smooth:false,enabled:true,source:d.src};
  changed(`Alinhamento criado com ${d.pts.length} vértices exatos do desenho (${(d.len||0).toFixed(3)} m). Clique “Analisar arquivos” para usá-lo como eixo de referência.`);return}return _fin()},'alinhamento: cliques, selecionar linha do desenho ou seleção contínua');
document.addEventListener('keydown',e=>{if(e.key!=='Backspace'||!draft||!draft.pts?.length)return;const t=e.target;if(t!==canvas&&!(t===document.body))return;e.preventDefault();
 if(draft.type==='align'&&draft.hist&&draft.hist.length){draft.pts=draft.hist.pop();draft.parts=Math.max(0,(draft.parts||1)-1);if(!draft.pts.length)draft=null;draw();return msg('Último trecho desfeito.')}
 draft.pts.pop();if(!draft.pts.length)draft=null;draw();msg('Último ponto desfeito.')},true);
estender('draw',_d=>function(){_d();if(!ready())return;try{if(draft&&draft.type==='align'&&draft.src&&draft.src!=='cliques'&&draft.pts.length>1){poly(draft.pts);ctx.strokeStyle='#ff4fd8';ctx.lineWidth=4;ctx.stroke();const [x,y]=W2C(draft.pts[0]);ctx.fillStyle='#ff4fd8';ctx.beginPath();ctx.arc(x,y,6,0,7);ctx.fill()}}catch(err){}},'alinhamento: cliques, selecionar linha do desenho ou seleção contínua');

// ---------- comandos novos, histórico e lista de comandos ----------
const CMD_HELP=[['AL / ALINHAMENTO','Alinhamento por cliques, por linha do desenho ou seleção contínua'],['PT / PORTICO','Pórtico: dois cliques nos apoios'],['M / MOVER','Move o(s) selecionado(s)'],['CO / COPIAR','Copia'],['RO / GIRAR','Gira em torno de um ponto'],['SC / ESCALA','Escala por um fator'],['MI / ESPELHAR','Espelha (cria cópias)'],['OF / OFFSET','Paralela a uma distância'],
 ['E / APAGAR','Apaga o(s) selecionado(s)'],['PR / PROPRIEDADES','Painel de propriedades'],['AT / ATRIB','Atributos em comum de vários objetos'],['MA / PINTAR','Copia as propriedades (estilo) do selecionado para outros objetos clicados'],['SELTUDO','Seleciona tudo'],['U / REFAZER','Desfaz / refaz'],
 ['OC / OCULTAR','Oculta a camada clicada'],['CG / CONGELAR','Congela a camada clicada'],['ISOLAR','Mostra só a camada clicada'],['MOSTRAR','Mostra e descongela todas as camadas'],['REGEN','Redesenha a tela (vetores e imagem)'],['RP / PREVIA','Regenera a prévia'],['SS / SESSAO','Salva a sessão de trabalho'],
 ['LOG / REGISTROS','Abre os registros de execução e erros'],['IA','Baixa o prompt para IA que reproduz a execução'],['DIST / ID','Mede distância / mostra coordenadas'],['TC / PN','Tela cheia / painel'],['SNAP / ORTO','Liga e desliga'],['? / AJUDA','Esta lista']];
{const dl=$('cmdList');if(dl)dl.innerHTML=CMD_HELP.flatMap(([c,h])=>c.split(' / ').map(k=>`<option value="${esc(k)}">${esc(h)}</option>`)).join('')}
let lastCmd='',cmdHist=[],cmdPos=-1;try{cmdHist=JSON.parse(localStorage.getItem('rodovia_cmdhist')||'[]')}catch{}
async function pickLayerCmd(label,fn){cadCmd={step(w){cadCmd=null;prompt_('Comando:');const n=layerAt(w);if(!n)return msg('Nenhuma linha do desenho perto do clique.',true);fn(n)}};prompt_(label);canvas.focus({preventScroll:true})}
let isolated=null;
function saveSessionPrompt(){const name=prompt('Nome da sessão (ex.: Revisão do trevo):',`Sessão ${new Date().toLocaleString('pt-BR')}`);if(name)saveSession(name.trim()).catch(e=>msg(e.message,true))}
estender('runCommand',_rc3=>function(raw){const t=(raw||'').trim().toUpperCase();if(t){if(cmdHist[cmdHist.length-1]!==raw.trim())cmdHist.push(raw.trim());cmdHist=cmdHist.slice(-50);cmdPos=-1;try{localStorage.setItem('rodovia_cmdhist',JSON.stringify(cmdHist))}catch{}}
 if(!t&&!cadCmd&&!draft&&lastCmd&&tool==='pan'){msg('Repetindo: '+lastCmd);return runCommand(lastCmd)}
 if(/^[A-ZÀ-Ú?]+$/.test(t)&&!['U','REFAZER','REDO','DESFAZER','UNDO'].includes(t))lastCmd=t;
 if(['PT','PORTICO','PÓRTICO'].includes(t)){setTool('gantry');prompt_('PÓRTICO — primeiro apoio:');return}
 if(['AT','ATRIB','ATRIBUTOS'].includes(t)){if(allSelected().length<1)return msg('Selecione os objetos (Shift+clique ou Ctrl+arrastar) e use ATRIB.',true);showProps();$('propPanel').scrollIntoView({block:'nearest'});return msg('Altere os atributos em comum e confirme com Enter.')}
 if(['MA','PINTAR','MATCHPROP'].includes(t)){const src=objOf(sel);if(!src)return msg('Selecione o objeto de origem e use PINTAR.',true);
  cadCmd={step(w){const c=W2C(w);const h=hitObject({cx:c[0],cy:c[1]});if(!h)return msg('Nenhum objeto no ponto. Clique outro ou Enter para encerrar.',true);const dst=objOf(h);if(dst.key!==src.key)return msg(`Só entre objetos do mesmo tipo (${src.label}).`,true);checkpoint();const n=matchProps(src,dst);changed(`${n} propriedade(s) copiada(s) para ${dst.label}. Clique o próximo ou Enter para encerrar.`)}};prompt_('PINTAR — clique os objetos de destino (Enter encerra):');return}
 if(['OC','OCULTAR','HIDE'].includes(t)){pickLayerCmd('OCULTAR — clique numa linha da camada:',n=>{setLayerState(n,'h',true);msg(layerMsg(n,'h',true))});return}
 if(['CG','CONGELAR','FREEZE'].includes(t)){pickLayerCmd('CONGELAR — clique numa linha da camada:',n=>{setLayerState(n,'f',true);msg(layerMsg(n,'f',true))});return}
 if(['ISOLAR','ISO'].includes(t)){pickLayerCmd('ISOLAR — clique numa linha da camada:',n=>{isolated=[...(cfg.hidden_layers||[])];cfg.hidden_layers=(vec.layer_names||[]).filter(x=>x!==n&&!Object.entries(cfg.layers||{}).some(([r,ls])=>r==='axis'&&ls.includes(x)));buildVectorPaths();snapIndex=null;draw();showLayers();scheduleSave();msg(`Só “${n}” (e o eixo) visíveis. MOSTRAR volta todas.`)});return}
 if(['MOSTRAR','MOSTRARTUDO','UNHIDE','DESCONGELAR'].includes(t)){cfg.hidden_layers=[];if(t!=='MOSTRAR')cfg.frozen_layers=[];isolated=null;buildVectorPaths();snapIndex=null;draw();showLayers();scheduleSave();return msg(t==='DESCONGELAR'?'Todas as camadas visíveis e descongeladas.':'Todas as camadas visíveis. Clique “Analisar arquivos” para recalcular com elas.')}
 if(t==='REGEN'){regenScreen();return}
 if(['RP','PREVIA','PRÉVIA','REGENPREVIA'].includes(t)){$('regenPreview')?.click();return}
 if(['SS','SESSAO','SESSÃO'].includes(t)){saveSessionPrompt();return}
 if(['LOG','REGISTROS','LOGS'].includes(t)){openLogs('execucao');return}
 if(t==='IA'){promptIA();return}
 if(['?','AJUDA','HELP'].includes(t)){$('cmdHelpBody').innerHTML='<table>'+CMD_HELP.map(([c,h])=>`<tr><td class="nowrap"><b>${esc(c)}</b></td><td>${esc(h)}</td></tr>`).join('')+'</table><p class="muted">Enter vazio repete o último comando. Setas ↑/↓ percorrem o histórico. Clique com o botão direito na tela para o menu de contexto.</p>';$('cmdHelpDlg').showModal();return}
 return _rc3(raw)},'comandos novos, histórico e lista de comandos');
Object.assign(CMD_ALIAS,{PT:'x',PORTICO:'x',AT:'x',ATRIB:'x',MA:'x',PINTAR:'x',OC:'x',OCULTAR:'x',CG:'x',CONGELAR:'x',ISOLAR:'x',MOSTRAR:'x',REGEN:'x',RP:'x',PREVIA:'x',SS:'x',SESSAO:'x',LOG:'x',IA:'x','?':'x',AJUDA:'x'});
$('cmdLine')?.addEventListener('keydown',e=>{if(e.key!=='ArrowUp'&&e.key!=='ArrowDown')return;if(!cmdHist.length)return;e.preventDefault();cmdPos=cmdPos<0?cmdHist.length:cmdPos;cmdPos=Math.max(0,Math.min(cmdHist.length,cmdPos+(e.key==='ArrowUp'?-1:1)));e.target.value=cmdHist[cmdPos]||''});
function regenScreen(){tiles.clear();snapIndex=null;exactSnap=null;buildVectorPaths();draw();msg('Tela regenerada (imagem, vetores e snap).')}

