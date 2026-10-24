// =====================================================================================================
// 1.40: Desktop Workspace
//  • desenho é a área principal; painéis laterais começam fechados e sempre encaixam/redimensionam o viewport;
//  • linha de comando vira gaveta inferior, fechada por padrão;
//  • faixa de opções inicia recolhida; abre apenas quando o usuário aciona uma aba;
//  • atalhos: Ctrl+Espaço = comando, Ctrl+B = painel esquerdo, Ctrl+Alt+B = painel direito, F11 = foco no projeto.
//  • comandos repetidos no cromo são reduzidos: ações de projeto ficam no menu/arquivo, edição no contexto/seleção.
// =====================================================================================================

const DW={
 get(k,d){try{const v=localStorage.getItem('rodovia_dw_'+k);return v==null?d:JSON.parse(v)}catch{return d}},
 set(k,v){try{localStorage.setItem('rodovia_dw_'+k,JSON.stringify(v))}catch{}}
};

function dwResize(){setTimeout(()=>{try{resizeCanvas()}catch{}},30)}
function dwSetRibbonMini(v=true){try{localStorage.setItem('rodovia_ribbon_min',v?'1':'0')}catch{}
 const b=document.querySelector('.rbMin');if(!b)return;
 const body=document.querySelector('.rbBody');
 if(body){body.hidden=!!v;b.textContent=v?'▾':'▴';b.title=v?'Expandir a faixa (Ctrl+F1)':'Recolher a faixa (Ctrl+F1)'}
}

function dwCommandDrawer(){
 const row=document.querySelector('.cmdRow');if(!row||row.closest('#dwCommandDrawer'))return;
 const drawer=document.createElement('div');drawer.id='dwCommandDrawer';drawer.className='dwCommandDrawer';drawer.hidden=true;
 drawer.innerHTML='<div class="dwCmdHead"><span>Linha de comando</span><span class="grow"></span><button type="button" data-dwc="help" title="Ajuda dos comandos">?</button><button type="button" data-dwc="close" title="Fechar">×</button></div><div class="dwCmdBody"></div>';
 row.parentNode.insertBefore(drawer,row);drawer.querySelector('.dwCmdBody').appendChild(row);
 const launcher=document.createElement('button');launcher.id='dwCmdLauncher';launcher.type='button';launcher.className='dwCmdLauncher';launcher.title='Linha de comando (Ctrl+Espaço)';launcher.innerHTML='<span>&gt;_</span><span class="dwCmdLaunchText">Comando</span>';
 const bb=$('bottomBar');if(bb)bb.insertBefore(launcher,bb.firstChild);else document.body.appendChild(launcher);
 const open=(focus=true)=>{drawer.hidden=false;document.body.classList.add('dwCmdOpen');DW.set('cmd',true);dwResize();if(focus)setTimeout(()=>$('cmdLine')?.focus(),40)};
 const close=()=>{drawer.hidden=true;document.body.classList.remove('dwCmdOpen');DW.set('cmd',false);try{canvas?.focus()}catch{}dwResize()};
 launcher.onclick=()=>drawer.hidden?open():close();
 drawer.onclick=e=>{const b=e.target.closest('[data-dwc]');if(!b)return;if(b.dataset.dwc==='close')close();else $('cmdHelpDlg')?.showModal?.()};
 window.dwCommandOpen=open;window.dwCommandClose=close;
 // Sempre recolhida ao iniciar: não rouba altura do projeto.
 close();
}

function dwForceDockedPanels(){
 // Painel esquerdo: nunca flutua sobre o desenho. Abrir = redimensionar viewport.
 try{pnEstado.fixado=true;PNPREF.set('fixado',true)}catch{}
 try{dockState.fixada=true;AREA.set('fixada',true)}catch{}
 const oldPnFix=window.pnFixar;window.pnFixar=function(){pnEstado.fixado=true;pnAplicar();msg('Painel encaixado: o desenho foi redimensionado.');};
 const oldDockFix=window.fixarDock;window.fixarDock=function(){dockState.fixada=true;aplicarDock();msg('Painel lateral encaixado: o desenho foi redimensionado.');};
 // Nenhum painel ocupa espaço ao abrir o programa.
 try{pnEstado.aberto=null;PNPREF.set('aberto',null);pnAplicar(false)}catch{}
 try{dockState.recolhida=true;AREA.set('recolhida',true);aplicarDock(false)}catch{}
 // Botões de pin deixam de sugerir modo sobreposto.
 $('pnFixar')?.setAttribute('title','Painéis da 1.40 sempre ficam encaixados e redimensionam o desenho');
 document.querySelector('[data-dk="pin"]')?.setAttribute('title','Painéis da 1.40 sempre ficam encaixados e redimensionam o desenho');
 // 1.40.7: em telas estreitas, nunca esmaga o viewport com os dois painéis abertos ao mesmo tempo.
 const basePnAbrir=window.pnAbrir,baseRecolher=window.recolherDock;
 if(typeof basePnAbrir==='function')window.pnAbrir=function(id,...args){if(id&&innerWidth<=1400&&typeof baseRecolher==='function')try{baseRecolher(true)}catch{};const r=basePnAbrir(id,...args);dwResize();return r};
 if(typeof baseRecolher==='function')window.recolherDock=function(v,...args){if(v===false&&innerWidth<=1400&&typeof basePnAbrir==='function')try{basePnAbrir(null)}catch{};const r=baseRecolher(v,...args);dwResize();return r};
}

function dwProjectFocus(v){
 const on=v??!document.body.classList.contains('dwProjectFocus');document.body.classList.toggle('dwProjectFocus',on);DW.set('focus',on);
 if(on){try{pnAbrir(null)}catch{};try{recolherDock(true)}catch{};try{dwCommandClose()}catch{};dwSetRibbonMini(true)}
 dwResize();msg(on?'Modo Projeto: área gráfica maximizada. F11 retorna aos controles.':'Controles restaurados.');
}

function dwChrome(){
 document.body.classList.add('desktop140');
 // Cabeçalho passa a ser uma barra de título compacta. Controles raros ficam nos menus.
 const h=document.querySelector('header');if(h){h.classList.add('dwTitleBar');const brand=h.querySelector('.brand');if(brand){brand.querySelector('.muted')?.classList.add('dwHide');brand.querySelector('.dev')?.classList.add('dwBrandLogo')}}
 // A área gráfica é a tela principal; mantém somente ações essenciais fora dos menus.
 document.querySelector('.sessRow')?.classList.add('dwSecondary');
 document.querySelector('.cursorRow')?.classList.add('dwCursor');
 // Ribbon recolhida por padrão, mas a aba clicada continua abrindo normalmente pelo código existente.
 try{if(localStorage.getItem('rodovia_dw_initialized')!=='1'){localStorage.setItem('rodovia_ribbon_min','1');localStorage.setItem('rodovia_paineis','1');localStorage.setItem('rodovia_dw_initialized','1')}}catch{}
}

function dwShortcuts(e){
 if(e.ctrlKey&&!e.altKey&&e.code==='Space'){e.preventDefault();const d=$('dwCommandDrawer');d?.hidden?dwCommandOpen():dwCommandClose();return}
 if(e.ctrlKey&&!e.altKey&&(e.key==='b'||e.key==='B')){e.preventDefault();try{pnAbrir(pnEstado.aberto?null:(pnItens[0]?.id||null))}catch{};return}
 if(e.ctrlKey&&e.altKey&&(e.key==='b'||e.key==='B')){e.preventDefault();try{recolherDock(!dockState.recolhida)}catch{};return}
 if(e.key==='F11'&&!e.ctrlKey&&!e.altKey){e.preventDefault();dwProjectFocus();return}
}

function dwDeduplicateChrome(){
 // Ações já presentes no menu Arquivo não precisam disputar espaço no cabeçalho.
 const ids=['twoWindows','oneWindow','layoutWide','layoutCompact','helpToggle'];
 ids.forEach(id=>{const el=$(id);const host=el?.closest('label')||el;if(host)host.classList.add('dwRare')});
 // Help permanece acessível pelo menu/atalho; cabeçalho fica limpo.
 $('helpBtn')?.classList.add('dwRare');
}

function dwInit(){
 dwChrome();dwCommandDrawer();dwForceDockedPanels();dwDeduplicateChrome();
 document.addEventListener('keydown',dwShortcuts,true);
 // Em resoluções pequenas, reduz automaticamente o painel lateral para no máximo 32%.
 const fit=()=>{const max=Math.max(280,Math.min(430,Math.round(innerWidth*.32)));document.documentElement.style.setProperty('--dwPanel',max+'px');dwResize()};
 window.addEventListener('resize',fit);fit();
 if(DW.get('focus',false))dwProjectFocus(true);
}

// Este arquivo roda depois dos módulos que criam painéis/ribbon e antes dos registros finais.
queueMicrotask(dwInit);
comando(['COMANDO','CMD'],()=>{const d=$('dwCommandDrawer');d?.hidden?dwCommandOpen():dwCommandClose()},'Abre/fecha a linha de comando (Ctrl+Espaço)');
comando(['FOCO','PROJETO'],()=>dwProjectFocus(),'Maximiza a área do projeto (F11)');
