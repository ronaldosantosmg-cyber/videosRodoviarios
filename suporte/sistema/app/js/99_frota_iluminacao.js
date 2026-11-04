// Iluminação e ajuda da revisão em execução; usa os mesmos controles e comandos do produto.
(()=>{'use strict';
const LIGHT_MODES={DIA:'off',NOITE:'night',ANOITECER:'transition'};
let openingHelp=null;

function commandCatalog(){
 const entries=[],documented=new Set();
 for(const [names,instruction] of CMD_HELP){
  const aliases=String(names).split(' / ').map(n=>n.trim()).filter(n=>COMANDOS.has(n));
  if(!aliases.length)continue;
  aliases.forEach(n=>documented.add(n));
  entries.push({names:aliases,instruction:String(instruction||'').trim()});
 }
 for(const name of COMANDOS.keys())if(!documented.has(name))entries.push({names:[name],instruction:'Ajuda específica ainda não cadastrada nesta revisão. Abra a paleta de comandos e confira a instrução da ferramenta antes de executar.'});
 return entries.sort((a,b)=>a.names[0].localeCompare(b.names[0],'pt-BR'));
}

function renderCommandCatalog(){
 const root=$('helpBody');root.querySelector('#rsCurrentCommandHelp')?.remove();
 const section=document.createElement('section');section.id='rsCurrentCommandHelp';
 const heading=document.createElement('h3');heading.textContent='Comandos disponíveis nesta revisão';section.appendChild(heading);
 const note=document.createElement('p');note.textContent='Esta lista vem dos comandos carregados pelo aplicativo. Enter conclui o comando quando indicado; Esc cancela conforme a confirmação da ferramenta. Use Ctrl+K para localizar e executar um comando.';section.appendChild(note);
 const table=document.createElement('table');const head=document.createElement('thead');head.innerHTML='<tr><th scope="col">Comando / atalhos</th><th scope="col">Instrução</th></tr>';table.appendChild(head);
 const body=document.createElement('tbody');
 for(const entry of commandCatalog()){const row=document.createElement('tr'),names=document.createElement('th'),help=document.createElement('td');names.scope='row';names.textContent=entry.names.join(' / ');help.textContent=entry.instruction;row.append(names,help);body.appendChild(row)}
 table.appendChild(body);section.appendChild(table);root.appendChild(section);
}

async function openHelp(){
 if(openingHelp)return openingHelp;
 openingHelp=(async()=>{
  const health=await api('/api/health'),version=String(health.version||'não informada'),root=$('helpBody');
  if(root.dataset.version!==version){const response=await fetch('/ajuda?version='+encodeURIComponent(version),{cache:'no-store'});if(!response.ok)throw Error('Não foi possível carregar a ajuda desta versão.');root.innerHTML=await response.text();root.dataset.version=version}
  const title=root.querySelector('h2');if(title)title.textContent='Como usar o Rodovia Studio '+version;
  renderCommandCatalog();
  const dialog=$('helpDialog');if(!dialog.open)dialog.showModal();else dialog.focus({preventScroll:true});return true;
 })().finally(()=>{openingHelp=null});return openingHelp;
}

function sync3D(mode){
 if(window.Rodovia3D?.setLighting&&Rodovia3D.stats().ready){Rodovia3D.setLighting({...cfg,day_night:mode});return true}
 const target={off:'dia',night:'noite',transition:'entardecer'}[mode];
 const control=document.querySelector('#rs3dControls [data-rs3d=light3d]');
 if(!control||!window.Rodovia3D?.stats().ready)return false;
 // A ação pública existente controla o mesmo viewer, sem criar outra cena ou simulação.
 for(let i=0;i<3&&Rodovia3D.stats().light!==target;i++)control.click();
 return Rodovia3D.stats().light===target;
}

async function applyLighting(mode){
 requireProject();if(!['off','night','transition'].includes(mode))throw Error('Modo de iluminação inválido.');
 if(window.RodoviaPanels?.opened&&!await RodoviaPanels.close())return false;
 const field=$('day_night');field.value=mode;cfg.day_night=mode;
 if(mode==='transition'&&Number($('night_start_s').value)>=Number($('duration_s').value)){
  $('night_start_s').value=String(Math.max(0,Number($('duration_s').value)/2));cfg.night_start_s=Number($('night_start_s').value);
 }
 if(mode==='transition'){$('night_transition_s').value=String(Math.max(.5,Math.min(Number($('night_transition_s').value)||8,Number($('duration_s').value)-Number($('night_start_s').value))));cfg.night_transition_s=Number($('night_transition_s').value)}
 changed();await save();sync3D(mode);
 const label={off:'Dia',night:'Noite',transition:'Anoitecer'}[mode];
 msg(label+' salvo. A próxima prévia ou vídeo usa esta iluminação; a vista 3D aberta foi sincronizada quando disponível.');
 return true;
}

async function openLighting(){
 requireProject();if(window.RodoviaPanels?.opened&&!await RodoviaPanels.close())return;
 let d;d=RodoviaModelDialog.open({id:'rsDayNight',title:'Dia e noite',html:`<p>Iluminação do projeto, aplicada à próxima preparação/prévia e ao vídeo. Sincroniza o 3D aberto.</p><label>Modo<select data-mode><option value="off">Dia</option><option value="night">Noite</option><option value="transition">Transição dia → noite</option></select></label><p>O início e a duração da transição continuam disponíveis em Configuração → Aparência → Dia e noite.</p>`,save:async()=>{if(!d.rsContext())throw Error('O projeto mudou.');return applyLighting(d.querySelector('[data-mode]').value)}});d.querySelector('[data-mode]').value=cfg.day_night||'off';return d;
}
for(const [name,mode] of Object.entries(LIGHT_MODES))if(!COMANDOS.has(name))comando([name],()=>applyLighting(mode),name==='ANOITECER'?'Salva a transição dia/noite; se o início estiver fora do vídeo, posiciona-o na metade da duração. Limita a transição ao tempo restante do vídeo. Ajuste os valores em Iluminação.':'Salva o modo '+(name==='DIA'?'dia':'noite')+' no projeto e sincroniza a vista 3D aberta. Gere uma prévia para conferir o MP4.');
if(!COMANDOS.has('AJUDAVERSAO'))comando(['AJUDAVERSAO'],openHelp,'Abre a ajuda da versão em execução e a instrução dos comandos registrados. F1 faz o mesmo.');

function install(){
 const field=$('day_night');if(field&&!$('rsLightingPresets')){
  const group=document.createElement('span');group.id='rsLightingPresets';group.setAttribute('role','group');group.setAttribute('aria-label','Aplicar iluminação ao projeto');
  for(const [name,mode] of Object.entries(LIGHT_MODES)){const button=document.createElement('button');button.type='button';button.className='mini';button.dataset.lighting=mode;button.textContent={DIA:'Dia',NOITE:'Noite',ANOITECER:'Anoitecer'}[name];button.title='Aplicar e salvar '+button.textContent.toLowerCase()+' no projeto';button.onclick=guard(e=>{e.preventDefault();e.stopPropagation();return applyLighting(mode)});group.appendChild(button)}
  field.closest('label').appendChild(group);
 }
 $('helpBtn').onclick=guard(openHelp,'Ajuda desta versão');
}
document.addEventListener('keydown',e=>{if(e.key==='F1'){e.preventDefault();e.stopImmediatePropagation();void guard(openHelp,'Ajuda desta versão')()}},true);
queueMicrotask(install);
window.RodoviaHelp=Object.freeze({open:openHelp,commands:commandCatalog});
window.RodoviaLighting=Object.freeze({apply:applyLighting,open:openLighting,sync3D});
})();
