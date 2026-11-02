// ---------- Ícones em menus e botões ----------
// Acrescenta um ícone decorativo (aria-hidden) a cada menu, item de menu e botão que ainda não tenha um. O nome acessível não muda.
(function(root){
 const RULES=[ // [expressão sobre o texto normalizado, ícone]
  [/^(novo|criar|adicionar|inserir|nova)/,'➕'],[/^(salvar como modelo|salvar modelo|salvar perfil)/,'📋'],[/^salvar e fechar/,'💾'],[/^(salvar|gravar)/,'💾'],
  [/^(abrir pasta|abrir pacote|abrir neste|abrir)/,'📂'],[/^(aplicar)/,'✅'],[/^(ok$|confirmar|sim$)/,'✔'],[/^(cancelar tarefa|parar|interromper)/,'⛔'],[/^(cancelar|nao$)/,'✖'],[/^fechar/,'✖'],
  [/^(desfazer limpeza|desfazer|reverter|restabelecer|restaurar)/,'↩'],[/^refazer/,'↪'],[/^(apagar|excluir|remover|retirar|limpar)/,'🗑'],
  [/^(gerar novo video|gerar video|renderizar)/,'🎬'],[/^(gerar|atualizar previa|regenerar|previa)/,'🖼'],[/^(atualizar|recarregar)/,'🔄'],
  [/^(analisar|diagnostic|auditar|verificar|validar)/,'🔍'],[/^(buscar|procurar|localizar)/,'🔎'],
  [/^(exportar|gerar exportacao|baixar)/,'📤'],[/^(importar|carregar|enviar|escolher)/,'📥'],[/^(copiar|duplicar)/,'⧉'],[/^(renomear|trocar nome)/,'✏'],
  [/^(editar|propriedades|atributos)/,'✏'],[/^(selecionar|isolar)/,'🔲'],[/^(mostrar|exibir|enquadrar|ver )/,'👁'],[/^ocultar/,'🙈'],[/^(congelar)/,'❄'],[/^descongelar/,'🔥'],
  [/^(arquivo)/,'📁'],[/^(projeto)/,'🗂'],[/^(trafego|fluxo|fluxos)/,'🚗'],[/^(cena)/,'🎞'],[/^(video)/,'🎥'],[/^(ferramentas)/,'🛠'],[/^(ajuda|como usar|comandos|sobre)/,'❓'],
  [/^(tela cheia|painel lateral|tela ampla|compacto)/,'🖥'],[/^(mover)/,'✥'],[/^(girar)/,'⟳'],[/^(escala)/,'⤢'],[/^(espelhar)/,'⇋'],[/^(paralela)/,'∥'],[/^(aparar)/,'✂'],[/^(pincel)/,'🖌'],
  [/^(placa|sinaliza)/,'🪧'],[/^(area|zebrado|hachura)/,'▨'],[/^(alinhamento|eixo)/,'📐'],[/^(portico)/,'🏗'],[/^(destaque)/,'🔆'],[/^(execucao|registros|erros|log)/,'📜'],
  [/^(medir|calcular|medicao)/,'📏'],[/^(erro|aviso)/,'⚠'],[/^(mais resultados)/,'⋯'],[/^(registros e suporte)/,'📜'],[/^(prompt)/,'🤖'],[/^(comparar)/,'⚖'],[/^(instalar|converter)/,'⚙'],[/^(ajustar|detalhar)/,'🎯']];
 function norm(t){return String(t||'').normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/[…\.]/g,'').trim().toLowerCase()}
 function iconFor(label){const n=norm(label);if(!n)return '';for(const [re,ic] of RULES)if(re.test(n))return ic;return ''}
 // Ícones de linha estilo Windows/CAD (mesmo conjunto dos menus em 45_menus_windows.js); emoji só quando não houver equivalente.
 const NOME={'💾':'salvar','📂':'abrir','➕':'inserir','✅':'concluir','✔':'concluir','✖':'cancelar','↩':'desfazer','↪':'refazer','🗑':'apagar','🎬':'video','🖼':'previa','🔄':'regenerar','🔍':'analisar','🔎':'zoom','📤':'exportar','📥':'importar','⧉':'copiar','✏':'nome','🔲':'grips','👁':'olho','🙈':'olho','📐':'alinhamento','📏':'medir','✂':'aparar','✥':'mover','⟳':'girar','⤢':'escala','⇋':'espelhar','∥':'paralela','🚗':'ligacao','🎥':'video','❓':'ajuda','🖥':'tela','🪧':'placa','▨':'hachura','🏗':'portico','🔆':'estrela','📜':'registros','📁':'pasta','🗂':'pasta','⚠':'aviso','❄':'congelar','🔥':'descongelar','⋯':'mais','🤖':'robo','⚖':'comparar','🎯':'alvo','🖌':'pincel','🛠':'propriedades','⚙':'propriedades','⛔':'proibir','📋':'copiar','🎞':'previa'};
 // 2.18: glifos de traço que faltavam, para nenhum comando depender de emoji.
 if(typeof ICO!=='undefined')Object.assign(ICO,{congelar:'M6 11h12v10H6zM8 11V7a4 4 0 0 1 8 0v4M12 15v2',descongelar:'M6 11h12v10H6zM8 11V7a4 4 0 0 1 7.5-2M12 15v2',mais:'M5 12h.01M12 12h.01M19 12h.01',robo:'M5 8h14v10H5zM12 4v4M9 13h.01M15 13h.01M9 21h6',comparar:'M12 3v18M5 7h14M7 7l-3 6h6zM17 7l-3 6h6z',alvo:'M12 4a8 8 0 1 0 0 16 8 8 0 0 0 0-16zM12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z',aviso:'M12 3l10 18H2zM12 10v5M12 18h.01'});
 function svgFor(label){const ic=iconFor(label);const n=NOME[ic];return n&&typeof icoSvg==='function'?icoSvg(n):''}
 const T={iconFor,norm,svgFor,NOME};
 if(typeof module!=='undefined'&&module.exports)module.exports=T;else root.RodoviaIcones=T;
})(typeof window!=='undefined'?window:globalThis);

if(typeof document!=='undefined'){
 (function(){
  const hasIcon=t=>/^[←-⯿\u{1F000}-\u{1FAFF}☀-➿]/u.test(t.trim());
  // Menus (barra, cascatas, contexto) já têm coluna própria de ícones: nunca são decorados aqui (evita ícone duplicado e colunas deslocadas).
  const MENU_AREA='#menuBar,#menuDrop,.rsCascade,.rsMenuBar,.ctxMenu,.ctxSub,[role=menu],[role=menubar],[role=menuitem]';
  const hasOwnIcon=el=>!!el.querySelector('svg,img,.ic,.rsMenuIcon,[class*=Icon],[class*=icon]');
  function put(el){if(!el||el.dataset.ic)return;el.dataset.ic='1';if(el.closest(MENU_AREA)||hasOwnIcon(el))return;
   const label=el.textContent||'';if(!label.trim()||hasIcon(label))return;
   const ic=RodoviaIcones.iconFor(label);if(!ic)return;const s=document.createElement('span');s.className='ic';s.setAttribute('aria-hidden','true');const sv=RodoviaIcones.svgFor(label);if(!sv)return;s.innerHTML=sv;s.dataset.auto='1';el.insertBefore(s,el.firstChild)}
  // 2.18: nunca dois ícones no mesmo comando (ícone próprio vence o automático) e botão só de ícone sempre tem nome/dica.
  function dedupe(el){const icons=[...el.querySelectorAll(':scope>.ic,:scope>svg,:scope>.rsMenuIcon,:scope>.ri')];
   if(icons.length>1){const own=icons.find(x=>!x.dataset.auto)||icons[0];icons.forEach(x=>{if(x!==own&&x.dataset.auto)x.remove()})}
   const first=el.firstChild;if(first&&first.nodeType===3&&hasIcon(first.textContent)&&el.querySelector(':scope>.ic[data-auto]'))el.querySelector(':scope>.ic[data-auto]').remove()}
  function nameIconOnly(el){if(el.textContent.trim())return;const n=el.getAttribute('aria-label')||el.title||el.dataset.tip;if(n){if(!el.title)el.title=n;if(!el.getAttribute('aria-label'))el.setAttribute('aria-label',n)}}
  function decorate(){
   document.querySelectorAll('button[data-ic],.rb,.it,[role=tab],[role=menuitem]').forEach(el=>{try{dedupe(el);nameIconOnly(el)}catch(_e){window.RodoviaErros&&RodoviaErros.avisar('icones_menus',_e)}});
   document.querySelectorAll('button:not(.mb):not([data-noicon]):not([role=tab])').forEach(b=>{if(b.getAttribute('aria-label')&&!b.textContent.trim())return;put(b)});
  }
  let pending=false;const schedule=()=>{if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;try{decorate()}catch(_e){window.RodoviaErros&&RodoviaErros.avisar('icones_menus',_e)}})};
  new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true});
  document.addEventListener('DOMContentLoaded',schedule);schedule();
 })();
}
