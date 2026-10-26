// Preferências de interface: mesmos comandos, sem alterar o projeto ou cálculos.
(()=>{'use strict';
const glyphs={
 'Arquivos do projeto':'M3 7V5h6l2 2h10v13H3Z',
 'Camadas e imagens':'m12 3 10 5-10 5L2 8Zm-9 10 9 5 9-5M3 18l9 4 9-4',
 'Analisar layers / IA':'M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14m5 12 6 6M8 10h4M10 8v4',
 'Proteção de dados':'m12 2 8 3v6c0 5-4 8-8 11-4-3-8-6-8-11V5Zm-4 10 3 3 5-6',
 'IA assistida de fluxos':'M4 6h6v5h10M4 18h6v-7M4 3v6M4 15v6M20 8v6M15 3l3 3-3 3',
 'Corrigir problemas':'m4 20 9-9M14 4a6 6 0 0 0 6 8l-4-4 4-4a6 6 0 0 0-6 0ZM3 17l4 4',
 'Gerar e visualizar':'m8 4 13 8-13 8ZM3 4v16',
 'Configurar vídeo':'M3 5h13v14H3ZM16 9l5-3v12l-5-3M6 9h7M6 13h4',
 'Gerar prévia':'M3 4h18v16H3Zm6 4v8l7-4Z',
 'Gerar vídeo':'M3 3h18v18H3ZM7 3v18M17 3v18M3 8h4M17 8h4M3 16h4M17 16h4'
};
function glyph(path){return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" stroke-linecap="round" aria-hidden="true"><path d="'+path+'"/></svg>'}
let mode=false,favorites=[];try{mode=localStorage.getItem('rodovia_cad_mode')==='1';const v=JSON.parse(localStorage.getItem('rodovia_favorites')||'[]');if(Array.isArray(v))favorites=v.filter(x=>typeof x==='string').slice(0,8)}catch{}
function init(){const nav=$('rsQuickNavigation');if(!nav||$('rsCadMode'))return;const tools=new Map();
 for(const b of document.querySelectorAll('#rsToolRibbon button[data-rs-tool],#rsToolRibbon button[data-rs-command],#rsToolRibbon .rsPrimaryAction')){
  const label=b.getAttribute('aria-label')||b.querySelector(':scope>span:not(.rsCadIcon)')?.textContent.trim()||b.textContent.trim()||b.title,key=b.dataset.rsTool?'tool:'+b.dataset.rsTool:b.dataset.rsCommand?'command:'+b.dataset.rsCommand:'action:'+label;
  if(!label||tools.has(key))continue;b.title=b.title||label;b.setAttribute('aria-label',label);
  if(!b.querySelector('svg')&&b.classList.contains('rsPrimaryAction')){b.replaceChildren();const icon=document.createElement('span');icon.innerHTML=toolIcon('inspect');icon.className='rsCadIcon';const text=document.createElement('span');text.textContent=label;b.append(icon,text)}
  if(glyphs[label]){const holder=document.createElement('span');holder.innerHTML=glyph(glyphs[label]);const svg=holder.firstElementChild;const old=b.querySelector('svg');if(old)old.replaceWith(svg)}
  tools.set(key,{b,label});
 }
 const toggle=document.createElement('button');toggle.id='rsCadMode';toggle.type='button';toggle.title='Alternar modo CAD compacto';toggle.setAttribute('aria-label',toggle.title);toggle.innerHTML=glyph('M3 3h18v18H3ZM3 8h18M8 8v13M12 12h5M12 16h5');nav.append(toggle);
 function paint(){document.body.classList.toggle('rsCadMode',mode);toggle.setAttribute('aria-pressed',String(mode));try{localStorage.setItem('rodovia_cad_mode',mode?'1':'0');localStorage.setItem('rodovia_favorites',JSON.stringify(favorites))}catch{}requestAnimationFrame(scheduleCanvasResize)}toggle.onclick=()=>{mode=!mode;paint()};
 const host=document.createElement('div');host.id='rsFavoriteTools';host.setAttribute('role','toolbar');host.setAttribute('aria-label','Favoritos');nav.append(host);
 function draw(){host.replaceChildren();for(const key of favorites){const item=tools.get(key);if(!item)continue;const b=document.createElement('button');b.type='button';b.title=item.label;b.setAttribute('aria-label','Favorito: '+item.label);b.innerHTML=item.b.querySelector('svg')?.outerHTML||toolIcon('inspect');b.onclick=()=>{if(item.b.disabled)return msg('Este comando está indisponível no contexto atual.');item.b.click()};host.append(b)}paint()}
 const configure=document.createElement('button');configure.id='rsFavoriteSettings';configure.type='button';configure.title='Configurar até oito favoritos';configure.setAttribute('aria-label',configure.title);configure.textContent='☆';configure.onclick=()=>{const d=document.createElement('dialog');d.className='winDlg rsFavoriteDialog';const h=document.createElement('h3');h.textContent='Favoritos — até oito comandos';d.append(h);const chosen=new Set(favorites);for(const [key,item] of tools){const label=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.checked=chosen.has(key);input.onchange=()=>{if(input.checked&&chosen.size>=8){input.checked=false;return msg('Limite de oito favoritos.')}if(input.checked)chosen.add(key);else chosen.delete(key)};label.append(input,document.createTextNode(item.label));d.append(label)}const apply=document.createElement('button');apply.textContent='Salvar preferências';apply.onclick=()=>{favorites=[...chosen];draw();d.close();d.remove()};const cancel=document.createElement('button');cancel.textContent='Cancelar';cancel.onclick=()=>{d.close();d.remove()};d.append(apply,cancel);d.oncancel=e=>{e.preventDefault();cancel.click()};document.body.append(d);d.showModal()};nav.append(configure);draw();
}
queueMicrotask(()=>queueMicrotask(()=>queueMicrotask(init)));
})();
