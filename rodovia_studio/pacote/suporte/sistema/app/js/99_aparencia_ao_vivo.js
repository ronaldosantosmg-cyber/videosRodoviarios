// 2.43: aparência ao vivo. Trocar o TIPO de textura/material/representação repinta o editor 2D na hora (antes só mudava ao dar zoom ou depois de gerar o vídeo).
// leitura(): o que a tela mostra AGORA = caixas de seleção + rascunho de quem ainda está arrastando um controle; assinatura() entra na chave do cache da camada técnica.
(()=>{'use strict';
const CAMPOS=['pavement_material','existing_material','shoulder_material','style_profile','texture_style','earthwork_look','joint_spacing_m','natural_materials_only','project_contrast'];
const rascunho={tp:{},ps:{}};
function el(id){return typeof document!=='undefined'?document.getElementById(id):null}
function leitura(){const o={};
 for(const k of CAMPOS){const e=el(k);o[k]=e?(e.type==='checkbox'?!!e.checked:(e.type==='number'||e.type==='range'?Number(e.value):e.value)):(typeof cfg!=='undefined'&&cfg?cfg[k]:undefined)}
 const base=(typeof cfg!=='undefined'&&cfg)||{};
 o.tp={...(base.texture_params||{}),...rascunho.tp};o.ps={...(base.pavement_styles||{}),...rascunho.ps};o.lm=base.layer_materials||{};o.rc=base.role_colors||{};return o}
function assinatura(){try{return JSON.stringify(leitura())}catch(_e){return ''}}
let ultima='';
function repintar(){const a=assinatura();if(a===ultima)return;ultima=a;try{window.RodoviaLayers?.invalidate?.('technical');if(typeof draw==='function')draw()}catch(e){window.RodoviaErros?.avisar?.('aparência ao vivo',e)}}
function agendar(){if(typeof requestAnimationFrame==='function')requestAnimationFrame(repintar);else repintar()}
function lerLinha(tr){const o={};tr.querySelectorAll('[data-k]').forEach(i=>{o[i.dataset.k]=i.type==='number'?Number(i.value):i.value});return o}
if(typeof document!=='undefined'){
 const alvo=e=>{const id=e.target&&e.target.id;return CAMPOS.includes(id)};
 document.addEventListener('change',e=>{if(alvo(e)||e.target.closest?.('#pavStyles,#texEditor,#layers')){rascunho.tp={};rascunho.ps={};agendar()}});
 document.addEventListener('input',e=>{
  if(alvo(e)){agendar();return}
  const card=e.target.closest?.('#texEditor [data-tex]');
  if(card&&typeof texVals==='function'){rascunho.tp={...rascunho.tp,[card.dataset.tex]:texVals(card)};agendar();return}
  const tr=e.target.closest?.('#pavStyles tr[data-role]');
  if(tr){const v=lerLinha(tr);const r=tr.dataset.role;rascunho.ps={...rascunho.ps,[r]:v.pattern==='auto'?{pattern:'auto'}:v};agendar()}});
}
// qualquer gravação de configuração (janelas de textura, pincel, catálogo de materiais...) também repinta se a aparência mudou
if(typeof scheduleSave==='function'){const antigo=scheduleSave;scheduleSave=function(...a){const r=antigo.apply(this,a);agendar();return r}}
window.RodoviaAparencia=Object.freeze({leitura,assinatura,repintar,rascunho});
})();
