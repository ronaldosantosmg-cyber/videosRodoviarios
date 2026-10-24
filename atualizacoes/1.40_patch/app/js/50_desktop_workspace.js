// =====================================================================================================
// Rodovia Studio 1.40 — Desktop Workspace Controller
// Arquitetura de UI: viewport-first, painéis encaixados, linha de comando retrátil e estado persistente.
// O módulo é deliberadamente isolado do motor de geometria/renderização.
// =====================================================================================================

(()=>{
  'use strict';

  const STORAGE_PREFIX='rodovia_dw_';
  const PANEL_MIN=300;
  const PANEL_MAX=460;
  const PANEL_RATIO=.30;

  const $id=(id)=>document.getElementById(id);
  const q=(sel,root=document)=>root.querySelector(sel);
  const qa=(sel,root=document)=>[...root.querySelectorAll(sel)];

  const Store={
    get(key,fallback){
      try{
        const raw=localStorage.getItem(STORAGE_PREFIX+key);
        return raw==null?fallback:JSON.parse(raw);
      }catch{return fallback}
    },
    set(key,value){
      try{localStorage.setItem(STORAGE_PREFIX+key,JSON.stringify(value))}catch{}
    }
  };

  const State={
    commandOpen:false,
    projectFocus:false,
    initialized:false,
    resizeFrame:0
  };

  function notify(text){
    try{if(typeof msg==='function')msg(text)}catch{}
  }

  function scheduleViewportResize(){
    cancelAnimationFrame(State.resizeFrame);
    State.resizeFrame=requestAnimationFrame(()=>{
      try{if(typeof resizeCanvas==='function')resizeCanvas()}catch{}
      window.dispatchEvent(new CustomEvent('rodovia:workspace-resize'));
    });
  }

  function setExpanded(el,expanded){
    if(!el)return;
    el.setAttribute('aria-expanded',expanded?'true':'false');
  }

  function setRibbonCollapsed(collapsed=true){
    try{localStorage.setItem('rodovia_ribbon_min',collapsed?'1':'0')}catch{}
    const button=q('.rbMin');
    const body=q('.rbBody');
    if(body)body.hidden=!!collapsed;
    if(button){
      button.textContent=collapsed?'▾':'▴';
      button.title=collapsed?'Expandir a faixa (Ctrl+F1)':'Recolher a faixa (Ctrl+F1)';
      button.setAttribute('aria-label',button.title);
      setExpanded(button,!collapsed);
    }
    document.body.classList.toggle('dwRibbonCollapsed',!!collapsed);
    scheduleViewportResize();
  }

  function buildCommandDrawer(){
    const row=q('.cmdRow');
    if(!row||$id('dwCommandDrawer'))return;

    const drawer=document.createElement('section');
    drawer.id='dwCommandDrawer';
    drawer.className='dwCommandDrawer';
    drawer.hidden=true;
    drawer.setAttribute('aria-label','Linha de comando');
    drawer.innerHTML=`
      <div class="dwCmdHead">
        <span class="dwCmdTitle">Linha de comando</span>
        <span class="grow"></span>
        <button type="button" class="dwIconButton" data-dwc="help" aria-label="Ajuda dos comandos" title="Ajuda dos comandos">?</button>
        <button type="button" class="dwIconButton" data-dwc="close" aria-label="Fechar linha de comando" title="Fechar">×</button>
      </div>
      <div class="dwCmdBody"></div>`;

    drawer.querySelector('.dwCmdBody').appendChild(row);
    const bottom=$id('bottomBar');
    if(bottom?.parentNode)bottom.parentNode.insertBefore(drawer,bottom);
    else document.body.appendChild(drawer);

    const launcher=document.createElement('button');
    launcher.id='dwCmdLauncher';
    launcher.type='button';
    launcher.className='dwCmdLauncher';
    launcher.title='Linha de comando (Ctrl+Espaço)';
    launcher.setAttribute('aria-controls','dwCommandDrawer');
    launcher.setAttribute('aria-expanded','false');
    launcher.innerHTML='<span aria-hidden="true">&gt;_</span><span class="dwCmdLaunchText">Comando</span>';
    if(bottom)bottom.insertBefore(launcher,bottom.firstChild);
    else document.body.appendChild(launcher);

    launcher.addEventListener('click',()=>toggleCommandDrawer());
    drawer.addEventListener('click',(event)=>{
      const button=event.target.closest('[data-dwc]');
      if(!button)return;
      if(button.dataset.dwc==='close')closeCommandDrawer();
      if(button.dataset.dwc==='help')$id('cmdHelpDlg')?.showModal?.();
    });
  }

  function openCommandDrawer({focus=true}={}){
    const drawer=$id('dwCommandDrawer');
    if(!drawer)return;
    drawer.hidden=false;
    State.commandOpen=true;
    document.body.classList.add('dwCmdOpen');
    Store.set('cmd',true);
    setExpanded($id('dwCmdLauncher'),true);
    scheduleViewportResize();
    if(focus)setTimeout(()=>$id('cmdLine')?.focus(),20);
  }

  function closeCommandDrawer({restoreFocus=true}={}){
    const drawer=$id('dwCommandDrawer');
    if(!drawer)return;
    drawer.hidden=true;
    State.commandOpen=false;
    document.body.classList.remove('dwCmdOpen');
    Store.set('cmd',false);
    setExpanded($id('dwCmdLauncher'),false);
    scheduleViewportResize();
    if(restoreFocus){try{canvas?.focus?.()}catch{}}
  }

  function toggleCommandDrawer(){
    State.commandOpen?closeCommandDrawer():openCommandDrawer();
  }

  function forceDockedPanels(){
    try{
      pnEstado.fixado=true;
      PNPREF.set('fixado',true);
      window.pnFixar=()=>{
        pnEstado.fixado=true;
        pnAplicar();
        notify('Painel encaixado: a área do projeto foi redimensionada.');
      };
    }catch{}

    try{
      dockState.fixada=true;
      AREA.set('fixada',true);
      window.fixarDock=()=>{
        dockState.fixada=true;
        aplicarDock();
        notify('Painel lateral encaixado: a área do projeto foi redimensionada.');
      };
    }catch{}

    try{pnEstado.aberto=null;PNPREF.set('aberto',null);pnAplicar(false)}catch{}
    try{dockState.recolhida=true;AREA.set('recolhida',true);aplicarDock(false)}catch{}

    $id('pnFixar')?.setAttribute('aria-hidden','true');
    q('[data-dk="pin"]')?.setAttribute('aria-hidden','true');
    scheduleViewportResize();
  }

  function setProjectFocus(value){
    const enabled=value??!State.projectFocus;
    State.projectFocus=enabled;
    document.body.classList.toggle('dwProjectFocus',enabled);
    Store.set('focus',enabled);

    if(enabled){
      try{pnAbrir(null)}catch{}
      try{recolherDock(true)}catch{}
      closeCommandDrawer({restoreFocus:false});
      setRibbonCollapsed(true);
    }

    scheduleViewportResize();
    notify(enabled?'Modo Projeto: área gráfica maximizada. F11 restaura os controles.':'Controles restaurados.');
  }

  function configureChrome(){
    document.body.classList.add('desktop140');
    const header=q('header');
    if(header){
      header.classList.add('dwTitleBar');
      header.querySelector('.brand .muted')?.classList.add('dwHide');
      header.querySelector('.brand .dev')?.classList.add('dwHide');
    }
    q('.sessRow')?.classList.add('dwSecondary');
    q('.cursorRow')?.classList.add('dwCursor');

    if(!Store.get('initialized',false)){
      try{localStorage.setItem('rodovia_ribbon_min','1')}catch{}
      Store.set('initialized',true);
    }
  }

  function hideDuplicateChrome(){
    // Somente duplicidades de cromo; as ações permanecem acessíveis no menu/contexto.
    ['twoWindows','oneWindow','layoutWide','layoutCompact','helpToggle'].forEach((id)=>{
      const el=$id(id);
      const host=el?.closest('label')||el;
      host?.classList.add('dwRare');
    });
    $id('helpBtn')?.classList.add('dwRare');
  }

  function isEditableTarget(target){
    return !!target?.closest?.('input,textarea,select,[contenteditable="true"]');
  }

  function handleShortcut(event){
    if(event.ctrlKey&&!event.altKey&&event.code==='Space'){
      event.preventDefault();
      toggleCommandDrawer();
      return;
    }
    if(isEditableTarget(event.target))return;

    if(event.ctrlKey&&!event.altKey&&(event.key==='b'||event.key==='B')){
      event.preventDefault();
      try{pnAbrir(pnEstado.aberto?null:(pnItens[0]?.id||null))}catch{}
      scheduleViewportResize();
      return;
    }
    if(event.ctrlKey&&event.altKey&&(event.key==='b'||event.key==='B')){
      event.preventDefault();
      try{recolherDock(!dockState.recolhida)}catch{}
      scheduleViewportResize();
      return;
    }
    if(event.key==='F11'&&!event.ctrlKey&&!event.altKey){
      event.preventDefault();
      setProjectFocus();
    }
  }

  function updatePanelWidth(){
    const width=Math.round(Math.min(PANEL_MAX,Math.max(PANEL_MIN,innerWidth*PANEL_RATIO)));
    document.documentElement.style.setProperty('--dwPanel',width+'px');
    document.documentElement.style.setProperty('--dwViewportMin',Math.max(420,Math.round(innerWidth*.46))+'px');
    scheduleViewportResize();
  }

  function installResizeObservers(){
    window.addEventListener('resize',updatePanelWidth,{passive:true});
    if('ResizeObserver' in window){
      const viewport=q('#editorSection .canvasWrap');
      if(viewport){
        const observer=new ResizeObserver(scheduleViewportResize);
        observer.observe(viewport);
        window.__rodoviaDesktopResizeObserver=observer;
      }
    }
    updatePanelWidth();
  }

  function initialize(){
    if(State.initialized)return;
    State.initialized=true;
    configureChrome();
    buildCommandDrawer();
    forceDockedPanels();
    hideDuplicateChrome();
    installResizeObservers();
    document.addEventListener('keydown',handleShortcut,true);

    // A solicitação da 1.40 é iniciar com máximo espaço para o projeto.
    closeCommandDrawer({restoreFocus:false});
    setRibbonCollapsed(true);
    if(Store.get('focus',false))setProjectFocus(true);
  }

  window.RodoviaDesktopWorkspace=Object.freeze({
    openCommand:openCommandDrawer,
    closeCommand:closeCommandDrawer,
    toggleCommand:toggleCommandDrawer,
    setProjectFocus,
    setRibbonCollapsed,
    resize:scheduleViewportResize
  });

  window.dwCommandOpen=openCommandDrawer;
  window.dwCommandClose=closeCommandDrawer;
  window.dwProjectFocus=setProjectFocus;

  queueMicrotask(initialize);

  try{
    if(typeof comando==='function'){
      comando(['COMANDO','CMD'],toggleCommandDrawer,'Abre/fecha a linha de comando (Ctrl+Espaço)');
      comando(['FOCO','PROJETO'],()=>setProjectFocus(),'Maximiza a área do projeto (F11)');
    }
  }catch{}
})();
