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
 close();
}

function dwForceDockedPanels(){
 try{pnEstado.fixado=true;PNPREF.set('fixado',true)}catch{}
 try{dockState.fixada=true;AREA.set('fixada',true)}catch{}
 window.pnFixar=function(){pnEstado.fixado=true;pnAplicar();msg('Painel encaixado: o desenho foi redimensionado.');};
 window.fixarDock=function(){dockState.fixada=true;aplicarDock();msg('Painel lateral encaixado: o desenho foi redimensionado.');};
 try{pnEstado.aberto=null;PNPREF.set('aberto',null);pnAplicar(false)}catch{}
 try{dockState.recolhida=true;AREA.set('recolhida',true);aplicarDock(false)}catch{}
 $('pnFixar')?.setAttribute('title','Painéis da 1.40 sempre ficam encaixados e redimensionam o desenho');
 document.querySelector('[data-dk="pin"]')?.setAttribute('title','Painéis da 1.40 sempre ficam encaixados e redimensionam o desenho');
}

function dwProjectFocus(v){
 const on=v??!document.body.classList.contains('dwProjectFocus');document.body.classList.toggle('dwProjectFocus',on);DW.set('focus',on);
 if(on){try{pnAbrir(null)}catch{};try{recolherDock(true)}catch{};try{dwCommandClose()}catch{};dwSetRibbonMini(true)}
 dwResize();msg(on?'Modo Projeto: área gráfica maximizada. F11 retorna aos controles.':'Controles restaurados.');
}

function dwChrome(){
 document.body.classList.add('desktop140');
 const h=document.querySelector('header');if(h){h.classList.add('dwTitleBar');const brand=h.querySelector('.brand');if(brand){brand.querySelector('.muted')?.classList.add('dwHide');brand.querySelector('.dev')?.classList.add('dwHide')}}
 document.querySelector('.sessRow')?.classList.add('dwSecondary');
 document.querySelector('.cursorRow')?.classList.add('dwCursor');
 try{if(localStorage.getItem('rodovia_dw_initialized')!=='1'){localStorage.setItem('rodovia_ribbon_min','1');localStorage.setItem('rodovia_paineis','1');localStorage.setItem('rodovia_dw_initialized','1')}}catch{}
}

function dwShortcuts(e){
 if(e.ctrlKey&&!e.altKey&&e.code==='Space'){e.preventDefault();const d=$('dwCommandDrawer');d?.hidden?dwCommandOpen():dwCommandClose();return}
 if(e.ctrlKey&&!e.altKey&&(e.key==='b'||e.key==='B')){e.preventDefault();try{pnAbrir(pnEstado.aberto?null:(pnItens[0]?.id||null))}catch{};return}
 if(e.ctrlKey&&e.altKey&&(e.key==='b'||e.key==='B')){e.preventDefault();try{recolherDock(!dockState.recolhida)}catch{};return}
 if(e.key==='F11'&&!e.ctrlKey&&!e.altKey){e.preventDefault();dwProjectFocus();return}
}

function dwDeduplicateChrome(){
 const ids=['twoWindows','oneWindow','layoutWide','layoutCompact','helpToggle'];
 ids.forEach(id=>{const el=$(id);const host=el?.closest('label')||el;if(host)host.classList.add('dwRare')});
 $('helpBtn')?.classList.add('dwRare');
}

function dwInit(){
 dwChrome();dwCommandDrawer();dwForceDockedPanels();dwDeduplicateChrome();
 document.addEventListener('keydown',dwShortcuts,true);
 const fit=()=>{const max=Math.max(280,Math.min(430,Math.round(innerWidth*.32)));document.documentElement.style.setProperty('--dwPanel',max+'px');dwResize()};
 window.addEventListener('resize',fit);fit();
 if(DW.get('focus',false))dwProjectFocus(true);
}

queueMicrotask(dwInit);
comando(['COMANDO','CMD'],()=>{const d=$('dwCommandDrawer');d?.hidden?dwCommandOpen():dwCommandClose()},'Abre/fecha a linha de comando (Ctrl+Espaço)');
comando(['FOCO','PROJETO'],()=>dwProjectFocus(),'Maximiza a área do projeto (F11)');
