// =====================================================================================================
// 1.35: menus como no Windows 11.
//  • Ícones de linha (monocromáticos, na cor de destaque) no menu do botão direito, na mini-barra da seleção
//    e na faixa de opções, no lugar dos emojis.
//  • Submenus abrem ao lado (flyout), ao passar o mouse ou clicar — sem trocar o menu inteiro.
//  • A ajuda do item aparece como dica (tooltip) e numa linha discreta no rodapé do menu.
// =====================================================================================================
const ICO={mover:'M12 3v18M3 12h18M12 3l-3 3M12 3l3 3M12 21l-3-3M12 21l3-3M3 12l3-3M3 12l3 3M21 12l-3-3M21 12l-3 3',
 copiar:'M8 8h11v11H8zM5 16V5h11',girar:'M20 12a8 8 0 1 1-2.3-5.7M20 4v5h-5',escala:'M4 20l7-7M4 20v-6M4 20h6M14 4h6v6M20 4l-7 7',
 espelhar:'M12 3v18M9 6L4 18h5zM15 6l5 12h-5z',paralela:'M4 18L14 4M10 20L20 6',pincel:'M14 4l6 6-8 8H6v-6zM4 21c2 0 3-1 3-3',
 apagar:'M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v6M14 11v6',desmarcar:'M4 4h4M16 4h4M4 20h4M16 20h4M4 4v4M4 16v4M20 4v4M20 16v4',
 propriedades:'M4 6h16M4 12h16M4 18h10',concluir:'M5 12l5 5 9-10',desfazer:'M9 14L4 9l5-5M4 9h10a6 6 0 0 1 0 12h-3',refazer:'M15 14l5-5-5-5M20 9H10a6 6 0 0 0 0 12h3',
 cancelar:'M6 6l12 12M18 6L6 18',inserir:'M12 5v14M5 12h14',aparencia:'M12 3a9 9 0 1 0 0 18c1.5 0 2-1 2-2s-1-2 0-3 2-1 3-1a4 4 0 0 0 4-4c0-4.4-4-8-9-8zM7.5 11h.01M12 7.5h.01M16.5 11h.01',
 tudo:'M4 4h16v16H4zM8 8h8v8H8z',enquadrar:'M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5',centro:'M12 2v4M12 18v4M2 12h4M18 12h4M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z',
 regenerar:'M4 12a8 8 0 0 1 14-5l2 2M20 12a8 8 0 0 1-14 5l-2-2M20 4v5h-5M4 20v-5h5',ajuda:'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM9.5 9a2.5 2.5 0 0 1 5 0c0 2-2.5 2-2.5 4M12 17h.01',
 olho:'M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12zM12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z',isolar:'M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z',
 camada:'M12 3l9 5-9 5-9-5zM3 13l9 5 9-5',textura:'M4 4h16v16H4zM4 10h16M4 16h16M10 4v16M16 4v16',nome:'M4 20h4L19 9l-4-4L4 16zM13 7l4 4',
 grips:'M5 5h4v4H5zM15 5h4v4h-4zM5 15h4v4H5zM15 15h4v4h-4zM9 7h6M7 9v6M17 9v6M9 17h6',portico:'M5 21V5h14v16M5 9h14',
 estrela:'M12 3l2.8 5.7 6.2.9-4.5 4.4 1 6.2L12 17.3 6.5 20.2l1-6.2L3 9.6l6.2-.9z',alinhamento:'M4 20L20 4M4 20h3M17 4h3',placa:'M12 2l9 9-9 9-9-9zM12 8v5M12 16h.01',
 salvar:'M5 3h11l3 3v15H5zM8 3v6h8V3M8 21v-7h8v7',velocidade:'M12 13l4-4M5 18a9 9 0 1 1 14 0',inverter:'M7 7h13l-4-4M17 17H4l4 4',
 agua:'M3 9c3-3 6 3 9 0s6 3 9 0M3 15c3-3 6 3 9 0s6 3 9 0',sinalizacao:'M4 4v16M20 4v16M12 4v3M12 10v4M12 17v3',pavimento:'M3 20L9 4h6l6 16zM12 8v2M12 13v2M12 18v2',
 talude:'M3 20l6-10 4 6 3-4 5 8z',proibir:'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM6 6l12 12',previa:'M3 5h18v14H3zM10 9l5 3-5 3z',ligacao:'M4 12h10M10 6l6 6-6 6M20 4v16',
 voltar:'M15 18l-6-6 6-6',caixa:'M4 6h16v10H8l-4 4z',obra:'M3 20h18M5 20V9l7-5 7 5v11M9 20v-6h6v6',zoom:'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM20 20l-4-4',
 abrir:'M3 7h6l2 2h10v10H3zM3 7v12',novo:'M6 3h9l4 4v14H6zM14 3v5h5M12 11v6M9 14h6',video:'M4 6h12v12H4zM16 10l5-3v10l-5-3',pasta:'M3 7h6l2 2h10v10H3z',
 analisar:'M10 4a6 6 0 1 0 0 12 6 6 0 0 0 0-12zM20 20l-5.5-5.5',dxf:'M4 20L12 4l8 16zM8 14h8',globo:'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18',
 registros:'M6 3h12v18H6zM9 8h6M9 12h6M9 16h4',importar:'M12 3v12M7 10l5 5 5-5M4 21h16',exportar:'M12 15V3M7 8l5-5 5 5M4 21h16',limpar:'M4 20h16M7 20l3-12h4l3 12M12 8V3',
 tela:'M3 5h18v12H3zM8 21h8M12 17v4',lista:'M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01',tema:'M12 3a9 9 0 1 0 9 9 7 7 0 0 1-9-9z',pino:'M9 4h6l-1 6 3 3H7l3-3zM12 13v8'};
const ICO_REGRAS=[[/^voltar/,'voltar'],[/copiar propriedades|pincel/,'pincel'],[/propriedades|atributos/,'propriedades'],[/^mover a caixa|caixa autom/,'caixa'],[/^mover|^mover$/,'mover'],[/copiar propriedades|pincel/,'pincel'],
 [/^copiar/,'copiar'],[/^girar/,'girar'],[/escala/,'escala'],[/espelhar/,'espelhar'],[/paralela|offset/,'paralela'],[/^apagar|excluir/,'apagar'],[/desmarcar/,'desmarcar'],
 [/^concluir|permitir/,'concluir'],[/desfazer último|^desfazer/,'desfazer'],[/refazer/,'refazer'],[/^cancelar/,'cancelar'],[/^inserir|^novo$/,'inserir'],[/aparência/,'aparencia'],
 [/selecionar tudo/,'tudo'],[/selecionar a área|tornar editável|grips/,'grips'],[/enquadrar|ajustar/,'enquadrar'],[/centralizar/,'centro'],[/regenerar|atualizar fluxos/,'regenerar'],
 [/comandos|ajuda|como usar/,'ajuda'],[/ocultar|mostrar/,'olho'],[/isolar/,'isolar'],[/camada|gerenciador/,'camada'],[/textura/,'textura'],[/trocar nome|renomear|editar traçado/,'nome'],
 [/pórtico|portico/,'portico'],[/destaque/,'estrela'],[/alinhamento|linha como/,'alinhamento'],[/^placa/,'placa'],[/sessão|^salvar/,'salvar'],[/velocidade/,'velocidade'],
 [/inverter|trocar tipo/,'inverter'],[/água|hidrografia/,'agua'],[/sinalização/,'sinalizacao'],[/pavimento|área de pista/,'pavimento'],[/talude|canteiro/,'talude'],
 [/proibir/,'proibir'],[/prévia|gerar vídeo|vídeos gerados/,'previa'],[/ligação|ligações/,'ligacao'],[/obra/,'obra'],[/zoom|detalhar/,'zoom'],[/^abrir|modelos/,'abrir'],
 [/vídeo/,'video'],[/pasta/,'pasta'],[/analisar/,'analisar'],[/dxf/,'dxf'],[/kmz|kml|web/,'globo'],[/registros|prompt/,'registros'],[/importar/,'importar'],[/exportar|baixar/,'exportar'],
 [/limpar/,'limpar'],[/tela cheia|tela ampla|área máxima|janela/,'tela'],[/tabela|lista/,'lista'],[/tema|claro|escuro/,'tema'],[/fixar/,'pino']];
function icoSvg(nome){const p=ICO[nome];return p?`<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${p}"/></svg>`:''}
function icoPara(texto){const t=String(texto||'').toLowerCase().trim();const r=ICO_REGRAS.find(([rx])=>rx.test(t));return r?icoSvg(r[1]):''}
function iconizar(raiz,sel,lab){raiz?.querySelectorAll(sel).forEach(el=>{const ic=el.querySelector(lab.ic);if(!ic||ic.dataset.svg)return;const s=icoPara(el.querySelector(lab.t)?.textContent||el.title);if(s){ic.innerHTML=s;ic.dataset.svg='1'}})}

// ---------- menu do botão direito ----------
estender('renderMenu',anterior=>function(el,items,x,y){anterior(el,items,x,y);
 el.querySelectorAll('.it[data-i]').forEach(d=>{const it=items[Number(d.dataset.i)];if(it?.h)d.title=it.h+(it.k?` (${it.k})`:'')});
 iconizar(el,'.it',{ic:'.ic',t:'span:nth-child(2)'})},'menus Windows: ícones e dicas');
let subTimer=null;
function abrirSub(i){if(!ctxState)return;const it=ctxState.items[i];const el=ctxState.el;el.querySelector('.ctxSub')?.remove();if(!it?.sub)return;
 const row=el.querySelector(`.it[data-i="${i}"]`);const sub=document.createElement('div');sub.className='ctxSub';sub.setAttribute('role','menu');
 sub.innerHTML=it.sub.map((s,k)=>s.sep?'<div class="sep"></div>':s.hd?`<div class="hd">${esc(s.hd)}</div>`:`<div class="it${s.dis?' dis':''}" data-si="${k}" role="menuitem" title="${esc((s.h||s.t)+(s.k?` (${s.k})`:''))}"><span class="ic">${s.ic||''}</span><span>${esc(s.t)}</span><span class="k">${esc(s.k||'')}</span></div>`).join('');
 el.appendChild(sub);iconizar(sub,'.it',{ic:'.ic',t:'span:nth-child(2)'});
 const r=row.getBoundingClientRect(),m=el.getBoundingClientRect(),w=sub.offsetWidth||260,h=sub.offsetHeight;
 const esquerda=r.right+w+4>innerWidth;sub.style.left=(esquerda?-w+2:m.width-4)+'px';sub.style.top=Math.max(-(m.top-4),Math.min(r.top-m.top-5,innerHeight-m.top-h-6))+'px';
 sub._it=it;row.classList.add('aberto')}
estender('menuActivate',anterior=>function(i){const it=ctxState?.items[i];if(it?.sub){abrirSub(i);return}return anterior(i)},'menus Windows: submenu ao lado');
$('ctxMenu')?.addEventListener('mouseover',e=>{const d=e.target.closest('.it[data-i]');if(!d||!ctxState)return;clearTimeout(subTimer);const i=Number(d.dataset.i),it=ctxState.items[i];
 subTimer=setTimeout(()=>{if(!ctxState)return;if(it?.sub)abrirSub(i);else{ctxState.el.querySelector('.ctxSub')?.remove();ctxState.el.querySelectorAll('.it.aberto').forEach(x=>x.classList.remove('aberto'))}},it?.sub?180:320)});
$('ctxMenu')?.addEventListener('click',e=>{const d=e.target.closest('.ctxSub .it[data-si]');if(!d)return;e.stopPropagation();const s=d.closest('.ctxSub')._it?.sub?.[Number(d.dataset.si)];if(!s||s.dis)return;
 if(s.sub){ctxState.stack.push(ctxState.items);ctxState.items=[{ic:'‹',t:'Voltar',h:'Volta ao menu anterior.',back:1},{sep:1},...s.sub];ctxState.on=-1;renderMenu(ctxState.el,ctxState.items,ctxState.x,ctxState.y);return}
 closeMenu();try{const r=s.f&&s.f();if(r&&r.catch)r.catch(err=>msg(err.message,true))}catch(err){msg(err.message,true)}},true);
$('ctxMenu')?.addEventListener('mousemove',e=>{const d=e.target.closest('.ctxSub .it[data-si]');if(!d)return;const s=d.closest('.ctxSub')._it?.sub?.[Number(d.dataset.si)];const h=ctxState?.el.querySelector(':scope>.ctxHelp');if(h&&s)h.textContent=(s.h||s.t)+(s.k?` (${s.k})`:'')});

// ---------- mini-barra da seleção e faixa de opções ----------
{const sb=$('selBar');if(sb)sb.querySelectorAll('[data-sb]').forEach(b=>{const m={move:'mover',rot:'girar',copy:'copiar',tex:'textura',name:'nome',edit:'grips',props:'propriedades',del:'apagar'}[b.dataset.sb];if(m)b.innerHTML=icoSvg(m)})}
{const bar=$('menuBar');if(bar){const f=()=>iconizar(bar,'.rb',{ic:'.ri',t:'.rl'});new MutationObserver(f).observe(bar,{childList:true,subtree:true});f()}}   // faixa de opções: refeita a cada troca de aba
