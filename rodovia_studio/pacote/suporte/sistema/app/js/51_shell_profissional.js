// =====================================================================================================
// 1.40.1 — Professional Shell
//  • quatro hubs principais: Projeto, Layers, Propriedades e Vídeo;
//  • faixa de opções reduzida a tarefas de alto nível, sem repetir o mesmo comando em várias abas;
//  • os painéis existentes continuam sendo a fonte dos dados: este módulo apenas organiza navegação e cromo.
// =====================================================================================================
const PS={
  hubs:[
    {id:'project',rotulo:'Projeto',ico:'▣',hint:'Arquivos, configuração e dados do projeto'},
    {id:'layers',rotulo:'Camadas',ico:'☷',hint:'Camadas, imagem local e intercâmbio'},
    {id:'props',rotulo:'Propriedades',ico:'☰',hint:'Propriedades do objeto selecionado'},
    {id:'video',rotulo:'Vídeo',ico:'🎬',hint:'Configuração, prévia e renderização'}
  ],
  extraOpen:false
};
function psFindSection(test){return pnItens.find(i=>test(i.t||'',i.el))||null}
function psOpenHub(id){
  const more=$('psMore');if(more)more.hidden=true;PS.extraOpen=false;
  if(id==='props'){
    pnAbrir(null);
    try{abrirAba('prop',true)}catch{}
    const p=$('propPanel');if(p?.hidden)msg('Propriedades: selecione um objeto no desenho para editar.');
    return;
  }
  const item=id==='project'?psFindSection(t=>/Projeto e arquivos/i.test(t)):
             id==='layers'?psFindSection(t=>/Camadas, imagem local/i.test(t)):
             id==='video'?psFindSection(t=>/Exportar vídeo/i.test(t)):null;
  if(item){recolherDock(true);pnAbrir(pnEstado.aberto===item.id?null:item.id);return}
  if(id==='layers'&&typeof openLayerManager==='function'){openLayerManager();return}
  if(id==='video')openSection('5. Exportar vídeo');
}
function psMoreMenu(anchor){
 if(!window.RodoviaMenus){msg('Os menus ainda estão sendo carregados. Aguarde a inicialização.');return}
 if(PS.moreWasOpen||document.querySelector('.rsMoreCascade')){PS.moreWasOpen=false;RodoviaMenus.close();return}
 const groups=[{t:'Projeto e configuração',sub:[]},{t:'Cena e apresentação',sub:[]},{t:'Manutenção e assistência',sub:[]}];
 for(const item of pnItens){
  if(/Projeto e arquivos|Camadas, imagem local|Exportar vídeo/i.test(item.t))continue;
  const group=/Manutenção/i.test(item.t)?2:/Materiais|Vista|Câmera|clima|apresentação/i.test(item.t)?1:0;
  groups[group].sub.push({t:item.t.replace(/^\d+\.\s*/,''),f:()=>openSection(item.t)});
 }
 groups[2].sub.push({t:'Diagnóstico do aplicativo / IA',f:()=>window.RodoviaIA.open('logs')},{t:'Resolver problemas dos fluxos',f:()=>window.RodoviaExecution.open(),dis:!pid},{t:'Proteção e recuperação de dados',f:()=>window.RodoviaProtection.open(),dis:!pid});
 const r=anchor.getBoundingClientRect();RodoviaMenus.open(groups.filter(g=>g.sub.length),{x:r.right+4,y:r.top},anchor);
 const menu=document.querySelector('.rsCascade');if(menu){menu.classList.add('rsMoreCascade');menu.setAttribute('aria-label','Outros painéis por função');menu.querySelector('button')?.focus()}psUpdateHubState();
}
function psUpdateHubState(){
 const item=pnItens.find(i=>i.id===pnEstado.aberto);let active=null;
 if(PS.extraOpen||document.querySelector('.rsMoreCascade'))active='more';
 else if(item)active=/Projeto e arquivos/i.test(item.t)?'project':/Camadas, imagem local/i.test(item.t)?'layers':/Exportar vídeo/i.test(item.t)?'video':'more';
 else if(!dockState.recolhida&&dockState.aba==='prop')active='props';
 document.querySelectorAll('#atividades .psHub').forEach(b=>{const on=(b.dataset.pshub||'more')===active;b.classList.toggle('on',on);b.setAttribute('aria-expanded',String(b.matches('[data-psmore]')?!!document.querySelector('.rsMoreCascade'):on));b.setAttribute('aria-pressed',String(on))});
}
function psSyncActivities(){
  const bar=$('atividades');if(!bar||bar.dataset.ps==='1')return;bar.dataset.ps='1';bar.classList.add('psActivityBar');
  bar.innerHTML=PS.hubs.map(h=>`<button type="button" class="psHub" data-pshub="${h.id}" title="${esc(h.hint)}"><span class="pnIco">${h.ico}</span><span class="pnRot">${esc(h.rotulo)}</span></button>`).join('')+
    '<button type="button" class="psHub psMoreBtn" data-psmore aria-haspopup="menu" title="Outros painéis"><span class="pnIco">⋯</span><span class="pnRot">Mais</span></button>';
  bar.onclick=e=>{const h=e.target.closest('[data-pshub]');if(h){psOpenHub(h.dataset.pshub);return}const m=e.target.closest('[data-psmore]');if(m)psMoreMenu(m)};
}
function psRibbon(){
  RIBBON.splice(0,RIBBON.length,
    ['Projeto',[
      ['Projeto',[
        ['Novo','➕',()=>$('new')?.click(),1],
        ['Abrir…','📂',()=>typeof openProjectDialog==='function'?openProjectDialog():$('projects')?.focus(),1],
        ['Salvar','💾',()=>$('saveProject')?.click(),1],
        ['Salvar como…','🗐',()=>$('saveAsProject')?.click()]
      ]],
      ['Arquivos',[
        ['DXF/DWG…','📐',()=>$('fileDxf')?.click(),1],
        ['KMZ/KML…','🌐',()=>$('fileKmz')?.click(),1],
        ['Analisar','🔎',()=>$('analyze')?.click(),1]
      ]],
      ['Dados',[
        ['Configuração','⚙',()=>openSection('2. Configuração')],
        ['Camadas','☷',()=>psOpenHub('layers')],
        ['Obras do PER','🏗',()=>openSection('Obras do PER')]
      ]]
    ]],
    ['Modelar',null],
    ['Propriedades',[
      ['Seleção',[
        ['Selecionar tudo','▦',()=>runCommand('SELTUDO')],
        ['Desmarcar','◌',()=>clearSelection()],
        ['Propriedades','☰',()=>psOpenHub('props'),1]
      ]],
      ['Modificar',[
        ['Mover','✥',()=>runCommand('MOVER'),1],
        ['Girar','⟳',()=>runCommand('GIRAR'),1],
        ['Copiar','⧉',()=>runCommand('COPIAR'),1],
        ['Escala','⤢',()=>runCommand('ESCALA')],
        ['Espelhar','⇋',()=>runCommand('ESPELHAR')],
        ['Paralela','∥',()=>runCommand('OFFSET')]
      ]],
      ['Aparência',[
        ['Textura','▦',()=>openTexDialog(),1],
        ['Pincel','🖌',()=>typeof startBrush==='function'?startBrush():runCommand('PINCEL')],
        ['Gerenciador de camadas','☷',()=>typeof openLayerManager==='function'?openLayerManager():psOpenHub('layers')]
      ]],
      ['Histórico',[
        ['Desfazer','↶',()=>undo(),1],['Refazer','↷',()=>redo(),1],['Apagar','🗑',()=>deleteSel()]
      ]]
    ]],
    ['Vídeo',[
      ['Produção',[
        ['Configurar','⚙',()=>psOpenHub('video')],
        ['Prévia no instante','▶',()=>$('openAtTime')?.click(),1],
        ['Gerar vídeo','🎬',()=>typeof gerarVideo==='function'?gerarVideo():$('render')?.click(),1]
      ]],
      ['Câmera e ambiente',[
        ['Ponto-chave','📍',()=>typeof adicionarVista==='function'?guard(adicionarVista)():openSection('Câmera, clima')],
        ['Clima e sol','⛅',()=>openSection('Câmera, clima')]
      ]],
      ['Resultados',[
        ['Vídeos gerados','🎞',()=>typeof openVideos==='function'?guard(openVideos)():null],
        ['Registros','📋',()=>openLogs('execucao')]
      ]]
    ]],
    ['Exibir',[
      ['Área de trabalho',[
        ['Modo Projeto','⛶',()=>window.RodoviaDesktopWorkspace.toggleProjectFocus(),1],
        ['Projeto','▣',()=>psOpenHub('project')],
        ['Propriedades','☰',()=>psOpenHub('props')],
        ['Linha de comando','>_',()=>window.RodoviaDesktopWorkspace.toggleCommand()]
      ]],
      ['Vista',[
        ['Enquadrar','⤧',()=>fitView(),1],['Regenerar','⟲',()=>regenScreen()],['Tela cheia','⛶',()=>toggleFullscreen()],
        ['Snap','⌖',()=>{$('snapOn')?.click();statusBar()}],['Orto','⊥',()=>{$('orthoOn')?.click();statusBar()}]
      ]]
    ]],
    ['Ajuda',[
      ['Ajuda',[
        ['Como usar','❔',()=>$('helpBtn')?.click(),1],['Comandos','⌨',()=>runCommand('?'),1],['Sobre','ⓘ',()=>openAbout(),1]
      ]]
    ]]
  );
  try{buildRibbon()}catch(e){msg('Não foi possível atualizar a faixa de opções: '+e.message,true)}
}
function psInit(){
  psRibbon();
  for(const name of ['pnAplicar','aplicarDock'])estender(name,previous=>function(...args){const r=previous(...args);psUpdateHubState();return r},'Sincroniza o botão lateral com o painel aberto');
  try{estender('pnEntrar',anterior=>function(){const r=anterior();queueMicrotask(()=>{psSyncActivities();psUpdateHubState()});return r},'1.40.1: quatro hubs principais no workspace')}catch{}
  queueMicrotask(()=>{psSyncActivities();psUpdateHubState()});
  document.addEventListener('pointerdown',e=>{PS.moreWasOpen=!!e.target.closest('[data-psmore]')&&!!document.querySelector('.rsMoreCascade');const p=$('psMore');if(p&&!p.hidden&&!e.target.closest('#psMore,[data-psmore]')){p.hidden=true;PS.extraOpen=false;psUpdateHubState()}},true);
}
queueMicrotask(psInit);
