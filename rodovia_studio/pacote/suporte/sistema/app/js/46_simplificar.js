// =====================================================================================================
// 1.35: tela simplificada (modo painéis): o que já está na faixa de opções sai dos painéis e do cabeçalho.
//  • Ferramentas: uma linha só — “Navegação” fica à mostra; os outros grupos viram botões com lista suspensa
//    (como os botões de grupo do Windows/Office). O botão mostra a ferramenta ativa do grupo.
//  • Cabeçalho: Duas janelas, Tela ampla, Compacto, Dicas e Como usar vão para Exibir/Ajuda.
//  • Painéis: Novo/Salvar/Salvar como/Excluir (faixa de opções e Arquivo), Manutenção (Arquivo › Limpar memória) e os
//    botões de janela do painel Vista (Exibir) não se repetem. A coluna clássica continua com tudo.
// =====================================================================================================
function simplificarFerramentas(){const tb=$('toolbar');if(!tb||!document.body.classList.contains('paineis'))return;
 tb.querySelectorAll('.tgroup').forEach((g,i)=>{if(i===0||g.querySelector(':scope>.tgBtn'))return;g.classList.add('dobravel');
  const nome=g.querySelector('.tgname')?.textContent||'Ferramentas';const b=document.createElement('button');b.type='button';b.className='tgBtn';b.title=nome+' (clique para ver as ferramentas)';
  b.innerHTML=`<span class="tgIco"></span><span class="tgTxt">${esc(nome)}</span><span class="tgSeta">▾</span>`;g.prepend(b);
  b.onclick=e=>{e.stopPropagation();const ab=!g.classList.contains('aberto');tb.querySelectorAll('.tgroup.aberto').forEach(x=>x.classList.remove('aberto'));g.classList.toggle('aberto',ab)}});
 marcarGrupos()}
function marcarGrupos(){const tb=$('toolbar');if(!tb)return;tb.querySelectorAll('.tgroup.dobravel').forEach(g=>{const at=g.querySelector('.tbtns button.active')||g.querySelector('.tbtns button');
 const ic=g.querySelector('.tgIco');if(ic&&at){const svg=at.querySelector('svg');ic.innerHTML=svg?svg.outerHTML:''}g.classList.toggle('temAtiva',!!g.querySelector('.tbtns button.active'));
 const t=g.querySelector('.tgTxt');if(t){const a=g.querySelector('.tbtns button.active span');t.textContent=a?a.textContent:(g.querySelector('.tgname')?.textContent||'')}})}
document.addEventListener('pointerdown',e=>{if(!e.target.closest('#toolbar .tgroup.aberto'))document.querySelectorAll('#toolbar .tgroup.aberto').forEach(x=>x.classList.remove('aberto'))},true);
document.addEventListener('click',e=>{if(e.target.closest('#toolbar .tgroup.aberto .tbtns button'))setTimeout(()=>document.querySelectorAll('#toolbar .tgroup.aberto').forEach(x=>x.classList.remove('aberto')),0)});
estender('setTool',anterior=>function(t){const r=anterior(t);try{marcarGrupos()}catch{}return r},'tela simplificada: grupo mostra a ferramenta ativa');
{const tb=$('toolbar');if(tb)new MutationObserver(()=>{if(!tb.querySelector('.tgBtn'))simplificarFerramentas()}).observe(tb,{childList:true})}
// Manutenção: fica só em Arquivo › Limpar memória (a seção continua na coluna clássica).
function simplificarPaineis(){if(!document.body.classList.contains('paineis'))return;
 const man=pnItens.find(i=>/^Manuten/.test(i.t));if(man){document.querySelector(`#atividades [data-pn="${man.id}"]`)?.remove();if(pnEstado.aberto===man.id)pnAbrir(null)}
 simplificarFerramentas()}
new MutationObserver(()=>{if(document.body.classList.contains('paineis')&&!document.querySelector('#toolbar .tgBtn'))simplificarPaineis()}).observe(document.body,{attributes:true,attributeFilter:['class']});
// O que saiu do cabeçalho entra na faixa de opções.
{const X=RIBBON.find(t=>t[0]==='Exibir');const J=X[1].find(g=>g[0]==='Janela');
 J[1].push(['Duas janelas','🗗',()=>$('twoWindows')?.click()],['Dicas nos campos','💬',()=>{const c=$('helpToggle');if(c){c.click();msg('Dicas nos campos '+(c.checked?'ligadas.':'desligadas.'))}}])}
simplificarPaineis();
