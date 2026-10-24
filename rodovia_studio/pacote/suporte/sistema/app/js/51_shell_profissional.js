// =====================================================================================================
// 1.40.1 — Professional Shell
//  • quatro hubs principais: Projeto, Layers, Propriedades e Vídeo;
//  • faixa de opções reduzida a tarefas de alto nível, sem repetir o mesmo comando em várias abas;
//  • os painéis existentes continuam sendo a fonte dos dados: este módulo apenas organiza navegação e cromo.
// =====================================================================================================
const PS={
  hubs:[
    {id:'project',rotulo:'Projeto',ico:'▣',hint:'Arquivos, configuração e dados do projeto'},
    {id:'layers',rotulo:'Layers',ico:'☷',hint:'Camadas, imagem local e intercâmbio'},
    {id:'props',rotulo:'Propriedades',ico:'☰',hint:'Propriedades do objeto selecionado'},
    {id:'video',rotulo:'Vídeo',ico:'🎬',hint:'Configuração, prévia e renderização'}
  ],
  extraOpen:false
};
function psFindSection(test){return pnItens.find(i=>test(i.t||'',i.el))||null}
function psOpenHub(id){
  if(id==='props'){
    try{abrirAba('prop',false)}catch{}
    const p=$('propPanel');if(p?.hidden)msg('Propriedades: selecione um objeto no desenho para editar.');
    return;
  }
  const item=id==='project'?psFindSection(t=>/Projeto e arquivos/i.test(t)):
             id==='layers'?psFindSection(t=>/Camadas, imagem local/i.test(t)):
             id==='video'?psFindSection(t=>/Exportar vídeo/i.test(t)):null;
  if(item){pnAbrir(pnEstado.aberto===item.id?null:item.id);return}
  if(id==='layers'&&typeof openLayerManager==='function'){openLayerManager();return}
  if(id==='video')openSection('5. Exportar vídeo');
}
function psMoreMenu(anchor){
  let pop=$('psMore');if(!pop){pop=document.createElement('div');pop.id='psMore';pop.className='psMore';pop.hidden=true;document.body.appendChild(pop)}
  const primary=new Set(['project','layers','video']);
  const rows=pnItens.filter(i=>{
    if(/Projeto e arquivos/i.test(i.t))return false;
    if(/Camadas, imagem local/i.test(i.t))return false;
    if(/Exportar vídeo/i.test(i.t))return false;
    return true;
  });
  pop.innerHTML=rows.map(i=>`<button type="button" data-pspn="${esc(i.id)}"><span>${i.ico||'▣'}</span><span>${esc(i.t)}</span></button>`).join('');
  const r=anchor.getBoundingClientRect();pop.style.left=Math.round(r.right+6)+'px';pop.style.top=Math.round(r.top)+'px';pop.hidden=false;PS.extraOpen=true;
  pop.onclick=e=>{const b=e.target.closest('[data-pspn]');if(!b)return;pnAbrir(b.dataset.pspn);pop.hidden=true;PS.extraOpen=false};
}
function psSyncActivities(){
  const bar=$('atividades');if(!bar||bar.dataset.ps==='1')return;bar.dataset.ps='1';bar.classList.add('psActivityBar');
  bar.innerHTML=PS.hubs.map(h=>`<button type="button" class="psHub" data-pshub="${h.id}" title="${esc(h.hint)}"><span class="pnIco">${h.ico}</span><span class="pnRot">${esc(h.rotulo)}</span></button>`).join('')+
    '<button type="button" class="psHub psMoreBtn" data-psmore title="Outros painéis"><span class="pnIco">⋯</span><span class="pnRot">Mais</span></button>';
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
        ['Layers','☷',()=>psOpenHub('layers')],
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
        ['Gerenciador de layers','☷',()=>typeof openLayerManager==='function'?openLayerManager():psOpenHub('layers')]
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
        ['Modo Projeto','⛶',()=>RodoviaDesktopWorkspace?.toggleProjectFocus?.(),1],
        ['Projeto','▣',()=>psOpenHub('project')],
        ['Propriedades','☰',()=>psOpenHub('props')],
        ['Linha de comando','>_',()=>RodoviaDesktopWorkspace?.toggleCommand?.()]
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
  try{estender('pnEntrar',anterior=>function(){const r=anterior();queueMicrotask(psSyncActivities);return r},'1.40.1: quatro hubs principais no workspace')}catch{}
  queueMicrotask(psSyncActivities);
  document.addEventListener('pointerdown',e=>{const p=$('psMore');if(p&&!p.hidden&&!e.target.closest('#psMore,[data-psmore]')){p.hidden=true;PS.extraOpen=false}},true);
}
queueMicrotask(psInit);
