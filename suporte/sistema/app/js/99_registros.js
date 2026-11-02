// =====================================================================================================
// 1.31: despachantes dos registros (ficam por último, por fora de todas as extensões).
// Ferramentas e comandos registrados com ferramenta() e comando() (00_nucleo.js) são tratados aqui; o resto segue
// para o comportamento anterior.
// =====================================================================================================
estender('click',anterior=>function(w,e){const f=FERRAMENTAS[tool];if(f&&f.clique){f.clique(w,e);return}return anterior(w,e)},'registro de ferramentas: clique');
estender('finishDraft',anterior=>async function(){const f=draft&&FERRAMENTAS[draft.type];if(f&&f.concluir)return f.concluir(draft);return anterior()},'registro de ferramentas: concluir (Enter)');
estender('toolOptions',anterior=>function(){anterior();const f=FERRAMENTAS[tool],el=$('toolOptions');if(f&&f.opcoes&&el)f.opcoes(el)},'registro de ferramentas: opções');
estender('escapeCommand',anterior=>async function(...a){const f=FERRAMENTAS[tool];if(f&&f.esc&&f.esc()!==false)return;return anterior(...a)},'registro de ferramentas: Esc');
estender('setTool',anterior=>function(t){const sai=FERRAMENTAS[tool],entra=FERRAMENTAS[t],de=tool;anterior(t);if(sai&&sai.sair&&de!==t)sai.sair(t);if(entra&&entra.entrar)entra.entrar(de)},'registro de ferramentas: entrar/sair');
estender('runCommand',anterior=>function(raw){const f=COMANDOS.get((raw||'').trim().toUpperCase());if(f){f(raw);return}return anterior(raw)},'registro de comandos');
// Ajuda › Sobre: estrutura da interface (para quem mantém o programa).
estender('openAbout',anterior=>async function(){await anterior();const ext=Object.entries(EXTENSOES).sort((a,b)=>b[1].length-a[1].length);
 $('aboutBody').insertAdjacentHTML('beforeend',`<details><summary>Estrutura da interface</summary><p class="muted">Arquivos em app/js (um por assunto). ${Object.keys(FERRAMENTAS).length} ferramentas e ${COMANDOS.size} nomes de comando registrados; extensões por função (na ordem em que foram acrescentadas):</p><table>${ext.map(([k,v])=>`<tr><td>${esc(k)}</td><td>${v.length}</td><td class="muted">${v.map(x=>esc(String(x).replace(/^1\.\d+:\s*/,''))).join(' · ')}</td></tr>`).join('')}</table></details>`)},'Sobre: estrutura da interface');
buildToolbar();if(window.ribbonRender)window.ribbonRender();
