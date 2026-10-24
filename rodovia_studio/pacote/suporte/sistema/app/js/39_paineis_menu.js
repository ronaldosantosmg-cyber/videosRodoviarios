// =====================================================================================================
// 1.34: painéis por menu (como no Windows/Visual Studio). Na tela ampla, a coluna da esquerda vira uma barra de
// ícones; cada ícone abre o painel da seção (Projeto, Configuração, Camadas, Exportar, Manutenção, Intervenções,
// Vista e prévia). Clicar de novo no ícone, ou em ×, fecha. 📌 fixa: o painel encaixa ao lado e o desenho diminui;
// desafixado, o painel abre por cima do desenho e o desenho fica do mesmo tamanho. Os campos são os mesmos (só
// mudam de lugar) — fechar um painel não interrompe cálculos, tarefas nem a edição.
// =====================================================================================================
const PNPREF={get(k,d){try{const v=localStorage.getItem('rodovia_pn_'+k);return v==null?d:JSON.parse(v)}catch{return d}},set(k,v){try{localStorage.setItem('rodovia_pn_'+k,JSON.stringify(v))}catch{}}};
let pnEstado={aberto:PNPREF.get('aberto',null),fixado:PNPREF.get('fixado',false)},pnItens=[],pnLugares=[];
function pnCurto(t){const M=[[/^Projeto/,'Projeto'],[/^Configura/,'Config.'],[/^Camadas/,'Camadas'],[/^Exportar/,'Vídeo'],[/^Manuten/,'Manut.'],[/^Interven/,'Interv.'],[/^Vista/,'Vista']];return (M.find(([r])=>r.test(t))||[0,t.split(/[ ,]/)[0]])[1]}
function pnModoPaineis(){try{return localStorage.getItem('rodovia_paineis')!=='0'}catch{return true}}
function pnAtivo(){return document.body.classList.contains('wide')&&JANELA==='unica'&&pnModoPaineis()}
function pnColunaClassica(v){try{localStorage.setItem('rodovia_paineis',v?'0':'1')}catch{}pnSincronizar();msg(v?'Coluna clássica: as seções ficam todas na coluna da esquerda.':'Painéis por menu: clique nos ícones da esquerda para abrir cada painel.')}
// Vista, prévia e sessões: as linhas de cima do editor viram um painel também (mais altura para o desenho).
function pnSecaoVista(){let s=$('secVista');if(s)return s;s=document.createElement('section');s.id='secVista';
 s.innerHTML='<h2><span class="ico"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12zM12 9a3 3 0 100 6 3 3 0 000-6z"/></svg></span>Vista, prévia e sessões</h2>';return s}
function pnMover(el,destino){if(!el)return;const marca=document.createComment('pn:'+(el.id||el.className));el.parentNode.insertBefore(marca,el);pnLugares.push([el,marca]);destino.appendChild(el)}
function pnEntrar(){if(document.body.classList.contains('paineis'))return;const main=document.querySelector('main');const cols=[...main.children].filter(x=>x.tagName==='DIV'&&!x.classList.contains('splitter'));
 const esq=cols[0],dir=cols[1];if(!esq||!dir)return;esq.classList.add('pnArea');dir.classList.add('pnDireita');pnLugares=[];
 // Intervenções (abaixo do editor) e as linhas de vista/prévia vão para a área dos painéis.
 const interv=[...dir.querySelectorAll(':scope>section')].find(s=>/Intervenções/.test(s.querySelector('h2')?.textContent||''));if(interv)pnMover(interv,esq);
 const vista=pnSecaoVista();const ed=$('editorSection');
 for(const el of [ed.querySelector(':scope>.row:not(.timeline):not(.baseRow)'),ed.querySelector(':scope>.timeline'),ed.querySelector(':scope>.baseRow'),ed.querySelector('.sessRow')])pnMover(el,vista);
 esq.appendChild(vista);
 if(!$('pnHead')){esq.insertAdjacentHTML('afterbegin','<div id="pnHead" class="pnHead"><span id="pnTitulo" class="pnTitulo"></span><button type="button" id="pnFixar" title="Fixar: o painel fica encaixado e o desenho se ajusta">📌</button><button type="button" id="pnFechar" title="Fechar o painel (os dados continuam como estão)">×</button></div>');
  $('pnFixar').onclick=()=>pnFixar(!pnEstado.fixado);$('pnFechar').onclick=()=>pnAbrir(null)}
 pnItens=[...esq.querySelectorAll(':scope>section')].filter(s=>!s.classList.contains('retirada')).map(s=>{if(!s.id)s.id='sec_'+Math.random().toString(36).slice(2,7);const h=s.querySelector(':scope>h2');
  const tt=[...(h?.childNodes||[])].filter(n=>!(n.classList&&n.classList.contains('ico'))).map(n=>n.textContent).join('');
  return {id:s.id,el:s,t:tt.trim().replace(/^\d+\.\s*/,''),ico:h?.querySelector('.ico')?.innerHTML||'▣'}});
 let bar=$('atividades');if(!bar){bar=document.createElement('nav');bar.id='atividades';bar.className='atividades';bar.setAttribute('aria-label','Painéis');main.prepend(bar)}
 bar.innerHTML=pnItens.map(i=>`<button type="button" data-pn="${i.id}" title="${esc(i.t)}"><span class="pnIco">${i.ico}</span><span class="pnRot">${esc(pnCurto(i.t))}</span></button>`).join('');
 bar.onclick=e=>{const b=e.target.closest('[data-pn]');if(b)pnAbrir(pnEstado.aberto===b.dataset.pn?null:b.dataset.pn)};
 document.body.classList.add('paineis');pnAplicar(false)}
function pnSair(){if(!document.body.classList.contains('paineis'))return;document.body.classList.remove('paineis','pnAberto','pnFixado');
 for(const [el,marca] of pnLugares.reverse()){marca.parentNode?.insertBefore(el,marca);marca.remove()}pnLugares=[];
 $('secVista')?.remove();$('pnHead')?.remove();$('atividades')?.remove();
 document.querySelectorAll('main section').forEach(s=>s.classList.remove('pnOculta'));setTimeout(()=>{try{resizeCanvas()}catch{}},40)}
function pnPosicao(){const main=document.querySelector('main'),bar=$('atividades');if(!main||!bar)return;const r=bar.getBoundingClientRect();
 document.documentElement.style.setProperty('--pnL',Math.round(r.right+4)+'px');document.documentElement.style.setProperty('--pnT',Math.round(r.top)+'px')}
function pnAplicar(salvar=true){if(!document.body.classList.contains('paineis'))return;const id=pnItens.some(i=>i.id===pnEstado.aberto)?pnEstado.aberto:null;
 document.body.classList.toggle('pnAberto',!!id);document.body.classList.toggle('pnFixado',!!pnEstado.fixado);
 for(const i of pnItens){i.el.classList.toggle('pnOculta',i.id!==id);if(i.id===id)i.el.classList.remove('collapsed')}
 $('atividades')?.querySelectorAll('[data-pn]').forEach(b=>b.classList.toggle('on',b.dataset.pn===id));
 const it=pnItens.find(i=>i.id===id);if($('pnTitulo'))$('pnTitulo').textContent=it?it.t:'';
 if($('pnFixar')){$('pnFixar').classList.toggle('on',!!pnEstado.fixado);$('pnFixar').title=pnEstado.fixado?'Desafixar: o painel abre por cima do desenho e fecha ao voltar a desenhar':'Fixar: o painel fica encaixado e o desenho se ajusta'}
 pnPosicao();if(salvar){PNPREF.set('aberto',id);PNPREF.set('fixado',!!pnEstado.fixado)}
 if(id)document.querySelector('main>div.pnArea')?.scrollTo({top:0});setTimeout(()=>{try{resizeCanvas()}catch{}},40)}
function pnAbrir(id){pnEstado.aberto=id;pnAplicar()}
function pnFixar(v){pnEstado.fixado=v;pnAplicar();msg(v?'Painel fixado: fica ao lado do desenho.':'Painel desafixado: abre por cima do desenho e fecha ao voltar a desenhar.')}
// Desafixado: voltar a navegar no desenho fecha o painel (como “ocultar automaticamente” do Windows).
// Com outra ferramenta ativa (ex.: Intervenção preenchendo X/Y) o painel fica aberto.
canvas.addEventListener('pointerdown',()=>{if(document.body.classList.contains('pnAberto')&&!pnEstado.fixado&&tool==='pan')pnAbrir(null)});
// Abrir uma seção pelos menus abre o painel dela.
estender('openSection',anterior=>function(title){if(document.body.classList.contains('paineis')){const it=pnItens.find(i=>i.el.querySelector(':scope>h2')?.textContent.includes(title)||[...i.el.querySelectorAll('summary,h2')].some(x=>x.textContent.includes(title)));if(it&&pnEstado.aberto!==it.id)pnAbrir(it.id)}return anterior(title)},'painéis: abrir a seção pelo menu');
// Área máxima: fecha o painel da esquerda (além de recolher a barra da direita).
estender('alternarAreaMax',anterior=>function(v){const r=anterior(v);if(areaMax&&document.body.classList.contains('paineis'))pnAbrir(null);return r},'painéis: área máxima fecha o painel');
function pnSincronizar(){if(pnAtivo())pnEntrar();else pnSair()}
new MutationObserver(()=>{const quer=pnAtivo(),tem=document.body.classList.contains('paineis');if(quer!==tem)pnSincronizar()}).observe(document.body,{attributes:true,attributeFilter:['class']});
window.addEventListener('resize',()=>pnPosicao());
{const X=RIBBON.find(t=>t[0]==='Exibir');const g=X[1].find(x=>x[0]==='Área de trabalho');g[1].push(['Fixar painel','📌',()=>pnFixar(!pnEstado.fixado)],['Fechar painel','✕',()=>pnAbrir(null)],['Coluna clássica','▥',()=>pnColunaClassica(pnModoPaineis())])}
comando(['PAINEIS','PNL'],()=>pnFixar(!pnEstado.fixado),'Fixa/desafixa o painel da esquerda');
pnSincronizar();
