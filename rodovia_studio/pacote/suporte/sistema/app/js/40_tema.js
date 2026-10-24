// =====================================================================================================
// 1.34: tema Claro, Escuro ou “Igual ao Windows” (segue a configuração de cores do Windows e muda junto).
// O tema é aplicado já no início da página (script no <head> do index.html), sem piscar.
// =====================================================================================================
const TEMAS={sistema:'Igual ao Windows',claro:'Claro',escuro:'Escuro'};
function temaPreferido(){try{return localStorage.getItem('rodovia_tema')||'sistema'}catch{return 'sistema'}}
function temaEfetivo(p=temaPreferido()){if(p==='claro'||p==='escuro')return p;try{return matchMedia('(prefers-color-scheme: dark)').matches?'escuro':'claro'}catch{return 'escuro'}}
function aplicarTema(p,avisar){if(p){try{localStorage.setItem('rodovia_tema',p)}catch{}}const ef=temaEfetivo();document.documentElement.dataset.tema=ef;
 document.querySelectorAll('[data-tema-op]').forEach(b=>b.classList.toggle('on',b.dataset.temaOp===temaPreferido()));
 try{draw()}catch{}if(avisar)msg(`Tema: ${TEMAS[temaPreferido()]}${temaPreferido()==='sistema'?` (agora ${ef==='escuro'?'escuro':'claro'})`:''}.`)}
try{matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{if(temaPreferido()==='sistema')aplicarTema()})}catch{}
{const X=RIBBON.find(t=>t[0]==='Exibir');X[1].push(['Tema',[['Igual ao Windows','🖥',()=>aplicarTema('sistema',true)],['Claro','☀',()=>aplicarTema('claro',true)],['Escuro','☾',()=>aplicarTema('escuro',true)]]])}
comando(['TEMA'],a=>{const k=String(a||'').trim().toLowerCase();const p=/^cl/.test(k)?'claro':/^es/.test(k)?'escuro':/^(si|wi|au)/.test(k)?'sistema':(temaEfetivo()==='escuro'?'claro':'escuro');aplicarTema(p,true)},'Alterna entre o tema claro e o escuro (Exibir › Tema tem também “Igual ao Windows”)');
aplicarTema();
