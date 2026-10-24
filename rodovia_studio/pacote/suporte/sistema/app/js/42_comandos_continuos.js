// =====================================================================================================
// 1.34: comandos contínuos — Enter confirma, Esc cancela, e o mesmo comando continua em outra entidade.
//  • Comandos sobre a seleção (MOVER, COPIAR, GIRAR, ESCALA, ESPELHAR, OFFSET, APAGAR): ao concluir, o comando
//    pede o próximo objeto; clicar num objeto repete o comando nele. Enter (sem nada digitado) ou Esc encerram.
//  • Ferramentas de desenho: Enter conclui o objeto e a ferramenta continua pronta para o próximo; Enter de novo
//    (sem pontos) ou Esc encerram.
//  • Arrastar: Shift prende o movimento na horizontal/vertical; Esc durante o arraste devolve o objeto ao lugar.
// =====================================================================================================
const CMD_CONTINUO={MOVER:['M','MOVE','MOVER'],COPIAR:['CO','COPIAR','COPY','CP'],GIRAR:['RO','GIRAR','ROTATE','ROTACIONAR'],ESCALA:['SC','ESCALA','ESCALAR','SCALE'],
 ESPELHAR:['MI','ESPELHAR','MIRROR'],OFFSET:['OF','OFFSET','DESLOCAR','PARALELA'],APAGAR:['E','DEL','ERASE','APAGAR','EXCLUIR']};
function nomeContinuo(t){t=String(t||'').trim().toUpperCase();return Object.keys(CMD_CONTINUO).find(k=>CMD_CONTINUO[k].includes(t))||null}
let cmdRep=null,cmdEscapando=false;
// cmdRep = nome do comando que continua. Sem comando pendente: o próximo clique num objeto o seleciona (como sempre)
// e repete o comando nele; clicar no vazio, Enter ou Esc encerram.
function encerrarRepeticao(texto){if(!cmdRep)return;const n=cmdRep;cmdRep=null;prompt_('Comando:');msg(texto||`${n} encerrado.`)}
function pedirProximo(){if(!cmdRep)return;prompt_(`${cmdRep} — clique no próximo objeto (Enter ou Esc encerra):`);msg(`${cmdRep}: clique no próximo objeto para repetir; Enter, Esc ou clique no vazio encerram.`)}
estender('runCommand',anterior=>function(raw){const t=String(raw||'').trim();
 if(cmdRep&&!cadCmd){if(!t){encerrarRepeticao();return}cmdRep=null}
 const nome=nomeContinuo(t),tinhaSel=nome&&selObjs().length>0;const r=anterior(raw);
 if(nome&&tinhaSel){if(cadCmd)cmdRep=nome;else if(nome==='APAGAR'&&!selObjs().length){cmdRep=nome;pedirProximo()}}
 return r},'comandos contínuos: o mesmo comando segue em outro objeto');
// Concluído o comando (o pedido volta a “Comando:”), passa a pedir o próximo objeto — exceto ao cancelar.
estender('prompt_',anterior=>function(t){const r=anterior(t);if(t==='Comando:'&&cmdRep&&!cadCmd&&!cmdEscapando)setTimeout(()=>{if(cmdRep&&!cadCmd)pedirProximo()},0);return r},'comandos contínuos: pedir o próximo objeto');
// Trocar de ferramenta encerra a repetição.
estender('setTool',anterior=>function(t){if(cmdRep&&t!=='pan'){cmdRep=null;prompt_('Comando:')}return anterior(t)},'comandos contínuos: outra ferramenta encerra a repetição');
// Clique (sem arrastar) num objeto durante a repetição: o objeto já foi selecionado pelo clique; repete o comando.
// (A seleção captura o ponteiro: o evento de captura informa onde o botão desceu, para separar clique de arraste.)
let repDown=null;canvas.addEventListener('gotpointercapture',e=>{repDown={x:e.clientX,y:e.clientY}});
canvas.addEventListener('click',e=>{const d=repDown;repDown=null;if(!cmdRep||cadCmd||draft||tool!=='pan'||e.button)return;if(d&&Math.hypot(e.clientX-d.x,e.clientY-d.y)>4)return;
 setTimeout(()=>{if(!cmdRep)return;if(!selObjs().length){encerrarRepeticao();return}const n=cmdRep;cmdRep=null;runCommand(n)},0)});
estender('escapeCommand',anterior=>async function(){
 // Arraste em andamento: Esc devolve o objeto ao lugar, sem perguntar (como no Windows).
 if(drag&&['mmove','rot','label','grip','objmove','move','vertex','span','anchor','imgadj'].includes(drag.type)){const d=drag;drag=null;if(d.moved!==false)undo();else{undoStack.pop();updateUndo()}draw();msg('Arraste cancelado: o objeto voltou ao lugar.');return}
 cmdEscapando=true;try{return await anterior()}finally{cmdEscapando=false;if(!cadCmd)cmdRep=null}},'comandos contínuos: Esc cancela');
// Enter/Esc com o comando esperando o próximo objeto encerram sem perguntar (nada está pela metade).
window.addEventListener('keydown',e=>{if(!cmdRep||cadCmd||draft||tool!=='pan'||document.querySelector('dialog[open]'))return;const t=e.target;
 if(e.key==='Escape'||(e.key==='Enter'&&(!inField(t)||(t.id==='cmdLine'&&!t.value.trim())))){e.preventDefault();e.stopImmediatePropagation();encerrarRepeticao()}},true);
// Ferramentas de desenho: Enter conclui o objeto e mantém a ferramenta para o próximo.
estender('endCommand',anterior=>async function(){if(!draft||tool==='pan')return anterior();const t=tool;await finishDraft();
 if(!draft&&tool===t&&t!=='pan'){const d=TOOLS.find(x=>x[0]===t);prompt_(`${d?toolLabel(d):t} — próximo (Enter sem pontos ou Esc encerra):`);msg(`${d?toolLabel(d):'Objeto'} concluído. Desenhe o próximo, ou Enter/Esc para encerrar.`)}},'comandos contínuos: ferramenta continua após Enter');
