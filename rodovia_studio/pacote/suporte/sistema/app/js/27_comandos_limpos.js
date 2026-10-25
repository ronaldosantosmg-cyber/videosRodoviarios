// ---------------- 1.28: comandos terminam limpos e as alterações chegam ao modelo ----------------
// • Terminado um comando (mover, girar, copiar, escala, espelhar, offset, pintar, textura, nome), a seleção,
//   os grips e a mini-barra somem, como no CAD. Durante o comando a mini-barra fica escondida.
// • O pedido do comando aparece também na área de mensagens (antes só na linha de comando).
// • A prévia é atualizada sozinha depois das alterações (pode desligar), com aviso de prévia desatualizada.
let cmdSel=false,previewStale=false;
function clearSelection(){sel=null;selSet=[];dxfSel=null;selLink=null;hotGrip=null;showProps();if($('propPanel')&&!selSeg)$('propPanel').hidden=true;draw()}
estender('runCommand',_rc=>function(raw){const had=!!cadCmd,hadSel=selObjs().length>0;const r=_rc(raw);if(!had&&cadCmd&&hadSel)cmdSel=true;placeSelBar();return r},'• A prévia é atualizada sozinha depois das alterações (pode desligar),');
estender('prompt_',_p=>function(t){_p(t);if(t==='Comando:'){if(cmdSel){cmdSel=false;if(!window.RodoviaSelectionPolicy?.preserveAfterCommand)setTimeout(clearSelection,0)}}else if(t)msg(t+' (Enter conclui · Esc cancela)')},'• A prévia é atualizada sozinha depois das alterações (pode desligar),');
estender('placeSelBar',_psb=>function(){_psb();const b=$('selBar');if(b&&(cadCmd||draft||tool!=='pan'))b.hidden=true},'• A prévia é atualizada sozinha depois das alterações (pode desligar),');
estender('texApply',_ta=>function(){_ta();if(!$('texDlg').open)setTimeout(clearSelection,0)},'• A prévia é atualizada sozinha depois das alterações (pode desligar),');
$('td_ok')?.addEventListener('click',()=>{if(!$('texDlg').open)setTimeout(clearSelection,0)});
estender('renameSel',_rn=>async function(){await _rn();if(!window.RodoviaSelectionPolicy?.preserveAfterCommand)clearSelection()},'• A prévia é atualizada sozinha depois das alterações (pode desligar),');
// Prévia automática depois das alterações (padrão: ligada).
try{if(localStorage.getItem('rodovia_autoprev')===null)autoPrev=true}catch{autoPrev=true}
let prevQueued=false;
function previewVisible(){return !useGeo()||baseMode==='preview'}
scheduleViewPreview=function(){previewStale=true;draw();if(!autoPrev||!pid||!ready()||!previewVisible())return;clearTimeout(prevTimer);prevTimer=setTimeout(runViewPreview,2500)};
$('baseMode')?.addEventListener('change',()=>{if(previewStale&&autoPrev&&previewVisible()){clearTimeout(prevTimer);prevTimer=setTimeout(runViewPreview,300)}});
// Recarregar o mesmo projeto (ao terminar uma tarefa) não apaga o histórico de desfazer nem a seleção.
estender('load',_l=>async (id,options={})=>{const same=id===pid&&!!pid;const u=undoStack.slice(),r=redoStack.slice(),S=sel,SS=selSet.slice(),seg=selSeg;const loaded=await _l(id,options);if(loaded===false||pid!==id)return false;if(options.resultsOnly||options.resetHistory)return loaded;
 if(same){undoStack=u;redoStack=r;updateUndo();if(S&&objOf(S)){sel=S;selSet=SS.filter(x=>objOf(x));showProps()}if(seg&&segById(seg.id)){selSeg=seg;showSegProps()}draw()}return loaded},'Recarregar o mesmo projeto (ao terminar uma tarefa) não apaga o histór');
async function runViewPreview(){if(!autoPrev||!pid||!ready())return;if(task||drag||draft||cadCmd){prevQueued=true;clearTimeout(prevTimer);prevTimer=setTimeout(runViewPreview,1500);return}
 prevQueued=false;try{const c=C2W(canvas.width/2,canvas.height/2),a=C2W(0,canvas.height/2),b=C2W(canvas.width,canvas.height/2);cfg.preview_center=c;cfg.preview_width_m=Math.max(5,Math.min(50000,Math.hypot(b.x-a.x,b.y-a.y)));$('preview_mode').value='custom';
  msg('Aplicando as alterações à prévia desta vista…');await start('preview');previewStale=false;draw();msg('Prévia atualizada com as alterações.')}catch(e){msg('A prévia não foi atualizada: '+e.message,true)}}
estender('changed',_ch=>function(text){_ch(text);if(pid&&ready())scheduleViewPreview()},'Recarregar o mesmo projeto (ao terminar uma tarefa) não apaga o histór');
estender('draw',_d=>function(){_d();if(!ready()||!previewStale)return;try{ctx.save();ctx.setTransform(1,0,0,1,0,0);const t=autoPrev&&previewVisible()?(task?'Prévia desatualizada · aguardando a tarefa atual…':'Prévia desatualizada · atualizando em instantes…'):'Alterações salvas · a prévia renderizada e o vídeo usam ao gerar (⟳ Regenerar prévia)';ctx.font='bold 13px system-ui';const w=ctx.measureText(t).width+20;ctx.fillStyle='#ffcf5ce6';ctx.fillRect(10,10,w,26);ctx.fillStyle='#1b1b1b';ctx.fillText(t,20,28);ctx.restore()}catch{}},'Recarregar o mesmo projeto (ao terminar uma tarefa) não apaga o histór');
estender('showProps',_sp=>function(){_sp();const el=document.getElementById('autoPrev');if(el)el.checked=autoPrev},'Recarregar o mesmo projeto (ao terminar uma tarefa) não apaga o histór');
// Área com textura própria: indicação no editor.
estender('draw',_d=>function(){_d();if(!ready())return;try{for(const a of M.pavement_areas||[])if(a.texture&&a.points?.length>2){const c=a.points.reduce((s,p)=>({x:s.x+p.x/a.points.length,y:s.y+p.y/a.points.length}),{x:0,y:0});label('🖌 textura própria',c,'#ffe7a3')}}catch{}},'Área com textura própria: indicação no editor.');
estender('start',_st=>async function(kind){const result=await _st(kind);if(result===false)return false;if(kind==='preview'||kind==='render'){previewStale=false;draw()}return result},'Área com textura própria: indicação no editor.');

